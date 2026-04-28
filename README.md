# 🛡️ IDS Machine Learning Project - TV3

<p align="center">
  <img src="https://img.shields.io/badge/Main_Member-Kim_An-blue?style=for-the-badge&logo=github" alt="Member">
  <img src="https://img.shields.io/badge/Role-AI_Developer-green?style=for-the-badge" alt="Role">
  <img src="https://img.shields.io/badge/Task-SVM_NB_LR-orange?style=for-the-badge" alt="Task">
</p>

---

## 📖 Giới thiệu
Phần này thuộc **Thành viên 3** trong dự án Phân tích xâm nhập mạng (IDS). Nhiệm vụ chính là nghiên cứu, huấn luyện và tối ưu hóa 3 thuật toán học máy truyền thống để phân loại các kiểu tấn công trên tập dữ liệu **CIC-IDS2017**.

### 🛠️ Thuật toán triển khai
1.  **Logistic Regression**: Tối ưu với kỹ thuật *Smoothed Class Weights* và *Clipping Outliers*.
2.  **Categorical Naive Bayes**: Áp dụng kỹ thuật *Binning* (Rời rạc hóa dữ liệu) để xử lý dữ liệu mạng.
3.  **Support Vector Machine (SVM)**: Sử dụng *Quantile Transformer* và *Nystroem Approximation* để tối ưu hiệu năng trên tập dữ liệu lớn.

---

## 📊 Kết quả thực nghiệm

Dưới đây là bảng so sánh hiệu năng của 3 mô hình đã thực hiện:

|         Mô hình         | Accuracy | Macro F1-Score |    Trạng thái     |
| :---------------------- | :------: | :------------: | :---------------- |
| **Logistic Regression** | 93%      | 0.71           | ✅ Hoàn thành     |
| **Naive Bayes**         | 83%      | 0.60           | ✅ Hoàn thành     |
| **SVM (Tối ưu)**        | 97%      | 0.64           | 🔥 Tốt nhất (TV3) |


---

## 📂 Cấu trúc thư mục (TV3)
```text
├── notebooks/
│   ├── logistic_regression.ipynb   # Xử lý Skewed Data & LR
│   ├── naive_bayes.ipynb           # Kỹ thuật Binning & NB
│   └── svm.ipynb                   # Nystroem & SVM v5
├── data/
│   ├── artifacts/                  # Chứa Confusion Matrix (.png)
│   └── models/                     # Chứa Model đã đóng gói (.pkl)
└── requirements.txt                # Danh sách thư viện cần thiết
```

Hướng dẫn sử dụng mô hình
Để chạy lại các mô hình của Thành viên 3, vui lòng thực hiện các bước sau:

1. Cài đặt thư viện
Bash
```bash 
pip install -r requirements.txt

```
2. Load Model nhanh với Joblib

```python
import joblib

# Load mô hình SVM v5 (Best Model)
model = joblib.load('data/models/svm_final_v5_model.pkl')
le = joblib.load('data/models/svm_label_encoder_v5.pkl')

# Dự đoán mẫu dữ liệu mới
# X_sample có 17 đặc trưng đã định nghĩa
prediction = model.predict(X_sample)
print(f"Kết quả dự đoán: {le.inverse_transform(prediction)}")
```