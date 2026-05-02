# Real-time Network Intrusion Detection System (IDS) using Machine Learning

A machine learning-based Network Intrusion Detection System (NIDS) built on the **CIC-IDS2017** dataset. The system trains and compares five ML models, then deploys the best-performing model (Random Forest) for real-time network traffic classification and Suricata-style alert generation.

---

## Table of Contents

1. [Project Introduction](#project-introduction)
2. [System Architecture](#system-architecture)
3. [Dataset](#dataset)
4. [Model Comparison Results](#model-comparison-results)
5. [Installation Guide](#installation-guide)
6. [Usage Instructions](#usage-instructions)
7. [Team & Responsibilities](#team--responsibilities)
8. [Project Structure](#project-structure)

---

## Project Introduction

Modern networks face a wide range of sophisticated attacks — DDoS, PortScan, Botnet, Web Attacks, and more. Traditional signature-based IDS systems cannot detect novel attack patterns. This project builds a **machine learning-based NIDS** that:

- Learns attack patterns from 2.8M+ real network flows (CIC-IDS2017)
- Handles severe class imbalance using SMOTE + RandomUnderSampler
- Selects 18 high-impact features for efficient real-time processing
- Compares 5 ML classifiers and deploys the best for live alert generation

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA PIPELINE                             │
│                                                                 │
│  8 CSV Files  ──►  Merge & Clean  ──►  Feature Selection (18)  │
│  (CIC-IDS2017)      (TV1: preprocess.py)                        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    PREPROCESSING PIPELINE                        │
│                                                                 │
│  LabelEncoder ──► StandardScaler ──► SMOTE ──► UnderSampler    │
│                       (TV2: prepare_model_data.py)              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
┌─────────▼──────┐  ┌──────────▼─────┐  ┌─────────▼──────────┐
│   TV3 Models   │  │   TV3 Models   │  │    TV4 Models      │
│                │  │                │  │                    │
│  Logistic Reg  │  │  Naive Bayes   │  │   KNN (K=5)        │
│  SVM (Nystroem)│  │  (Binning)     │  │   Random Forest    │
└────────────────┘  └────────────────┘  └────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│               DEPLOYMENT: REAL-TIME ALERT GENERATION            │
│                                                                 │
│  Network Flow ──► Scaler ──► Random Forest ──► Alert Log       │
│                 (Suricata-style: alerts.log)                    │
└─────────────────────────────────────────────────────────────────┘
```

**Key design decisions:**
- Only the **train set** is balanced (SMOTE + undersampling); the test set is kept original to reflect real-world distribution.
- Preprocessing artifacts (`scaler.pkl`, `label_encoder.pkl`) are saved and reused across all model notebooks to ensure consistency.
- The Random Forest model is selected for deployment because it achieves the best balance of detection recall on attack classes (especially PortScan and Bot) with fast inference time.

---

## Dataset

**CIC-IDS2017** — Canadian Institute for Cybersecurity

| Property | Value |
|----------|-------|
| Total records | ~2.83 million flows |
| Features | 79 columns (78 numerical + 1 label) |
| Traffic types | BENIGN, DoS, DDoS, PortScan, Bot, Web Attacks (Brute Force, XSS, SQL Injection), Infiltration, Heartbleed |
| Class imbalance | ~80% BENIGN, <1% for rare attacks |
| Source | 8 daily CSV files (Monday–Friday captures) |

**Selected 18 Features:**

```python
SELECTED_FEATURES = [
    'Protocol',        'Flow Duration',    'Tot Fwd Pkts',
    'Tot Bwd Pkts',    'TotLen Fwd Pkts',  'TotLen Bwd Pkts',
    'Fwd Pkt Len Mean','Bwd Pkt Len Mean', 'Flow Byts/s',
    'Flow Pkts/s',     'Pkt Len Mean',     'Pkt Len Std',
    'SYN Flag Cnt',    'ACK Flag Cnt',     'FIN Flag Cnt',
    'RST Flag Cnt',    'PSH Flag Cnt',     'URG Flag Cnt'
]
```

Dataset source: [Kaggle — CIC-IDS2017](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/code)

---

## Model Comparison Results

All models trained on the same preprocessed CIC-IDS2017 data (80/20 train-test split, SMOTE + RandomUnderSampler on train set only).

| Model | Accuracy | Precision | Recall | F1-Score | Notes |
|-------|:--------:|:---------:|:------:|:--------:|-------|
| **KNN (K=5)** | **98.20%** | 98.20% | 98.20% | 98.20% | High accuracy but weaker on PortScan (84.8% recall) and Bot (62.4%) |
| **Random Forest** | 97.59% | 97.59% | 97.59% | 97.59% | Best attack recall: PortScan 99.9%, Bot 92.3% — **Deployed model** |
| **SVM (Nystroem)** | 97.00% | — | — | 0.64* | Nystroem approximation for scalability; strong overall accuracy |
| **Logistic Regression** | 93.00% | — | — | 0.71* | Smoothed class weights + outlier clipping |
| **Naive Bayes** | 83.00% | — | — | 0.60* | Categorical NB with binning for continuous features |

> *Macro-averaged F1-score reported for TV3 models. KNN and Random Forest report weighted-average metrics.
>
> **Why Random Forest for deployment?** Although KNN achieves marginally higher overall accuracy (+0.61%), Random Forest detects PortScan nearly perfectly (99.9% vs 84.8%) and has substantially better Bot detection (92.3% vs 62.4%). In cybersecurity, **missing a real attack is more costly than a false alarm**.

---

## Installation Guide

### Prerequisites

- Python 3.9+
- Recommended: run on Kaggle (GPU/CPU, free RAM) for full training

### 1. Clone the repository

```bash
git clone <repository-url>
cd is_security_group1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Download the dataset

Download CIC-IDS2017 from Kaggle and place the 8 CSV files in `data/raw/`:

```
data/raw/
├── Monday-WorkingHours.pcap_ISCX.csv
├── Tuesday-WorkingHours.pcap_ISCX.csv
├── Wednesday-WorkingHours.pcap_ISCX.csv
├── Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
├── Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
├── Friday-WorkingHours-Morning.pcap_ISCX.csv
├── Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
└── Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv
```

### 4. Download trained models (optional)

The trained Random Forest model (~2.6 GB uncompressed) is hosted on Google Drive:

**Google Drive:** [https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam](https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam)

Files: `random_forest_model.pkl`, `scaler.pkl`, `label_encoder.pkl`

---

## Usage Instructions

### Step 1 — Data Preprocessing (TV1)

```bash
cd HoangAnh_N23DCCN071
python preprocess.py
```

Outputs: `data/processed/merged_cleaned.csv`, EDA plots in `outputs/`

### Step 2 — Feature Selection & Balancing (TV2)

```bash
python prepare_model_data.py
```

Outputs: `data/final/X_train.csv`, `X_test.csv`, `y_train.csv`, `y_test.csv`, encoder/scaler in `artifacts/`

### Step 3 — Train Logistic Regression, SVM, Naive Bayes (TV3)

Open and run notebooks in `N23DCCN001_DangKimAn/nodebook/`:

```bash
jupyter notebook N23DCCN001_DangKimAn/nodebook/logistic_regression.ipynb
jupyter notebook N23DCCN001_DangKimAn/nodebook/naive_bayes.ipynb
jupyter notebook N23DCCN001_DangKimAn/nodebook/svm.ipynb
```

### Step 4 — Train KNN + Random Forest + Real-time Deploy (TV4)

Run on Kaggle (recommended) or locally:

```bash
# On Kaggle: upload IDS_ML_Notebook.py as a script notebook
# Locally (requires full dataset in memory):
python N23DCCN138_PhamQuocAn/notebooks/IDS_ML_Notebook.py
```

### Step 5 — View Model Comparison

```bash
python model_comparison.py
```

### Real-time Alert Example

```
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: PortScan. Destination Port: 47.
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: Bot. Destination Port: 47.
[2026-04-27 00:48:35] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 42.
✅ [2026-04-27 00:48:35] [INFO] Normal traffic — BENIGN
```

Alerts are saved to `N23DCCN138_PhamQuocAn/logs/alerts.log`.

---

## Team & Responsibilities

| Member | Student ID | Role | Responsibility |
|--------|-----------|------|----------------|
| Hoàng Anh | N23DCCN071 | TV1 + TV2 | EDA, Preprocessing, Feature Selection, Balancing |
| Đặng Kim An | N23DCCN001 | TV3 | Logistic Regression, Naive Bayes, SVM |
| Phạm Quốc An | N23DCCN138 | TV4 | KNN, Random Forest, Real-time Deployment |

---

## Project Structure

```
is_security_group1/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── config.py                          # Paths, features, hyperparameters
├── utils.py                           # Shared utility functions
├── model_comparison.py                # 5-model comparison & visualization
│
├── HoangAnh_N23DCCN071/               # TV1 + TV2
│   ├── preprocess.py                  # Load, clean, EDA (TV1)
│   ├── prepare_model_data.py          # Encode, scale, balance (TV2)
│   ├── requirements.txt
│   └── outputs/
│       ├── attack_distribution.png
│       └── correlation_heatmap.png
│
├── N23DCCN001_DangKimAn/              # TV3
│   ├── nodebook/
│   │   ├── logistic_regression.ipynb
│   │   ├── naive_bayes.ipynb
│   │   └── svm.ipynb
│   ├── data/artifacts/                # Confusion matrix images
│   └── README.md
│
└── N23DCCN138_PhamQuocAn/             # TV4
    ├── notebooks/
    │   └── IDS_ML_Notebook.py         # KNN + RF + Real-time deploy
    ├── logs/
    │   └── alerts.log                 # Real-time alert output
    └── README.md
```

---

## References

- [CIC-IDS2017 Dataset on Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/code)
- [Reference Implementation — marxgoo](https://github.com/marxgoo/Network-intrusion-detection-ml)
- [Kaggle Notebook Reference — ujjwalks9](https://www.kaggle.com/code/ujjwalks9/intrusion-detection-system)
- Canadian Institute for Cybersecurity (CIC) — IDS 2017 Dataset
