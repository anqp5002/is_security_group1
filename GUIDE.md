# 📖 Complete Project Guide

**Real-time Network Intrusion Detection System using Machine Learning**

---

## 📑 Table of Contents

1. [Quick Start (5 min)](#quick-start)
2. [Project Overview](#project-overview)
3. [File Structure & What Each File Does](#file-structure)
4. [How to Run (Step by Step)](#how-to-run)
5. [Model Comparison & Results](#model-comparison)
6. [Config & Utils Explanation](#config--utils)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### For Impatient People (Demo in 1 minute)
```bash
# Install dependencies
pip install -r requirements.txt

# Run instant demo (creates synthetic data if models don't exist)
python phase6_demo.py
```

**Output:** Real-time predictions on network flows with Suricata-format alerts

### For Full Understanding (2-4 hours)
```bash
# Download dataset from Kaggle (~2GB)
mkdir -p data/raw
# Extract 8 CSV files to data/raw/

# TV1: Data Preprocessing (10-15 min)
cd HoangAnh_N23DCCN071
python preprocess.py

# TV2: Feature Selection (5-10 min)
python prepare_model_data.py

# TV3: Train 3 Models (30-60 min)
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
jupyter notebook nodebook/naive_bayes.ipynb
jupyter notebook nodebook/svm.ipynb

# TV4: Train Advanced Models (60-120 min) - Use Kaggle recommended
cd ../N23DCCN138_PhamQuocAn
python notebooks/IDS_ML_Notebook.py

# TV5: Compare All Models (1 min)
cd ../
python model_comparison.py
```

---

## Project Overview

### What This Project Does

Trains 5 ML models on **CIC-IDS2017** network intrusion dataset:
1. **Logistic Regression** - Baseline (93% accuracy)
2. **Naive Bayes** - Simple classifier (83% accuracy)
3. **SVM (Nystroem)** - Scalable kernel method (97% accuracy)
4. **KNN (K=5)** - Nearest neighbors (98.20% accuracy)
5. **Random Forest** - **DEPLOYED** (97.59% accuracy, best attack detection)

### Why Random Forest?

Despite KNN having **0.61% higher accuracy**, Random Forest was chosen for **production** because:

| Metric | KNN | Random Forest | Winner |
|--------|-----|---------------|--------|
| Overall Accuracy | 98.20% | 97.59% | KNN |
| **PortScan Recall** | 84.8% | **99.9%** | **RF** ✓ |
| **Bot Recall** | 62.4% | **92.3%** | **RF** ✓ |
| DDoS Recall | 98.1% | 98.5% | RF |

**Real impact:** RF detects **15% more reconnaissance** and **30% more botnets** → Better security

---

## File Structure

### Root Level Files

| File | Purpose | What It Contains |
|------|---------|------------------|
| **README.md** | Quick project overview | Links to this guide |
| **GUIDE.md** | This file - Complete documentation | Everything you need to know |
| **config.py** | Central configuration | 18 features, hyperparameters, paths |
| **utils.py** | Shared utility functions | load_data(), plot_confusion_matrix(), format_alert_log() |
| **requirements.txt** | Python dependencies | All packages needed |
| **model_comparison.py** | Model aggregation script | Compares 5 models, generates charts |
| **phase6_demo.py** | Real-time prediction demo | Demo predictions without training |

### Team Member Folders

| Folder | Team Member | TV (Task) | What It Does |
|--------|-------------|----------|--------------|
| **HoangAnh_N23DCCN071** | Hoàng Anh | TV1 + TV2 | Data preprocessing & feature selection |
| **N23DCCN001_DangKimAn** | Đặng Kim An | TV3 | Trains 3 models (LR, NB, SVM) |
| **N23DCCN138_PhamQuocAn** | Phạm Quốc An | TV4 | Trains 2 models (KNN, RF) + deployment |

---

## How to Run

### Phase 1: Data Preprocessing (TV1)
```bash
cd HoangAnh_N23DCCN071
python preprocess.py
```

**What it does:**
- Loads 8 CSV files (~2.8M network flows)
- Cleans column names, removes duplicates/NaN
- Generates EDA charts (attack distribution, correlation heatmap)

**Output:**
```
data/processed/merged_cleaned.csv  (2.8M rows × 79 columns)
outputs/attack_distribution.png
outputs/correlation_heatmap.png
```

---

### Phase 2: Feature Selection & Balancing (TV2)
```bash
python prepare_model_data.py
```

**What it does:**
- Selects **18 core features** (from config.py)
- Encodes Protocol column (TCP/UDP/ICMP)
- Applies SMOTE (oversample minorities to 10%)
- Applies RandomUnderSampler (cap majority at 3× minority)
- Standardizes features with StandardScaler
- Splits into train/test (80/20, stratified)

**Output:**
```
data/final/X_train.csv           (144K rows × 18 columns)
data/final/X_test.csv            (36K rows × 18 columns)
data/final/y_train.csv
data/final/y_test.csv
artifacts/scaler.pkl             ← Feature scaling
artifacts/label_encoder.pkl      ← Class encoding
```

---

### Phase 3: Train 3 Models (TV3)
```bash
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
```

**Option A: Jupyter (Interactive)**
- Click "Run All" or Ctrl+A then Ctrl+Enter
- See predictions & confusion matrices in real-time

**Option B: Kaggle (Recommended)**
- Create new Kaggle notebook
- Add dataset: chethuhn/network-intrusion-dataset
- Copy code from notebook & run

**Models trained:**
1. Logistic Regression (93% accuracy)
2. Naive Bayes (83% accuracy)
3. SVM with Nystroem (97% accuracy)

**Output:**
```
N23DCCN001_DangKimAn/data/artifacts/
├── logistic_regression.png
├── naive_algorithm.png
└── svm_v5_confusion_matrix.png
```

---

### Phase 4: Train Advanced Models (TV4)
```bash
cd ../N23DCCN138_PhamQuocAn
python notebooks/IDS_ML_Notebook.py
```

**Or on Kaggle (⭐ Recommended - more RAM):**
- Create new Kaggle notebook
- Copy code from `notebooks/IDS_ML_Notebook.py`
- Run

**Models trained:**
1. KNN (K=5) - 98.20% accuracy
2. Random Forest (100 trees) - 97.59% accuracy, **best attack detection**

**Output:**
```
artifacts/
├── knn_model.pkl
└── random_forest_model.pkl
logs/alerts.log  ← Sample Suricata-format alerts
```

---

### Phase 5: Compare All Models
```bash
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
Random Forest          0.9759     0.9759     0.9759  0.9759   DEPLOYED
SVM (Nystroem)         0.9700     N/A        N/A     0.64
Logistic Regression    0.9300     N/A        N/A     0.71
Naive Bayes            0.8300     N/A        N/A     0.60
==========================================================================================
```

**Output charts:**
```
outputs/comparison/
├── bar_accuracy.png              ← Model accuracy ranking
├── bar_all_metrics.png           ← Accuracy vs F1 grouped bars
├── radar_chart.png               ← Multi-dimensional spider chart
└── comparison_table.csv          ← Raw metrics
```

---

## Config & Utils

### ⚠️ Important: Understand the Architecture

**Current State:**
- ✅ config.py exists (18 features, hyperparameters, paths)
- ✅ utils.py exists (load_data, plot_confusion_matrix, format_alert_log)
- ❌ **Training scripts DON'T import them** (hardcoded values instead)

**Why?**
- Scripts written by different team members separately
- Notebooks developed independently
- Integration happened late in project

**Where they ARE used:**
- ✅ `phase6_demo.py` - Uses config.py and utils.py properly
- ✅ Documentation & future maintenance

### config.py Contents

```python
# 18 Core Features (must be identical across all models)
SELECTED_FEATURES = [
    "Protocol", "Flow Duration", "Tot Fwd Pkts", "Tot Bwd Pkts",
    "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Fwd Pkt Len Mean", 
    "Bwd Pkt Len Mean", "Flow Byts/s", "Flow Pkts/s", "Pkt Len Mean",
    "Pkt Len Std", "SYN Flag Cnt", "ACK Flag Cnt", "FIN Flag Cnt",
    "RST Flag Cnt", "PSH Flag Cnt", "URG Flag Cnt"
]

# Hyperparameters for all models
HYPERPARAMS = {
    "train_test_split": {"test_size": 0.2, "stratify": True},
    "smote": {"minority_threshold_pct": 0.10},
    "random_under_sampler": {"majority_ratio": 3},
    "random_forest": {"n_estimators": 100, "random_state": 42},
    ...
}
```

### utils.py Functions

```python
# Load & concat 8 CSV files
df = load_data("data/raw")

# Generate confusion matrix heatmap
cm = plot_confusion_matrix(
    y_true, y_pred, 
    class_names=["BENIGN", "DDoS", ...],
    save_path="outputs/cm.png"
)

# Format Suricata-style alert
alert = format_alert_log(
    label="DDoS",
    dst_port=80,
    dst_ip="10.0.0.1"
)
# Output: "[2026-05-02 14:35:22] [ALERT] DDoS. Destination Port: 80. Dst IP: 10.0.0.1."
```

---

## How to Use Trained Models

### Load and Predict
```python
import joblib
import pandas as pd
from config import SELECTED_FEATURES

# Load artifacts
model = joblib.load('artifacts/random_forest_model.pkl')
scaler = joblib.load('artifacts/scaler.pkl')
label_encoder = joblib.load('artifacts/label_encoder.pkl')

# Load test data
X_test = pd.read_csv('data/final/X_test.csv').head(10)

# Predict
X_scaled = scaler.transform(X_test)
predictions = model.predict(X_scaled)
attack_types = label_encoder.inverse_transform(predictions)

print("Predictions:")
for i, attack in enumerate(attack_types):
    print(f"  Flow {i+1}: {attack}")
```

### Run Phase 6 Demo (No Training Required)
```bash
python phase6_demo.py
```

---

## Model Comparison Summary

### Key Findings

**Overall Accuracy:** KNN wins (98.20% vs RF's 97.59%)

**But for Security:** Random Forest wins
- **PortScan detection:** RF 99.9% vs KNN 84.8% (+15.1%)
- **Bot detection:** RF 92.3% vs KNN 62.4% (+29.9%)
- **Annual impact:** RF prevents 52,000+ port scans & 6.5M+ bot flows vs KNN

### Model Details

| Model | Accuracy | Use Case | Recommendation |
|-------|----------|----------|-----------------|
| **Random Forest** | 97.59% | **Production IDS** | ⭐ **DEPLOY** |
| KNN | 98.20% | Research/Benchmarking | Consider accuracy |
| SVM | 97.00% | Scalability needed | Good alternative |
| Logistic Reg | 93.00% | Fast baseline | Baseline only |
| Naive Bayes | 83.00% | Quick filter | Not recommended |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `FileNotFoundError: data/raw` | Download 8 CSVs from Kaggle and extract to data/raw/ |
| `MemoryError` during TV4 | Run TV4 on Kaggle instead (cloud has more RAM) |
| `ModuleNotFoundError: sklearn` | Run `pip install -r requirements.txt` again |
| Script runs very slow | Jupyter notebooks on local machine are slow; use Kaggle |
| Can't open PNG files | Use image viewer or browser: `open outputs/comparison/bar_accuracy.png` |
| `KeyError: Feature name` | Some CSVs have different column names; config.FEATURE_ALT_NAMES handles this |

---

## Expected Runtime

| Phase | Duration | Notes |
|-------|----------|-------|
| Setup | 5 min | Install + download dataset |
| TV1 | 10-15 min | Data cleaning |
| TV2 | 5-10 min | Feature selection |
| TV3 | 30-60 min | Train 3 models |
| TV4 | 60-120 min | Train RF/KNN (RF is slow, 100 trees) |
| TV5 | <1 min | Generate charts |
| **Total** | **2-4 hours** | Can run TV3 & TV4 in parallel to save time |

---

## Next Steps

1. **Want quick demo?** → `python phase6_demo.py`
2. **Want to understand models?** → Read the MODEL_COMPARISON section above
3. **Want detailed analysis?** → Read REPORT.md
4. **Want to run full pipeline?** → Follow "How to Run" sections (needs Kaggle dataset)
5. **Want to modify config?** → Edit config.py (affects all models)

---

## Team

| Member | ID | Role | Contribution |
|--------|----|----|--------------|
| Hoàng Anh | N23DCCN071 | TV1 + TV2 | Data preprocessing, feature selection, balancing |
| Đặng Kim An | N23DCCN001 | TV3 | Logistic Regression, Naive Bayes, SVM |
| Phạm Quốc An | N23DCCN138 | TV4 | KNN, Random Forest, real-time deployment |

---

## Files in This Project

```
is_security_group1/
├── README.md                      ← Quick overview (points to GUIDE.md)
├── GUIDE.md                       ← This file - Complete documentation
├── REPORT.md                      ← Detailed model analysis & deployment decision
├── config.py                      ← Central configuration (18 features, hyperparams)
├── utils.py                       ← Shared utilities (load, plot, alerts)
├── model_comparison.py            ← Aggregate & compare 5 models
├── phase6_demo.py                 ← Real-time prediction demo
├── requirements.txt               ← Python dependencies
│
├── HoangAnh_N23DCCN071/           (TV1 + TV2)
│   ├── preprocess.py
│   ├── prepare_model_data.py
│   ├── outputs/ (EDA charts)
│   └── artifacts/ (scaler, encoder)
│
├── N23DCCN001_DangKimAn/          (TV3)
│   ├── nodebook/
│   │   ├── logistic_regression.ipynb
│   │   ├── naive_bayes.ipynb
│   │   └── svm.ipynb
│   ├── data/artifacts/ (confusion matrices)
│   └── README.md
│
└── N23DCCN138_PhamQuocAn/         (TV4)
    ├── notebooks/
    │   └── IDS_ML_Notebook.py
    ├── logs/ (alerts.log)
    ├── artifacts/ (models)
    └── README.md
```

---

**Last Updated:** May 2, 2026  
**Status:** ✅ Complete & Ready for Deployment  
**Model Deployed:** Random Forest (97.59% accuracy, 99.9% PortScan detection)
