# Hệ thống phát hiện xâm nhập mạng sử dụng học máy

Hệ thống phát hiện xâm nhập mạng (IDS - Intrusion Detection System) dựa trên học máy, sử dụng tập dữ liệu CIC-IDS2017 để huấn luyện và so sánh 5 mô hình phân loại. Mô hình Random Forest được chọn để triển khai thực tế nhờ khả năng phát hiện tấn công vượt trội.

---

## Giới thiệu

Dự án này xây dựng một hệ thống IDS có khả năng:
- Phân loại lưu lượng mạng thành 6 nhãn: BENIGN, DDoS, PortScan, Bot, Web Attack, Infiltration
- So sánh hiệu năng của 5 thuật toán học máy khác nhau
- Mô phỏng phát hiện xâm nhập thời gian thực với cảnh báo theo định dạng Suricata

Toàn bộ quá trình huấn luyện được thực hiện trên Kaggle. Mô hình đã train có thể tải về từ Google Drive.

---

## Thành viên nhóm

| Thành viên | Mã số | Nhiệm vụ | Nội dung |
|-----------|-------|----------|----------|
| Hoàng Anh | N23DCCN071 | TV1| Tiền xử lý dữ liệu, chọn đặc trưng|
| Trần Đức Anh | N23DCCN072 | TV2 | cân bằng dữ liệu |
| Đặng Kim An | N23DCCN001 | TV3 | Huấn luyện Logistic Regression, Naive Bayes, SVM |
| Phạm Quốc An | N23DCCN138 | TV4 | Huấn luyện KNN, Random Forest, triển khai thời gian thực |

---

## Kết quả so sánh 5 mô hình

| Mô hình | Độ chính xác | F1-Score | Trạng thái |
|---------|:------------:|:--------:|-----------|
| KNN (K=5) | 98.20% | 98.20% | Độ chính xác cao nhất |
| Random Forest (100 cây) | 97.59% | 97.59% | Được chọn để triển khai |
| SVM (Nystroem) | 97.00% | 0.64 (macro) | Thay thế khả thi |
| Logistic Regression | 93.00% | 0.71 (macro) | Mô hình nền tảng |
| Naive Bayes | 83.00% | 0.60 (macro) | Không khuyến nghị |

Lý do chọn Random Forest thay vì KNN: Random Forest phát hiện PortScan đạt 99.9% (KNN chỉ 84.8%) và Bot đạt 92.3% (KNN chỉ 62.4%). Trong bảo mật, bỏ sót tấn công nghiêm trọng hơn việc giảm 0.61% độ chính xác.

Chi tiết phân tích xem tại [REPORT.md](REPORT.md).

---

## 📚 Tài liệu

| Tài liệu | Mục đích | Đọc khi |
|----------|---------|---------|
| **[GETTING_STARTED.md](GETTING_STARTED.md)** | Tổng quan cho người mới & lộ trình học | **Bắt đầu từ đây!** |
| **[GUIDE.md](GUIDE.md)** | Hướng dẫn đầy đủ từng bước | Muốn hiểu tất cả |
| **[REPORT.md](REPORT.md)** | Phân tích mô hình chi tiết & quyết định triển khai | Cần ví dụ code hoặc phân tích sâu |
| **[WAZUH_REPORT.md](WAZUH_REPORT.md)** | Triển khai Wazuh SIEM (Docker, pfSense, Suricata) | Muốn tài liệu SOC Lab |

---

## 🧪 SOC Lab — Wazuh SIEM Stack

Dự án bao gồm một **SOC Lab hoàn chỉnh** với Wazuh 4.9.0 SIEM stack chạy trên Docker, tích hợp pfSense firewall, Suricata IDS, và VirusTotal threat intelligence.

### Kiến trúc

```
                         ┌──────────────────┐
                         │   pfSense  WAN    │ 192.168.100.1
                         │    Firewall       │
                         └────────┬─────────┘
                                  │
                         ┌────────┴─────────┐
                         │   Docker Host     │ 192.168.100.102
                         │  ┌────────────┐  │
                         │  │   Wazuh     │  │
                         │  │   Manager   │  │
                         │  │ 172.20.0.10 │  │
                         │  └──────┬─────┘  │
                         │  ┌──────┴─────┐  │
                         │  │  Wazuh     │  │
                         │  │  Indexer   │  │
                         │  │ 172.20.0.11│  │
                         │  └──────┬─────┘  │
                         │  ┌──────┴─────┐  │
                         │  │  Wazuh     │  │
                         │  │  Dashboard │  │
                         │  │172.20.0.12 │  │
                         │  └────────────┘  │
                         │  ┌────────────┐  │
                         │  │  Suricata  │  │
                         │  │(host mode) │  │
                         │  └────────────┘  │
                         └──────────────────┘
```

### Tài liệu SOC Lab

| File | Nội dung |
|------|----------|
| **[soc-lab/CONFIGURATION.md](soc-lab/CONFIGURATION.md)** | Cấu hình chi tiết toàn bộ hệ thống (19 sections) |
| **[soc-lab/pfsense/README.md](soc-lab/pfsense/README.md)** | Hướng dẫn cài đặt & cấu hình pfSense |
| **[soc-lab/wazuh/README.md](soc-lab/wazuh/README.md)** | Báo cáo triển khai Wazuh chi tiết |
| **[WAZUH_REPORT.md](WAZUH_REPORT.md)** | Báo cáo tổng hợp Wazuh SOC Lab |

### Tính năng SOC Lab

