import os
import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler

# =========================
# 1. Tạo thư mục output
# =========================
os.makedirs("data/final", exist_ok=True)
os.makedirs("artifacts", exist_ok=True)

# =========================
# 2. Đọc dữ liệu sạch từ TV1
# =========================
df = pd.read_csv("data/processed/merged_cleaned.csv")

print("Shape ban đầu:", df.shape)
print("Các cột hiện có:", list(df.columns))

# Nếu tên cột có khoảng trắng thừa thì strip lại cho chắc
df.columns = df.columns.str.strip()

# =========================
# 3. Chọn đúng 18 feature theo đề bài
# =========================
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

# Kiểm tra các cột còn đủ không
missing_features = [col for col in selected_features if col not in df.columns]
if missing_features:
    raise ValueError(f"Thiếu các cột feature sau: {missing_features}")

if "Label" not in df.columns:
    raise ValueError("Không tìm thấy cột Label")

X = df[selected_features].copy()
y = df["Label"].copy()

print("\nPhân bố nhãn ban đầu:")
print(y.value_counts())

# =========================
# 4. Chia train/test trước
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nShape train:", X_train.shape)
print("Shape test:", X_test.shape)

# =========================
# 5. Encode Label
# =========================
label_encoder = LabelEncoder()
y_train_enc = label_encoder.fit_transform(y_train)
y_test_enc = label_encoder.transform(y_test)

print("\nCác lớp label:")
for i, cls in enumerate(label_encoder.classes_):
    print(i, "->", cls)

# =========================
# 6. Scale feature
# =========================
scaler = StandardScaler()

X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Chuyển lại về DataFrame để dễ xử lý tiếp
X_train_scaled = pd.DataFrame(X_train_scaled, columns=selected_features)
X_test_scaled = pd.DataFrame(X_test_scaled, columns=selected_features)

# =========================
# 7. Xử lý mất cân bằng dữ liệu
#    - chỉ làm trên TRAIN
# =========================

# Đếm số lượng từng lớp train
train_class_counts = pd.Series(y_train_enc).value_counts().sort_index()
majority_class_size = train_class_counts.max()

# Mục tiêu của đề: minority classes đạt khoảng 10% majority
target_minority_size = int(0.1 * majority_class_size)

# Tạo sampling_strategy cho SMOTE:
# chỉ tăng những lớp nhỏ hơn target_minority_size lên tới mức đó
smote_strategy = {}
for cls, count in train_class_counts.items():
    if count < target_minority_size:
        smote_strategy[cls] = target_minority_size

# Dùng SMOTE nếu có lớp cần tăng
if smote_strategy:
    smote = SMOTE(sampling_strategy=smote_strategy, random_state=42)
    X_train_balanced, y_train_balanced = smote.fit_resample(X_train_scaled, y_train_enc)
else:
    X_train_balanced, y_train_balanced = X_train_scaled.copy(), pd.Series(y_train_enc).copy()

# Sau SMOTE, giảm lớp majority để bớt bias
balanced_counts = pd.Series(y_train_balanced).value_counts().sort_index()
new_majority_size = balanced_counts.max()

# Ví dụ: giữ majority = 2 lần target_minority_size hoặc giữ hợp lý hơn
# Ở đây dùng cách an toàn: giảm majority xuống tối đa 3 lần target_minority_size
under_target_majority = max(target_minority_size * 3, target_minority_size + 1)

rus_strategy = {}
for cls, count in balanced_counts.items():
    if count == new_majority_size:
        rus_strategy[cls] = min(count, under_target_majority)

if rus_strategy:
    rus = RandomUnderSampler(sampling_strategy=rus_strategy, random_state=42)
    X_train_balanced, y_train_balanced = rus.fit_resample(X_train_balanced, y_train_balanced)

print("\nPhân bố nhãn train sau xử lý imbalance:")
print(pd.Series(y_train_balanced).value_counts().sort_index())

# =========================
# 8. Lưu dữ liệu cho TV3, TV4
# =========================
pd.DataFrame(X_train_balanced, columns=selected_features).to_csv("data/final/X_train.csv", index=False)
pd.DataFrame(X_test_scaled, columns=selected_features).to_csv("data/final/X_test.csv", index=False)

pd.DataFrame({"Label": y_train_balanced}).to_csv("data/final/y_train.csv", index=False)
pd.DataFrame({"Label": y_test_enc}).to_csv("data/final/y_test.csv", index=False)

# Lưu encoder + scaler để các bước sau dùng lại
joblib.dump(label_encoder, "artifacts/label_encoder.pkl")
joblib.dump(scaler, "artifacts/scaler.pkl")

print("\nĐã lưu:")
print("- data/final/X_train.csv")
print("- data/final/X_test.csv")
print("- data/final/y_train.csv")
print("- data/final/y_test.csv")
print("- artifacts/label_encoder.pkl")
print("- artifacts/scaler.pkl")

print("\n=== KIỂM TRA PROTOCOL ===")

for col in df.columns:
    if "protocol" in col.lower():
        print("Tim thay cot:", col)