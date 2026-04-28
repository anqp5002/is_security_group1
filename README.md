TV3 - Huấn luyện mô hình Logistic Regression, Naive Bayes và SVM
Thành viên: Kim An - Ma so sinh vien : N23DCCN001


Mô tả: Huấn luyện và tối ưu hóa 3 thuật toán phân loại: Logistic Regression (LR), Categorical Naive Bayes (CNB) và Support Vector Machine (SVM) trên tập dữ liệu CIC-IDS2017. Tập trung vào việc xử lý dữ liệu mất cân bằng và tối ưu hóa tốc độ huấn luyện cho các mô hình học máy truyền thống.


Cấu trúc thư mục:
logistic_regression.ipynb — Notebook huấn luyện LR với Smoothed Class Weights.
naive_bayes.ipynb — Notebook huấn luyện Naive Bayes với kỹ thuật Binning.
svm.ipynb — Notebook huấn luyện SVM tối ưu (Quantile + Nystroem)
.data/artifacts/ — Chứa ma trận nhầm lẫn (CM) của 3 mô hình.
data/models/ — Chứa các file model .pkl đã đóng gói.


Kết quả huấn luyện
So sánh tổng quan 3 mô hình

Mô hình                 Accuracy      MacroAvgF1     Đặc điểm nổi bật
Logistic Regression     93%             0.71       Tốc độ nhanh, ổn định nhờ Clipping Outliers.Categorical 
Naive Bayes             83%             0.60       Hiệu quả sau khi dùng Binning, cực kỳ nhẹ.
SVM (Tối ưu)            97%             0.64       Độ chính xác cao nhất, xử lý nhiễu cực tốt.

Phân tích chi tiết
1. Logistic Regression (Đã tối ưu)
Kết quả: Đạt Accuracy 93%. Điểm ấn tượng là Recall của các lớp thiểu số rất cao (Bot: 92%, Web Attack: 91%) nhờ kỹ thuật làm mềm trọng số lớp (Smoothed Class Weights).

Ưu điểm: Khả năng hội tụ nhanh và không bị ảnh hưởng quá nhiều bởi nhiễu sau khi đã thực hiện Clipping tại phân vị 99%.

2. Categorical Naive Bayes (Binning)
Kết quả: Accuracy 83%. Đây là mô hình có tốc độ dự đoán nhanh nhất.

Ưu điểm: Việc áp dụng KBinsDiscretizer giúp mô hình hoạt động tốt trên dữ liệu mạng vốn không tuân theo phân phối chuẩn. Tuy nhiên, độ chính xác thấp hơn do giả định các đặc trưng độc lập.

3. SVM (Quantile + Nystroem)
Kết quả: Đạt Accuracy vượt trội 97%.

Ưu điểm: Sử dụng QuantileTransformer giúp chuẩn hóa dữ liệu cực đoan và Nystroem để xấp xỉ RBF Kernel, cho phép đạt độ chính xác của SVM phi tuyến trên tập dữ liệu lớn mà không bị treo máy.

Hạn chế: Độ chính xác của các lớp Web Attack vẫn còn thấp (F1-score từ 0.02 - 0.61) do đặc trưng của các cuộc tấn công này rất tinh vi và giống lưu lượng bình thường.





Hướng dẫn triển khai (TV3)
Yêu cầu môi trường
Cài đặt các thư viện cần thiết theo file requirements.txt:

```bash
pip install -r requirements.txt  
```
Sử dụng Model
Mô hình được đóng gói dưới dạng Pipeline (bao gồm cả bộ tiền xử lý và mô hình):

```python
import joblib

# Load mô hình SVM (Phiên bản tốt nhất của TV3)
model = joblib.load('data/models/svm_final_v5_model.pkl')
label_encoder = joblib.load('data/models/svm_label_encoder_v5.pkl')


# Dự đoán
# sample: mảng 2D chứa 17 đặc trưng mạng
prediction = model.predict(sample)
result = label_encoder.inverse_transform(prediction)
print(f"Cảnh báo: {result[0]}")
```

Đóng góp cho Team
Cung cấp các mô hình baseline (LR, NB) để so sánh hiệu năng với KNN/Random Forest của TV4.
Đóng gói toàn bộ quy trình tiền xử lý vào Pipeline giúp việc tích hợp vào hệ thống thời gian thực của nhóm trở nên dễ dàng và đồng bộ.