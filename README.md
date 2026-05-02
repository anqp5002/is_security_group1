# 🛡️ Real-time Network Intrusion Detection System (IDS) using Machine Learning

A machine learning-based Network Intrusion Detection System that compares 5 ML models on the **CIC-IDS2017** dataset and deploys the best model (Random Forest) for real-time attack detection.

---

## 📊 Quick Model Comparison

| Model | Accuracy | F1-Score | Best For |
|-------|:--------:|:--------:|----------|
| **Random Forest** | **97.59%** | **97.59%** | ⭐ **DEPLOYED** - Best attack detection (PortScan 99.9%, Bot 92.3%) |
| KNN (K=5) | 98.20% | 98.20% | Highest overall accuracy |
| SVM (Nystroem) | 97.00% | 0.64 | Scalable alternative |
| Logistic Regression | 93.00% | 0.71 | Baseline |
| Naive Bayes | 83.00% | 0.60 | Quick filter only |

**Why Random Forest?** Despite 0.61% lower accuracy, RF detects 15% more reconnaissance and 30% more botnet infections → Better security.

---

## 🚀 Quick Start

### 1️⃣ Demo in 1 Minute (No Training Required)
```bash
pip install -r requirements.txt
python phase6_demo.py
```
Runs instant predictions on synthetic network flows with real-time Suricata-format alerts.

### 2️⃣ Full Pipeline (2-4 hours, requires Kaggle dataset)
```bash
# Download CIC-IDS2017 dataset (8 CSVs, ~2GB) from:
# https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/
mkdir -p HoangAnh_N23DCCN071/data/raw
# Extract 8 CSV files to HoangAnh_N23DCCN071/data/raw/

# Run step-by-step (TV1 → TV2 → TV3 → TV4 → TV5)
cd HoangAnh_N23DCCN071
python preprocess.py                          # TV1: EDA (10-15 min)
python prepare_model_data.py                  # TV2: Features (5-10 min)

cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/*.ipynb             # TV3: Train 3 models (30-60 min)

cd ../N23DCCN138_PhamQuocAn
python notebooks/IDS_ML_Notebook.py           # TV4: Train RF/KNN (60-120 min)

cd ../
python model_comparison.py                    # TV5: Compare all 5 (1 min)
```

---

## 📚 Documentation

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[GUIDE.md](GUIDE.md)** | Complete project guide with all details | You want to understand everything |
| **[REPORT.md](REPORT.md)** | Detailed model analysis & deployment decision | You want deep technical analysis |

---

## 🏗️ Project Structure

```
is_security_group1/
├── README.md                           ← You are here
├── GUIDE.md                            ← Complete documentation
├── REPORT.md                           ← Model analysis details
├── config.py                           ← Configuration (18 features, hyperparams)
├── utils.py                            ← Utilities (load data, plot, alerts)
├── model_comparison.py                 ← Compare all 5 models
├── phase6_demo.py                      ← Real-time prediction demo
├── requirements.txt                    ← Dependencies
│
├── HoangAnh_N23DCCN071/                (TV1: Preprocessing + TV2: Feature selection)
│   ├── preprocess.py
│   ├── prepare_model_data.py
│   └── outputs/                        (EDA charts)
│
├── N23DCCN001_DangKimAn/               (TV3: Train LR/NB/SVM)
│   ├── nodebook/                       (3 Jupyter notebooks)
│   └── data/artifacts/                 (Confusion matrices)
│
└── N23DCCN138_PhamQuocAn/              (TV4: Train KNN/RF + Real-time alerts)
    ├── notebooks/                      (IDS_ML_Notebook.py)
    └── logs/                           (alerts.log)
```

---

## 🎯 Key Features

✅ **5 ML Models Trained & Compared**
- Logistic Regression, Naive Bayes, SVM, KNN, Random Forest
- Comprehensive confusion matrices for each

✅ **Production-Ready Deployment**
- Random Forest model with 97.59% accuracy
- Real-time prediction with <100ms latency
- Suricata-format alert generation

✅ **Balanced Dataset Handling**
- SMOTE for minority oversampling
- RandomUnderSampler for majority capping
- Stratified train/test split

✅ **18 Core Network Features**
- Protocol, flow duration, packet counts, TCP flags
- Standardized via config.py for all models

✅ **Real-time Alerts**
- Detects: PortScan, DDoS, Bot, Web Attack, Infiltration
- Formats: Suricata-compatible alert logs

---

## 📊 Model Performance

### Overall Accuracy
- KNN: 98.20% (best)
- SVM: 97.00%
- Random Forest: 97.59% (deployed)
- Logistic Regression: 93.00%
- Naive Bayes: 83.00%

