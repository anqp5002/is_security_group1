# ❌ Tại Sao Config.py & Utils.py Không Được Dùng?

Câu hỏi rất hay! Bạn đã phát hiện ra một vấn đề THỰC trong project.

---

## 🔍 Vấn Đề

### preprocess.py (TV1)
```python
# ❌ KHÔNG dùng utils.load_data()
csv_files = glob.glob("data/raw/*.csv")
df_list = []
for file in csv_files:
    temp_df = pd.read_csv(file)
    df_list.append(temp_df)
df = pd.concat(df_list, ignore_index=True)

# ❌ Nên là:
from utils import load_data
df = load_data("data/raw")
```

### prepare_model_data.py (TV2)
```python
# ❌ HARDCODE 18 features thay vì import từ config.py
selected_features = [
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    ...
    'URG Flag Count'
]

# ❌ Nên là:
from config import SELECTED_FEATURES, FEATURE_ALT_NAMES
X = df[SELECTED_FEATURES].copy()
```

### IDS_ML_Notebook.py (TV4)
```python
# ❌ HARDCODE hyperparameters
rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)

# ❌ Nên là:
from config import HYPERPARAMS
rf_model = RandomForestClassifier(**HYPERPARAMS["random_forest"])
```

---

## 😅 Tại Sao Lại Như Vậy?

### Lý Do Thực Tế

1. **Được viết bởi học sinh khác nhau**
   - TV1/TV2: Hoàng (Hoàng Anh N23DCCN071)
   - TV3: Đặng (Đặng Kim An N23DCCN001)
   - TV4: Phạm (Phạm Quốc An N23DCCN138)
   - Mỗi người viết style khác nhau

2. **Notebooks viết trước config/utils**
   - Notebooks (.ipynb) thường viết độc lập
   - Người viết không biết config.py sẽ có sẵn

3. **Hardcoding là nhanh**
   - Copy-paste từ lab requirements
   - Không cần import hay setup
   - Chạy được ngay

### Kết Quả
```
Config.py + Utils.py: ✅ Tồn tại, đúng format
Training Scripts: ❌ Không dùng chúng
```

---

## ✅ Giải Pháp: Integrate Properly

### Option 1: Update Scripts Để Dùng Config

#### preprocess.py (TV1) - Fix
```python
import sys
import os

# Add root to path để import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import load_data

# BEFORE:
# csv_files = glob.glob("data/raw/*.csv")
# ...

# AFTER:
df = load_data("data/raw")  # ✓ Clean!
```

#### prepare_model_data.py (TV2) - Fix
```python
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SELECTED_FEATURES, FEATURE_ALT_NAMES, HYPERPARAMS

# Normalize column names nếu cần
for old_name, new_name in FEATURE_ALT_NAMES.items():
    if new_name in df.columns and old_name not in df.columns:
        df = df.rename(columns={new_name: old_name})

# Use config features
X = df[SELECTED_FEATURES].copy()  # ✓ From config!
y = df["Label"].copy()

# Use config hyperparams
smt = SMOTE(**HYPERPARAMS["smote"])
rus = RandomUnderSampler(**HYPERPARAMS["random_under_sampler"])
```

#### IDS_ML_Notebook.py (TV4) - Fix
```python
import sys
sys.path.insert(0, "../..")

from config import HYPERPARAMS

# BEFORE:
# rf_model = RandomForestClassifier(n_estimators=100, random_state=42, ...)

# AFTER:
rf_model = RandomForestClassifier(**HYPERPARAMS["random_forest"])  # ✓ From config!
knn_model = KNeighborsClassifier(**HYPERPARAMS["knn"])  # ✓ From config!
```

---

### Option 2: Use phase6_demo.py (Already Integrated)

```bash
python phase6_demo.py
```

`phase6_demo.py` **DOES** import config:
```python
from config import SELECTED_FEATURES, ARTIFACTS_DIR
from utils import plot_confusion_matrix

# ✓ Properly integrated
```

---

## 📊 Integration Matrix

