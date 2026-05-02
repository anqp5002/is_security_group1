# 🏗️ Project Architecture & Configuration

Hiểu cách project được tổ chức và tại sao cần vào từng folder.

---

## 🎯 Overview: Tại Sao 4 Folder Riêng?

Dự án được chia thành **4 work streams** với người khác nhau:

```
┌─────────────────────────────────────────────────────────────┐
│ Root Level: Shared Config & Utilities                       │
│ • config.py        ← Central config for ALL teams           │
│ • utils.py         ← Shared functions (avoid duplication)   │
│ • requirements.txt ← Dependencies for ALL teams             │
└─────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        ↓                     ↓                     ↓
    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
    │ TV1: Hoàng  │    │ TV2: Hoàng  │    │ TV3: Đặng   │    │ TV4: Phạm  │
    │ N23DCCN071  │    │ N23DCCN071  │    │ N23DCCN001  │    │ N23DCCN138 │
    │             │    │             │    │             │    │            │
    │ EDA Data    │ → │ Feature     │ → │ Train 3     │ → │ Train RF   │
    │ Cleaning    │    │ Selection   │    │ Models      │    │ + Deploy   │
    │             │    │ + Balancing │    │ (LR/NB/SVM) │    │ (KNN/RF)   │
    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       10-15 min          5-10 min           30-60 min           60-120 min
```

---

## 📋 config.py — Central Configuration

**Tác dụng:** Giữ toàn bộ project **SYNCHRONIZED** trên cùng configuration.

### ❌ WRONG - Mỗi folder có config khác nhau
```
HoangAnh_N23DCCN071/config.py      ← Có 18 features
N23DCCN001_DangKimAn/config.py     ← Có 20 features ❌ KHÁC!
N23DCCN138_PhamQuocAn/config.py    ← Có 18 features
```
**Problem:** Features không match → models train sai

### ✅ CORRECT - Một config duy nhất ở root
```
config.py (root level)
  ↓
  Dùng bởi TV1, TV2, TV3, TV4
  ↓
  Tất cả dùng CÙNG 18 features
```

---

## 📊 config.py Chi Tiết

### 1️⃣ SELECTED_FEATURES (18 features chính)

```python
SELECTED_FEATURES = [
    "Protocol",           # TCP (6), UDP (17), ICMP (1)
    "Flow Duration",      # Thời gian flow (ms)
    "Tot Fwd Pkts",       # Tổng packets forward
    "Tot Bwd Pkts",       # Tổng packets backward
    "TotLen Fwd Pkts",    # Tổng bytes forward
    "TotLen Bwd Pkts",    # Tổng bytes backward
    "Fwd Pkt Len Mean",   # Avg packet size forward
    "Bwd Pkt Len Mean",   # Avg packet size backward
    "Flow Byts/s",        # Bytes per second
    "Flow Pkts/s",        # Packets per second
    "Pkt Len Mean",       # Avg packet size (both)
    "Pkt Len Std",        # Std dev packet size
    "SYN Flag Cnt",       # SYN flags (reconnaissance)
    "ACK Flag Cnt",       # ACK flags (normal)
    "FIN Flag Cnt",       # FIN flags (connection close)
    "RST Flag Cnt",       # RST flags (reset)
    "PSH Flag Cnt",       # PSH flags (data push)
    "URG Flag Cnt",       # URG flags (urgent)
]
```

**Tại sao 18 này?** Từ lab requirements - phải biết protocol, packet patterns, flags.

### 2️⃣ FEATURE_ALT_NAMES (Handle Column Name Variations)

```python
FEATURE_ALT_NAMES = {
    "Tot Fwd Pkts": "Total Fwd Packets",      # Dataset có tên dài
    "Flow Byts/s": "Flow Bytes/s",            # Dataset viết khác
    ...
}
```

**Tại sao cần?** CIC-IDS2017 dataset có nhiều versions khác nhau:
- Version 1: `Tot Fwd Pkts`
- Version 2: `Total Fwd Packets`

Script sẽ normalize → đảm bảo feature names match.

### 3️⃣ HYPERPARAMS (Configuration cho mỗi model)

```python
HYPERPARAMS = {
    "train_test_split": {
        "test_size": 0.2,          # 80% train, 20% test
        "stratify": True,          # Giữ class distribution
    },
    "smote": {
        "minority_threshold_pct": 0.10,  # Over-sample tới 10% của majority
    },
    "random_under_sampler": {
        "majority_ratio": 3,       # Cap majority ở 3× minority
    },
    "random_forest": {
        "n_estimators": 100,       # 100 trees
        "random_state": 42,        # Reproducible results
    },
}
```

**Ý nghĩa:**
- Tất cả models train trên **SAME balanced data**
- Fair comparison → chọn model tốt nhất

---

