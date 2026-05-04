"""
phase6_demo.py - Demo Phase 6: Real-time Prediction on All 5 Models

This script demonstrates:
1. Loading pre-trained models (all 5) from demo/ folder
2. Making predictions on network flows with all models
3. Comparing predictions across models
4. Formatting Suricata-style alerts

Trained models are stored as .pkl files in demo/ folder:

  MODELS (trained on 18 features):
    - logistic_regression_model.pkl  (TV3 - Logistic Regression)
    - naive_bayes_model.pkl           (TV3 - Naive Bayes)
    - svm_model.pkl                   (TV3 - SVM with Nystroem)
    - knn_model.pkl                   (TV4 - KNN with K=5)
    - random_forest_model.pkl         (TV4 - Random Forest, DEPLOYED)

  SHARED PREPROCESSING (used by all models):
    - scaler.pkl                      (Feature StandardScaler - scales 18 features to [-1, 1])
    - label_encoder.pkl               (Converts text labels ↔ numbers: BENIGN↔0, DDoS↔1, etc.)

If trained models don't exist in demo/ folder, creates quick demo models for testing.

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

# Fix encoding for Windows terminal
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 17 core features used across all models
SELECTED_FEATURES = [
    "Flow Duration", "Tot Fwd Pkts", "Tot Bwd Pkts",
    "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Fwd Pkt Len Mean", "Bwd Pkt Len Mean",
    "Flow Byts/s", "Flow Pkts/s", "Pkt Len Mean", "Pkt Len Std",
    "SYN Flag Cnt", "ACK Flag Cnt", "FIN Flag Cnt", "RST Flag Cnt", "PSH Flag Cnt", "URG Flag Cnt"
]

DEMO_DIR = "demo"

# 5 Models to load
MODEL_CONFIGS = {
    "logistic_regression": {
        "file": "logistic_ids_model.pkl",
        "name": "Logistic Regression",
        "accuracy": 93.0
    },
    "naive_bayes": {
        "file": "categorical_nb_model.pkl",
        "name": "Naive Bayes",
        "accuracy": 83.0
    },
    "svm": {
        "file": "svm_final_v5_model.pkl",
        "name": "SVM (Nystroem)",
        "accuracy": 97.0
    },
    "knn": {
        "file": "knn_model.pkl",
        "name": "KNN (K=5)",
        "accuracy": 98.2
    },
    "random_forest": {
        "file": "random_forest_model-002.pkl",
        "name": "Random Forest (DEPLOYED)",
        "accuracy": 97.59
    }
}

# ============================================================================
# Step 1: Load All 5 Models & Artifacts
# ============================================================================

def load_all_models():
    """
    Load all 5 trained models + shared preprocessing artifacts from demo folder.

    Each model file (.pkl) contains a trained classifier.
    Shared artifacts:
      - scaler.pkl: StandardScaler that normalizes 18 features to ~[-1, 1]
        (trained on the entire dataset, used by all 5 models)
      - label_encoder.pkl: Maps text labels ↔ numeric indices
        (BENIGN↔0, DDoS↔1, PortScan↔2, Bot↔3, Web Attack↔4, Infiltration↔5)
    """

    models = {}
    scaler_path = os.path.join(DEMO_DIR, "scaler.pkl")
    encoder_path = os.path.join(DEMO_DIR, "label_encoder.pkl")

    print("🔍 Loading trained models from demo/ folder...")
    print()

    loaded_count = 0
    missing_count = 0

    # Load each model
    for model_key, config in MODEL_CONFIGS.items():
        model_path = os.path.join(DEMO_DIR, config["file"])

        try:
            model = joblib.load(model_path)
            models[model_key] = model
            print(f"  ✓ {config['name']:30} ({config['accuracy']:.2f}% accuracy) loaded")
            loaded_count += 1
        except FileNotFoundError:
            print(f"  ✗ {config['name']:30} NOT FOUND")
            missing_count += 1

    print()

    # Load shared artifacts
    try:
        scaler = joblib.load(scaler_path)
        label_encoder = joblib.load(encoder_path)
        print(f"✓ Scaler loaded: {scaler_path}")
        print(f"✓ Label encoder loaded: {encoder_path}")
        print(f"✓ Classes: {list(label_encoder.classes_)}\n")
    except FileNotFoundError as e:
        print(f"⚠️  Artifacts not found: {e}")
        print("    Creating demo artifacts...\n")
        return None, None, None

    if loaded_count < 5:
        print(f"⚠️  Only {loaded_count}/5 models loaded. Creating demo models for missing ones...\n")
        models, scaler, label_encoder = create_demo_models(models, scaler, label_encoder)

    return models, scaler, label_encoder


def create_demo_models(partial_models=None, scaler=None, label_encoder=None):
    """Create quick demo models if real ones don't exist"""
    from sklearn.linear_model import LogisticRegression
    from sklearn.naive_bayes import GaussianNB
    from sklearn.svm import SVC
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler, LabelEncoder

    print("📊 Creating demo dataset...")

    # Generate synthetic network flow data
    np.random.seed(42)
    n_samples = 5000

    X_demo = np.random.rand(n_samples, 17) * 100

    # Labels: 70% BENIGN, 15% DDoS, 10% PortScan, 5% Bot
    y_demo = np.random.choice(
        [0, 1, 2, 3],  # [BENIGN, DDoS, PortScan, Bot]
        size=n_samples,
        p=[0.70, 0.15, 0.10, 0.05]
    )

    # Train all 5 models
    print("🤖 Training demo models...\n")

    models = partial_models if partial_models else {}

    if "logistic_regression" not in models:
        print("  Training: Logistic Regression...")
        models["logistic_regression"] = LogisticRegression(max_iter=1000, random_state=42)
        models["logistic_regression"].fit(X_demo, y_demo)

    if "naive_bayes" not in models:
        print("  Training: Naive Bayes...")
        models["naive_bayes"] = GaussianNB()
        models["naive_bayes"].fit(X_demo, y_demo)

    if "svm" not in models:
        print("  Training: SVM...")
        models["svm"] = SVC(kernel='rbf', probability=True, random_state=42)
        models["svm"].fit(X_demo, y_demo)

    if "knn" not in models:
        print("  Training: KNN (K=5)...")
        models["knn"] = KNeighborsClassifier(n_neighbors=5)
        models["knn"].fit(X_demo, y_demo)

    if "random_forest" not in models:
        print("  Training: Random Forest...")
        models["random_forest"] = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        models["random_forest"].fit(X_demo, y_demo)

    # Create shared artifacts
    if scaler is None:
        print("  Creating: StandardScaler...")
        scaler = StandardScaler()
        scaler.fit(X_demo)

    if label_encoder is None:
        print("  Creating: LabelEncoder...")
        label_encoder = LabelEncoder()
        label_encoder.fit(["BENIGN", "DDoS", "PortScan", "Bot"])

    print(f"\n✓ Demo models trained on {n_samples} samples")
    print(f"✓ Features: 17")
    print(f"✓ Classes: {list(label_encoder.classes_)}\n")

    return models, scaler, label_encoder


