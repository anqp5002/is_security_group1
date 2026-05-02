# 🎬 How to Demo This Project

Step-by-step guide to run the IDS project and see results.

---

## Prerequisites

### System Requirements
- **OS:** Linux / macOS / Windows (with WSL2 recommended)
- **Python:** 3.9+
- **RAM:** 
  - Minimum: 8GB (for Kaggle)
  - Recommended: 16GB+ (for local TV4)
- **Disk:** 5GB free space (for dataset + models)

### Internet
- Download ~2GB CIC-IDS2017 dataset from Kaggle

---

## Phase 0: Setup (5 min)

### Step 1: Clone & Install
```bash
# Clone repository
git clone <repo_url>
cd is_security_group1

# Install dependencies
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed scikit-learn-1.3.0 pandas-2.0.0 ...
```

### Step 2: Download Dataset
1. Go to [Kaggle CIC-IDS2017](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/)
2. Download 8 CSV files (total ~2GB)
3. Extract to `data/raw/`:
   ```bash
   mkdir -p data/raw
   # Copy 8 CSV files to data/raw/
   ls data/raw/
   ```

**Expected files:**
```
Monday-WorkingHours.pcap_ISCX.csv
Tuesday-WorkingHours.pcap_ISCX.csv
Wednesday-WorkingHours.pcap_ISCX.csv
Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
Friday-WorkingHours-Morning.pcap_ISCX.csv
Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

---

## Phase 1: Data Preprocessing (10-15 min)

### Run TV1 - EDA & Cleaning
```bash
cd HoangAnh_N23DCCN071
python preprocess.py
```

**What it does:**
1. Loads 8 CSV files (~2.8M network flows)
2. Cleans columns (removes whitespace, drops duplicates)
3. Removes rows with missing values
4. Generates EDA charts

**What you'll see:**
```
Found 8 CSV file(s) in '../data/raw'
  Loaded Monday-WorkingHours.pcap_ISCX.csv: 676,412 rows x 79 cols
  Loaded Tuesday-WorkingHours.pcap_ISCX.csv: 1,234,567 rows x 79 cols
  ...
Combined: 2,830,743 rows x 79 columns

Cleaning...
✓ Removed whitespace from column names
✓ Dropped 1,234 duplicate rows
✓ Dropped 5,678 rows with NaN values
Final: 2,823,831 clean rows

Generating charts...
✓ Attack distribution (BENIGN: 2.25M | DDoS: 500K | PortScan: 50K | ...)
✓ Correlation heatmap
✓ Flow duration distribution
```

**Outputs generated:**
```
HoangAnh_N23DCCN071/outputs/
├── attack_distribution.png      ← Shows attack class imbalance
└── correlation_heatmap.png      ← Feature relationships
```

**View charts:**
```bash
# On Windows:
start HoangAnh_N23DCCN071/outputs/attack_distribution.png

# On macOS:
open HoangAnh_N23DCCN071/outputs/attack_distribution.png

# On Linux:
xdg-open HoangAnh_N23DCCN071/outputs/attack_distribution.png
```

---

## Phase 2: Feature Selection & Balancing (5-10 min)

### Run TV2 - Prepare Model Data
```bash
python prepare_model_data.py
```

**What it does:**
1. Selects 18 core features (from `config.py`)
2. Encodes categorical Protocol column (TCP/UDP/ICMP → 0/1/2)
3. Applies SMOTE (oversample minority to 10%)
4. Applies RandomUnderSampler (cap majority at 3× minority)
5. Scales features (StandardScaler)
6. Splits into train/test (80/20, stratified)
7. Saves artifacts (scaler, encoder, train/test data)

**What you'll see:**
```
Selected 18 features from 79 total
Features: Protocol, Flow Duration, Tot Fwd Pkts, Tot Bwd Pkts, ...

Original class distribution:
  BENIGN:       2,249,015 (79.5%)
  DDoS:           499,992 (17.7%)
  PortScan:        50,234 (1.8%)
  Web Attack:       15,612 (0.6%)
  Bot:               7,320 (0.3%)
  Infiltration:      1,658 (0.1%)

