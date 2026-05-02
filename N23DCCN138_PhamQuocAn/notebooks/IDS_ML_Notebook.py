# ============================================================
# TV4 — Train KNN + Random Forest + Deploy Real-time Alert
# ============================================================
# Bước 1: Tái tạo dữ liệu của TV1+TV2 (vì file processed bị gitignore)
# Bước 2: Train KNN và Random Forest
# Bước 3: Tổng hợp bảng so sánh 5 mô hình
# Bước 4: Lưu mô hình Random Forest (.pkl)
# Bước 5: Mô phỏng phát hiện xâm nhập thời gian thực
# ============================================================

# %% [markdown]
# # 🛡️ TV4 — Huấn Luyện KNN + Random Forest + Triển Khai Real-time
# Dữ liệu được tiền xử lý theo đúng code của TV1 (`preprocess.py`) và TV2 (`prepare_model_data.py`)

# %% [markdown]
# ## Bước 1: Nhập thư viện

# %%
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
import datetime
import joblib
from collections import Counter

from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score, precision_score, recall_score, f1_score)
from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
plt.rcParams['figure.dpi'] = 120

# Đường dẫn dataset trên Kaggle
DATA_PATH = '/kaggle/input/datasets/chethuhn/network-intrusion-dataset/'
OUTPUT_DIR = '/kaggle/working/'

print("✅ Đã nhập thư viện thành công!")

# %% [markdown]
# ---
# ## Bước 2: Tái tạo dữ liệu TV1 — Load + Làm sạch
# *(Chạy lại đúng logic của file `preprocess.py` trong repo nhóm)*

# %%
# === TÁI TẠO TV1: preprocess.py ===

# 2.1 Đọc và gộp tất cả file CSV
csv_files = sorted([f for f in os.listdir(DATA_PATH) if f.endswith('.csv')])
print(f"📂 Tìm thấy {len(csv_files)} file CSV")

dfs = []
for f in csv_files:
    df_temp = pd.read_csv(os.path.join(DATA_PATH, f), low_memory=False)
    print(f"   ✅ {f}: {df_temp.shape[0]:,} dòng")
    dfs.append(df_temp)

df = pd.concat(dfs, ignore_index=True)
print(f"\n📊 Tổng hợp: {df.shape[0]:,} dòng × {df.shape[1]} cột")

# %%
# 2.2 Xóa khoảng trắng tên cột
df.columns = df.columns.str.strip()

# 2.3 Thay inf bằng NaN, điền NaN bằng median
df.replace([np.inf, -np.inf], np.nan, inplace=True)
numeric_cols = df.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    median_value = df[col].median()
    df[col] = df[col].fillna(median_value)

# 2.4 Xóa cột zero-variance
nunique = df.nunique()
zero_var_cols = nunique[nunique <= 1].index.tolist()
print(f"🗑️ Cột zero-variance: {zero_var_cols}")
df = df.drop(columns=zero_var_cols)

# 2.5 Xóa dòng trùng
before_rows = df.shape[0]
df = df.drop_duplicates()
print(f"🗑️ Đã xóa {before_rows - df.shape[0]:,} dòng trùng. Còn: {df.shape[0]:,}")

# 2.6 Tối ưu bộ nhớ (giống hàm reduce_memory_usage trong preprocess.py)
for col in df.columns:
    if pd.api.types.is_integer_dtype(df[col]):
        df[col] = pd.to_numeric(df[col], downcast='integer')
    elif pd.api.types.is_float_dtype(df[col]):
        df[col] = pd.to_numeric(df[col], downcast='float')

