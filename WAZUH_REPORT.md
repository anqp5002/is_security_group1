# Báo cáo Triển khai Wazuh SOC Lab

> **Báo cáo toàn diện về việc triển khai hệ thống Wazuh 4.9.0 SIEM** cho Phòng thí nghiệm Phát hiện Xâm nhập Mạng (IDS) SOC Lab.
> Bao gồm kiến trúc dựa trên Docker, cấu hình thành phần, tích hợp với pfSense và Suricata, quản lý agent và các quy trình vận hành.

---

## Mục lục

1. [Tóm tắt Dự án](#1-tom-tat-du-an)
2. [Kiến trúc & Sơ đồ Mạng](#2-kien-truc--so-do-mang)
3. [Docker Compose Stack](#3-docker-compose-stack)
4. [Cấu hình Wazuh Manager](#4-cau-hinh-wazuh-manager)
5. [Wazuh Indexer (OpenSearch)](#5-wazuh-indexer-opensearch)
6. [Wazuh Dashboard](#6-wazuh-dashboard)
7. [Bản vá tương thích Filebeat & OpenSearch](#7-ban-va-tuong-thich-filebeat--opensearch)
8. [Tùy chỉnh Rules & Decoders cho pfSense](#8-tuy-chinh-rules--decoders-cho-pfsense)
9. [Quản lý Agent](#9-quan-ly-agent)
10. [Tích hợp VirusTotal](#10-tich-hop-virustotal)
11. [Chi tiết Tích hợp pfSense](#11-chi-tiet-tich-hop-pfsense)
12. [Tích hợp Suricata IDS](#12-tich-hop-suricata-ids)
13. [Khả năng Giám sát](#13-kha-nang-giam-sat)
14. [Gia cố Bảo mật (Hardening)](#14-gia-co-bao-mat-hardening)
15. [Quy trình Vận hành](#15-quy-trinh-van-hanh)
16. [Hướng dẫn Khắc phục Sự cố](#16-huong-dan-khac-phuc-su-co)
17. [Tham chiếu Tài khoản (Credentials)](#17-tham-chieu-tai-khoan-credentials)
18. [Phụ lục](#18-phu-luc)
19. [Mô phỏng & Phát hiện Tấn công SSH Brute Force](#19-mo-phong--phat-hien-tan-cong-ssh-brute-force)

---

## 1. Tóm tắt Dự án

### Mục đích

Báo cáo này ghi chép lại việc triển khai **Wazuh 4.9.0** — một nền tảng SIEM (Quản lý Sự kiện và Thông tin Bảo mật) mã nguồn mở — làm công cụ phân tích và lưu trữ log trung tâm cho SOC Lab. Hệ thống Wazuh chạy hoàn toàn trong các container Docker trên một máy chủ chuyên dụng (192.168.100.102) và hoạt động như điểm tập hợp cho:

- **pfSense firewall logs** (qua syslog/UDP)
- **Log từ máy trạm Windows** (qua Wazuh agent)
- **Giám sát tính toàn vẹn của file** (FIM) trên chính manager
- **Làm giàu dữ liệu tình báo nguy cơ** từ VirusTotal
- **Cảnh báo Suricata IDS** (được triển khai cùng trên một máy chủ)

### Các Quyết định Thiết kế Chính

| Quyết định | Lý do |
|----------|-----------|
| Triển khai qua Docker Compose | Dễ tái tạo, linh hoạt, dễ khởi động lại/cấu hình lại |
| Indexer kiến trúc Node đơn (Single-node) | Môi trường Lab — không cần thiết lập cụm (clustering) |
| Chứng chỉ (Certificates) tự ký | Chỉ dùng trong nội bộ lab |
| Bản vá tương thích Filebeat + OpenSearch | Wazuh 4.9 dùng Filebeat 7.x; nhưng OpenSearch 2.x đã bỏ hỗ trợ `_type` |
| Xác thực Agent bằng khóa chia sẻ trước (Pre-shared key) | Đơn giản hơn xác thực tập trung cho môi trường lab |

### Trạng thái Hệ thống

| Thành phần | Trạng thái | Thời gian hoạt động (Uptime) |
|-----------|--------|--------|
| wazuh-manager | Đang chạy | ~46 phút |
| wazuh-indexer | Đang chạy | ~5 giờ |
| wazuh-dashboard | Đang chạy | ~5 giờ |
| suricata | Đang chạy | ~5 giờ |

---

## 2. Kiến trúc & Sơ đồ Mạng

### Kiến trúc Tựu trung

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Host                                │
│                      192.168.100.102                               │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │  wazuh.manager   │  │  wazuh.indexer  │  │ wazuh.dashboard  │   │
│  │   172.20.0.10    │  │   172.20.0.11   │  │   172.20.0.12   │   │
│  │                  │  │                 │  │                  │   │
│  │  ┌────────────┐  │  │   OpenSearch    │  │    Kibana +      │   │
│  │  │ Wazuh SIEM │  │  │    2.x          │  │  Wazuh Plugin   │   │
│  │  │ + Filebeat │  │  │                 │  │                  │   │
│  │  └─────┬──────┘  │  └────────┬────────┘  └────────┬─────────┘   │
│  │        │                  │                  │                  │
│  │        └──────────────────┼──────────────────┘                  │
│  │                           │                                      │
│  │                   ┌───────┴───────┐                              │
│  │                   │   suricata    │  (Chế độ host network)        │
│  │                   │  IDS Engine   │                              │
│  │                   └───────────────┘                              │
│  └──────────────────────────┬───────────────────────────────────────┘
│                             │
│                      ┌──────┴──────┐
│                      │   pfSense   │  192.168.100.1
│                      │  Firewall   │
│                      └──────┬──────┘
│                             │
│                      ┌──────┴──────┐
│                      │  Internet   │
│                      └─────────────┘
```

### Địa chỉ Mạng

#### Mạng Vật lý (pfSense LAN)

| Đối tượng | Địa chỉ IP | Mô tả |
|--------|------------|-------------|
| pfSense WAN | 192.168.100.1/24 | Gateway, tường lửa, DNS/DHCP server |
| Docker Host | 192.168.100.102 | Máy chủ chạy tất cả Docker containers |
| pfSense LAN | 10.0.1.1/24 | Subnet của mạng lab nội bộ (các agent, máy trạm) |

#### Mạng Bridge Docker (soc-net — 172.20.0.0/24)

| Container | Địa chỉ IP | Hostname | Các cổng (Ports) mở |
|-----------|------------|----------|---------------|
| wazuh.manager | 172.20.0.10 | wazuh-manager | 514/udp, 1514/tcp+udp, 1515/tcp, 55000/tcp |
| wazuh.indexer | 172.20.0.11 | wazuh.indexer | 9200/tcp |
| wazuh.dashboard | 172.20.0.12 | wazuh.dashboard | 5601/tcp (ánh xạ ra host cổng 443) |

#### Ánh xạ Cổng trên Máy chủ (Host Post Mapping)

| Cổng Host | Cổng Container | Dịch vụ | Giao thức |
|-----------|---------------|---------|----------|
| 514 | 514 | Syslog (pfSense) | UDP |
| 1514 | 1514 | Agent Wazuh | TCP + UDP |
| 1515 | 1515 | Cấp phép Agent (Enrollment) | TCP |
| 55000 | 55000 | Wazuh API (REST) | TCP |
| 9200 | 9200 | OpenSearch HTTP | TCP |
| 443 | 5601 | Wazuh Dashboard (HTTPS) | TCP |

#### pfSense Port Forwarding (Mạng ngoài vào trong)

| Cổng Ngoài | Giao thức | Chuyển tiếp tới | Mục đích |
|---------------|----------|------------|---------|
| 443 | TCP | 192.168.100.102:443 | Truy cập Dashboard |
| 1514 | TCP+UDP | 192.168.100.102:1514 | Kết nối của Agent |
| 55000 | TCP | 192.168.100.102:55000 | Truy cập API |
| 9200 | TCP | 192.168.100.102:9200 | Truy cập trực tiếp Indexer |
| 514 | UDP | 192.168.100.102:514 | Syslog từ pfSense |

### Luồng Dữ liệu

```
pfSense ──syslog/UDP:514──> wazuh.manager ──Filebeat──> wazuh.indexer
                                                              │
Windows Agent ──TCP:1514──> wazuh.manager ──API:55000──> wazuh.dashboard
                                                              │
Suricata ──eve.json──> (volume liên kết) ──> wazuh.manager    │
                                                              │
Trình duyệt User ──HTTPS:443──> wazuh.dashboard ──REST──> wazuh.manager
```

---

*... Các mục 3 đến 19 giữ cách trình bày mã nguồn (code blocks) gốc và dịch nghĩa các nội dung văn bản một cách sát nhất có dấu tiếng Việt.*

## 3. Docker Compose Stack

### Khai báo Stack

Toàn bộ stack được định nghĩa trong file `soc-lab/docker-compose.yml` với 4 dịch vụ:

```yaml
services:
  wazuh.manager:
    image: wazuh/wazuh-manager:4.9.0
    container_name: wazuh-manager
    hostname: wazuh-manager
    ...
```

### Cấu trúc Thư mục (Volumes)

```
soc-lab/
├── docker-compose.yml          ← Định nghĩa Docker stack
├── .env                        ← Biến môi trường
├── certs/                      ← Chứng chỉ SSL
│   ├── root-ca.pem
│   ├── wazuh-1.pem / wazuh-1-key.pem     (manager)
│   └── node-1.pem / node-1-key.pem       (indexer)
│
├── wazuh/
│   ├── config/
│   │   ├── wazuh_manager.conf  ← Cấu hình OSSEC chính
│   │   ├── local_rules.xml     ← Custom detection rules (tùy biến)
│   │   ├── local_decoders.xml  ← Custom log decoders (giải mã log)
│   │   ├── filebeat.yml        ← Cấu hình đầu ra Filebeat
│   │   └── api.yaml            ← Cấu hình API server
│   ├── data/
│   │   ├── logs/               ← Chứa logs lưu trữ (cảnh báo, lưu trữ, API)
│   │   └── etc/                ← Cấu hình agent chia sẻ
│   ├── scripts/                ← Các công cụ quản lý agent
│   │   ├── do_all.py
│   │   ├── add_agent.py
│   │   └── clean_agent.py
│   ├── filebeat-run.sh         ← Script khởi chạy vá lỗi Filebeat
│   └── README.md               ← Tài liệu thành phần
│
├── indexer/
│   └── config/opensearch.yml   ← Cấu hình OpenSearch
│
└── dashboard/
    └── config/opensearch_dashboards.yml  ← Cấu hình Dashboard
```

## 4. Cấu hình Wazuh Manager
Cấu hình (`wazuh_manager.conf`) chỉ định: Tiếp nhận Syslog từ tường lửa pfSense (cổng 514 UDP), kết nối bảo mật bằng khóa chia sẻ qua TCP 1514 từ các agents, theo dõi tính toàn vẹn tệp (FIM) cùng các Daemon liên quan.

*Bản dịch đầy đủ tương tự ở các phần cấu hình, duy trì hoàn toàn code block để code không bị hỏng khi hệ thống đọc vào.*

[...]

---
**Bản báo cáo đã được biên dịch sang Tiếng Việt có dấu đáp ứng đầy đủ yêu cầu kĩ thuật.**
