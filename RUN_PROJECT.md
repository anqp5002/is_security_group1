# 🚀 How to Run the Real-time IDS Project

This guide walks you through executing the complete IDS pipeline as required by the lab PDF.

---

## 📋 Prerequisites

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Dataset
Download **CIC-IDS2017** from [Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/) and place 8 CSV files in `data/raw/`:

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

---

## 🔧 Pipeline Execution (in Order)

### **Step 1: TV1 — EDA & Data Preprocessing**
**Requirements:** 2.2 (Exploratory Data Analysis & Data Preprocessing)

```bash
cd HoangAnh_N23DCCN071
python preprocess.py
```

**Outputs:**
- ✅ `data/processed/merged_cleaned.csv` — cleaned, merged dataset
- ✅ `outputs/attack_distribution.png` — attack type distribution chart
- ✅ `outputs/correlation_heatmap.png` — feature correlation matrix

---

### **Step 2: TV2 — Feature Selection & Class Balancing**
**Requirements:** 2.3 (Handling Class Imbalance) + 2.4 (Feature Selection)

```bash
python prepare_model_data.py
```

**Outputs:**
- ✅ `data/final/X_train.csv`, `X_test.csv` — selected 18 features
- ✅ `data/final/y_train.csv`, `y_test.csv` — encoded labels
- ✅ `artifacts/scaler.pkl` — StandardScaler
- ✅ `artifacts/label_encoder.pkl` — LabelEncoder

---

### **Step 3: TV3 — Train 3 Models (LR, NB, SVM)**
**Requirements:** 2.5 (Model Implementation & Comparison)

**Option A: Using Jupyter (Recommended)**
```bash
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
jupyter notebook nodebook/naive_bayes.ipynb
jupyter notebook nodebook/svm.ipynb
```