## 🔧 utils.py — Shared Utilities

**Tác dụng:** Viết code 1 lần, dùng nhiều lần → **Avoid duplication**

### ❌ WRONG - Copy-paste code
```python
# TV1 (preprocess.py)
def load_data(path):
    csv_files = glob.glob(path + "/*.csv")
    dfs = [pd.read_csv(f) for f in csv_files]
    return pd.concat(dfs)

# TV3 (notebook.py)
def load_data(path):  # DUPLICATE!
    csv_files = glob.glob(path + "/*.csv")
    dfs = [pd.read_csv(f) for f in csv_files]
    return pd.concat(dfs)

# TV4 (IDS_ML_Notebook.py)
def load_data(path):  # DUPLICATE AGAIN!
    csv_files = glob.glob(path + "/*.csv")
    dfs = [pd.read_csv(f) for f in csv_files]
    return pd.concat(dfs)
```
**Problem:** Code duplication, hard to maintain, bugs multiply

### ✅ CORRECT - Centralized utilities
```python
# utils.py (root level)
def load_data(data_path: str) -> pd.DataFrame:
    csv_files = sorted(glob.glob(os.path.join(data_path, "*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in: {data_path}")
    dfs = [pd.read_csv(path, low_memory=False) for path in csv_files]
    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.strip()
    return df

# TV1: preprocess.py
from utils import load_data
df = load_data("data/raw")

# TV3: notebook.py
from utils import load_data
df = load_data("data/raw")

# TV4: IDS_ML_Notebook.py
from utils import load_data
df = load_data("data/raw")
```

---

## 📚 utils.py Functions

### 1️⃣ load_data(data_path)
```python
df = load_data("data/raw")
# Returns: DataFrame với 8 CSV files merged
# Automatically strips whitespace từ column names
```

**Used by:** TV1, TV3, TV4

**Example output:**
```
Found 8 CSV file(s) in 'data/raw'
  Loaded Monday-WorkingHours.pcap_ISCX.csv: 676,412 rows
  Loaded Tuesday-WorkingHours.pcap_ISCX.csv: 1,234,567 rows
  ...
Combined: 2,830,743 rows x 79 columns
```

---

### 2️⃣ plot_confusion_matrix(y_true, y_pred, class_names, ...)
```python
from utils import plot_confusion_matrix

cm = plot_confusion_matrix(
    y_true=y_test,
    y_pred=predictions,
    class_names=["BENIGN", "DDoS", "PortScan", "Bot", "Web Attack"],
    title="Random Forest Confusion Matrix",
    save_path="outputs/rf_confusion_matrix.png"
)
```

**Used by:** TV3 (3 models), TV4 (2 models) = 5 confusion matrices

**What it does:**
- Generate heatmap từ predictions
- Add titles, labels, colors
- Save PNG automatically

---

### 3️⃣ format_alert_log(label, dst_port, src_ip, dst_ip, timestamp)
```python
from utils import format_alert_log

alert = format_alert_log(
    label="DDoS",
    dst_port=80,
    src_ip="192.168.1.100",
    dst_ip="10.0.0.1",
    timestamp="2026-05-02 14:35:22"
)

print(alert)
# Output: [2026-05-02 14:35:22] [ALERT] Suspicious traffic detected: DDoS. 
#         Destination Port: 80. Src IP: 192.168.1.100. Dst IP: 10.0.0.1.
```

**Used by:** TV4 (Real-time alerts)

---

## 📂 Tại Sao Phải Vào Từng Folder?

Vì **mỗi work stream có data output khác nhau**:

### TV1: HoangAnh_N23DCCN071
```bash
cd HoangAnh_N23DCCN071
python preprocess.py
# Output: preprocess data đặc thù cho TV1
#   - data/processed/merged_cleaned.csv
#   - outputs/attack_distribution.png
#   - outputs/correlation_heatmap.png
```

### TV2: Vẫn HoangAnh_N23DCCN071
```bash
# Vẫn trong folder, dùng output của TV1
python prepare_model_data.py
# Output: Feature-selected data cho model training
#   - data/final/X_train.csv
#   - data/final/y_train.csv
#   - artifacts/scaler.pkl
#   - artifacts/label_encoder.pkl
```

### TV3: N23DCCN001_DangKimAn
```bash
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
# Output: Model-specific artifacts
#   - Logistic Regression model
#   - data/artifacts/logistic_regression.png
```

### TV4: N23DCCN138_PhamQuocAn
```bash
cd ../N23DCCN138_PhamQuocAn
python notebooks/IDS_ML_Notebook.py
# Output: Advanced models + real-time alerts
#   - artifacts/knn_model.pkl
#   - artifacts/random_forest_model.pkl
#   - logs/alerts.log
```

---

## 🔄 Data Flow

