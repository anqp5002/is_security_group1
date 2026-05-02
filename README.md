# 🛡️ Real-time Network Intrusion Detection System (IDS) using Machine Learning

A machine learning-based Network Intrusion Detection System that compares 5 ML models on the **CIC-IDS2017** dataset and deploys the best model (Random Forest) for real-time attack detection.

---

## 📊 Model Comparison

| Model | Accuracy | Precision | Recall | F1-Score | Notes |
|-------|:--------:|:---------:|:------:|:--------:|-------|
| **Random Forest** | **97.59%** | 97.59% | 97.59% | 97.59% | ⭐ **DEPLOYED** |
| KNN (K=5) | 98.20% | 98.20% | 98.20% | 98.20% | Best accuracy |
| SVM | 97.00% | — | — | 0.64 | Scalable |
| Logistic Regression | 93.00% | — | — | 0.71 | Baseline |
| Naive Bayes | 83.00% | — | — | 0.60 | Weakest |

**Why Random Forest?** Best attack detection: PortScan 99.9%, Bot 92.3% recall

---

## 🚀 Quick Start

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Download Dataset
Download **CIC-IDS2017** from [Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/) and extract 8 CSV files to `data/raw/`:

```bash
mkdir -p data/raw
# Place these 8 files in data/raw/:
# - Monday-WorkingHours.pcap_ISCX.csv
# - Tuesday-WorkingHours.pcap_ISCX.csv
# - Wednesday-WorkingHours.pcap_ISCX.csv
# - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
# - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
# - Friday-WorkingHours-Morning.pcap_ISCX.csv
# - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
# - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

### 3️⃣ Run Pipeline (Step by Step)

#### **TV1 — Data Preprocessing & EDA**
```bash
cd HoangAnh_N23DCCN071
python preprocess.py
```
**Output:** Cleaned dataset + EDA charts (attack distribution, correlation heatmap)

#### **TV2 — Feature Selection & Balancing**
```bash
python prepare_model_data.py
```
**Output:** 18 selected features, balanced train/test data, scaler + encoder

#### **TV3 — Train 3 Models (LR, NB, SVM)**
```bash
cd ../N23DCCN001_DangKimAn
# Option A: Jupyter (interactive)
jupyter notebook nodebook/logistic_regression.ipynb
jupyter notebook nodebook/naive_bayes.ipynb
jupyter notebook nodebook/svm.ipynb

# Option B: Kaggle (recommended for large datasets)
# 1. Create new Kaggle notebook
# 2. Add dataset: chethuhn/network-intrusion-dataset
# 3. Copy & run notebook content
```
**Output:** Classification reports, confusion matrices, trained models

#### **TV4 — Train KNN + Random Forest + Real-time Alerts**
```bash
cd ../N23DCCN138_PhamQuocAn
# Option A: Kaggle (recommended, no RAM issues)
# 1. Create new Kaggle notebook
# 2. Add dataset: chethuhn/network-intrusion-dataset
# 3. Copy & run notebooks/IDS_ML_Notebook.py content

# Option B: Local (requires 16GB+ RAM)
python notebooks/IDS_ML_Notebook.py
```
**Output:** KNN + RF confusion matrices, real-time alert log, trained models

#### **Compare All 5 Models**
```bash
cd ../
python model_comparison.py
```
**Output:** 
- `outputs/comparison/bar_accuracy.png` — accuracy comparison
- `outputs/comparison/bar_all_metrics.png` — detailed metrics
- `outputs/comparison/radar_chart.png` — spider chart
- `outputs/comparison/comparison_table.csv` — CSV table

---

## 📂 Project Structure

```
is_security_group1/
├── README.md                     ← You are here
├── requirements.txt              ← Dependencies
├── config.py                     ← Configuration (18 features, hyperparams)
├── utils.py                      ← Utility functions
├── model_comparison.py           ← Compare 5 models
│
├── HoangAnh_N23DCCN071/          (TV1 + TV2)
│   ├── preprocess.py             → EDA + data cleaning
│   ├── prepare_model_data.py     → Feature selection + balancing
│   └── outputs/                  (generated: charts)
│
├── N23DCCN001_DangKimAn/         (TV3)
│   ├── nodebook/
│   │   ├── logistic_regression.ipynb
│   │   ├── naive_bayes.ipynb
│   │   └── svm.ipynb
│   └── data/artifacts/           (generated: confusion matrices)
│
└── N23DCCN138_PhamQuocAn/        (TV4)
    ├── notebooks/
    │   └── IDS_ML_Notebook.py    → KNN + RF + deployment
    └── logs/                     (generated: alerts.log)
