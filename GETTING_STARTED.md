# Hướng dẫn bắt đầu

Hướng dẫn này giúp bạn hiểu dự án từ cơ bản nhất. Đọc file này trước, sau đó tham khảo các tài liệu chi tiết hơn.

---

## Dự án này làm gì?

Đây là Hệ thống phát hiện xâm nhập mạng (IDS) sử dụng Học máy.

Nói đơn giản:
- Hệ thống theo dõi lưu lượng mạng (dữ liệu truyền giữa các máy tính)
- Phát hiện lưu lượng bình thường hay đáng ngờ (tấn công)
- Xác định loại tấn công cụ thể (DDoS, dò quét cổng, botnet, v.v.)

Ví dụ thực tế:
```
Người dùng bình thường lướt web
  -> Mô hình: "BENIGN" (bình thường, an toàn)

Hacker dò quét mạng của bạn
  -> Mô hình: "PortScan" (phát hiện tấn công!)

Malware liên lạc với máy chủ điều khiển
  -> Mô hình: "Bot" (phát hiện botnet!)
```

---

## 5 mô hình học máy

Dự án huấn luyện 5 mô hình AI khác nhau và so sánh:

| Mô hình | Độ chính xác | Phù hợp cho | Sử dụng? |
|---------|:------------:|-------------|----------|
| Random Forest | 97.59% | Triển khai thực tế | Được chọn |
| KNN | 98.20% | Nghiên cứu, kiểm thử | Thay thế |
| SVM | 97.00% | Khi cần mở rộng | Thay thế |
| Logistic Regression | 93.00% | Mô hình nền tảng | Để học |
| Naive Bayes | 83.00% | Lọc nhanh | Không khuyến nghị |

Tại sao chọn Random Forest dù không phải cao nhất:
- KNN cao hơn 0.61% độ chính xác nhưng bỏ sót 30% tấn công botnet
- Random Forest phát hiện 99.9% dò quét mạng so với 84.8% của KNN
- Trong bảo mật, bỏ sót tấn công nguy hiểm hơn giảm nhẹ độ chính xác

---

## Cấu trúc dự án

```
is_security_group1/
|
|-- Tài liệu
|   |-- README.md              -- Tổng quan dự án
|   |-- GETTING_STARTED.md     -- Hướng dẫn bắt đầu (file này)
|   |-- GUIDE.md               -- Hướng dẫn chi tiết
|   |-- REPORT.md              -- Báo cáo phân tích mô hình
|
|-- Script Python
|   |-- phase6_demo.py         -- Demo: tải 5 mô hình, dự đoán
|   |-- model_comparison.py    -- Tạo biểu đồ so sánh
|
|-- demo/ (Mô hình đã train)
|   |-- logistic_regression_model.pkl
|   |-- naive_bayes_model.pkl
|   |-- svm_model.pkl
|   |-- knn_model.pkl
|   |-- random_forest_model.pkl    -- Mô hình được triển khai
|   |-- scaler.pkl                 -- Bộ chuẩn hóa đặc trưng
|   |-- label_encoder.pkl          -- Bộ chuyển đổi nhãn
|
|-- Thư mục thành viên
|   |-- HoangAnh_N23DCCN071/   -- Tiền xử lý dữ liệu và chọn đặc trưng
|   |-- N23DCCN001_DangKimAn/  -- Huấn luyện 3 mô hình (LR, NB, SVM)
|   |-- N23DCCN138_PhamQuocAn/ -- Huấn luyện 2 mô hình (KNN, RF) + cảnh báo
```

---

## Các khái niệm chính

### 1. File .pkl là gì?

File .pkl là đối tượng Python đã được lưu lại. Tương tự như việc lưu "bộ não đã huấn luyện" vào file.

```
Quá trình huấn luyện:
  Dữ liệu thô -> Đưa vào AI -> AI học các mẫu -> Lưu bộ não vào file .pkl

Sử dụng sau này:
  Tải file .pkl -> Bộ não nhớ lại các mẫu -> Dự đoán
```

### 2. Tại sao có 7 file trong thư mục demo/?

