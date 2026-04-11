import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Tạo thư mục output nếu chưa có
os.makedirs("outputs", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

print("=== BAT DAU LOAD DATA ===")

# 1. Tìm tất cả file CSV trong data/raw
csv_files = glob.glob("data/raw/*.csv")

print(f"So file CSV tim thay: {len(csv_files)}")
for file in csv_files:
    print(file)

# Kiểm tra có đúng 8 file không
if len(csv_files) != 8:
    print("CANH BAO: Khong phai 8 file. Hay kiem tra lai thu muc data/raw")

# 2. Đọc từng file và gộp lại
df_list = []

for file in csv_files:
    print(f"Dang doc: {file}")
    temp_df = pd.read_csv(file)
    df_list.append(temp_df)

df = pd.concat(df_list, ignore_index=True)

print("\n=== SAU KHI GOP ===")
print("Kich thuoc du lieu:", df.shape)
print("5 dong dau:")
print(df.head())

# 3. Xóa khoảng trắng thừa ở tên cột
df.columns = df.columns.str.strip()

# 4. Thay inf thành NaN
df.replace([np.inf, -np.inf], np.nan, inplace=True)

# 5. Điền NaN bằng median của cột số
numeric_cols = df.select_dtypes(include=[np.number]).columns

for col in numeric_cols:
    median_value = df[col].median()
    df[col] = df[col].fillna(median_value)

print("\n=== KIEM TRA NaN SAU KHI FILL ===")
print(df.isna().sum().sort_values(ascending=False).head(10))

# 6. Xóa dòng trùng lặp
before_rows = df.shape[0]
df = df.drop_duplicates()
after_rows = df.shape[0]

print(f"\nSo dong bi trung da xoa: {before_rows - after_rows}")

# 7. Xóa cột zero-variance
nunique = df.nunique()
zero_var_cols = nunique[nunique <= 1].index.tolist()

print("\nCac cot zero-variance:")
print(zero_var_cols)

df = df.drop(columns=zero_var_cols)

print("Kich thuoc sau khi xoa cot zero-variance:", df.shape)

# 8. Tối ưu bộ nhớ
def reduce_memory_usage(dataframe):
    start_mem = dataframe.memory_usage(deep=True).sum() / 1024**2
    print(f"\nMemory truoc toi uu: {start_mem:.2f} MB")

    for col in dataframe.columns:
        if pd.api.types.is_integer_dtype(dataframe[col]):
            dataframe[col] = pd.to_numeric(dataframe[col], downcast='integer')
        elif pd.api.types.is_float_dtype(dataframe[col]):
            dataframe[col] = pd.to_numeric(dataframe[col], downcast='float')

    end_mem = dataframe.memory_usage(deep=True).sum() / 1024**2
    print(f"Memory sau toi uu: {end_mem:.2f} MB")
    print(f"Giam: {(start_mem - end_mem) / start_mem * 100:.2f}%")

    return dataframe

df = reduce_memory_usage(df)

# 9. Vẽ biểu đồ phân bố nhãn
if "Label" in df.columns:
    plt.figure(figsize=(14, 6))
    label_counts = df["Label"].value_counts()

    sns.barplot(x=label_counts.index, y=label_counts.values)
    plt.title("Distribution of Traffic Labels")
    plt.xlabel("Label")
    plt.ylabel("Count")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig("outputs/attack_distribution.png")
    plt.show()
else:
    print("KHONG TIM THAY COT Label")

# 10. Vẽ correlation heatmap
numeric_df = df.select_dtypes(include=[np.number])

if numeric_df.shape[1] >= 2:
    corr = numeric_df.iloc[:, :20].corr()

    plt.figure(figsize=(14, 10))
    sns.heatmap(corr, cmap="coolwarm", center=0)
    plt.title("Correlation Heatmap")
    plt.tight_layout()
    plt.savefig("outputs/correlation_heatmap.png")
    plt.show()

# 11. Lưu file cleaned
output_file = "data/processed/merged_cleaned.csv"
df.to_csv(output_file, index=False)

print(f"\nDa luu file cleaned tai: {output_file}")
print("=== HOAN THANH PREPROCESSING ===")