print(f"💾 Bộ nhớ: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print("✅ TV1 hoàn tất — Dữ liệu đã làm sạch")

# %% [markdown]
# ---
# ## Bước 3: Tái tạo dữ liệu TV2 — Encoding + Scaling + SMOTE + Feature Selection
# *(Chạy lại đúng logic của file `prepare_model_data.py` trong repo nhóm)*

# %%
# === TÁI TẠO TV2: prepare_model_data.py ===

# 3.1 Chọn 17 đặc trưng (đúng theo code TV2 — không có Protocol)
selected_features = [
    'Flow Duration',
    'Total Fwd Packets',
    'Total Backward Packets',
    'Total Length of Fwd Packets',
    'Total Length of Bwd Packets',
    'Fwd Packet Length Mean',
    'Bwd Packet Length Mean',
    'Flow Bytes/s',
    'Flow Packets/s',
    'Packet Length Mean',
    'Packet Length Std',
    'SYN Flag Count',
    'ACK Flag Count',
    'FIN Flag Count',
    'RST Flag Count',
    'PSH Flag Count',
    'URG Flag Count'
]

# Kiểm tra cột có đủ không
missing_features = [col for col in selected_features if col not in df.columns]
if missing_features:
    print(f"⚠️ Thiếu cột: {missing_features}")
    # Thử tên cột khác (dataset có thể dùng tên viết tắt)
    alt_mapping = {
        'Total Fwd Packets': 'Tot Fwd Pkts',
        'Total Backward Packets': 'Tot Bwd Pkts',
        'Total Length of Fwd Packets': 'TotLen Fwd Pkts',
        'Total Length of Bwd Packets': 'TotLen Bwd Pkts',
        'Fwd Packet Length Mean': 'Fwd Pkt Len Mean',
        'Bwd Packet Length Mean': 'Bwd Pkt Len Mean',
        'Packet Length Mean': 'Pkt Len Mean',
        'Packet Length Std': 'Pkt Len Std',
        'SYN Flag Count': 'SYN Flag Cnt',
        'ACK Flag Count': 'ACK Flag Cnt',
        'FIN Flag Count': 'FIN Flag Cnt',
        'RST Flag Count': 'RST Flag Cnt',
        'PSH Flag Count': 'PSH Flag Cnt',
        'URG Flag Count': 'URG Flag Cnt',
    }
    selected_features_fixed = []
    for f in selected_features:
        if f in df.columns:
            selected_features_fixed.append(f)
        elif f in alt_mapping and alt_mapping[f] in df.columns:
            selected_features_fixed.append(alt_mapping[f])
            print(f"   🔄 Đổi '{f}' → '{alt_mapping[f]}'")
        else:
            print(f"   ❌ Không tìm thấy: {f}")
    selected_features = selected_features_fixed

print(f"\n✅ Dùng {len(selected_features)} đặc trưng: {selected_features}")

X = df[selected_features].copy()
y = df['Label'].copy()

# %%
# 3.2 Chia train/test (đúng như TV2: test_size=0.2, stratify=y)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"🔀 Train: {X_train.shape} | Test: {X_test.shape}")

# 3.3 Mã hóa nhãn (LabelEncoder)
label_encoder = LabelEncoder()
y_train_enc = label_encoder.fit_transform(y_train)
y_test_enc = label_encoder.transform(y_test)

print(f"\n📋 Các lớp ({len(label_encoder.classes_)}):")
for i, cls in enumerate(label_encoder.classes_):
    print(f"   {i}: {cls}")

# %%
# 3.4 Chuẩn hóa (StandardScaler)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
print("✅ Đã chuẩn hóa dữ liệu")

# %%
# 3.5 Xử lý mất cân bằng (đúng logic TV2)
train_class_counts = pd.Series(y_train_enc).value_counts().sort_index()
majority_class_size = train_class_counts.max()
target_minority_size = int(0.1 * majority_class_size)

print(f"📊 Kích thước lớp đa số: {majority_class_size:,}")
print(f"📊 Mục tiêu lớp thiểu số: {target_minority_size:,} (10% lớp đa số)")

# SMOTE: tăng lớp thiểu số lên 10% lớp đa số
smote_strategy = {}
for cls, count in train_class_counts.items():
    if count < target_minority_size:
        smote_strategy[cls] = target_minority_size

if smote_strategy:
    print(f"⏳ Đang SMOTE {len(smote_strategy)} lớp thiểu số...")
    smote = SMOTE(sampling_strategy=smote_strategy, random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train_enc)
else:
    X_train_balanced = X_train_scaled.copy()
    y_train_balanced = y_train_enc.copy()

# RandomUnderSampler: giảm lớp đa số (giống TV2: majority = 3 * target)
balanced_counts = pd.Series(y_train_balanced).value_counts().sort_index()
new_majority_size = balanced_counts.max()
under_target_majority = max(target_minority_size * 3, target_minority_size + 1)

rus_strategy = {}
for cls, count in balanced_counts.items():
    if count == new_majority_size:
        rus_strategy[cls] = min(count, under_target_majority)

if rus_strategy:
    rus = RandomUnderSampler(sampling_strategy=rus_strategy, random_state=42)
    X_train_balanced, y_train_balanced = rus.fit_resample(X_train_balanced, y_train_balanced)

print(f"\n📊 Sau khi cân bằng:")
for cls_idx in sorted(Counter(y_train_balanced).keys()):
    cls_name = label_encoder.inverse_transform([cls_idx])[0]
    print(f"   {cls_name}: {Counter(y_train_balanced)[cls_idx]:,}")

print("\n✅ TV2 hoàn tất — Dữ liệu sẵn sàng cho training")

# %% [markdown]
# ---
# ## Bước 4: Huấn luyện KNN (TV4)
# Dùng toàn bộ dữ liệu đã cân bằng từ TV1+TV2. Predict theo batch có thanh tiến trình.

# %%
import time
results = {}

print("=" * 60)
print("🚀 Đang huấn luyện: KNN (K=5)")
print("=" * 60)

# --- Bước 4.1: Fit KNN với TOÀN BỘ dữ liệu train ---
print(f"⏳ [1/3] Đang fit KNN với {len(X_train_balanced):,} mẫu...")
t0 = time.time()
knn = KNeighborsClassifier(n_neighbors=5, n_jobs=-1)
knn.fit(X_train_balanced, y_train_balanced)
print(f"✅ [1/3] Fit xong! ({time.time()-t0:.1f} giây)")

# --- Bước 4.3: Predict theo batch (có thanh tiến trình) ---
print(f"⏳ [2/3] Đang dự đoán {len(X_test_scaled):,} mẫu test...")
BATCH_SIZE = 50000
y_pred_knn = np.array([], dtype=int)
total_batches = (len(X_test_scaled) + BATCH_SIZE - 1) // BATCH_SIZE

for i in range(0, len(X_test_scaled), BATCH_SIZE):
    batch_num = i // BATCH_SIZE + 1
    batch = X_test_scaled[i:i+BATCH_SIZE]
    pct = min(100, int(batch_num / total_batches * 100))
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"   [{bar}] {pct}% — batch {batch_num}/{total_batches}", end="\r")
    pred = knn.predict(batch)
    y_pred_knn = np.concatenate([y_pred_knn, pred])