5 mô hình khác nhau:
- Mỗi mô hình học các mẫu hơi khác nhau
- Kết quả không phải lúc nào cũng giống nhau
- Bằng cách biểu quyết đa số, ta được kết quả đáng tin cậy hơn

2 công cụ dùng chung:
- scaler.pkl: Chuẩn hóa số liệu trước khi đưa vào mô hình
  ```
  Đặc trưng thô: 1250 bytes/giây
  Sau chuẩn hóa: 0.5 (nằm trong khoảng -1 đến 1)
  Không chuẩn hóa thì mô hình dự đoán sai!
  ```

- label_encoder.pkl: Chuyển đổi giữa ngôn ngữ máy và ngôn ngữ người
  ```
  Đầu ra máy tính: 2
  Ngôn ngữ người: "PortScan" (qua label_encoder)
  Mô hình xuất số 0-5
  Bộ chuyển đổi: 0->BENIGN, 1->DDoS, 2->PortScan, 3->Bot, 4->Web Attack, 5->Infiltration
  ```

### 3. "17 đặc trưng" là gì?

Đặc trưng là một thông tin về lưu lượng mạng:

```
Mỗi luồng mạng có 17 thông số:
  1. Flow Duration (thời gian kết nối)
  2. Total Fwd Packets (số gói tin gửi đi)
  3. Total Backward Packets (số gói tin gửi lại)
  ... (14 đặc trưng nữa)

Tất cả 5 mô hình dùng CÙNG 17 đặc trưng để quyết định
```

---

## 3 cách sử dụng dự án

### Cách 1: Demo nhanh (1 phút)

Mục tiêu: Xem mô hình hoạt động mà không cần huấn luyện

```bash
pip install -r requirements.txt
python phase6_demo.py
```

Kết quả:
- Tải 5 mô hình từ thư mục demo/
- Tạo các luồng mạng giả lập
- Mỗi mô hình đưa ra dự đoán
- Hiển thị kết quả biểu quyết đa số
- Định dạng cảnh báo giống IDS thật

Phù hợp cho: Xem nhanh, kiểm thử, trình bày

---

### Cách 2: Tải kết quả đã train (5 phút)

Mục tiêu: Xem biểu đồ so sánh mà không cần huấn luyện

```bash
# Tải từ Google Drive:
# https://drive.google.com/drive/folders/11JVbhnkZmTAB5ptHeTcQ9F00Y51MoEam

# Giải nén vào thư mục demo/, sau đó chạy:
python model_comparison.py
```

Kết quả:
- Biểu đồ cột (so sánh độ chính xác)
- Biểu đồ radar (tất cả chỉ số)
- File CSV với dữ liệu
- Hiểu tại sao chọn Random Forest

Phù hợp cho: Tìm hiểu quyết định, thuyết trình

---

### Cách 3: Huấn luyện từ đầu trên Kaggle (2-4 giờ)

Mục tiêu: Xem toàn bộ quy trình từ dữ liệu thô đến mô hình

Đây là phần phức tạp - đọc GUIDE.md trước.

Tóm tắt:
1. TV1 (10-15 phút): Làm sạch dữ liệu thô từ Kaggle
2. TV2 (5-10 phút): Chọn đặc trưng tốt nhất
3. TV3 (30-60 phút): Huấn luyện 3 mô hình trên Kaggle
4. TV4 (60-120 phút): Huấn luyện 2 mô hình trên Kaggle
5. TV5 (dưới 1 phút): So sánh tất cả 5 mô hình

Phù hợp cho: Học tập, nghiên cứu, hiểu toàn bộ quy trình

---

## Hướng dẫn đọc tài liệu

Tùy theo nhu cầu:

- Chỉ muốn xem hoạt động: Chạy Cách 1, đọc file này
- Muốn hiểu quyết định chọn mô hình: Đọc REPORT.md, chạy Cách 2
- Muốn hiểu tất cả: Đọc GUIDE.md
- Cần tích hợp vào ứng dụng: Đọc phần "Ví dụ code" trong REPORT.md
- Muốn tự huấn luyện: Đọc GUIDE.md, chạy Cách 3