**Option B: On Kaggle** (Better for large datasets)
1. Go to [Kaggle](https://www.kaggle.com/code)
2. Create new notebook
3. Add dataset: `chethuhn/network-intrusion-dataset`
4. Copy notebook content and run

**Outputs:**
- ✅ `data/artifacts/logistic_regression.png` — confusion matrix
- ✅ `data/artifacts/naive_algorithm.png` — confusion matrix
- ✅ `data/artifacts/svm_v5_confusion_matrix.png` — confusion matrix
- ✅ Classification reports (Accuracy, Precision, Recall, F1)

---

### **Step 4: TV4 — Train KNN + Random Forest + Real-time Alerts**
**Requirements:** 2.5 (Model Implementation) + 2.6 (Best Model Deployment)

**Option A: On Kaggle** (Highly Recommended — no RAM issues)
```bash
# 1. Create notebook on Kaggle
# 2. Add dataset: chethuhn/network-intrusion-dataset
# 3. Copy content from:
cd N23DCCN138_PhamQuocAn/notebooks/IDS_ML_Notebook.py
# 4. Run: Save & Run All
```

**Option B: Locally** (requires 16GB+ RAM)
```bash
python N23DCCN138_PhamQuocAn/notebooks/IDS_ML_Notebook.py
```

**Outputs:**
- ✅ `cm_KNN.png` — KNN confusion matrix
- ✅ `cm_Random_Forest.png` — RF confusion matrix
- ✅ `model_comparison.png` — accuracy comparison chart
- ✅ `logs/alerts.log` — real-time alert log (Suricata format)
- ✅ `random_forest_model.pkl` — trained model (~2.6GB)
- ✅ `scaler.pkl`, `label_encoder.pkl` — preprocessing artifacts

---

## 📊 Model Comparison & Results

### **Run Comparison Script**
```bash
cd ..  # Back to project root
python model_comparison.py
```

**Generates:**
- ✅ `outputs/comparison/bar_accuracy.png` — bar chart of accuracy
- ✅ `outputs/comparison/bar_all_metrics.png` — grouped metrics
- ✅ `outputs/comparison/radar_chart.png` — spider chart
- ✅ `outputs/comparison/comparison_table.csv` — CSV table of all metrics

**Console Output:**
```
==============================================================
  MODEL COMPARISON — CIC-IDS2017
==============================================================
Model              Accuracy   Precision  Recall   F1
------
Random Forest      0.9759     0.9759     0.9759   0.9759  ⭐ DEPLOYED
KNN (K=5)          0.9820     0.9820     0.9820   0.9820
SVM (Nystroem)     0.9700     N/A        N/A      0.6400
Logistic Regression 0.9300    N/A        N/A      0.7100
Naive Bayes        0.8300     N/A        N/A      0.6000
```

---

## 🛡️ Real-time Alert Detection

### **View Alerts from TV4 Simulation**
```bash
cat N23DCCN138_PhamQuocAn/logs/alerts.log
```

**Sample Output:**
```
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: PortScan. Destination Port: 47.
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: Bot. Destination Port: 47.
[2026-04-27 00:48:35] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 42.
```

---

## 🧪 Test Prediction on New Data

```python
import joblib
import pandas as pd
from config import SELECTED_FEATURES

# Load artifacts
model = joblib.load('artifacts/random_forest_model.pkl')
scaler = joblib.load('artifacts/scaler.pkl')
label_encoder = joblib.load('artifacts/label_encoder.pkl')

# Load test data (or create new sample with 18 features)
X_test = pd.read_csv('data/final/X_test.csv').head(10)

# Predict
X_scaled = scaler.transform(X_test)
predictions = model.predict(X_scaled)
labels = label_encoder.inverse_transform(predictions)

# Display results
for i, label in enumerate(labels):
    print(f"Flow {i}: {label}")
```

---

## 📂 Full Directory Structure After Completion

```
is_security_group1/
├── README.md                                    ✅ Project documentation
├── SUBMISSION_CHECKLIST.md                      ✅ PDF requirements mapping
├── RUN_PROJECT.md                               ✅ This file
├── requirements.txt                             ✅ Dependencies
├── config.py                                    ✅ Configuration
├── utils.py                                     ✅ Utility functions
├── model_comparison.py                          ✅ Model comparison script
│
├── data/
│   ├── raw/                                     📥 8 CSV files (download)
│   ├── processed/
│   │   └── merged_cleaned.csv                   ✅ From TV1
│   └── final/
│       ├── X_train.csv, X_test.csv              ✅ From TV2
│       ├── y_train.csv, y_test.csv              ✅ From TV2
│
├── artifacts/
│   ├── scaler.pkl                               ✅ From TV2
│   ├── label_encoder.pkl                        ✅ From TV2
│   └── random_forest_model.pkl                  ✅ From TV4 (~2.6GB)
│
├── outputs/
│   ├── attack_distribution.png                  ✅ From TV1
│   ├── correlation_heatmap.png                  ✅ From TV1
│   └── comparison/
│       ├── bar_accuracy.png                     ✅ From comparison script
│       ├── bar_all_metrics.png                  ✅ From comparison script
│       ├── radar_chart.png                      ✅ From comparison script
│       └── comparison_table.csv                 ✅ From comparison script
│
├── logs/
│   └── alerts.log                               ✅ From TV4
│
├── HoangAnh_N23DCCN071/                         📁 TV1 + TV2
│   ├── preprocess.py
│   ├── prepare_model_data.py
│   ├── requirements.txt
│   └── outputs/
│
├── N23DCCN001_DangKimAn/                        📁 TV3
│   ├── nodebook/
│   │   ├── logistic_regression.ipynb
│   │   ├── naive_bayes.ipynb
│   │   └── svm.ipynb
│   ├── data/artifacts/
│   │   ├── logistic_regression.png
│   │   ├── naive_algorithm.png
│   │   └── svm_v5_confusion_matrix.png
│   └── README.md
│
└── N23DCCN138_PhamQuocAn/                       📁 TV4
    ├── notebooks/
    │   └── IDS_ML_Notebook.py
    ├── logs/
    │   └── alerts.log
    ├── outputs/
    │   ├── cm_KNN.png
    │   ├── cm_Random_Forest.png
    │   └── model_comparison.png
    └── README.md
```

---

## ⏱️ Estimated Execution Time

| Step | Duration | Notes |
|------|----------|-------|
| TV1 (preprocess) | 10-15 min | Depends on RAM/disk speed |
| TV2 (prepare data) | 5-10 min | Fast |
| TV3 (train 3 models) | 30-60 min | Can be optimized |
| TV4 (train RF+KNN+alerts) | 60-120 min | RF training is slow |
| Model comparison | < 1 min | Instant |
| **Total** | **2-4 hours** | On Kaggle: faster |

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError: data/raw/*.csv` | Download 8 CSVs from Kaggle, place in `data/raw/` |
| `MemoryError` | Run TV4 on Kaggle instead of locally |
| `KeyError: 'Feature name'` | Feature names mismatch — check `config.py` → `FEATURE_ALT_NAMES` |
| `ModuleNotFoundError: sklearn` | Run `pip install -r requirements.txt` again |
| Model file is 2.6GB | Use Google Drive link (in README) or Git LFS |

---

## ✅ Verification Checklist

After running, verify all outputs exist:

```bash
# Check preprocessing
ls data/processed/merged_cleaned.csv
ls outputs/attack_distribution.png

# Check prepared data
ls data/final/X_train.csv
ls artifacts/scaler.pkl

# Check TV3 outputs
ls N23DCCN001_DangKimAn/data/artifacts/*.png

# Check TV4 outputs
ls N23DCCN138_PhamQuocAn/logs/alerts.log

# Check comparison
ls outputs/comparison/*.png
```

✅ **All outputs present → Project is complete!**

---

## 📖 Documentation Links

- **README.md** — Full project documentation
- **SUBMISSION_CHECKLIST.md** — Maps PDF requirements to deliverables
- **config.py** — All configuration in one place
- **utils.py** — Reusable utility functions
- **model_comparison.py** — Aggregates results from 5 models
