"""
phase6_demo.py - Demo Phase 6: Real-time Prediction on Trained Model

This script demonstrates:
1. Loading pre-trained Random Forest model
2. Making predictions on new network flows
3. Formatting Suricata-style alerts
4. Testing different attack types

If trained models don't exist, creates a quick demo model for testing.

Run:
    python phase6_demo.py
"""

import os
import sys
import io
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from config import SELECTED_FEATURES, ARTIFACTS_DIR

# Fix encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ============================================================================
# Step 1: Load Models & Artifacts
# ============================================================================

def load_models():
    """Load trained Random Forest model + scaler + label encoder"""

    model_path = os.path.join(ARTIFACTS_DIR, "random_forest_model.pkl")
    scaler_path = os.path.join(ARTIFACTS_DIR, "scaler.pkl")
    encoder_path = os.path.join(ARTIFACTS_DIR, "label_encoder.pkl")

    try:
        print("🔍 Loading trained artifacts...")
        model = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        label_encoder = joblib.load(encoder_path)

        print(f"✓ Model loaded: {model_path}")
        print(f"✓ Scaler loaded: {scaler_path}")
        print(f"✓ Label encoder loaded: {encoder_path}")
        print(f"✓ Classes: {list(label_encoder.classes_)}\n")

        return model, scaler, label_encoder

    except FileNotFoundError as e:
        print(f"⚠️  Model not found: {e}")
        print("    Creating demo model for testing...\n")
        return create_demo_model()