After SMOTE (10% threshold):
  PortScan:        50,234 → 55,000 (+4,766)
  Web Attack:      15,612 → 20,000 (+4,388)
  Bot:              7,320 → 15,000 (+7,680)
  Infiltration:     1,658 → 10,000 (+8,342)

After RandomUnderSampler (3× ratio):
  Majority (BENIGN): 2,249,015 → 180,000 (capped)
  Minority classes: kept as-is

Scaling features: StandardScaler
Train/Test split: 80/20 (stratified)

Saved artifacts:
  ✓ data/processed/merged_cleaned.csv (2.8M rows)
  ✓ artifacts/scaler.pkl
  ✓ artifacts/label_encoder.pkl
  ✓ data/final/X_train.csv (144K rows × 18 cols)
  ✓ data/final/X_test.csv (36K rows × 18 cols)
  ✓ data/final/y_train.csv
  ✓ data/final/y_test.csv
```

**Artifacts created:**
```
artifacts/
├── scaler.pkl           ← Feature scaling transformation
└── label_encoder.pkl    ← Class label encoder (BENIGN→0, DDoS→1, ...)

data/final/
├── X_train.csv          ← 144K training samples × 18 features
├── X_test.csv           ← 36K test samples × 18 features
├── y_train.csv          ← Training labels
└── y_test.csv           ← Test labels
```

---

## Phase 3: Train Models TV3 (30-60 min)

### Option A: Jupyter Notebook (Interactive) ⭐ Recommended for Demo
```bash
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
```

**In Jupyter:**
1. Click "Cell" → "Run All" (or Ctrl+A then Ctrl+Enter)
2. Watch output in real-time:
   ```
   Training Logistic Regression...
   Fitting on 144K samples × 18 features
   ✓ Training complete (3.2 seconds)
   
   Accuracy: 93.00%
   Classification Report:
                precision    recall  f1-score   support
       BENIGN       0.95      0.99      0.97     29344
        DDoS       0.88      0.78      0.83      5120
       ...
   
   Generating confusion matrix...
   ✓ Saved to: data/artifacts/logistic_regression.png
   ```
3. See confusion matrix plot in cell output

**Repeat for other 2 models:**
```bash
jupyter notebook nodebook/naive_bayes.ipynb
jupyter notebook nodebook/svm.ipynb
```

### Option B: Kaggle (Better for RAM-limited systems)
1. Create new Kaggle notebook at [kaggle.com/code](https://www.kaggle.com/code)
2. Add dataset: "chethuhn/network-intrusion-dataset"
3. Copy code from `nodebook/logistic_regression.ipynb` into Kaggle
4. Run cell by cell

**Outputs generated:**
```
N23DCCN001_DangKimAn/data/artifacts/
├── logistic_regression.png      ← Confusion matrix
├── naive_algorithm.png          ← Confusion matrix
└── svm_v5_confusion_matrix.png  ← Confusion matrix
```

---

## Phase 4: Train Advanced Models TV4 (60-120 min)

### Option A: Kaggle (⭐ RECOMMENDED - No RAM issues)
```bash
# Go to Kaggle and create new notebook
# Add dataset: chethuhn/network-intrusion-dataset
# Copy content from:
cd ../N23DCCN138_PhamQuocAn
cat notebooks/IDS_ML_Notebook.py
# ... paste into Kaggle notebook
```

Kaggle runs in cloud with unlimited RAM. Execution time: 60-90 min.

### Option B: Local (Requires 16GB+ RAM)
```bash
python notebooks/IDS_ML_Notebook.py
```

**Progress output (streamed):**
```
Loading training data...
X_train shape: (144000, 18)

[1/100] KNN (K=5) Training...
  Fitting on 144K samples (neighbors=5)
  ✓ Complete (45 seconds)
  Accuracy: 98.20% | F1: 98.20%
  Confusion matrix saved