```
Root: config.py + utils.py (Shared)
  ↓
┌────────────────────────────────────────────┐
│ TV1: preprocess.py (HoangAnh)              │
│ Input: data/raw/ (8 CSV files)             │
│ Output: data/processed/merged_cleaned.csv  │
│ (Uses: utils.load_data)                    │
└────────────────────────────────────────────┘
  ↓
┌────────────────────────────────────────────┐
│ TV2: prepare_model_data.py (HoangAnh)      │
│ Input: data/processed/merged_cleaned.csv   │
│ Config: config.SELECTED_FEATURES           │
│ Config: config.HYPERPARAMS                 │
│ Output: data/final/X_train.csv             │
│         artifacts/scaler.pkl               │
│         artifacts/label_encoder.pkl        │
└────────────────────────────────────────────┘
  ↓
┌────────────────────────────────────────────┐
│ TV3: Train 3 Models (Đặng)                 │
│ Input: data/final/X_train.csv              │
│ Config: config.HYPERPARAMS                 │
│ Output: LR/NB/SVM models + confusion mats  │
│ (Uses: utils.plot_confusion_matrix)        │
└────────────────────────────────────────────┘
  ↓
┌────────────────────────────────────────────┐
│ TV4: Train RF + KNN (Phạm)                 │
│ Input: data/final/X_train.csv              │
│ Config: config.HYPERPARAMS                 │
│ Output: RF/KNN models + alerts             │
│ (Uses: utils.plot_confusion_matrix)        │
│ (Uses: utils.format_alert_log)             │
└────────────────────────────────────────────┘
  ↓
┌────────────────────────────────────────────┐
│ TV5: Compare All 5 Models (Root)           │
│ Input: outputs từ TV3 + TV4                │
│ Config: config.HYPERPARAMS (cho reference) │
│ Output: Comparison charts + CSV            │
└────────────────────────────────────────────┘
```

---

## 💡 Ví Dụ: Thay Đổi Config Ảnh Hưởng Gì?

### Scenario: Thay đổi số features từ 18 → 15

**Nếu config ở mỗi folder:**
```
HoangAnh_N23DCCN071/config.py: 18 features
N23DCCN001_DangKimAn/config.py: 15 features ❌ MISMATCH!
N23DCCN138_PhamQuocAn/config.py: 18 features ❌ MISMATCH!

Kết quả:
- TV2 select 18 features
- TV3 train models với 15 features
- Models crash! (feature count mismatch)
```

**Với root config.py:**
```
config.py (root): 18 → 15 features (change here)
  ↓
All TV1, TV2, TV3, TV4 automatically use 15 features
  ↓
All models train consistently
  ✓ Synchronized!
```

---

## 🎓 Best Practices (Tại Sao Tổ Chức Vậy?)

| Vấn đề | Giải pháp | File |
|--------|----------|------|
| Features không sync | Centralize features | config.py |
| Hyperparams khác nhau | Centralize hyperparams | config.py |
| Code duplication | Shared utilities | utils.py |
| Data path khác | Centralize paths | config.py |
| Column name variations | FEATURE_ALT_NAMES | config.py |
| Reusable functions | Load data, plot, alerts | utils.py |

---

## 📝 Khi Nào Modify Config?

### ✅ Modify config.py khi:
- Muốn change số features
- Muốn change hyperparameters
- Muốn change data paths
- Muốn change train/test split ratio

### ❌ KHÔNG modify các folder khác:
- Mỗi folder chỉ modify nội dung analysis nó
- TV1 improve EDA charts? Modify TV1 scripts
- TV3 add new model? Modify TV3 notebooks
- Nhưng config vẫn share từ root

---

## 🚀 Summary

```
┌─────────────────────────────────────────────┐
│ config.py + utils.py (ROOT LEVEL)          │
│ ────────────────────────────────────────   │
│ • config.py: Làm gì?                       │
│   - 18 features (SELECTED_FEATURES)        │
│   - 6 hyperparameters (HYPERPARAMS)        │
│   - Paths & settings centralized           │
│                                             │
│ • utils.py: Làm gì?                        │
│   - load_data() → load 8 CSVs              │
│   - plot_confusion_matrix() → heatmaps     │
│   - format_alert_log() → Suricata alerts   │
│                                             │
│ Result:                                     │
│ ✓ Tất cả teams dùng config giống nhau     │
│ ✓ Không code duplication                   │
│ ✓ Easy to modify (1 file affect all)       │
│ ✓ Reproducible results                     │
└─────────────────────────────────────────────┘
```

**Điểm quan trọng:** Không phải tất cả config ở root! Mỗi folder TV1-TV4 vẫn có scripting logic riêng. Root config chỉ **shared settings** mà tất cả dùng.

---

**Last Updated:** May 2, 2026