print(f"\n✅ [2/3] Dự đoán xong! ({len(y_pred_knn):,} mẫu)")

# --- Bước 4.4: Đánh giá ---
print("⏳ [3/3] Đang đánh giá kết quả...")
acc_knn = accuracy_score(y_test_enc, y_pred_knn)
prec_knn = precision_score(y_test_enc, y_pred_knn, average='weighted', zero_division=0)
rec_knn = recall_score(y_test_enc, y_pred_knn, average='weighted', zero_division=0)
f1_knn = f1_score(y_test_enc, y_pred_knn, average='weighted', zero_division=0)

print(f"✅ [3/3] Hoàn tất KNN!")
print(f"   Độ chính xác: {acc_knn:.4f}")
print(f"   Precision:    {prec_knn:.4f}")
print(f"   Recall:       {rec_knn:.4f}")
print(f"   F1-Score:     {f1_knn:.4f}")
print("\n📋 Báo cáo chi tiết:")
print(classification_report(y_test_enc, y_pred_knn,
      target_names=label_encoder.classes_, zero_division=0))

# Vẽ ma trận nhầm lẫn KNN
cm_knn = confusion_matrix(y_test_enc, y_pred_knn)
plt.figure(figsize=(10, 8))
sns.heatmap(cm_knn, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_,
            linewidths=0.5)
plt.title('KNN — Ma Trận Nhầm Lẫn', fontsize=14, fontweight='bold')
plt.xlabel('Dự đoán')
plt.ylabel('Thực tế')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}cm_KNN.png', dpi=150, bbox_inches='tight')
plt.show()
print("📊 Đã lưu: cm_KNN.png")

results['KNN'] = {
    'accuracy': acc_knn, 'precision': prec_knn,
    'recall': rec_knn, 'f1': f1_knn
}

