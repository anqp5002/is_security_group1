# 📋 Submission Checklist — Real-time IDS using ML

Based on requirements from: **2. Real-time Network Intrusion Detection System (IDS) using Machine Learning.pdf**

---

## ✅ 2.1. Source Code Management with Git & GitHub

- ✅ **Repository Name:** `is_security_group1` (GitHub/GitLab)
- ✅ **Commit History:** Frequent commits with meaningful messages (e.g., `feat: implement data preprocessing`, `feat: train random forest`, `merge: integrate tv3 models`)
- ✅ **Branch Strategy:** Main branch + feature branches (HoangAnh_N23DCCN071, N23DCCN001_DangKimAn, N23DCCN138_PhamQuocAn)

---

## ✅ 2.2. Exploratory Data Analysis (EDA) & Data Preprocessing

**File:** `HoangAnh_N23DCCN071/preprocess.py`

- ✅ **Merge Data:** Load 8 CSV files and concatenate into single DataFrame
- ✅ **Data Cleaning:**
  - ✅ Strip trailing/leading whitespace from column names
  - ✅ Handle infinite (np.inf) and missing (NaN) values → replace with median
  - ✅ Drop zero-variance features and duplicate rows
- ✅ **Memory Optimization:** Downcast data types (int64 → uint8/int16, float64 → float32)
- ✅ **EDA Visualizations:**
  - ✅ Attack type distribution plot → `outputs/attack_distribution.png`
  - ✅ Correlation heatmap → `outputs/correlation_heatmap.png`

**Output:** `data/processed/merged_cleaned.csv` ✅

---

## ✅ 2.3. Handling Class Imbalance

**File:** `HoangAnh_N23DCCN071/prepare_model_data.py`

- ✅ **Encoding:** LabelEncoder for Label column
- ✅ **Scaling:** StandardScaler for numerical features
- ✅ **Data Balancing Pipeline:**
  - ✅ SMOTE: Over-sample minority classes to ~10% of majority class size
  - ✅ RandomUnderSampler: Reduce majority class (BENIGN) to prevent bias

**Output:**
- ✅ `data/final/X_train.csv`, `X_test.csv`
- ✅ `data/final/y_train.csv`, `y_test.csv`
- ✅ `artifacts/scaler.pkl` (StandardScaler)
- ✅ `artifacts/label_encoder.pkl` (LabelEncoder)

---

## ✅ 2.4. Feature Selection

**File:** `config.py` → `SELECTED_FEATURES`

Exactly **18 core features** as specified in PDF:

```python
SELECTED_FEATURES = [
    'Protocol',           # Feature 1
    'Flow Duration',      # Feature 2
    'Tot Fwd Pkts',       # Feature 3
    'Tot Bwd Pkts',       # Feature 4
    'TotLen Fwd Pkts',    # Feature 5
    'TotLen Bwd Pkts',    # Feature 6
    'Fwd Pkt Len Mean',   # Feature 7
    'Bwd Pkt Len Mean',   # Feature 8
    'Flow Byts/s',        # Feature 9
    'Flow Pkts/s',        # Feature 10
    'Pkt Len Mean',       # Feature 11
    'Pkt Len Std',        # Feature 12
    'SYN Flag Cnt',       # Feature 13
    'ACK Flag Cnt',       # Feature 14
    'FIN Flag Cnt',       # Feature 15
    'RST Flag Cnt',       # Feature 16
    'PSH Flag Cnt',       # Feature 17
    'URG Flag Cnt'        # Feature 18
]
```

✅ Applied to both Train and Test datasets

---

## ✅ 2.5. Model Implementation & Comparison

### Implemented Models:

| Model | Member | File | Status |
|-------|--------|------|--------|
| **Logistic Regression** | TV3 (N23DCCN001_DangKimAn) | `nodebook/logistic_regression.ipynb` | ✅ Trained |
| **Support Vector Machine** | TV3 (N23DCCN001_DangKimAn) | `nodebook/svm.ipynb` | ✅ Trained |
| **Naive Bayes** | TV3 (N23DCCN001_DangKimAn) | `nodebook/naive_bayes.ipynb` | ✅ Trained |
| **K-Nearest Neighbors** | TV4 (N23DCCN138_PhamQuocAn) | `notebooks/IDS_ML_Notebook.py` | ✅ Trained |
| **Random Forest** | TV4 (N23DCCN138_PhamQuocAn) | `notebooks/IDS_ML_Notebook.py` | ✅ Trained |

### Evaluation Metrics:

✅ Classification reports (Accuracy, Precision, Recall, F1-score) for each model

### Confusion Matrices:

| Model | Location | Status |
|-------|----------|--------|
| Logistic Regression | `N23DCCN001_DangKimAn/data/artifacts/logistic_regression.png` | ✅ |
| Naive Bayes | `N23DCCN001_DangKimAn/data/artifacts/naive_algorithm.png` | ✅ |
| SVM | `N23DCCN001_DangKimAn/data/artifacts/svm_v5_confusion_matrix.png` | ✅ |
| KNN | `N23DCCN138_PhamQuocAn/outputs/cm_KNN.png` | ✅ |
| Random Forest | `N23DCCN138_PhamQuocAn/outputs/cm_Random_Forest.png` | ✅ |

### Model Comparison:

✅ **Comparison Script:** `model_comparison.py`
- ✅ Comparison table of all 5 models (Accuracy, Precision, Recall, F1)
- ✅ Bar chart: Accuracy comparison
- ✅ Bar chart: All metrics (Acc vs F1)
- ✅ Radar chart: Performance across metrics