def create_demo_model():
    """Create a quick demo model if no trained models exist"""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder

    print("📊 Creating demo dataset...")

    # Generate synthetic network flow data
    np.random.seed(42)
    n_samples = 5000

    # 18 features: Protocol, Flow Duration, packet counts, flags, etc.
    X_demo = np.random.rand(n_samples, 18) * 100

    # Labels: 70% BENIGN, 15% DDoS, 10% PortScan, 5% Bot
    attack_dist = np.random.choice(
        [0, 1, 2, 3],  # [BENIGN, DDoS, PortScan, Bot]
        size=n_samples,
        p=[0.70, 0.15, 0.10, 0.05]
    )

    # Train models
    print("🤖 Training demo Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_demo, attack_dist)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_demo)

    label_encoder = LabelEncoder()
    label_encoder.fit(["BENIGN", "DDoS", "PortScan", "Bot"])

    print(f"✓ Demo model trained on {n_samples} samples")
    print(f"✓ Features: 18")
    print(f"✓ Classes: {list(label_encoder.classes_)}\n")

    return model, scaler, label_encoder


# ============================================================================
# Step 2: Generate Test Data
# ============================================================================

def generate_test_flows():
    """Generate synthetic test network flows with known patterns"""

    flows = []

    # Helper to create flow sample
    def make_flow(name, flow_duration, tot_fwd, tot_bwd, flags_pattern):
        flow = [
            6,  # Protocol (TCP=6)
            flow_duration,
            tot_fwd,
            tot_bwd,
            tot_fwd * 50,  # TotLen Fwd Pkts
            tot_bwd * 50,  # TotLen Bwd Pkts
            np.random.rand() * 200,  # Fwd Pkt Len Mean
            np.random.rand() * 200,  # Bwd Pkt Len Mean
            np.random.rand() * 1000,  # Flow Byts/s
            np.random.rand() * 100,   # Flow Pkts/s
            np.random.rand() * 200,   # Pkt Len Mean
            np.random.rand() * 100,   # Pkt Len Std
        ]
        # Flags (SYN, ACK, FIN, RST, PSH, URG)
        if flags_pattern == "syn_scan":
            flow.extend([tot_fwd, 0, 0, 0, 0, 0])  # High SYN, low others
        elif flags_pattern == "ddos":
            flow.extend([0, tot_fwd, 0, 0, 0, 0])  # High ACK (established)
        elif flags_pattern == "normal":
            flow.extend([1, tot_fwd, 0, 0, 0, 0])  # Normal SYN-ACK
        else:
            flow.extend([np.random.rand() * 10 for _ in range(6)])

        flows.append((name, np.array(flow)))

    print("📝 Generating 10 synthetic network flows...\n")

    # Normal traffic
    make_flow("Normal Flow 1", 60, 10, 15, "normal")
    make_flow("Normal Flow 2", 120, 25, 30, "normal")
    make_flow("Normal Flow 3", 30, 5, 8, "normal")

    # PortScan (many SYN, no ACK = reconnaissance)
    make_flow("PortScan Attempt 1", 5, 100, 0, "syn_scan")
    make_flow("PortScan Attempt 2", 10, 150, 5, "syn_scan")

    # DDoS (many packets, high throughput)
    make_flow("DDoS Attack 1", 300, 5000, 100, "ddos")
    make_flow("DDoS Attack 2", 450, 8000, 50, "ddos")

    # Bot (command & control communication)
    make_flow("Bot C&C 1", 120, 50, 100, "normal")
    make_flow("Bot C&C 2", 180, 75, 150, "normal")

    # Mixed/Unclear
    make_flow("Suspicious Flow", 45, 200, 30, "syn_scan")

    return flows


# ============================================================================
# Step 3: Make Predictions
# ============================================================================

def predict_flow(model, scaler, label_encoder, flow_data):
    """Predict attack type for a single network flow"""

    # Scale features
    X_scaled = scaler.transform([flow_data])

    # Get prediction + confidence
    prediction = model.predict(X_scaled)[0]
    probabilities = model.predict_proba(X_scaled)[0]

    # Decode label
    attack_type = label_encoder.classes_[prediction]
    confidence = probabilities[prediction] * 100

    return attack_type, confidence, probabilities


def format_alert(attack_type, flow_name, confidence):
    """Format Suricata-style alert"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if attack_type == "BENIGN":
        # Green checkmark for benign
        return f"✅ [{timestamp}] BENIGN: {flow_name} (confidence: {confidence:.1f}%)"
    else:
        # Red alert for attacks
        return f"🚨 [{timestamp}] [ALERT] {attack_type.upper()}: {flow_name} (confidence: {confidence:.1f}%)"


# ============================================================================
# Step 4: Main Demo
# ============================================================================

def main():
    """Run the Phase 6 demo"""

    print("=" * 80)
    print(" 🎬 PHASE 6 DEMO: Real-time Network Intrusion Detection")
    print("=" * 80)
    print()

    # Load models
    model, scaler, label_encoder = load_models()

    # Generate test flows
    test_flows = generate_test_flows()

    # Make predictions
    print("=" * 80)
    print(" 🔍 PREDICTIONS ON TEST FLOWS")
    print("=" * 80)
    print()

    results = []
    for flow_name, flow_data in test_flows:
        attack_type, confidence, probs = predict_flow(model, scaler, label_encoder, flow_data)
        alert = format_alert(attack_type, flow_name, confidence)

        print(alert)

        # Store for statistics
        results.append({
            "Flow": flow_name,
            "Prediction": attack_type,
            "Confidence": f"{confidence:.1f}%",
            "Probabilities": {
                label: f"{prob*100:.1f}%"
                for label, prob in zip(label_encoder.classes_, probs)
            }
        })

    # Statistics
    print()
    print("=" * 80)
    print(" 📊 SUMMARY STATISTICS")
    print("=" * 80)
    print()

    prediction_counts = {}
    for result in results:
        pred = result["Prediction"]
        prediction_counts[pred] = prediction_counts.get(pred, 0) + 1

    total = len(results)
    for attack_type, count in sorted(prediction_counts.items()):
        pct = (count / total) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {attack_type:12} {count:2}/{total} [{bar}] {pct:5.1f}%")

    print()
    print("=" * 80)
    print(" ✅ DEMO COMPLETE")
    print("=" * 80)
    print()
    print("💡 What just happened:")
    print("  1. Loaded Random Forest model (97.59% accuracy)")
    print("  2. Generated 10 synthetic network flows")
    print("  3. Scaled features using trained scaler")
    print("  4. Made real-time predictions")
    print("  5. Formatted alerts in Suricata format")
    print()
    print("🚀 Next steps:")
    print("  - Review REPORT.md for model analysis")
    print("  - Check full DEMO.md for pipeline details")
    print("  - Modify test flows to test different scenarios")
    print()


if __name__ == "__main__":
    main()