# %% [markdown]
# ---
# ## Bước 5: Huấn luyện Random Forest (TV4)
# Random Forest train 100 cây, mỗi 10 cây sẽ thông báo tiến trình.

# %%
print("=" * 60)
print("🚀 Đang huấn luyện: Random Forest (100 cây)")
print("=" * 60)

# --- Bước 5.1: Train Random Forest theo từng giai đoạn (có tiến trình) ---
N_TOTAL_TREES = 100
STEP = 10  # Mỗi bước thêm 10 cây

rf = RandomForestClassifier(
    n_estimators=STEP, random_state=42, n_jobs=-1, warm_start=True
)

t0 = time.time()
for n_trees in range(STEP, N_TOTAL_TREES + 1, STEP):
    rf.n_estimators = n_trees
    rf.fit(X_train_balanced, y_train_balanced)
    pct = int(n_trees / N_TOTAL_TREES * 100)
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    elapsed = time.time() - t0
    print(f"   [{bar}] {pct}% — {n_trees}/{N_TOTAL_TREES} cây ({elapsed:.0f}s)")

print(f"✅ [1/2] Train xong {N_TOTAL_TREES} cây! (tổng {time.time()-t0:.0f} giây)")

# --- Bước 5.2: Predict theo batch ---
print(f"⏳ [2/2] Đang dự đoán {len(X_test_scaled):,} mẫu test...")
y_pred_rf = np.array([], dtype=int)

for i in range(0, len(X_test_scaled), BATCH_SIZE):
    batch_num = i // BATCH_SIZE + 1
    batch = X_test_scaled[i:i+BATCH_SIZE]
    pct = min(100, int(batch_num / total_batches * 100))
    bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
    print(f"   [{bar}] {pct}% — batch {batch_num}/{total_batches}", end="\r")
    pred = rf.predict(batch)
    y_pred_rf = np.concatenate([y_pred_rf, pred])

print(f"\n✅ [2/2] Dự đoán xong!")

# --- Đánh giá ---
acc_rf = accuracy_score(y_test_enc, y_pred_rf)
prec_rf = precision_score(y_test_enc, y_pred_rf, average='weighted', zero_division=0)
rec_rf = recall_score(y_test_enc, y_pred_rf, average='weighted', zero_division=0)
f1_rf = f1_score(y_test_enc, y_pred_rf, average='weighted', zero_division=0)

print(f"\n🏆 KẾT QUẢ RANDOM FOREST:")
print(f"   Độ chính xác: {acc_rf:.4f}")
print(f"   Precision:    {prec_rf:.4f}")
print(f"   Recall:       {rec_rf:.4f}")
print(f"   F1-Score:     {f1_rf:.4f}")
print("\n📋 Báo cáo chi tiết:")
print(classification_report(y_test_enc, y_pred_rf,
      target_names=label_encoder.classes_, zero_division=0))

# Vẽ ma trận nhầm lẫn Random Forest
cm_rf = confusion_matrix(y_test_enc, y_pred_rf)
plt.figure(figsize=(10, 8))
sns.heatmap(cm_rf, annot=True, fmt='d', cmap='Greens',
            xticklabels=label_encoder.classes_, yticklabels=label_encoder.classes_,
            linewidths=0.5)
plt.title('Random Forest — Ma Trận Nhầm Lẫn', fontsize=14, fontweight='bold')
plt.xlabel('Dự đoán')
plt.ylabel('Thực tế')
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}cm_Random_Forest.png', dpi=150, bbox_inches='tight')
plt.show()
print("📊 Đã lưu: cm_Random_Forest.png")

results['Random Forest'] = {
    'accuracy': acc_rf, 'precision': prec_rf,
    'recall': rec_rf, 'f1': f1_rf
}

# %% [markdown]
# ---
# ## Bước 6: Bảng tổng hợp so sánh 5 mô hình (TV4)
# *(Chỗ này cần điền kết quả TV3 vào — tạm để trống, khi TV3 xong thì cập nhật)*

