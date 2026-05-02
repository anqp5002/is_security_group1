# 🛡️ Real-time Network Intrusion Detection System (IDS) using Machine Learning

A machine learning-based Network Intrusion Detection System that compares 5 ML models on the **CIC-IDS2017** dataset and deploys the best model (Random Forest) for real-time attack detection.

**⭐ All training done on Kaggle** - Download results from Google Drive link below

---

## 👋 New Here?

**Start with [GETTING_STARTED.md](GETTING_STARTED.md)** — A beginner-friendly guide that explains everything in simple terms.

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
Runs real-time predictions with **all 5 models** on synthetic network flows:
- Loads all 5 trained models from demo/ folder (or creates demo models if missing)
- Shows predictions from each model side-by-side with confidence scores
- Computes consensus prediction (majority vote)
- Displays Suricata-format alerts
- Compares model agreement

### 2️⃣ Get Pre-trained Results (Recommended ⭐)
```bash
# Download pre-trained models from Google Drive:
# https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam

# For QUICK DEMO:
# 1. Download demo folder contents:
#    - random_forest_model.pkl
#    - scaler.pkl
#    - label_encoder.pkl
# 2. Place in: demo/ folder
# 3. Run:
python phase6_demo.py

# For FULL ANALYSIS (with comparison charts):
# Option A: Download comparison outputs to generate charts
# Extract to outputs/comparison/
# Then run:
python model_comparison.py  # View all comparison charts

# Option B: Download pre-trained models for real-time predictions
# Extract demo/ folder (7 model files)
# Then run:
python phase6_demo.py       # Real-time predictions with all 5 models
```

### 3️⃣ Train Yourself on Kaggle (2-4 hours)
```bash
# Download CIC-IDS2017 dataset from:
# https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/

# TV1: Data Preprocessing
cd HoangAnh_N23DCCN071
# Create: mkdir -p data/raw
# Extract 8 CSV files to data/raw/
python preprocess.py          # 10-15 min

# TV2: Feature Selection  
python prepare_model_data.py  # 5-10 min

# TV3: Train 3 Models (LR/NB/SVM) - ON KAGGLE
cd ../N23DCCN001_DangKimAn
# Create Kaggle notebook, copy nodebook/*.ipynb code
# Run on Kaggle (recommended for RAM)

# TV4: Train Advanced Models (KNN/RF) - ON KAGGLE
cd ../N23DCCN138_PhamQuocAn
# Create Kaggle notebook, copy notebooks/IDS_ML_Notebook.py code
# Run on Kaggle (recommended for RAM)

# TV5: Compare Models (local)
cd ../
python model_comparison.py    # 1 min
```

---

## 📚 Documentation

| Document | Purpose | Read When |
|----------|---------|-----------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Beginner-friendly overview & learning path | **Start here first!** |
| **[GUIDE.md](GUIDE.md)** | Complete step-by-step guide with all details | You want to understand everything |
| **[REPORT.md](REPORT.md)** | Detailed model analysis & deployment decision | You need code examples or deep analysis |

---

## 🏗️ Project Structure

```
is_security_group1/
├── README.md                           ← You are here
├── GUIDE.md                            ← Complete documentation
├── REPORT.md                           ← Model analysis details
├── model_comparison.py                 ← Compare all 5 models
├── phase6_demo.py                      ← Real-time prediction demo
├── requirements.txt                    ← Dependencies
│
├── demo/                               ← Pre-trained models (download from Google Drive)
│   ├── logistic_regression_model.pkl   ← TV3 model
│   ├── naive_bayes_model.pkl           ← TV3 model
│   ├── svm_model.pkl                   ← TV3 model
│   ├── knn_model.pkl                   ← TV4 model
│   ├── random_forest_model.pkl         ← TV4 model (DEPLOYED)
│   ├── scaler.pkl                      ← Feature scaling
│   └── label_encoder.pkl               ← Class labels
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
    └── outputs/                        (Confusion matrices & charts)
```

---

## 🎯 Key Features

✅ **5 ML Models - Load & Compare**
- Load all 5 models from `demo/` folder
- `phase6_demo.py`: Side-by-side predictions + consensus voting
- `model_comparison.py`: Compare training metrics & generate charts
- Logistic Regression (93%), Naive Bayes (83%), SVM (97%), KNN (98.2%), Random Forest (97.59% deployed)

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

### Model Comparison Visualization

![Model Accuracy Comparison](outputs/comparison/bar_accuracy.png)

---

## 📦 .pkl Files (Trained Models)

All models are stored as `.pkl` (pickled) files - serialized Python objects that contain trained classifiers.

**5 Model Files (in demo/ folder):**
| File | Model | Accuracy | Source |
|------|-------|----------|--------|
| `logistic_regression_model.pkl` | Logistic Regression | 93.00% | TV3 |
| `naive_bayes_model.pkl` | Naive Bayes | 83.00% | TV3 |
| `svm_model.pkl` | SVM (Nystroem) | 97.00% | TV3 |
| `knn_model.pkl` | KNN (K=5) | 98.20% | TV4 |
| `random_forest_model.pkl` | Random Forest | 97.59% | TV4 (DEPLOYED) |

**2 Shared Files (used by all models):**
- `scaler.pkl` — StandardScaler that normalizes features to [-1, 1]
  - **Must be used** before predictions, otherwise models give wrong results
- `label_encoder.pkl` — Maps numeric predictions to text labels
  - 0↔BENIGN, 1↔DDoS, 2↔PortScan, 3↔Bot, 4↔Web Attack, 5↔Infiltration

---

## 🔧 18 Core Features Used

The model uses these standardized network flow features:

```
Protocol, Flow Duration, Tot Fwd Pkts, Tot Bwd Pkts,
TotLen Fwd Pkts, TotLen Bwd Pkts, Fwd Pkt Len Mean, Bwd Pkt Len Mean,
Flow Byts/s, Flow Pkts/s, Pkt Len Mean, Pkt Len Std,
SYN Flag Cnt, ACK Flag Cnt, FIN Flag Cnt, RST Flag Cnt, PSH Flag Cnt, URG Flag Cnt
```

**Training Configuration:**
- Train/Test Split: 80/20 (stratified)
- SMOTE: Oversample minorities to 10%
- RandomUnderSampler: Cap majority at 3× minority
- Random Forest: 100 decision trees, random_state=42

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