# ============================================================================
# Step 2: Generate Test Data
# ============================================================================

def generate_test_flows(scaler, label_encoder, n_samples=10):
    """Lấy dữ liệu thực tế từ tập X_test.csv đã được chia tỷ lệ (scaled) thay vì sinh ra fake data."""
    flows = []
    
    print(f"📝 Lấy ngẫu nhiên {n_samples} luồng trích xuất từ dữ liệu thật...\n")
    
    try:
        # Tải dữ liệu thực tế từ file đã lưu
        X_df = pd.read_csv('HoangAnh_N23DCCN071/data/X_test.csv')
        y_df = pd.read_csv('HoangAnh_N23DCCN071/data/y_test.csv')
        
        np.random.seed(42)
        random_indices = np.random.choice(len(X_df), size=n_samples, replace=False)
        
        for i, idx in enumerate(random_indices):
            scaled_vals = X_df.iloc[idx].values
            
            # Vì phase6_demo.py sẽ thực hiện scaler.transform lại (cho đúng cấu trúc pipeline real-time), 
            # chúng ta phải "unscale" về lại dạng RAW ban đầu để các model tuyến tính không bị quá nhỏ.
            raw_vals = scaler.inverse_transform([scaled_vals])[0]
            
            true_label_idx = y_df.iloc[idx].values[0]
            true_label = label_encoder.inverse_transform([true_label_idx])[0]
            
            flows.append((f"Real Flow {i+1} (Truth: {true_label})", raw_vals))
            
    except Exception as e:
        print(f"Lỗi khi load dữ liệu thực: {e}")
        
    return flows


# ============================================================================
# Step 3: Make Predictions with All 5 Models
# ============================================================================

def predict_flow_all_models(models, scaler, label_encoder, flow_data):
    """Predict attack type using all 5 models and return consensus"""

    # Scale features
    X_scaled = scaler.transform([flow_data])

    predictions = {}
    confidences = {}
    all_probs = {}

    # Get predictions from each model
    for model_key, model in models.items():
        try:
            prediction = model.predict(X_scaled)[0]
            attack_type = label_encoder.classes_[prediction]

            # Try to get probabilities (not all models support this)
            try:
                probabilities = model.predict_proba(X_scaled)[0]
                confidence = probabilities[prediction] * 100
            except (AttributeError, IndexError):
                # For models that don't support predict_proba
                confidence = 100.0
                probabilities = np.zeros(len(label_encoder.classes_))

            predictions[model_key] = attack_type
            confidences[model_key] = confidence
            all_probs[model_key] = probabilities
        except Exception as e:
            predictions[model_key] = "ERROR"
            confidences[model_key] = 0.0
            all_probs[model_key] = []

    # Get consensus prediction (most common)
    from collections import Counter
    valid_preds = [p for p in predictions.values() if p != "ERROR"]
    if valid_preds:
        consensus = Counter(valid_preds).most_common(1)[0][0]
    else:
        consensus = "UNKNOWN"

    return predictions, confidences, all_probs, consensus