**Output:** `outputs/comparison/` containing:
- ✅ `bar_accuracy.png`
- ✅ `bar_all_metrics.png`
- ✅ `radar_chart.png`
- ✅ `comparison_table.csv`

### Best Model Selected:

✅ **Random Forest** — Highest attack-class recall (PortScan 99.9%, Bot 92.3%)

---

## ✅ 2.6. Best Model Deployment (Real-time Alert Generation)

**File:** `N23DCCN138_PhamQuocAn/notebooks/IDS_ML_Notebook.py` (Section 8)

- ✅ **Real-time Simulation Function:** `simulate_realtime_detection()`
  - ✅ Receive network flow inputs
  - ✅ Use trained Random Forest to classify
  - ✅ Generate **Suricata-style alerts** for non-BENIGN predictions

✅ **Alert Format Example:**
```
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: PortScan. Destination Port: 47.
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: Bot. Destination Port: 47.
[2026-04-27 00:48:35] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 42.
```

✅ **Output File:** `N23DCCN138_PhamQuocAn/logs/alerts.log`

---

## ✅ 3. Deliverables

### 3.1. Public GitHub Repository Link

✅ Repository: `is_security_group1`  
✅ Accessibility: Public (shared with instructors)

### 3.2. Commit History

✅ Evidence of continuous, structured work:
- Feature commits (preprocessing, balancing, model training)
- Merge commits from different team members
- Clear commit messages following conventions

### 3.3. Source Code (.ipynb or .py)

**TV1 + TV2 (Preprocessing):**
- ✅ `HoangAnh_N23DCCN071/preprocess.py` — runs smoothly, displays all charts
- ✅ `HoangAnh_N23DCCN071/prepare_model_data.py` — clear comments

**TV3 (Models):**
- ✅ `N23DCCN001_DangKimAn/nodebook/logistic_regression.ipynb` — with plots
- ✅ `N23DCCN001_DangKimAn/nodebook/naive_bayes.ipynb` — with plots
- ✅ `N23DCCN001_DangKimAn/nodebook/svm.ipynb` — with plots

**TV4 (Deployment):**
- ✅ `N23DCCN138_PhamQuocAn/notebooks/IDS_ML_Notebook.py` — end-to-end pipeline with progress bars

**Root-level Utilities:**
- ✅ `config.py` — centralized paths, features, hyperparams
- ✅ `utils.py` — reusable functions (load_data, plot_confusion_matrix, format_alert_log)
- ✅ `requirements.txt` — all dependencies
- ✅ `model_comparison.py` — full comparison script

### 3.4. README.md Document

✅ **Location:** Root directory (`README.md`)

**Contains:**
- ✅ **Project Introduction** — overview of NIDS system
- ✅ **System Architecture** — ASCII diagram of data pipeline
- ✅ **Dataset Characteristics** — CIC-IDS2017 specs, 18 features, class distribution
- ✅ **Model Comparison Table** — all 5 models with metrics
  - Accuracy, Precision, Recall, F1-score comparison
  - Analysis of why Random Forest is deployed
- ✅ **Installation Guide** — pip install requirements.txt
- ✅ **Usage Instructions** — step-by-step (TV1 → TV2 → TV3 → TV4)
- ✅ **Team & Responsibilities** — member roles
- ✅ **Project Structure** — directory layout
- ✅ **Setup Instructions** — download dataset, run steps

### 3.5. Saved Best Model (.pkl)

✅ **Random Forest Model:** `N23DCCN138_PhamQuocAn/` (from TV4)

**If model file > 100MB:**
- ⚠️ **Option 1:** Use Git LFS (Large File Storage)
- ⚠️ **Option 2:** Provide Google Drive link in README ✅ (DONE in `N23DCCN138_PhamQuocAn/README.md`)

**Supporting files:**
- ✅ `artifacts/scaler.pkl` — StandardScaler for preprocessing
- ✅ `artifacts/label_encoder.pkl` — LabelEncoder for decoding predictions

### 3.6. Log File (alerts.log — Optional)

✅ **Location:** `N23DCCN138_PhamQuocAn/logs/alerts.log`

**Contains:** Real-time alert outputs from simulation

---

## 📊 Summary Table

| Requirement | Status | Location |
|-------------|--------|----------|
| **Git Repository** | ✅ | `is_security_group1` (GitHub) |
| **Commit History** | ✅ | `git log` shows continuous work |
| **Preprocessing** | ✅ | `HoangAnh_N23DCCN071/*.py` |
| **EDA Plots** | ✅ | `outputs/*.png` |
| **Class Balancing** | ✅ | `prepare_model_data.py` |
| **Feature Selection (18)** | ✅ | `config.py` → `SELECTED_FEATURES` |
| **5 ML Models** | ✅ | LR, SVM, NB, KNN, RF |
| **Classification Reports** | ✅ | In each notebook |
| **Confusion Matrices** | ✅ | 5 PNG files generated |
| **Model Comparison** | ✅ | `model_comparison.py` + 3 charts |
| **Best Model Selection** | ✅ | Random Forest (highest recall) |
| **Real-time Alerts** | ✅ | Suricata-style format in `alerts.log` |
| **README.md** | ✅ | Professional + architecture + table |
| **requirements.txt** | ✅ | All dependencies listed |
| **Saved Model (.pkl)** | ✅ | Google Drive link in README |
| **Utility Functions** | ✅ | `utils.py` (load_data, plot_cm, format_alert) |
| **Configuration File** | ✅ | `config.py` (paths, features, hyperparams) |

---

## 🎯 Submission Status: **COMPLETE ✅**

All requirements from the PDF have been implemented and are ready for submission.