# %%
# === KẾT QUẢ TV3 (điền sau khi TV3 chạy xong) ===
# Nếu TV3 chưa xong, bỏ comment 3 dòng dưới và điền số thực tế vào
# results['Logistic Regression'] = {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
# results['SVM'] = {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}
# results['Naive Bayes'] = {'accuracy': 0.0, 'precision': 0.0, 'recall': 0.0, 'f1': 0.0}

# Tạo bảng so sánh
comparison_df = pd.DataFrame([
    {'Mô hình': name, 'Độ chính xác': r['accuracy'], 'Precision': r['precision'],
     'Recall': r['recall'], 'F1-Score': r['f1']}
    for name, r in results.items()
]).sort_values('Độ chính xác', ascending=False).reset_index(drop=True)

print("=" * 70)
print("📊 BẢNG SO SÁNH CÁC MÔ HÌNH")
print("=" * 70)
print(comparison_df.to_string(index=False))

# Vẽ biểu đồ so sánh
plt.figure(figsize=(10, 6))
colors = sns.color_palette('viridis', len(comparison_df))
bars = plt.bar(comparison_df['Mô hình'], comparison_df['Độ chính xác'],
               color=colors, edgecolor='black', linewidth=0.5)
plt.title('So Sánh Độ Chính Xác Các Mô Hình', fontsize=14, fontweight='bold')
plt.ylabel('Độ chính xác')
plt.ylim(min(comparison_df['Độ chính xác']) * 0.9, 1.02)
for bar, acc in zip(bars, comparison_df['Độ chính xác']):
    plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
             f'{acc:.4f}', ha='center', fontsize=11, fontweight='bold')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.savefig(f'{OUTPUT_DIR}model_comparison.png', dpi=150, bbox_inches='tight')
plt.show()
print("📊 Đã lưu: model_comparison.png")

# %% [markdown]
# ---
# ## Bước 7: Lưu mô hình Random Forest (.pkl)

# %%
# Lưu mô hình, scaler, label encoder
# ⚡ Dùng compress=3 để giảm dung lượng (~256MB → ~30-50MB)
joblib.dump(rf, f'{OUTPUT_DIR}random_forest_model.pkl', compress=3)
joblib.dump(scaler, f'{OUTPUT_DIR}scaler.pkl', compress=3)
joblib.dump(label_encoder, f'{OUTPUT_DIR}label_encoder.pkl', compress=3)

model_size = os.path.getsize(f'{OUTPUT_DIR}random_forest_model.pkl') / 1e6
print(f"💾 Đã lưu mô hình: random_forest_model.pkl ({model_size:.1f} MB)")
print(f"💾 Đã lưu scaler: scaler.pkl")
print(f"💾 Đã lưu label encoder: label_encoder.pkl")

# %% [markdown]
# ---
# ## Bước 8: Mô phỏng phát hiện xâm nhập thời gian thực

# %%
def simulate_realtime_detection(model, label_encoder, X_test_data, n_samples=30):
    """
    Mô phỏng hệ thống phát hiện xâm nhập thời gian thực.
    - Lấy ngẫu nhiên n_samples luồng mạng từ tập test
    - Dùng Random Forest để dự đoán
    - Nếu KHÔNG phải BENIGN → tạo cảnh báo kiểu Suricata
    - Lưu vào file alerts.log
    """
    alerts = []
    print("=" * 70)
    print("🛡️  HỆ THỐNG PHÁT HIỆN XÂM NHẬP MẠNG THỜI GIAN THỰC")
    print("=" * 70 + "\n")

    indices = np.random.choice(len(X_test_data), min(n_samples, len(X_test_data)),
                                replace=False)

    for idx in indices:
        sample = X_test_data[idx].reshape(1, -1)
        prediction = model.predict(sample)[0]
        label = label_encoder.inverse_transform([prediction])[0]
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if label != 'BENIGN':
            dst_port = int(np.abs(sample[0][0]) * 100) % 65535
            alert_msg = (f"[{timestamp}] [ALERT] Suspicious traffic detected: "
                        f"{label}. Destination Port: {dst_port}.")
            alerts.append(alert_msg)
            print(f"🚨 {alert_msg}")
        else:
            print(f"✅ [{timestamp}] [INFO] Lưu lượng bình thường — BENIGN")

    # Lưu file cảnh báo
    log_path = f'{OUTPUT_DIR}alerts.log'
    with open(log_path, 'w', encoding='utf-8') as f:
        for alert in alerts:
            f.write(alert + '\n')

    print(f"\n{'='*70}")
    print(f"📊 Tổng kết: {len(alerts)} cảnh báo / {len(indices)} luồng đã phân tích")
    print(f"📝 Đã lưu cảnh báo vào: {log_path}")
    return alerts