def format_model_predictions(model_name, attack_type, confidence):
    """Format prediction from a single model"""
    if attack_type == "BENIGN":
        return f"    {model_name:30} → {attack_type:12} ({confidence:6.1f}%)"
    else:
        return f"    {model_name:30} → {attack_type:12} ({confidence:6.1f}%) ⚠️"


def format_alert(consensus, flow_name, predictions_summary):
    """Format Suricata-style alert with consensus"""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if consensus == "BENIGN":
        # Green checkmark for benign
        return f"✅ [{timestamp}] BENIGN: {flow_name}\n{predictions_summary}"
    else:
        # Red alert for attacks
        return f"🚨 [{timestamp}] [ALERT] {consensus.upper()}: {flow_name}\n{predictions_summary}"


# ============================================================================
# Step 4: Main Demo
# ============================================================================

def main():
    """Run the Phase 6 demo with all 5 models"""

    print("=" * 100)
    print(" 🎬 PHASE 6 DEMO: Real-time Network Intrusion Detection (All 5 Models)")
    print("=" * 100)
    print()

    # Load all 5 models
    models, scaler, label_encoder = load_all_models()

    if models is None:
        print("❌ Failed to load models. Exiting.")
        return

    # Generate test flows
    test_flows = generate_test_flows(scaler, label_encoder)

    # Make predictions
    print("=" * 100)
    print(" 🔍 PREDICTIONS ON TEST FLOWS (All 5 Models)")
    print("=" * 100)
    print()

    results = []
    for flow_name, flow_data in test_flows:
        predictions, confidences, all_probs, consensus = predict_flow_all_models(
            models, scaler, label_encoder, flow_data
        )

        # Build detailed prediction summary
        pred_lines = []
        for model_key in sorted(predictions.keys()):
            model_name = MODEL_CONFIGS[model_key]["name"]
            attack_type = predictions[model_key]
            confidence = confidences[model_key]
            pred_lines.append(format_model_predictions(model_name, attack_type, confidence))

        predictions_summary = "\n".join(pred_lines)
        alert = format_alert(consensus, flow_name, predictions_summary)

        print(alert)
        print()

        # Store for statistics
        results.append({
            "Flow": flow_name,
            "Consensus": consensus,
            "Predictions": predictions,
            "Confidences": confidences
        })

    # Statistics by consensus
    print("=" * 100)
    print(" 📊 SUMMARY STATISTICS (CONSENSUS PREDICTIONS)")
    print("=" * 100)
    print()

    consensus_counts = {}
    for result in results:
        consensus = result["Consensus"]
        consensus_counts[consensus] = consensus_counts.get(consensus, 0) + 1

    total = len(results)
    for attack_type, count in sorted(consensus_counts.items()):
        pct = (count / total) * 100
        bar = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
        print(f"  {attack_type:12} {count:2}/{total} [{bar}] {pct:5.1f}%")

    # Per-model accuracy comparison
    print()
    print("=" * 100)
    print(" 📊 MODEL ACCURACY COMPARISON ON TEST SET")
    print("=" * 100)
    print()

    for model_key in sorted(models.keys()):
        model_name = MODEL_CONFIGS[model_key]["name"]
        model_acc = MODEL_CONFIGS[model_key]["accuracy"]
        agreement_count = sum(1 for r in results if r["Predictions"][model_key] == r["Consensus"])
        agreement_pct = (agreement_count / total) * 100

        print(f"  {model_name:30} Training Accuracy: {model_acc:6.2f}%  |  Agreement with Consensus: {agreement_pct:5.1f}%")

    print()
    print("=" * 100)
    print(" ✅ DEMO COMPLETE")
    print("=" * 100)
    print()
    print("💡 What just happened:")
    print("  1. Loaded all 5 ML models from demo/ folder")
    print("  2. Lấy dữ liệu 10 luồng thật chưa scale từ thư mục của HoangAnh")
    print("  3. Scaled features using trained scaler")
    print("  4. Made predictions with all 5 models")
    print("  5. Determined consensus prediction (most common vote)")
    print("  6. Formatted alerts in Suricata format")
    print()
    print("🚀 Next steps:")
    print("  - Review REPORT.md for detailed model analysis")
    print("  - Check GUIDE.md for full training pipeline")
    print("  - Run: python model_comparison.py (to compare models with actual metrics)")
    print("  - Download pre-trained models from Google Drive if you need real results")
    print()


if __name__ == "__main__":
    main()