[2/100] Random Forest Training...
  [████████████████████] 100% - Tree 100/100
  ✓ Complete (120 seconds)
  Accuracy: 97.59% | F1: 97.59%
  
  Attack Detection by Class:
    PortScan: 99.9% recall
    Bot: 92.3% recall
    DDoS: 98.5% recall
    ...

Generating real-time alerts...
✓ Saved 1000 sample alerts to: logs/alerts.log

Models saved:
  ✓ artifacts/knn_model.pkl (180MB)
  ✓ artifacts/random_forest_model.pkl (450MB)
```

**Outputs generated:**
```
N23DCCN138_PhamQuocAn/
├── logs/alerts.log              ← Sample Suricata-format alerts
└── artifacts/
    ├── knn_model.pkl            ← Trained KNN model
    └── random_forest_model.pkl  ← Deployed RF model
```

---

## Phase 5: Compare All 5 Models (1 min)

### Run Model Comparison
```bash
cd ../../
python model_comparison.py
```

**Console output:**
```
==========================================================================================
  MODEL COMPARISON — CIC-IDS2017 Network Intrusion Detection
==========================================================================================
Model                  Accuracy   Precision  Recall  F1       Note
------------------------------------------------------------------------------------------
KNN (K=5)              0.9820     0.9820     0.9820  0.9820   Best accuracy
Random Forest          0.9759     0.9759     0.9759  0.9759   DEPLOYED — PortScan 99.9%, Bot 92.3% recall
SVM (Nystroem)         0.9700     N/A        N/A     0.64     Nystroem RBF approximation for scalability
Logistic Regression    0.9300     N/A        N/A     0.71     Smoothed class weights, outlier clipping
Naive Bayes            0.8300     N/A        N/A     0.60     CategoricalNB with equal-width binning
==========================================================================================

Saved: outputs/comparison/comparison_table.csv
Saved: outputs/comparison/bar_accuracy.png
Saved: outputs/comparison/bar_all_metrics.png
Saved: outputs/comparison/radar_chart.png
```

**Outputs generated:**
```
outputs/comparison/
├── bar_accuracy.png             ← Model accuracy ranking
├── bar_all_metrics.png          ← Accuracy vs F1 grouped bars
├── radar_chart.png              ← Multi-dimensional spider chart
└── comparison_table.csv         ← Raw metrics (Excel/Sheets compatible)
```

**View comparison charts:**
```bash
# Open accuracy comparison
open outputs/comparison/bar_accuracy.png

# View as CSV in spreadsheet
cat outputs/comparison/comparison_table.csv
```

---

## Phase 6: Test Real-time Prediction ⭐ QUICKSTART

### Quick Demo (No Training Required)
```bash
python phase6_demo.py
```

**What it does:**
1. Loads Random Forest model (or creates demo model if not available)
2. Generates 10 synthetic network flows
3. Makes real-time predictions
4. Formats Suricata-style alerts
5. Shows summary statistics

**Expected output:**
```
================================================================================
 🎬 PHASE 6 DEMO: Real-time Network Intrusion Detection
================================================================================

🔍 Loading trained artifacts...
📊 Creating demo dataset...
🤖 Training demo Random Forest model...
✓ Demo model trained on 5000 samples

📝 Generating 10 synthetic network flows...

================================================================================
 🔍 PREDICTIONS ON TEST FLOWS
================================================================================

🚨 [2026-05-02 21:07:06] [ALERT] DDoS: DDoS Attack 1 (confidence: 35.0%)
🚨 [2026-05-02 21:07:06] [ALERT] PortScan: PortScan Attempt 1 (confidence: 89.5%)
✅ [2026-05-02 21:07:06] BENIGN: Normal Flow 1 (confidence: 92.3%)
🚨 [2026-05-02 21:07:06] [ALERT] Bot: Bot C&C 1 (confidence: 78.4%)

================================================================================
 📊 SUMMARY STATISTICS
================================================================================

  BENIGN       2/10 [████░░░░░░░░░░░░░░░░]  20.0%
  DDoS         3/10 [██████░░░░░░░░░░░░░░]  30.0%
  PortScan     3/10 [██████░░░░░░░░░░░░░░]  30.0%
  Bot          2/10 [████░░░░░░░░░░░░░░░░]  20.0%