**I want to explore the SOC Lab (Wazuh SIEM):**
- Read [WAZUH_REPORT.md](WAZUH_REPORT.md) — Wazuh deployment & architecture
- Read [soc-lab/CONFIGURATION.md](soc-lab/CONFIGURATION.md) — Cấu hình chi tiết
- Read [soc-lab/pfsense/README.md](soc-lab/pfsense/README.md) — pfSense setup
- Read [soc-lab/wazuh/README.md](soc-lab/wazuh/README.md) — Wazuh component details

---

## Câu hỏi thường gặp

Hỏi: Có cần tự huấn luyện mô hình không?
Đáp: Không. Tải mô hình đã train từ Google Drive.

Hỏi: Tại sao có 5 mô hình mà chỉ dùng Random Forest?
Đáp: Để so sánh và chứng minh quyết định. Ngoài ra, biểu quyết từ 5 mô hình có thể đáng tin cậy hơn.

Hỏi: Độ chính xác bao nhiêu?
Đáp: Random Forest đạt 97.59% tổng thể, nhưng 99.9% với PortScan (quan trọng nhất cho bảo mật).

Hỏi: Có thể cải thiện mô hình không?
Đáp: Có. Huấn luyện lại với nhiều dữ liệu hơn, điều chỉnh siêu tham số, hoặc thử thuật toán khác.

Hỏi: Khi các mô hình không đồng ý?
Đáp: Bình thường. phase6_demo.py hiển thị dự đoán riêng lẻ và kết quả biểu quyết đa số.

### **Week 4: SOC Lab (Optional)**
- [ ] Read [WAZUH_REPORT.md](WAZUH_REPORT.md) - 30 min
- [ ] Deploy Wazuh stack: `cd soc-lab && docker compose up -d` - 10 min
- [ ] Read [soc-lab/pfsense/README.md](soc-lab/pfsense/README.md) - 20 min
- [ ] Configure pfSense syslog forwarding - 15 min
- [ ] Install Windows Wazuh agent - 15 min

---

## Bước tiếp theo

1. Ngay bây giờ (2 phút): Chạy `python phase6_demo.py`
2. Tiếp theo (10 phút): Đọc README.md
3. Sau đó (1 giờ): Đọc GUIDE.md hoặc REPORT.md tùy mục tiêu

---

## Tham khảo tài liệu

| File | Nội dung | Đọc khi |
|------|---------|---------|
| GETTING_STARTED.md | Tổng quan cho người mới (file này) | Bắt đầu |
| README.md | Tóm tắt dự án | Muốn xem nhanh |
| GUIDE.md | Hướng dẫn chi tiết từng bước | Muốn hiểu tất cả |
| REPORT.md | Phân tích mô hình chi tiết + ví dụ code | Cần phân tích sâu |

---

## 📚 Document Reference

| File | What's In It | Read When |
|------|-------------|-----------|
| **GETTING_STARTED.md** | Overview for beginners (you are here) | First thing |
| **README.md** | Quick project summary + quick start | Want quick overview |
| **GUIDE.md** | Complete step-by-step guide | Want to understand everything |
| **REPORT.md** | Why Random Forest? Deep analysis + code examples | Need code examples or deep analysis |
| **WAZUH_REPORT.md** | Wazuh SIEM deployment report | Want SOC Lab documentation |
| **soc-lab/CONFIGURATION.md** | Cấu hình chi tiết SOC Lab | Need config references |
| **soc-lab/pfsense/README.md** | pfSense firewall setup | Need pfSense guide |
| **soc-lab/wazuh/README.md** | Wazuh component configs | Need Wazuh integration details |
| **phase6_demo.py** | Code that demonstrates predictions | Want to see how it works |
| **model_comparison.py** | Code that compares all 5 models | Want to generate charts |

---

## 🎉 You're Ready!

Pick Option 1, 2, or 3 above and get started! 

If anything is confusing, jump to the relevant section in the docs. We wrote them to be beginner-friendly.

**Good luck! 🚀**

---

Cập nhật lần cuối: 04/05/2026