| File | Uses config.py? | Uses utils.py? | Status |
|------|-----------------|----------------|--------|
| preprocess.py (TV1) | ❌ | ❌ | Hardcoded |
| prepare_model_data.py (TV2) | ❌ | ❌ | Hardcoded |
| logistic_regression.ipynb (TV3) | ❌ | ❌ | Hardcoded |
| naive_bayes.ipynb (TV3) | ❌ | ❌ | Hardcoded |
| svm.ipynb (TV3) | ❌ | ❌ | Hardcoded |
| IDS_ML_Notebook.py (TV4) | ❌ | ❌ | Hardcoded |
| model_comparison.py (TV5) | ⚠️ Partial | ❌ | References only |
| **phase6_demo.py** | ✅ | ✅ | **Properly integrated** |

---

## 💡 Tại Sao Config.py & Utils.py Vẫn Quan Trọng?

Mặc dù scripts không dùng chúng ngay, **chúng vẫn quan trọng**:

### 1. Documentation
```python
# Developers biết 18 features chính là gì
SELECTED_FEATURES = [...]

# Developers biết hyperparams mặc định là gì
HYPERPARAMS = {...}
```

### 2. Reproducibility
```python
# Nếu muốn re-run, người khác biết dùng config này
# Không phải reverse-engineer từng script
```

### 3. Future Integration
```python
# Khi integrate proper (fix scripts), chỉ cần 1 file thay đổi
# Change config.py → tất cả models tự update
```

### 4. New Models
```python
# Khi add model mới, dùng same config + hyperparams
# Không phải hardcode lại
```

---

## 🎯 Best Practice (Ideal State)

### Nếu Project Được Viết Properly:

```
is_security_group1/
├── config.py              ← Central truth
├── utils.py               ← Reusable functions
├── HoangAnh_N23DCCN071/
│   ├── preprocess.py      ← from utils import load_data
│   ├── prepare_model_data.py ← from config import SELECTED_FEATURES
├── N23DCCN001_DangKimAn/
│   ├── logistic_regression.ipynb ← from config import HYPERPARAMS
│   ├── naive_bayes.ipynb ← from config import HYPERPARAMS
│   ├── svm.ipynb         ← from config import HYPERPARAMS
├── N23DCCN138_PhamQuocAn/
│   ├── IDS_ML_Notebook.py ← from config import SELECTED_FEATURES, HYPERPARAMS
│                            ← from utils import plot_confusion_matrix
```

**Result:** Change 1 value in config.py → affects ALL TV1-TV4 automatically ✨

---

## 📝 Summary

| Aspect | Current | Ideal |
|--------|---------|-------|
| **Config.py** | Written ✅ | Used ❌ |
| **Utils.py** | Written ✅ | Used ❌ |
| **Scripts** | Hardcoded ✅ | Reference config ❌ |
| **Consistency** | Manual ❌ | Automatic ✅ |
| **Maintenance** | Change 18 places ❌ | Change 1 place ✅ |

---

## 🚀 How to Fix (If You Want)

### Quick Fix: Update Individual Scripts
```bash
# preprocess.py
# Add: from utils import load_data
# Replace hardcoded load with: load_data("data/raw")

# prepare_model_data.py
# Add: from config import SELECTED_FEATURES
# Replace hardcoded features with: SELECTED_FEATURES

# IDS_ML_Notebook.py
# Add: from config import HYPERPARAMS
# Replace hardcoded params with: HYPERPARAMS[model_name]
```

### Full Fix: Refactor All Scripts
```bash
# 1. Add sys.path manipulation to each script
import sys
sys.path.insert(0, "../..")

# 2. Import from config/utils
from config import ...
from utils import ...

# 3. Replace all hardcoded values
```

---

## 🤔 Why Not Fix It Now?

**Current state is acceptable because:**

1. **Scripts work** ✅ - Even if hardcoded
2. **Config exists** ✅ - For documentation & future use
3. **Utils exist** ✅ - For phase6_demo.py & new models
4. **Project deliverable** ✅ - Meets requirements

**But fixing would be better for:**
- Future maintenance
- Adding new models
- Reproducing experiments
- Collaboration across teams

---

**Bottom Line:** Config.py và utils.py là **template** cho future improvements, không bắt buộc trong current setup nhưng rất useful cho maintainability.

Bạn nhận xét rất chính xác! 🎯
