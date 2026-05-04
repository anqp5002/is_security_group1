# Hướng dẫn dự án đầy đủ

Hệ thống phát hiện xâm nhập mạng thời gian thực sử dụng Học máy

---

## Mục lục

1. [Bắt đầu nhanh](#bắt-đầu-nhanh)
2. [Tổng quan dự án](#tổng-quan-dự-án)
3. [Cấu trúc file và chức năng](#cấu-trúc-file)
4. [Hướng dẫn chạy từng bước](#hướng-dẫn-chạy)
5. [So sánh mô hình và kết quả](#so-sánh-mô-hình)
6. [Google Drive: Kết quả đã train](#google-drive)
7. [Xử lý sự cố](#xử-lý-sự-cố)

---

## Bắt đầu nhanh

### Lựa chọn 1: Chỉ chạy demo (1 phút)
```bash
pip install -r requirements.txt
python phase6_demo.py
```
Kết quả: Dự đoán thời gian thực từ 5 mô hình với biểu quyết đa số.

### Lựa chọn 2: Dùng mô hình đã train (khuyến nghị)

Để chạy demo nhanh:
```bash
# 1. Tải từ Google Drive:
# https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam

# 2. Tải 3 file sau:
#    - random_forest_model.pkl
#    - scaler.pkl
#    - label_encoder.pkl

# 3. Đặt vào thư mục demo/
mkdir -p demo/
# Sao chép 3 file vào demo/

# 4. Chạy demo:
python phase6_demo.py
```

Để phân tích đầy đủ (có biểu đồ so sánh):
```bash
# Giải nén tất cả đầu ra vào các thư mục tương ứng
# Sau đó chạy:
python model_comparison.py
```

### Lựa chọn 3: Huấn luyện từ đầu trên Kaggle (2-4 giờ)

```bash
# TV1: Tiền xử lý dữ liệu (Chạy local)
cd HoangAnh_N23DCCN071
mkdir -p data/raw
# Tải 8 file CSV từ Kaggle về data/raw/
python preprocess.py          # 10-15 phút

# TV2: Chọn đặc trưng (Chạy local)
python prepare_model_data.py  # 5-10 phút

# TV3: Huấn luyện 3 mô hình (Trên Kaggle)
cd ../N23DCCN001_DangKimAn
# 1. Tạo notebook mới trên Kaggle
# 2. Thêm dataset: chethuhn/network-intrusion-dataset
# 3. Sao chép code từ nodebook/logistic_regression.ipynb
# 4. Chạy trên Kaggle
# Thời gian: 30-60 phút

# TV4: Huấn luyện mô hình nâng cao (Trên Kaggle)
cd ../N23DCCN138_PhamQuocAn
# 1. Tạo notebook mới trên Kaggle
# 2. Thêm dataset: chethuhn/network-intrusion-dataset
# 3. Sao chép code từ notebooks/IDS_ML_Notebook.py
# 4. Chạy trên Kaggle (khuyến nghị vì cần nhiều RAM)
# Thời gian: 60-120 phút

# TV5: So sánh tất cả mô hình (Chạy local)
cd ../
python model_comparison.py    # 1 phút
```

---

## Tổng quan dự án

### Dự án này làm gì

Huấn luyện 5 mô hình học máy trên tập dữ liệu xâm nhập mạng CIC-IDS2017:
1. Logistic Regression - Mô hình nền tảng (93%)
2. Naive Bayes - Phân loại đơn giản (83%)
3. SVM (Nystroem) - Phương pháp kernel mở rộng (97%)
4. KNN (K=5) - Láng giềng gần nhất (98.20%)
5. Random Forest - Được triển khai (97.59%, phát hiện tấn công tốt nhất)

### Tại sao chọn Random Forest?

Dù KNN có độ chính xác cao hơn 0.61%, Random Forest được chọn cho triển khai vì:

| Chỉ số | KNN | Random Forest | Thắng |
|--------|:---:|:-------------:|:-----:|
| Độ chính xác tổng thể | 98.20% | 97.59% | KNN |
| Recall PortScan | 84.8% | 99.9% | RF |
| Recall Bot | 62.4% | 92.3% | RF |
| Recall DDoS | 98.1% | 98.5% | RF |

Tác động thực tế: RF phát hiện thêm 15% dò quét mạng và 30% botnet so với KNN.

---

## Cấu trúc file

### File ở thư mục gốc

| File | Chức năng |
|------|----------|
| README.md | Tổng quan dự án |
| GUIDE.md | Hướng dẫn đầy đủ (file này) |
| REPORT.md | Phân tích mô hình chi tiết và quyết định triển khai |
| requirements.txt | Thư viện Python cần thiết |
| model_comparison.py | So sánh 5 mô hình, tạo biểu đồ |
| phase6_demo.py | Demo dự đoán thời gian thực |

### Thư mục thành viên

| Thư mục | Thành viên | Nhiệm vụ | Nội dung |
|---------|-----------|----------|----------|
| HoangAnh_N23DCCN071 | Hoàng Anh | TV1 + TV2 | Tiền xử lý dữ liệu và chọn đặc trưng |
| N23DCCN001_DangKimAn | Đặng Kim An | TV3 | Huấn luyện 3 mô hình (LR, NB, SVM) |
| N23DCCN138_PhamQuocAn | Phạm Quốc An | TV4 | Huấn luyện 2 mô hình (KNN, RF) + triển khai |

---

## Hướng dẫn chạy

### Giai đoạn 1: Tiền xử lý dữ liệu (TV1)
```bash
# Trước tiên: Tải 8 file CSV từ Kaggle về:
mkdir -p HoangAnh_N23DCCN071/data/raw
# Đặt 8 file CSV vào HoangAnh_N23DCCN071/data/raw/:
# - Monday-WorkingHours.pcap_ISCX.csv
# - Tuesday-WorkingHours.pcap_ISCX.csv
# - Wednesday-WorkingHours.pcap_ISCX.csv
# - Thursday-WorkingHours-Morning-WebAttacks.pcap_ISCX.csv
# - Thursday-WorkingHours-Afternoon-Infilteration.pcap_ISCX.csv
# - Friday-WorkingHours-Morning.pcap_ISCX.csv
# - Friday-WorkingHours-Afternoon-PortScan.pcap_ISCX.csv
# - Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv

cd HoangAnh_N23DCCN071
python preprocess.py
```

Chức năng:
- Tải 8 file CSV từ data/raw/ (khoảng 2.8 triệu luồng mạng)
- Làm sạch tên cột, xóa trùng lặp/NaN
- Tạo biểu đồ EDA (phân bố tấn công, tương quan đặc trưng)

Đầu ra:
```
data/processed/merged_cleaned.csv  (2.8 triệu dòng x 79 cột)
outputs/attack_distribution.png
outputs/correlation_heatmap.png
```

Biểu đồ kết quả:

#### Phân bố tấn công
![Phân bố tấn công](HoangAnh_N23DCCN071/outputs/attack_distribution.png)

#### Tương quan đặc trưng
![Tương quan đặc trưng](HoangAnh_N23DCCN071/outputs/correlation_heatmap.png)

---

### Giai đoạn 2: Chọn đặc trưng và cân bằng (TV2)
```bash
python prepare_model_data.py
```

Chức năng:
- Chọn 17 đặc trưng chính: Flow Duration, Total Fwd Packets, Total Backward Packets, Total Length of Fwd Packets, Total Length of Bwd Packets, Fwd Packet Length Mean, Bwd Packet Length Mean, Flow Bytes/s, Flow Packets/s, Packet Length Mean, Packet Length Std, SYN Flag Count, ACK Flag Count, FIN Flag Count, RST Flag Count, PSH Flag Count, URG Flag Count
- Áp dụng SMOTE (tăng mẫu lớp thiểu số lên 10%)
- Áp dụng RandomUnderSampler (giảm lớp đa số xuống 3 lần lớp thiểu số)
- Chuẩn hóa bằng StandardScaler
- Chia train/test theo tỷ lệ 80/20 (stratified)

Đầu ra:
```
data/final/X_train.csv           (144 nghìn dòng x 17 cột)
data/final/X_test.csv            (36 nghìn dòng x 17 cột)
data/final/y_train.csv
data/final/y_test.csv
artifacts/scaler.pkl
artifacts/label_encoder.pkl
```

---

### Giai đoạn 3: Huấn luyện 3 mô hình (TV3)
```bash
cd ../N23DCCN001_DangKimAn
jupyter notebook nodebook/logistic_regression.ipynb
```

Cách A: Jupyter (tương tác)
- Mở notebook, nhấn "Run All"
- Xem dự đoán và ma trận nhầm lẫn trực tiếp

Cách B: Kaggle (khuyến nghị)
- Tạo notebook mới trên Kaggle
- Thêm dataset: chethuhn/network-intrusion-dataset
- Sao chép code từ notebook rồi chạy

Các mô hình được huấn luyện:
1. Logistic Regression (93%)
2. Naive Bayes (83%)
3. SVM với Nystroem (97%)

Ma trận nhầm lẫn:

#### Logistic Regression
![Ma trận nhầm lẫn - Logistic Regression](N23DCCN001_DangKimAn/data/artifacts/logistic_regression.png)

#### Naive Bayes
![Ma trận nhầm lẫn - Naive Bayes](N23DCCN001_DangKimAn/data/artifacts/naive_algorithm.png)

#### SVM (Nystroem)
![Ma trận nhầm lẫn - SVM](N23DCCN001_DangKimAn/data/artifacts/svm_v5_confusion_matrix.png)

---

### Giai đoạn 4: Huấn luyện mô hình nâng cao (TV4)
```bash
cd ../N23DCCN138_PhamQuocAn
python notebooks/IDS_ML_Notebook.py
```

Hoặc trên Kaggle (khuyến nghị vì cần nhiều RAM):
- Tạo notebook mới trên Kaggle
- Sao chép code từ notebooks/IDS_ML_Notebook.py
- Chạy

Các mô hình được huấn luyện:
1. KNN (K=5) - 98.20% (độ chính xác cao nhất)
2. Random Forest (100 cây) - 97.59% (phát hiện tấn công tốt nhất)

Ma trận nhầm lẫn:

#### KNN (K=5) - Độ chính xác 98.20%
![Ma trận nhầm lẫn - KNN](N23DCCN138_PhamQuocAn/outputs/cm_KNN.png)

#### Random Forest - Độ chính xác 97.59% (Được triển khai)
![Ma trận nhầm lẫn - Random Forest](N23DCCN138_PhamQuocAn/outputs/cm_Random_Forest.png)

---

### Giai đoạn 5: So sánh tất cả mô hình
```bash
cd ../
python model_comparison.py
```

Chức năng:
- Sử dụng kết quả huấn luyện từ TV3 và TV4 (hardcoded)
- Tạo biểu đồ so sánh
- Xuất số liệu ra CSV

Đầu ra:
```
outputs/comparison/
|-- bar_accuracy.png              -- Xếp hạng độ chính xác
|-- bar_all_metrics.png           -- So sánh Accuracy và F1
|-- radar_chart.png               -- Biểu đồ radar đa chiều
|-- comparison_table.csv          -- Số liệu thô
```

---

### Giai đoạn 6: Demo dự đoán thời gian thực
```bash
python phase6_demo.py
```

Chức năng:
- Tải tất cả 5 mô hình đã train từ thư mục demo/ (hoặc tạo mô hình demo nếu thiếu)
- Tạo 10 luồng mạng giả lập
- Dự đoán với từng mô hình
- Hiển thị kết quả biểu quyết đa số
- Định dạng cảnh báo kiểu Suricata

---

## So sánh mô hình

### Kết quả chính

Độ chính xác tổng thể: KNN cao nhất (98.20% so với 97.59% của RF)

Nhưng về bảo mật: Random Forest thắng
- Phát hiện PortScan: RF 99.9% so với KNN 84.8% (hơn 15.1%)
- Phát hiện Bot: RF 92.3% so với KNN 62.4% (hơn 29.9%)
- Tác động hàng năm: RF ngăn chặn hơn 52,000 lượt dò quét và 6.5 triệu luồng botnet so với KNN

### Chi tiết từng mô hình

| Mô hình | Độ chính xác | Phù hợp | Khuyến nghị |
|---------|:------------:|---------|------------|
| Random Forest | 97.59% | IDS thực tế | Triển khai |
| KNN | 98.20% | Nghiên cứu | Cân nhắc |
| SVM | 97.00% | Mở rộng | Thay thế |
| Logistic Regression | 93.00% | Nền tảng | Chỉ để so sánh |
| Naive Bayes | 83.00% | Lọc nhanh | Không khuyến nghị |

### Hai cách xem kết quả so sánh

1. Biểu đồ từ kết quả huấn luyện (model_comparison.py)
   - Dùng số liệu từ TV3 và TV4
   - Tạo biểu đồ cột và radar
   - Chạy: `python model_comparison.py`

2. Dự đoán thời gian thực (phase6_demo.py)
   - Tải mô hình thực từ thư mục demo/
   - Dự đoán trên luồng mạng giả lập
   - Hiển thị sự đồng thuận giữa 5 mô hình
   - Chạy: `python phase6_demo.py`

---

## Cách sử dụng mô hình đã train

### Tải và dự đoán
```python
import joblib

# Tải các thành phần đã train
model = joblib.load('demo/random_forest_model.pkl')
scaler = joblib.load('demo/scaler.pkl')
label_encoder = joblib.load('demo/label_encoder.pkl')

# Chuẩn bị đặc trưng (17 đặc trưng)
flow_features = [120, 25, 30, 1250, 1500, 150, 100, 500, 50, 120, 80, 1, 5, 0, 0, 0, 0]

# Chuẩn hóa đặc trưng (quan trọng!)
X_scaled = scaler.transform([flow_features])

# Dự đoán
prediction = model.predict(X_scaled)[0]

# Chuyển số thành nhãn văn bản
attack_type = label_encoder.inverse_transform([prediction])[0]

print(f"Phát hiện: {attack_type}")
```

---

## Giải thích file .pkl

### File .pkl là gì?

File .pkl là đối tượng Python đã được tuần tự hóa (serialize) bằng joblib/pickle. Chứa mô hình học máy và công cụ tiền xử lý đã được huấn luyện.

### Các file trong thư mục demo/:

File mô hình (5 file):
```
logistic_regression_model.pkl   -- Phân loại từ TV3
naive_bayes_model.pkl           -- Phân loại từ TV3
svm_model.pkl                   -- Phân loại từ TV3
knn_model.pkl                   -- Phân loại từ TV4
random_forest_model.pkl         -- Phân loại từ TV4 (Được triển khai)
```

File tiền xử lý dùng chung (2 file):
```
scaler.pkl          -- StandardScaler: Chuẩn hóa đặc trưng đầu vào về khoảng [-1, 1]
                       (Tất cả 5 mô hình dùng chung, tạo từ TV2)

label_encoder.pkl   -- LabelEncoder: Chuyển đổi nhãn văn bản và số
                       Văn bản: "BENIGN", "DDoS", "PortScan", "Bot", "Web Attack", "Infiltration"
                       Số:      0,        1,      2,          3,     4,             5
                       (Tất cả 5 mô hình dùng chung)
```

### Luồng hoạt động:

```
Đặc trưng đầu vào thô [120, 25, 30, ...] (17 giá trị)
  |
  v
scaler.pkl (StandardScaler.transform)
  |
  v
Đặc trưng chuẩn hóa [-0.5, 1.2, 0.3, ...] (đã scale)
  |
  v
Model.predict(đặc trưng đã scale)
  |
  v
Đầu ra dạng số [2] (ví dụ: chỉ số 2)
  |
  v
label_encoder.pkl (inverse_transform)
  |
  v
Kết quả văn bản "PortScan" (con người đọc được)
```

---

## Cấu trúc file đầy đủ

```
is_security_group1/
|-- README.md                      -- Tổng quan dự án
|-- GUIDE.md                       -- Hướng dẫn đầy đủ (file này)
|-- REPORT.md                      -- Phân tích mô hình và quyết định triển khai
|-- GETTING_STARTED.md             -- Hướng dẫn cho người mới
|-- model_comparison.py            -- So sánh 5 mô hình, tạo biểu đồ
|-- phase6_demo.py                 -- Demo dự đoán thời gian thực
|-- requirements.txt               -- Thư viện Python
|
|-- demo/                          -- Mô hình đã train (từ Google Drive)
|   |-- logistic_regression_model.pkl
|   |-- naive_bayes_model.pkl
|   |-- svm_model.pkl
|   |-- knn_model.pkl
|   |-- random_forest_model.pkl    -- Được triển khai
|   |-- scaler.pkl                 -- Bộ chuẩn hóa dùng chung
|   |-- label_encoder.pkl          -- Bộ mã hóa nhãn dùng chung
|
|-- HoangAnh_N23DCCN071/           (TV1: Tiền xử lý + TV2: Chọn đặc trưng)
|   |-- preprocess.py              -- Tải 8 CSV, tạo biểu đồ EDA
|   |-- prepare_model_data.py      -- Chọn đặc trưng, cân bằng, chia dữ liệu
|   |-- data/
|   |   |-- raw/                   (Đầu vào: 8 file CSV từ Kaggle)
|   |   |-- processed/             (Đầu ra: dữ liệu đã làm sạch)
|   |   |-- final/                 (Đầu ra: dữ liệu train/test)
|   |-- artifacts/                 (scaler.pkl, label_encoder.pkl)
|   |-- outputs/                   (Biểu đồ EDA)
|
|-- N23DCCN001_DangKimAn/          (TV3: LR, NB, SVM)
|   |-- nodebook/
|   |   |-- logistic_regression.ipynb
|   |   |-- naive_bayes.ipynb
|   |   |-- svm.ipynb
|   |-- data/artifacts/            (Ma trận nhầm lẫn 3 mô hình)
|   |-- README.md
|
|-- N23DCCN138_PhamQuocAn/         (TV4: KNN, RF + cảnh báo)
|   |-- notebooks/
|   |   |-- IDS_ML_Notebook.py     -- Huấn luyện KNN và RF
|   |-- outputs/                   (Ma trận nhầm lẫn KNN, RF, biểu đồ so sánh)
|   |-- logs/                      (alerts.log)
|   |-- README.md
```

---

## Google Drive

Tất cả kết quả huấn luyện có tại:
```
https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam
```

Nội dung:
- Dữ liệu đã làm sạch (đầu ra TV1)
- Tập dữ liệu đã cân bằng (đầu ra TV2)
- Ma trận nhầm lẫn (đầu ra TV3 + TV4)
- Mô hình Random Forest đã train (thư mục demo)
- Biểu đồ EDA và so sánh mô hình
- File cảnh báo thời gian thực

### Tải nhanh 5 mô hình cho demo

1. Tải từ Google Drive
2. Tìm 7 file: 5 file mô hình + scaler.pkl + label_encoder.pkl
3. Tạo thư mục demo/ và đặt vào đó
4. Chạy: `python phase6_demo.py`

Nếu thiếu file, script tự động tạo mô hình demo để so sánh.

---

---

## 🧪 SOC Lab — Wazuh SIEM Stack

Bên cạnh ML-based IDS, dự án còn bao gồm một **SOC Lab hoàn chỉnh** với Wazuh 4.9.0, pfSense, và Suricata.

### Tài liệu tham khảo

| File | Mô tả |
|------|-------|
| **[WAZUH_REPORT.md](WAZUH_REPORT.md)** | Báo cáo triển khai Wazuh (18 sections) |
| **[soc-lab/CONFIGURATION.md](soc-lab/CONFIGURATION.md)** | Cấu hình chi tiết (19 sections — network, Docker, Wazuh, rules, scripts, SSH brute-force) |
| **[soc-lab/pfsense/README.md](soc-lab/pfsense/README.md)** | Hướng dẫn pfSense từ A-Z (installation, NAT, DHCP, DNS, VLAN, hardening) |
| **[soc-lab/wazuh/README.md](soc-lab/wazuh/README.md)** | Báo cáo Wazuh (architecture, configs, agent management, troubleshooting) |

### Quick Deploy

```bash
cd soc-lab
docker compose up -d
```

Sau 3-5 phút truy cập Dashboard tại `https://192.168.100.102:443` (user: `admin`, pass: `admin`).

---

## Xử lý sự cố

| Vấn đề | Giải pháp |
|--------|----------|
| FileNotFoundError: data/raw | Tải 8 file CSV từ Kaggle về HoangAnh_N23DCCN071/data/raw/ |
| MemoryError khi chạy TV4 | Chạy TV4 trên Kaggle thay vì máy local |
| ModuleNotFoundError: sklearn | Chạy lại `pip install -r requirements.txt` |
| Script chạy chậm | Dùng Kaggle notebook thay vì máy local |
| Thiếu mô hình trong demo/ | Tải từ Google Drive và đặt 7 file vào demo/ |

---

## Thời gian dự kiến

| Giai đoạn | Thời gian | Ghi chú |
|-----------|----------|---------|
| Cài đặt | 5 phút | Cài thư viện + tải dataset |
| TV1 | 10-15 phút | Làm sạch dữ liệu |
| TV2 | 5-10 phút | Chọn đặc trưng |
| TV3 | 30-60 phút | Huấn luyện 3 mô hình |
| TV4 | 60-120 phút | Huấn luyện RF/KNN (RF chậm vì 100 cây) |
| TV5 | dưới 1 phút | Tạo biểu đồ |
| Tổng | 2-4 giờ | Có thể chạy TV3 và TV4 song song |

---

## Thành viên

| Thành viên | Mã số | Nhiệm vụ | Đóng góp |
|-----------|-------|----------|----------|
| Hoàng Anh | N23DCCN071 | TV1 + TV2 | Tiền xử lý dữ liệu, chọn đặc trưng, cân bằng |
| Đặng Kim An | N23DCCN001 | TV3 | Logistic Regression, Naive Bayes, SVM |
| Phạm Quốc An | N23DCCN138 | TV4 | KNN, Random Forest, triển khai thời gian thực |

---

Cập nhật lần cuối: 04/05/2026
Trạng thái: Hoàn thành
Mô hình triển khai: Random Forest (độ chính xác 97.59%, phát hiện PortScan 99.9%)
