# TV4 - Huấn luyện KNN, Random Forest và triển khai phát hiện xâm nhập thời gian thực

Thành viên: Phạm Quốc An - N23DCCN138

## Mô tả

Huấn luyện 2 mô hình KNN (K=5) và Random Forest (100 cây) trên tập dữ liệu CIC-IDS2017 đã tiền xử lý từ TV1 và TV2. Sau đó triển khai mô hình Random Forest để mô phỏng phát hiện xâm nhập mạng thời gian thực, tạo cảnh báo theo định dạng Suricata.

## Cấu trúc thư mục

```
notebooks/IDS_ML_Notebook.py    -- notebook huấn luyện và đánh giá
outputs/tv4/cm_KNN.png          -- ma trận nhầm lẫn KNN
outputs/tv4/cm_Random_Forest.png -- ma trận nhầm lẫn Random Forest
outputs/tv4/model_comparison.png -- biểu đồ so sánh độ chính xác
logs/alerts.log                 -- file cảnh báo từ mô phỏng thời gian thực
```

## Kết quả huấn luyện

### So sánh 2 mô hình

| Mô hình | Accuracy | Precision | Recall | F1-Score |
|---------|----------|-----------|--------|----------|
| KNN (K=5) | 98.20% | 98.20% | 98.20% | 98.20% |
| Random Forest (100 cây) | 97.59% | 97.59% | 97.59% | 97.59% |

### Phân tích chi tiết

- **KNN** đạt accuracy cao hơn 0.61%, nhưng bỏ sót nhiều PortScan (recall 84.8%) và Bot (recall 62.4%)
- **Random Forest** phát hiện PortScan gần hoàn hảo (99.9%) và Bot tốt hơn nhiều (92.3%)
- Cả 2 mô hình đều yếu với các loại Web Attack (Brute Force, XSS, SQL Injection) do đặc trưng mạng tương tự nhau

### Lý do chọn Random Forest để deploy

1. Phát hiện PortScan và Bot vượt trội so với KNN
2. Tốc độ dự đoán nhanh hơn (traverse cây thay vì tính khoảng cách)
3. Sự chênh lệch accuracy 0.61% không đáng kể so với lợi thế phát hiện tấn công

## Hướng dẫn triển khai

### Yêu cầu

```
pip install scikit-learn pandas numpy imbalanced-learn joblib matplotlib seaborn
```

### Tải model từ Google Drive

File model quá nặng (~2.6GB) nên không push lên GitHub. Tải từ link sau:

**Google Drive:** [https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam](https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam)

Gồm 3 file:
- `random_forest_model.pkl` -- mô hình Random Forest đã train
- `scaler.pkl` -- bộ chuẩn hóa StandardScaler
- `label_encoder.pkl` -- bộ mã hóa nhãn LabelEncoder

### Chạy dự đoán

```python
import joblib
import numpy as np

# load model
model = joblib.load('random_forest_model.pkl')
scaler = joblib.load('scaler.pkl')
label_encoder = joblib.load('label_encoder.pkl')

# dự đoán 1 mẫu (17 features)
sample = np.array([[...]])  # thay bằng dữ liệu thực
sample_scaled = scaler.transform(sample)
prediction = model.predict(sample_scaled)
label = label_encoder.inverse_transform(prediction)
print(f"Kết quả: {label[0]}")
```

### Chạy notebook trên Kaggle

1. Tạo notebook mới trên Kaggle
2. Thêm dataset: `chethuhn/network-intrusion-dataset`
3. Copy nội dung file `notebooks/IDS_ML_Notebook.py` vào notebook
4. Chạy toàn bộ (Save & Run All)
5. Tải output từ tab Output

## Mô phỏng thời gian thực

Hệ thống lấy ngẫu nhiên 30 luồng mạng từ tập test, dùng Random Forest dự đoán. Nếu không phải BENIGN thì tạo cảnh báo kiểu Suricata và ghi vào `logs/alerts.log`.

Ví dụ cảnh báo:
```
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: PortScan. Destination Port: 47.
[2026-04-27 00:48:34] [ALERT] Suspicious traffic detected: Bot. Destination Port: 47.
[2026-04-27 00:48:35] [ALERT] Suspicious traffic detected: DDoS. Destination Port: 42.
```