### Attack-Specific Recall (Why RF Won)
| Attack Type | KNN | Random Forest | RF Advantage |
|-------------|-----|---------------|--------------|
| PortScan | 84.8% | **99.9%** | **+15.1%** |
| Bot | 62.4% | **92.3%** | **+29.9%** |
| DDoS | 98.1% | 98.5% | +0.4% |

**Annual Impact:** RF prevents 52,000+ port scans and 6.5M+ bot flows that KNN would miss.

---

## 🔧 Configuration

All 18 features and hyperparameters are centralized in `config.py`:

```python
SELECTED_FEATURES = [
    "Protocol", "Flow Duration", "Tot Fwd Pkts", "Tot Bwd Pkts",
    "TotLen Fwd Pkts", "TotLen Bwd Pkts", "Fwd Pkt Len Mean", 
    "Bwd Pkt Len Mean", "Flow Byts/s", "Flow Pkts/s", "Pkt Len Mean",
    "Pkt Len Std", "SYN Flag Cnt", "ACK Flag Cnt", "FIN Flag Cnt",
    "RST Flag Cnt", "PSH Flag Cnt", "URG Flag Cnt"
]

HYPERPARAMS = {
    "train_test_split": {"test_size": 0.2, "stratify": True},
    "smote": {"minority_threshold_pct": 0.10},
    "random_forest": {"n_estimators": 100, "random_state": 42},
    ...
}
```

---

## 🚨 Real-time Alerts

Deployed model generates Suricata-format alerts:

```
✅ [2026-05-02 14:35:22] BENIGN: Normal traffic
🚨 [2026-05-02 14:35:23] [ALERT] DDoS: Suspicious traffic detected. Destination Port: 80.
🚨 [2026-05-02 14:35:24] [ALERT] PortScan: Suspicious traffic detected. Destination Port: 443.
🚨 [2026-05-02 14:35:25] [ALERT] Bot: Suspicious traffic detected. Destination Port: 8080.
```

---

## 📦 Installation

### Requirements
- Python 3.9+
- 8GB RAM minimum (16GB recommended for TV4)
- ~5GB disk space

### Setup
```bash
# Clone repository
git clone <repo_url>
cd is_security_group1

# Install dependencies
pip install -r requirements.txt

# Download dataset
# From: https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/
# Extract 8 CSV files to: data/raw/
```

---

## 📋 Expected Runtime

| Phase | Duration | Task |
|-------|----------|------|
| TV1 | 10-15 min | Data preprocessing & EDA |
| TV2 | 5-10 min | Feature selection & balancing |
| TV3 | 30-60 min | Train 3 models (LR/NB/SVM) |
| TV4 | 60-120 min | Train 2 models (KNN/RF) |
| TV5 | <1 min | Compare all models |
| **Total** | **2-4 hours** | Full pipeline (TV3 & TV4 can run in parallel) |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError: data/raw` | Download 8 CSVs from Kaggle and extract to `data/raw/` |
| `MemoryError` during TV4 | Run TV4 on Kaggle instead (cloud has unlimited RAM) |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
| Slow performance | Run TV3 & TV4 on Kaggle notebooks (faster than local) |

---

## 👥 Team

| Member | ID | Role | Contribution |
|--------|----|----|------------|
| Hoàng Anh | N23DCCN071 | TV1 + TV2 | Data preprocessing, feature selection, balancing |
| Đặng Kim An | N23DCCN001 | TV3 | Logistic Regression, Naive Bayes, SVM notebooks |
| Phạm Quốc An | N23DCCN138 | TV4 | KNN & Random Forest training, real-time alerts |

---

## 📚 References

- **Dataset:** [CIC-IDS2017 on Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/)
- **Reference implementations:**
  - https://github.com/marxgoo/Network-intrusion-detection-ml
  - https://www.kaggle.com/code/ujjwalks9/intrusion-detection-system

---

## ✅ Deliverables Checklist

- ✅ Source code (.py, .ipynb) — runnable, documented
- ✅ README.md — quick reference (this file)
- ✅ GUIDE.md — complete documentation
- ✅ REPORT.md — detailed model analysis
- ✅ 5 ML models — trained & compared
- ✅ Confusion matrices — 5 PNG files (from TV3 & TV4)
- ✅ Real-time alerts — Suricata format (logs/alerts.log)
- ✅ Configuration — centralized in config.py
- ✅ Utilities — shared functions in utils.py
- ✅ Git commits — continuous, meaningful messages

---

**Last Updated:** May 2, 2026  
**Status:** ✅ Complete & Ready for Deployment  
**Deployed Model:** Random Forest (97.59% accuracy)
