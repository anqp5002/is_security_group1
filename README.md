# 🛡️ IDS Machine Learning Project - TV3

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


---

📈 Ma trận nhầm lẫn (Confusion Matrix)

Thuật toán Naive_Bayes:
<img src="https://storage.googleapis.com/kaggle-script-versions/314940672/output/artifacts/naive_algorithm.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=databundle-worker-v2%40kaggle-161607.iam.gserviceaccount.com%2F20260428%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260428T091721Z&X-Goog-Expires=345600&X-Goog-SignedHeaders=host&X-Goog-Signature=6b5411967e36159b0177f8bad35a31ab225702865aee4c7524a74170cef1a2a16275882a21047fc2d62cb00adba1621401aa511d5cedec97aa86166789fd1ce735f1201f5b7b74541dc8c58c93052dfde2d7861a5987fae662859d3465e2c95482c0c5ef018614b86d4cc81b5b37fc3ab04a9a760cad2ac77a1e150d95708931ab73a587508d7afb5d1753445a5b6051e794192185ffbac9ee64fc3ecdcaebb9c1381374a43e420ebfcb9ca29722ee9bf8f14403cebf66fac549a961f947a303fb5b0897be43263d4bbcf64515b620a5e12bf8b31b99f29f910bf6959d533e8ef957e12fff393246c665bb7e46e37cc6820931cf64e2b97d69f2444a2810919a"></img>

Thuật toán Logistic_Regression:
<img src="https://storage.googleapis.com/kaggle-script-versions/314940176/output/artifacts/logistic_regression.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=databundle-worker-v2%40kaggle-161607.iam.gserviceaccount.com%2F20260428%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260428T091802Z&X-Goog-Expires=345600&X-Goog-SignedHeaders=host&X-Goog-Signature=c34bf9454313c30c535d97ae6dd7ed1b1fcfab20d23f8ea8dce0b95d9fadd0e0852edc852e25b9c505916311501e1d59ec951583e7d78eb5b9b53a30333dfcc5995b4a2c5898af488a2c81a23de19afb48fb467b512321269abb3ac2fe315ff3ac5afd6fe6a78b1de17dc4b85fb1d4e758f81a4f8eb41464e063a76327f5366774e05758229b8ec793730532a9d43621f09f6f63816a726a4103d7f1fefc7ac9237355e1bdcf98aeac17fc52391141cf5dbbf57085ff4c51a0751a8d0fae2553a8c3107c36e8d0d711e47e43f3f9d37d691ee2f41c7fae0757e942c86799597a4f530a8065fd4129f0acc1600f206a64ef777b34b4839f7d53704c2e68636640"></img>

Thuật toán SVM:
<img src="https://storage.googleapis.com/kaggle-script-versions/314958570/output/modules/svm_v5_confusion_matrix.png?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=databundle-worker-v2%40kaggle-161607.iam.gserviceaccount.com%2F20260428%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20260428T091945Z&X-Goog-Expires=345600&X-Goog-SignedHeaders=host&X-Goog-Signature=d29b94124dcaf3f91628e68e9b12cde8167e13bf0a3a72068892baab282656a38d779d731534b5f1a769653d54be18ba8f1131d12cf047c69c555e47fa9605b145ab52751cacd90df69f4b3c70033953019293eea6f1e3a1ab407563fa297d94830effbbb4a7dd12c17f3e62a217915de983b5bc1049454de476544b470823267e8da097b3df63a5321a830aa188e5e5948c0c9539f355ebc2c31e21a7fe280f4d738787a15b5a748dd21a0cd735ad29d7ad66081f7e6014c5561fe2c56cd9e755e73151966077acf6d65520c218e57f9e748cc51471874f2b175b29646f4338a735c228c687c708fd7d41e000a97b5164a630dc66328d9ff929b2bc1e57fd47"></img>