```

---

## 🔧 Configuration

**18 Core Features** (in `config.py`):
```python
Protocol, Flow Duration, Tot Fwd Pkts, Tot Bwd Pkts,
TotLen Fwd Pkts, TotLen Bwd Pkts, Fwd Pkt Len Mean, Bwd Pkt Len Mean,
Flow Byts/s, Flow Pkts/s, Pkt Len Mean, Pkt Len Std,
SYN Flag Cnt, ACK Flag Cnt, FIN Flag Cnt, RST Flag Cnt,
PSH Flag Cnt, URG Flag Cnt
```

**Hyperparameters** (in `config.py`):
- Train/Test split: 80/20
- SMOTE: minority threshold = 10% of majority
- RandomUnderSampler: majority = 3× minority target
- Random Forest: 100 trees

---

## 🧪 Test Prediction

```python
import joblib
import pandas as pd
from config import SELECTED_FEATURES

# Load artifacts
model = joblib.load('artifacts/random_forest_model.pkl')
scaler = joblib.load('artifacts/scaler.pkl')
label_encoder = joblib.load('artifacts/label_encoder.pkl')

# Predict on test data
X_test = pd.read_csv('data/final/X_test.csv').head(10)
X_scaled = scaler.transform(X_test)
predictions = model.predict(X_scaled)
labels = label_encoder.inverse_transform(predictions)

print(labels)  # e.g., ['BENIGN', 'DDoS', 'PortScan', ...]
```

---

## 📋 Model Comparison Report

**See detailed report:** [`REPORT.md`](REPORT.md)

### Quick Summary

| Metric | Best | Score | Notes |
|--------|------|-------|-------|
| Overall Accuracy | KNN | 98.20% | But weak on minority attacks |
| Attack Detection | **Random Forest** | **97.59%** | **DEPLOYED** |
| PortScan Recall | **Random Forest** | **99.9%** | vs KNN 84.8% |
| Bot Recall | **Random Forest** | **92.3%** | vs KNN 62.4% |

**Why Random Forest?** Despite 0.61% lower accuracy, RF detects 15% more reconnaissance and 30% more botnet infections—critical for production security.

For full analysis: [Read REPORT.md](REPORT.md)

---

## 🚨 Real-time Alerts (Suricata Format)

```
[2026-04-27 14:35:22] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 80.
[2026-04-27 14:35:23] [ALERT] Suspicious traffic detected: PortScan. Destination Port: 443.
[2026-04-27 14:35:24] [ALERT] Suspicious traffic detected: Bot. Destination Port: 8080.
✅ [2026-04-27 14:35:25] Normal traffic: BENIGN
```

See `N23DCCN138_PhamQuocAn/logs/alerts.log` for generated alerts.

---

## 👥 Team

| Member | Student ID | Role |
|--------|-----------|------|
| Hoàng Anh | N23DCCN071 | TV1 + TV2: EDA, preprocessing, balancing |
| Đặng Kim An | N23DCCN001 | TV3: Logistic Regression, Naive Bayes, SVM |
| Phạm Quốc An | N23DCCN138 | TV4: KNN, Random Forest, deployment |

---

## 📚 References

- Dataset: [CIC-IDS2017 on Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/)
- Reference implementations:
  - https://github.com/marxgoo/Network-intrusion-detection-ml
  - https://www.kaggle.com/code/ujjwalks9/intrusion-detection-system

---

## ⏱️ Execution Time

| Step | Duration |
|------|----------|
| TV1 (preprocessing) | 10-15 min |
| TV2 (feature selection) | 5-10 min |
| TV3 (train 3 models) | 30-60 min |
| TV4 (train RF+KNN) | 60-120 min |
| Model comparison | <1 min |
| **Total** | **2-4 hours** |

💡 **Tip:** Run TV3 & TV4 on Kaggle (faster, no RAM issues)

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError: data/raw` | Download 8 CSVs from Kaggle |
| `MemoryError` | Run TV4 on Kaggle instead of locally |
| `KeyError: Feature name` | Check `config.py` for column name mapping |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |

---

## ✅ Deliverables Checklist

- ✅ Source code (.py, .ipynb) — runnable, with comments
- ✅ README.md — comprehensive guide
- ✅ 5 ML models — trained & compared
- ✅ Confusion matrices — 5 PNG files
- ✅ Real-time alerts — Suricata format
- ✅ Git commits — continuous, meaningful messages
- ✅ Saved models — `.pkl` files with Google Drive link (if >100MB)

---

**Last Updated:** May 2, 2026  
**Status:** ✅ Complete & Ready for Submission