- **Wazuh 4.9.0** — SIEM trung tâm (manager, indexer, dashboard)
- **pfSense integration** — Firewall logs qua syslog UDP port 514
- **Windows Agent** — Thu thập event logs, FIM, Sysmon
- **Suricata IDS** — Phát hiện tấn công mạng theo signature
- **VirusTotal** — Enrich file hashes với threat intelligence
- **File Integrity Monitoring** — Theo dõi thay đổi file real-time
- **Sysmon** — Enhanced Windows monitoring
- **SSH Brute Force Detection** — Phát hiện tấn công brute-force

---

## Cấu trúc dự án

```
is_security_group1/
├── README.md                          -- Tổng quan dự án (file này)
├── REPORT.md                          -- Báo cáo phân tích chi tiết
├── GUIDE.md                           -- Hướng dẫn đầy đủ
├── GETTING_STARTED.md                 -- Hướng dẫn cho người mới
├── WAZUH_REPORT.md                    -- Báo cáo triển khai Wazuh SIEM
├── model_comparison.py                -- So sánh 5 mô hình, tạo biểu đồ
├── phase6_demo.py                     -- Demo dự đoán thời gian thực
├── requirements.txt                   -- Thư viện Python cần thiết
│
├── HoangAnh_N23DCCN071/               (TV1: Tiền xử lý + TV2: Chọn đặc trưng)
│   ├── preprocess.py                  -- Load 8 file CSV, làm sạch dữ liệu
│   ├── prepare_model_data.py          -- Chọn 17 đặc trưng, SMOTE, scaling
│   └── outputs/                       -- Biểu đồ phân bố tấn công, heatmap
│
├── N23DCCN001_DangKimAn/              (TV3: Huấn luyện LR, NB, SVM)
│   ├── nodebook/                      -- 3 Jupyter notebook
│   └── data/artifacts/                -- Ma trận nhầm lẫn 3 mô hình
│
├── N23DCCN138_PhamQuocAn/             (TV4: Huấn luyện KNN, RF + cảnh báo)
│   ├── notebooks/                     -- IDS_ML_Notebook.py
│   ├── outputs/                       -- Ma trận nhầm lẫn KNN, RF
│   └── logs/                          -- File cảnh báo alerts.log
│
├── demo/                              -- Mô hình đã train (tải từ Google Drive)
│   ├── logistic_regression_model.pkl
│   ├── naive_bayes_model.pkl
│   ├── svm_model.pkl
│   ├── knn_model.pkl
│   ├── random_forest_model.pkl        -- Mô hình được triển khai
│   ├── scaler.pkl                     -- Bộ chuẩn hóa đặc trưng
│   └── label_encoder.pkl              -- Bộ mã hóa nhãn
│
└── soc-lab/                           -- SOC Lab (Wazuh SIEM + pfSense + Suricata)
    ├── CONFIGURATION.md               -- Chi tiết cấu hình toàn bộ hệ thống
    ├── docker-compose.yml             -- Docker Compose stack
    ├── pfsense/README.md              -- pfSense firewall setup guide
    ├── wazuh/README.md                -- Wazuh SIEM deployment details
    ├── wazuh/config/                  -- Wazuh config files (manager, rules, decoders)
    ├── wazuh/scripts/                 -- Agent management scripts
    ├── suricata/                      -- Suricata IDS config & rules
    ├── indexer/config/                -- OpenSearch config
    └── dashboard/config/              -- Dashboard config
```

---

## Hướng dẫn chạy nhanh

### Cách 1: Chạy demo (1 phút)

```bash
pip install -r requirements.txt
python phase6_demo.py
```

Script sẽ tải 5 mô hình từ thư mục demo/, dự đoán 10 luồng mạng giả lập, hiển thị kết quả từ từng mô hình và kết quả biểu quyết đa số.

### Cách 2: Tải mô hình đã train từ Google Drive

```
https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam
```

Tải 7 file .pkl về thư mục demo/ rồi chạy:

```bash
python phase6_demo.py       # Demo dự đoán thời gian thực
python model_comparison.py  # Tạo biểu đồ so sánh 5 mô hình
```

### Cách 3: Train từ đầu trên Kaggle (2-4 giờ)

1. TV1: Tải dataset CIC-IDS2017 từ Kaggle, chạy `preprocess.py` (10-15 phút)
2. TV2: Chạy `prepare_model_data.py` (5-10 phút)
3. TV3: Chạy 3 notebook trong `N23DCCN001_DangKimAn/nodebook/` trên Kaggle (30-60 phút)
4. TV4: Chạy `IDS_ML_Notebook.py` trong `N23DCCN138_PhamQuocAn/notebooks/` trên Kaggle (60-120 phút)
5. TV5: Chạy `python model_comparison.py` (1 phút)

---

## Yêu cầu hệ thống

- Python 3.9 trở lên
- RAM tối thiểu 8GB (khuyến nghị 16GB cho TV4)
- Khoảng 5GB dung lượng đĩa

---

## Tài liệu tham khảo

- Dataset: [CIC-IDS2017 trên Kaggle](https://www.kaggle.com/datasets/chethuhn/network-intrusion-dataset/)
- Tham khảo: https://github.com/marxgoo/Network-intrusion-detection-ml
- Tham khảo: https://www.kaggle.com/code/ujjwalks9/intrusion-detection-system

---

Cập nhật lần cuối: 04/05/2026
Trạng thái: Hoàn thành
Mô hình triển khai: Random Forest (độ chính xác 97.59%)