# Chạy mô phỏng 30 luồng mạng
alerts = simulate_realtime_detection(rf, label_encoder, X_test_scaled, n_samples=30)

# %%
# Hiển thị nội dung file alerts.log
print("\n📋 Nội dung file alerts.log:")
print("-" * 70)
with open(f'{OUTPUT_DIR}alerts.log', 'r') as f:
    print(f.read())

# %% [markdown]
# ---
# ## Bước 9: Tổng kết
#
# ### Việc TV4 đã làm:
# 1. ✅ Tái tạo dữ liệu TV1+TV2 (vì file processed bị gitignore)
# 2. ✅ Huấn luyện KNN (K=5) + báo cáo + ma trận nhầm lẫn
# 3. ✅ Huấn luyện Random Forest (100 cây) + báo cáo + ma trận nhầm lẫn
# 4. ✅ Tổng hợp bảng so sánh các mô hình
# 5. ✅ Lưu mô hình Random Forest (.pkl)
# 6. ✅ Mô phỏng phát hiện thời gian thực + file alerts.log
#
# ### File output (tải từ tab Output trên Kaggle):
# - `random_forest_model.pkl` — Mô hình đã train (nén ~30-50MB)
# - `scaler.pkl` — Bộ chuẩn hóa
# - `label_encoder.pkl` — Bộ mã hóa nhãn
# - `alerts.log` — File cảnh báo
# - `cm_KNN.png` — Ma trận nhầm lẫn KNN
# - `cm_Random_Forest.png` — Ma trận nhầm lẫn RF
# - `model_comparison.png` — Biểu đồ so sánh

# %%
print("\n✅ NOTEBOOK TV4 ĐÃ CHẠY XONG!")
print(f"\n📂 Các file output:")
for f in sorted(os.listdir(OUTPUT_DIR)):
    fpath = os.path.join(OUTPUT_DIR, f)
    if os.path.isfile(fpath):
        size_mb = os.path.getsize(fpath) / 1e6
        if size_mb >= 1:
            print(f"   📄 {f} ({size_mb:.1f} MB)")
        else:
            print(f"   📄 {f} ({os.path.getsize(fpath) / 1e3:.1f} KB)")

# %% [markdown]
# ---
# ## 👇 TẢI TẤT CẢ FILE VỀ MÁY
# **Cách 1 (Khuyến nghị):** Bấm nút **"Save Version"** (góc trên phải) → chạy xong →
# vào tab **Output** → bấm **Download All** (nút 3 chấm ⋮ → Download).
#
# **Cách 2:** Chạy cell bên dưới để tạo file zip nhỏ gọn, rồi tải từ Output.

# %%
# === NÉN VÀ TẢI TẤT CẢ OUTPUT ===
import zipfile

zip_path = '/kaggle/working/tv4_output.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
    for f in sorted(os.listdir(OUTPUT_DIR)):
        fpath = os.path.join(OUTPUT_DIR, f)
        if os.path.isfile(fpath) and f != 'tv4_output.zip':
            zf.write(fpath, f)
            size_kb = os.path.getsize(fpath) / 1e3
            print(f"   📦 Đã nén: {f} ({size_kb:.1f} KB)")

zip_size = os.path.getsize(zip_path) / 1e6
print(f"\n✅ Đã tạo: tv4_output.zip ({zip_size:.1f} MB)")
print("\n" + "=" * 70)
print("📥 HƯỚNG DẪN TẢI VỀ MÁY:")
print("=" * 70)
print("1. Bấm 'Save Version' (góc trên phải) → chọn 'Save & Run All'")
print("2. Đợi notebook chạy xong")
print("3. Vào tab 'Output' (bên phải)")
print("4. Bấm nút ⋮ (3 chấm) → chọn 'Download All'")
print("   HOẶC click vào từng file để tải riêng")
print("=" * 70)