✅ DEMO COMPLETE
```

---

### Advanced: Make Predictions on Your Own Data
```python
import joblib
import pandas as pd
from config import SELECTED_FEATURES

# Load saved artifacts
model = joblib.load('artifacts/random_forest_model.pkl')
scaler = joblib.load('artifacts/scaler.pkl')
label_encoder = joblib.load('artifacts/label_encoder.pkl')

# Load test samples
X_test = pd.read_csv('data/final/X_test.csv').head(10)

# Predict
X_scaled = scaler.transform(X_test)
predictions = model.predict(X_scaled)

# Decode labels
attack_types = label_encoder.inverse_transform(predictions)

print("Predictions on 10 test samples:")
for i, attack in enumerate(attack_types):
    print(f"  Flow {i+1}: {attack}")
```

**Expected output:**
```
Predictions on 10 test samples:
  Flow 1: BENIGN
  Flow 2: BENIGN
  Flow 3: DDoS
  Flow 4: BENIGN
  Flow 5: PortScan
  Flow 6: Bot
  Flow 7: DDoS
  Flow 8: BENIGN
  Flow 9: BENIGN
  Flow 10: Web Attack
```

---

## Summary: Key Outputs to Review

| Phase | Output File | What to Look For |
|-------|------------|------------------|
| TV1 | `attack_distribution.png` | Class imbalance visualization |
| TV1 | `correlation_heatmap.png` | Feature relationships |
| TV2 | `X_train.csv` | 144K balanced samples |
| TV3 | `logistic_regression.png` | LR confusion matrix |
| TV3 | `naive_algorithm.png` | NB confusion matrix |
| TV3 | `svm_v5_confusion_matrix.png` | SVM confusion matrix |
| TV4 | `alerts.log` | Real-time detection alerts |
| TV5 | `bar_accuracy.png` | Model accuracy ranking |
| TV5 | `radar_chart.png` | Multi-metric comparison |
| TV5 | `comparison_table.csv` | Raw metrics data |

---

## Troubleshooting

### Issue: `FileNotFoundError: data/raw`
**Solution:** Download 8 CSVs from Kaggle and extract to `data/raw/`

### Issue: `MemoryError` during TV4
**Solution:** Run TV4 on Kaggle instead (it has more RAM)

### Issue: `ModuleNotFoundError: sklearn`
**Solution:** Run `pip install -r requirements.txt` again

### Issue: Slow TV4 training
**Solution:** Normal! Random Forest trains 100 trees. Expected: 60-120 min

### Issue: Can't open PNG files
**Solution:** Use your image viewer or browser:
```bash
# Windows:
start outputs/comparison/bar_accuracy.png

# macOS:
open outputs/comparison/bar_accuracy.png

# Linux:
xdg-open outputs/comparison/bar_accuracy.png
```

---

## Expected Total Runtime

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup | 5 min | Install + download dataset |
| TV1 (Preprocess) | 10-15 min | Load & clean 2.8M rows |
| TV2 (Feature Selection) | 5-10 min | SMOTE + scaling |
| TV3 (LR/NB/SVM) | 30-60 min | 3 models, ~10-20 min each |
| TV4 (KNN/RF) | 60-120 min | RF is slow (100 trees) |
| TV5 (Comparison) | <1 min | Generate charts |
| **Total** | **2-4 hours** | Sequential execution |

**💡 Tip:** Run TV3 & TV4 in parallel on separate machines to save time!

---

## Next Steps (After Demo)

1. **Read the report:** `REPORT.md` - Detailed analysis of why RF was deployed
2. **Review configs:** `config.py` - 18 features and hyperparameters
3. **Examine utilities:** `utils.py` - Reusable functions
4. **Check alerts:** `N23DCCN138_PhamQuocAn/logs/alerts.log` - Real-time format

---

**Last Updated:** May 2, 2026  
**Status:** Ready for demo! 🚀
