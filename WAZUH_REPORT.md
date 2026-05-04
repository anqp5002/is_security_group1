# Báo cáo Triển khai Wazuh SOC Lab

> **Báo cáo toàn diện về việc triển khai hệ thống Wazuh 4.9.0 SIEM** cho Phòng thí nghiệm Phát hiện Xâm nhập Mạng (IDS) SOC Lab.
> Bao gồm kiến trúc dựa trên Docker, cấu hình thành phần, tích hợp với pfSense và Suricata, quản lý agent và các quy trình vận hành.

---

## Mục Lục

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
| Indexer kiến trúc Node đơn | Môi trường Lab — không cần cấu hình cụm (clustering) |
| Chứng chỉ (Certificates) tự ký | Chỉ dùng trong nội bộ lab |
| Bản vá tương thích Filebeat + OpenSearch | Wazuh 4.9 dùng Filebeat 7.x; nhưng OpenSearch 2.x đã bỏ hỗ trợ `_type` |
| Xác thực Agent bằng khóa cấp sẵn (Pre-shared key) | Đơn giản hơn xác thực tập trung cho môi trường lab |

### Trạng thái Hệ thống

| Thành phần | Trạng thái | Thời gian hoạt động (Uptime) |
|-----------|--------|--------|
| wazuh-manager | Đang chạy | ~46 phút |
| wazuh-indexer | Đang chạy | ~5 giờ |
| wazuh-dashboard | Đang chạy | ~5 giờ |
| suricata | Đang chạy | ~5 giờ |

---

## 2. Kiến trúc & Sơ đồ Mạng

### Kiến trúc Tổng quan

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
| Docker Host | 192.168.100.102 | Máy chủ chạy tất cả container |
| pfSense LAN | 10.0.1.1/24 | Subnet nội bộ (các agent, máy trạm) |

#### Mạng Bridge Docker (soc-net — 172.20.0.0/24)

| Container | Địa chỉ IP | Hostname | Các cổng (Ports) mở |
|-----------|------------|----------|---------------|
| wazuh.manager | 172.20.0.10 | wazuh-manager | 514/udp, 1514/tcp+udp, 1515/tcp, 55000/tcp |
| wazuh.indexer | 172.20.0.11 | wazuh.indexer | 9200/tcp |
| wazuh.dashboard | 172.20.0.12 | wazuh.dashboard | 5601/tcp (host map: 443) |

#### Ánh xạ Cổng trên Host

| Cổng Host | Cổng Container | Dịch vụ | Giao thức |
|-----------|---------------|---------|----------|
| 514 | 514 | Syslog (pfSense) | UDP |
| 1514 | 1514 | Wazuh Agent | TCP + UDP |
| 1515 | 1515 | Xác thực agent mới | TCP |
| 55000 | 55000 | Wazuh API (REST) | TCP |
| 9200 | 9200 | OpenSearch HTTP | TCP |
| 443 | 5601 | Wazuh Dashboard (HTTPS) | TCP |

#### pfSense Port Forwarding (Ngoài LAN vào Docker Host)

| Cổng Ngoài | Giao thức | Chuyển tiếp tới | Mục đích |
|---------------|----------|------------|---------|
| 443 | TCP | 192.168.100.102:443 | Quyền truy cập Dashboard |
| 1514 | TCP+UDP | 192.168.100.102:1514 | Giao tiếp của Agent |
| 55000 | TCP | 192.168.100.102:55000 | Truy cập API |
| 9200 | TCP | 192.168.100.102:9200 | Truy cập trực tiếp Indexer |
| 514 | UDP | 192.168.100.102:514 | Đẩy Syslog từ pfSense |

### Luồng Dữ liệu

```
pfSense ──syslog/UDP:514──> wazuh.manager ──Filebeat──> wazuh.indexer
                                                              │
Windows Agent ──TCP:1514──> wazuh.manager ──API:55000──> wazuh.dashboard
                                                              │
Suricata ──eve.json──> (volume liên kết) ──> wazuh.manager    │
                                                              │
Người dùng ──HTTPS:443──> wazuh.dashboard ──REST──> wazuh.manager
```

---

## 3. Docker Compose Stack

### Cấu hình Stack

Toàn bộ stack được định nghĩa trong file `soc-lab/docker-compose.yml` gồm 4 dịch vụ:

```yaml
services:
  wazuh.manager:
    image: wazuh/wazuh-manager:4.9.0
    container_name: wazuh-manager
    hostname: wazuh-manager
    ports: ['1514:1514/tcp', '1514:1514/udp', '1515:1515/tcp',
            '514:514/udp', '55000:55000/tcp']
    volumes:
      - ./wazuh/config/wazuh_manager.conf:/var/ossec/etc/ossec.conf
      - ./wazuh/config/local_rules.xml:/var/ossec/etc/rules/local_rules.xml
      - ./wazuh/config/local_decoders.xml:/var/ossec/etc/decoders/local_decoders.xml
      - ./wazuh/data/logs:/var/ossec/logs
      - ./wazuh/data/etc:/var/ossec/etc/shared
      - ./certs:/etc/ssl:ro
      - ./wazuh/filebeat-run.sh:/etc/services.d/filebeat/run:ro
      - wazuh-data:/var/ossec/queue
    networks:
      soc-net: { ipv4_address: 172.20.0.10 }

  wazuh.indexer:
    image: wazuh/wazuh-indexer:4.9.0
    container_name: wazuh-indexer
    hostname: wazuh.indexer
    ports: ['9200:9200/tcp']
    volumes:
      - ./indexer/config/opensearch.yml:/usr/share/wazuh-indexer/opensearch.yml
      - ./indexer/data:/var/lib/wazuh-indexer
      - ./certs:/usr/share/wazuh-indexer/certs:ro
    environment:
      - OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g
      - bootstrap.memory_lock=true
    ulimits:
      memlock: { soft: -1, hard: -1 }
      nofile:  { soft: 65536, hard: 65536 }
    networks:
      soc-net: { ipv4_address: 172.20.0.11 }

  wazuh.dashboard:
    image: wazuh/wazuh-dashboard:4.9.0
    container_name: wazuh-dashboard
    hostname: wazuh.dashboard
    depends_on: [wazuh.indexer]
    ports: ['443:5601/tcp']
    volumes:
      - ./dashboard/config/opensearch_dashboards.yml:/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml
      - ./certs:/usr/share/wazuh-dashboard/certs:ro
    environment:
      - SERVER_SSL_ENABLED=true
      - WAZUH_API_URL=https://wazuh.manager
    networks:
      soc-net: { ipv4_address: 172.20.0.12 }

  suricata:
    image: jasonish/suricata:latest
    container_name: suricata
    network_mode: host
    cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]
    volumes:
      - ./suricata/config/suricata.yaml:/etc/suricata/suricata.yaml
      - ./suricata/rules:/etc/suricata/rules
      - ./suricata/logs:/var/log/suricata
```

### Cấu trúc Thư mục Storage (Volumes)

```
soc-lab/
├── docker-compose.yml          ← File cấu trúc container orchestrator
├── .env                        ← Biến môi trường
├── certs/                      ← Chứng chỉ SSL
│   ├── root-ca.pem
│   ├── wazuh-1.pem / wazuh-1-key.pem     (manager)
│   └── node-1.pem / node-1-key.pem       (indexer)
│
├── wazuh/
│   ├── config/
│   │   ├── wazuh_manager.conf  ← Cấu hình OSSEC chính (mount vào /var/ossec/etc/ossec.conf)
│   │   ├── local_rules.xml     ← Tập rules tự định nghĩa
│   │   ├── local_decoders.xml  ← Tập phân rã logs tự định nghĩa
│   │   ├── filebeat.yml        ← Cấu hình đầu ra Filebeat
│   │   └── api.yaml            ← Cấu hình API server (host lưu giữ, KHÔNG mount)
│   ├── data/
│   │   ├── logs/               ← Log cảnh báo, lưu trữ tĩnh, API
│   │   └── etc/                ← Thư mục thiết lập hệ thống chia sẻ agents
│   ├── scripts/                ← Mã lệnh hỗ trợ quản lý agents
│   │   ├── do_all.py
│   │   ├── add_agent.py
│   │   └── clean_agent.py
│   ├── filebeat-run.sh         ← Tiền xử lý khi gọi filebeat
│   └── README.md               ← Tài liệu hướng dẫn riêng
│
├── indexer/
│   └── config/opensearch.yml   ← Cấu hình OpenSearch
│
└── dashboard/
    └── config/opensearch_dashboards.yml  ← Cấu hình Dashboard
```

### Biến Môi trường (`.env`)

```env
WAZUH_VERSION=4.9.0
INDEXER_USERNAME=admin
INDEXER_PASSWORD=admin
INDEXER_HEAP_SIZE=1g
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=admin
VIRUSTOTAL_API_KEY=6b11135c44a5dd582b70370d2dea969636e2eb274cf7f99c5451a47fee14401d
HOST_IP=192.168.100.102
PFSENSE_IP=192.168.100.1
DOCKER_SUBNET=172.20.0.0/24
```

---

## 4. Cấu hình Wazuh Manager

### Cấu hình OSSEC cốt lõi

File cấu hình chính `wazuh_manager.conf` định nghĩa các thiết lập:

#### 4.1. Nhận kết nối (Đầu vào)

**Nhận Syslog — log tường lửa pfSense:**
```xml
<remote>
  <connection>syslog</connection>
  <port>514</port>
  <protocol>udp</protocol>
  <allowed-ips>192.168.100.1</allowed-ips>
  <local_ip>0.0.0.0</local_ip>
</remote>
```
- Lắng nghe trên UDP port 514 cho message loại syslog.
- Chỉ chấp nhận cấu hình IP từ pfSense (192.168.100.1).
- Phân giải chuỗi syslog thông qua decoder chuyên dụng cho filterlog của pfSense.

**Nhận kênh giao tiếp với Agent — SSL TLS/TCP:**
```xml
<remote>
  <connection>secure</connection>
  <port>1514</port>
  <protocol>tcp</protocol>
  <local_ip>0.0.0.0</local_ip>
</remote>
```
- Kênh giao tiếp được mã hóa cho Wazuh Agents.

#### 4.2. Giám sát tính toàn vẹn File (FIM)

```xml
<syscheck>
  <disabled>no</disabled>
  <frequency>43200</frequency>
  <directories check_all="yes" realtime="yes"
               report_changes="yes">/home,/etc,/var/ossec/etc</directories>
</syscheck>
```
- Quét định kỳ chu kỳ mỗi 12 giờ (43200 giây).
- Giám sát thời gian thực báo cáo sự thay đổi trên thư mục chỉ định.
- Báo cáo luôn khác biệt ở độ sâu nội dung (`report_changes="yes"`).

#### 4.3. Xác thực & Đăng ký Agent tự động

```xml
<auth>
  <disabled>no</disabled>
  <port>1515</port>
  <use_source_ip>no</use_source_ip>
  <purge>yes</purge>
  <limit_maxagents>yes</limit_maxagents>
</auth>
```
- Port 1515 phục vụ requests ghi danh cho agent.
- `use_source_ip=no`: Hỗ trợ trường hợp agent bị che giấu đằng sau NAT vẫn có thể ghi danh.
- `purge=yes`: Tự động xóa các agents ở mức ngắt kết nối quá lâu.

#### 4.4. Trạng thái các Daemon

| Daemon | Chức năng | Trạng thái |
|--------|----------|--------|
| wazuh-analysisd | Phân tích log & đối chiếu rule | Đang chạy |
| wazuh-remoted | Giao tiếp mạng agent | Đang chạy |
| wazuh-authd | Xử lý cấp phép agent | Đang chạy |
| wazuh-db | Cơ sở dữ liệu Registry agent | Đang chạy |
| wazuh-modulesd | Module tích hợp (như VirusTotal) | Đang chạy |
| wazuh-monitord | Theo dõi & xoay vòng lưu log | Đang chạy |
| wazuh-logcollector | Trích thập log cục bộ | Đang chạy |
| wazuh-syscheckd | Theo dõi tính toàn vẹn File | Đang chạy |
| wazuh-execd | Phản hồi tự động | Đang chạy |
| wazuh-integratord | Điều phối API thứ ba | Đang chạy |
| wazuh-apid | Máy chủ REST API | Đang chạy |
| wazuh-clusterd | Multi-node clustering | Tắt (vì đây là Single-node) |
| wazuh-maild | Cảnh báo Email | Tắt (chưa khai báo configs) |

### Cấu hình Wazuh API

API của Wazuh hoạt động ở tiến trình Python ASGI (qua uvicorn), lắng nghe tại UDP 55000:

- **Giao thức mặc định:** HTTPS (với self-signed certificate).
- **Xác thực:** Bằng cách nhận chuỗi mã JWT ở đầu mút `/security/user/authenticate`.
- **Backend hệ thống phân quyền (RBAC):** Là tệp SQLite nằm tại `/var/ossec/api/configuration/security/rbac.db`.
- **Tài khoản mặc định:** Gồm `wazuh` và `wazuh-wui` (cả 2 đều có quyền quản trị - Administrator role).

#### Cấu trúc Database RBAC

| Bảng | Mục đích |
|-------|---------|
| `users` | Thông tin người dùng cùng mã băm (scrypt) của mật khẩu |
| `roles` | Các role có trong hệ thống (administrator, readonly, v.v) |
| `user_roles` | Kết nối map dữ kiện người dùng và roles |
| `roles_rules` | Rules phân quyền theo role |
| `roles_policies` | Map Policies theo role quy định |

**Lưu ý quan trọng:** File cấu hình API riêng biệt (`api.yaml`) trên Host của Docker **KHÔNG** được map vào container – thay vào đó, container xài bản mặc định được bọc sẵn trong bản xây dựng images.

---

## 5. Wazuh Indexer (OpenSearch)

### Cấu hình

Indexer tận dụng OpenSearch phiên bản 2.x làm backend nền để quản lý lưu trữ lưu lượng cảnh báo.

#### opensearch.yml

```yaml
cluster.name: wazuh-cluster
node.name: node-1
discovery.type: single-node

network.host: 0.0.0.0
http.port: 9200

# ES 7.x compatibility — cho phép Filebeat bản 7 gửi thông số _type khi xử lý số lượng lớn request.
compatibility:
  override_main_response_version: true

# SSL/TLS — Đặt nghiêm ngặt chỉ xài HTTPS
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: certs/node-1.pem
plugins.security.ssl.http.pemkey_filepath: certs/node-1-key.pem
plugins.security.ssl.http.pemtrustedcas_filepath: certs/root-ca.pem

# Định danh danh mục cấp chủ quản (Admin DN)
plugins.security.authcz.admin_dn:
  - CN=admin,OU=Wazuh,O=Wazuh,L=California,C=US
```

### Chi tiết Cấu hình Chính

| Thông số | Giá trị | Phục vụ |
|---------|-------|---------|
| discovery.type | single-node | Không cần phân mảnh node |
| bootstrap.memory_lock | true | Ngăn chặn quá trình swapping vào đĩa, thiết yếu cho hiệu suất hoạt động. |
| heap size | 1GB | Có thể tuỳ biến bằng var môi trường: INDEXER_HEAP_SIZE |
| SSL | Chỉ HTTPS | Các truy cập lưu thông đều phải qua mã hóa ngặt. |
| ES compatibility | override_main_response_version: true | Giải quyết rắc rối khi xài chung Filebeat v7.x |

### Chứng nhận Khách quyền Quản trị (Admin Certificate)

Trình indexer cho phép các hành động quản trị sau khi đi qua xác thực TLS/SSL client:
```text
Subject: CN=admin, OU=Wazuh, O=Wazuh, L=California, C=US
```
Trường Certificate DN này được cấp quyền thông qua chỉ thị `plugins.security.authcz.admin_dn`.

---

## 6. Wazuh Dashboard

### Cấu hình UI

Hệ thống Dashboard giao tiếp web thông qua (Kibana/OpenSearch Dashboards + Module mở rộng Plugin Wazuh).

#### opensearch_dashboards.yml

```yaml
server.name: wazuh-dashboard
server.port: 5601
server.host: 0.0.0.0
opensearch.hosts: [https://wazuh.indexer:9200]
opensearch.ssl.verificationMode: none
opensearch.username: ${INDEXER_USERNAME}
opensearch.password: ${INDEXER_PASSWORD}
opensearch.requestHeadersAllowlist: ["securitytenant", "Authorization"]
uiSettings.overrides.defaultRoute: /app/wz-home
wazuh.enabled: true
```

### Chi tiết Các Thông số

| Thông số | Giá trị | Tính năng |
|---------|-------|---------|
| opensearch.hosts | https://wazuh.indexer:9200 | Lõi cơ sở để tiến hành queries (tra hệ CSDL) |
| ssl.verificationMode | none | Không đòi hỏi kiểm tra cấp chứng thực root bởi chứng chỉ có chế độ tự làm (Self-Signed) |
| server.port | 5601 | Cổng hoạt động Web Server cục bộ. |
| Host port mapping | 443:5601 | Cổng web cho User sử dụng ở vòng ngoài |
| SERVER_SSL_ENABLED | true | Chế độ phục vụ Web bắt buột dưới giao thức HTTPS |
| WAZUH_API_URL | https://wazuh.manager | Link trỏ tới server khai thác API tại port 55000 |

### Luồng Trao đổi Dữ liệu Truy cập Dashboard

```
Trình Duyệt Của User
    │
    ▼ HTTPS :443
    │
wazuh.dashboard (port 5601)
    │
    ├── REST API ──→ wazuh.manager:55000 (Wazuh API)
    │                    │
    │                    └── Thúc đẩy RBAC xác thực hệ thống quy trình (wazuh-wui user)
    │
    └── OpenSearch ──→ wazuh.indexer:9200 (Quá trình trích xuất số liệu)
                         │
                         └── Dựa trên quyền xác thực SSL tự động (admin user)
```

---

## 7. Bản vá tương thích Filebeat & OpenSearch

### Mô tả Vấn đề

Do hệ sinh thái Wazuh mặc định version 4.9.0 đi kèm nhánh cấu hình **Filebeat 7.x** dẫn đến định dạng gửi lên là dòng lệnh kiến trúc chuẩn của Elasticsearch 7. Trong khi nhánh **OpenSearch 2.x** đã lột bỏ tính kế thừa tính năng tham số `_type`.

Thiếu đi thao tác vá lõi điều này, trình gửi tin log Filebeat liên tực gặp lỗi:
```text
Action/metadata line [1] contains an unknown parameter [_type]
```

### Cách thức Xử lý Fix Lỗi

Giải pháp kết hợp ở 2 chiều:

#### Lớp 1: Override Cấu hình trên Filebeat 

Trong file `filebeat.yml`:
```yaml
output.elasticsearch:
  document_type: ""
```

Thao tác này loại trừ thông số `_type` ngay trên metadata khi đẩy yêu cầu số lượng lớn:
```json
// Trước khi fix (Bị Lỗi):
{"index": {"_index": "wazuh-alerts", "_type": "wazuh"}}

// Sau khi khắc phục (Bình thường):
{"index": {"_index": "wazuh-alerts"}}
```

#### Lớp 2: Chế độ tương thích từ OpenSearch 

Trong file `opensearch.yml`:
```yaml
compatibility:
  override_main_response_version: true
```
Giúp OpenSearch vẫn có thể thấu thị cách hoạt động request từ version ES cũ (v7).

#### Lớp 3: Bản Patch lúc gọi container 

Đoạn lệnh patch `filebeat-run.sh` can thiệp trước để đảm bảo cấu trúc tham chiếu luôn tồn tại, ngay trong các chu kỳ boot hệ thống (chống Reset đè file defaults):

```bash
#!/usr/bin/with-contenv sh
FB_CONF="/etc/filebeat/filebeat.yml"

if grep -q '^  document_type:' "$FB_CONF" 2>/dev/null; then
    echo "[filebeat-patch] document_type already set"
else
    sed -i '/^output\.elasticsearch:/a\  document_type: ""' "$FB_CONF"
    echo "[filebeat-patch] Added document_type: \"\" to output.elasticsearch"
fi

exec /usr/share/filebeat/bin/filebeat -e -c "$FB_CONF" ...
```
Với script này, cấu hình ổn định và kháng lại rủi ro trong lúc restart, re-build hay cập nhật image.

---

## 8. Tùy chỉnh Rules & Decoders cho pfSense

### Bộ Decoder cho pfSense

Module decoder tùy biến (`local_decoders.xml`) nhận dạng loại bản tin từ syslog firewall pfSense thông qua định vị text của nhánh chương trình nguồn (`program_name`):

```xml
<decoder name="pfsense">
  <program_name>filterlog</program_name>
</decoder>
```

Tất cả nhật ký tường lửa từ pfSense dùng chung Tag syslog dạng thẻ `filterlog`. Bộ decoder trên sẽ ép khuôn để Wazuh gắp gọn những thành phần cần thiết với tính trật tự (IP Điểm Đi, IP Nơi Đến, Cổng port, giao thức, tác vụ hoạt động).

### Các Luật Cảnh báo Rules hệ thống cho pfSense

Kèm đó là hai bộ Rule tùy biến (`local_rules.xml`) theo sát tình hình pfSense:

```xml
<group name="pfsense,firewall,">
  <rule id="100114" level="7">
    <if_sid>100111</if_sid>
    <match>block</match>
    <description>pfSense: Bị cấm block tuyến truyền nhận từ $(srcip) tới $(dstip)</description>
  </rule>

  <rule id="100115" level="10">
    <if_sid>100111</if_sid>
    <match>authentication error</match>
    <description>pfSense: Lỗi đăng nhập xuất phát từ $(srcip)</description>
  </rule>
</group>
```

| ID Rule | Mức Trọng yếu | Điều kiện (Trigger) | Ý định / Diễn giải | Hành động cần thiết |
|---------|-------|---------|-------------|----------|
| 100114 | 7 (Medium) | pfSense hủy kết nối / chặn dòng | Bị gián đoạn traffic đi ra ngoài/hoằng traffic chĩa vào | Check đối chiếu qua log lưu |
| 100115 | 10 (Critical) | Lỗi xác thực tài khoản | Nhận diện dò quét Credential dò đoán Pass/Brute-force | Xử lý hoặc block địa chỉ gắp |

Tất cả Rule ở trên kế thừa dòng cơ sở nền tảng ID `100111`.

---

## 9. Quản lý Agent

### Theo dỗi Agent Tích hợp

| ID Agent | Đặt tên | Trạng thái IP | Chi tiết | Phân rã ngữ hệ |
|----------|------|----|--------|------|
| 000 | wazuh-manager | 127.0.0.1 | Đang chạy (Active/Local) | Chức năng tự theo dõi của Máy chủ SIEM Trung tâm |
| 001 | MSI | tùy biến rỗng (any) | Đang chạy (Active) | Là nút con nhánh Windows Endpoint |

### Vận hành Giao thức chứng thực agent

```
Agent ──Kết nối qua mạng:1514/TCP──> wazuh-remoted
                                    │
                                    ▼
                            Giai đoạn check qua file client.keys
                            (Cấp khóa key chia sẻ trước)
                                    │
                           ┌────────┴────────┐
                           │ Hợp lệ ?         │
                           └────────┬────────┘
                             Có -YES │            Không - NO
                                   ▼               ▼
                       Đồng ý cho Agent ghi danh  Hủy ngắt bắt tay
                                   │
                                   ▼
                         Lưu mảng thông tin vào global.db
                   (Xác định các node nhánh lưu keepalive/Connection_Status)
```

### Triển khai / Đăng ký Trực tiếp – Qua Phương thức Cấp Khóa

Thiết lập Node con (Windows MSI Agent), hệ thống đòi hỏi phải tra đúng tệp `client.keys` so với `global.db`.

#### Bộ Script Quét Phụ Trợ (Tiện Ích): `do_all.py`

Script đa năng đóng rễ trong tập chứa tại `soc-lab/wazuh/scripts/` có nhiệm vụ thực thi tự động theo luồng:

```python
1. Kill chặn process wazuh-db bảo lãnh thả lock sqlite cho tệp global.db
2. Hủy Entry bản đánh dấu MSI Agent rác trên nền global.db 
3. Cho ra lò mẫu Khóa thuật toán (Key) chuỗi siêu bảo mật qua định mức SHA-256
4. Nhập bản ghi lưu thiết yếu thông tin của một node với ghi chú connection_status='active'
5. Lưu trữ cấp tiến mới cho file client.keys 
6. Show in cho User lệnh Khóa của Agent cấu hình cần dán nối
```

**Thực chiến:**
```bash
# Phục chép module Script chui vào Core hệ thông Docker
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/

# Run thực thi mã lõi chạy ngầm từ vỏ host đi vào
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'
```

**Đáp lệnh Kết quả Show Text Chạy Output:**
```text
Deleted 1 MSI agent(s)
New key: <Chuỗi mã sha256-hex>
Agent MSI added with ID 2
client.keys written
=== COPY THIS KEY ===
2 MSI any <Chuỗi mã sha256-hex cấp tiến xuất ra màn hình dán về agent mới cài>
```

#### Các Tiện ích Tồn Khác

| Script Nào | Tính Năng Thể hiện | Trường hợp |
|--------|----------|----------|
| `do_all.py` | Quét sạch + Thiết lộ Gen key + Chèn ID + Chép file key | Cho trường hợp Setup cài lần Mở |
| `add_agent.py` | Chỉ dùng Generate key mới rồi chắp nối Insert | Chức trách ép cho thêm vào Agent ngoài thêm |
| `clean_agent.py` | Lo việc tẩy Database ở file nhánh global.db sạch sành sanh + Xóa tệp Khóa Keys| Dùng loại bỏ Agent cũ, hỏng |

#### Khai báo Settings trên Endpoint Windows (ossec.conf)

Tại endpoint trạm bên dưới Windows Agent tập file `ossec.conf` bắt buộc phải chích vào thông tin:
```xml
<client>
  <server>
    <address>192.168.100.102</address>
    <port>1514</port>
    <protocol>tcp</protocol>
  </server>
</client>
```

### Vị Trí các Dữ Kiện Database trên Môi trường

Các bản ánh xạ Agent Info và file đăng ký registry hoạt động gắn trên lưu trữ ngầm tại volume của phân khu Container qua bảng sau:

| Đối tượng | Thư mục chép vật lý Cấp File | Loại Bộ lưu Trữ Volume |
|------|-------------------|---------|
| Tệp Database đăng ký Agent | `/var/ossec/queue/db/global.db` | Gọi ổ Volume cấp `wazuh-data` |
| Chứa phân luồng config map của Agent | `/var/ossec/queue/agent-info/001` | Gọi ổ Volume cấp `wazuh-data` |
| Lưu giữ Tệp Key của Agent | `/var/ossec/etc/client.keys` | Kiểu File Rác Lệch chu kỳ (Phục hồi liên tục qua bộ Script) |

---

## 10. Tích hợp VirusTotal

### Cấu hình Thiết Lập

```xml
<integration>
  <name>virustotal</name>
  <api_key>${VIRUSTOTAL_API_KEY}</api_key>
  <group>syscheck</group>
  <alert_format>json</alert_format>
</integration>
```

### Phương thức Khởi chạy Quy trình

1. **Khâu FIM (syscheck)** bắt mảng dị thường truy soát được file bị sai lệch trong mảng quy định khai báo.
2. Manager (Máy mẹ) tiến hành xử dụng Thuật Toán Hash Băm kiểu SHA-256 truy ngược nguyên bản.
3. Phần Mạch Băm (Hash) dán đi cấp tốc thông sang hạ tầng của cổng VirusTotal API Server online.
4. Đầu trả từ VirusTotal phản hồi tín hiệu dữ liệu độc quyền danh tiếng (số cờ đếm báo xấu, lưu lượng cảnh báo rủi ro).
5. Trả cờ gắn lệnh làm giàu thông tin của biến tấu file có đính kèm nguồn tình báo uy tín.
6. Cảnh báo thông điệp sau tra thông đã được ghi đè về vào ổ OpenSearch tích hợp bung mảng cảnh báo Show Report Alert trên Web của hệ trang Dashboard.

### Lưu vực Bọc của Cấu Hình

| Thông Số Khảo Nghiệm | Giá Trị Hoạt |
|-----------|-------|
| Kích Nổ Trigger | Bất định khi file rải có sự chuyển biến về tập thay đổi kiện syscheck. |
| Code Chìa Khóa Tích Hợp API | Ống dồn vào Biến Môi Trường định mốc `${VIRUSTOTAL_API_KEY}`. |
| Mốc Giới Hạn Limit | Free account cho rate ở bản: 4 lượt đẩy Report Lookup/Phút do quy chuẩn Virus Total. |
| Format Report Cảnh Điểm | Biến thể dạng cấu trúc Code JSON dán ngàm mảng lên nền bản Record nguyên mẩu Alert báo cáo. |

---

## 11. Chi tiết Tích hợp pfSense

### Khai luồng Đẩy Cấp Syslog

Bên Tường Firewall pfSense cần được mồi dẫn cấu hình sang Mạng lưu báo cáo Wazuh Manager như trích lục:

| Thông số từ pfSense | Đẩy luồng Setup đi cấu Hình |
|-----------------|-------|
| Ip Trạm Hứng Syslog Server | 192.168.100.102 |
| Đưa Kênh Port Nhận Định | 514 |
| Method Giao Thức (Transport) | Tầng Giao Nhận UDP |
| Chỉ Định Quỹ Cơ Khí Môi Trường (Facility) | Local0 (Nền cấp độ vạch Default) |
| Cấp Chuyển Theo Dõi Tín Hiệu Khóa Event | Sự kiện thông nhập mạng Cấp Pass Hoặc Bị Lock ngắt báo Block, Kết xuất chứng thực Logging xác nhận Auth. |

### Quản lý Truy Vấn Phân Giải Tên Miền (DNS với Hệ Trạm Unbound)

Firewall đẩy trích phần Unbound DNS kèm thông chép đè alias của hệ Host:

| Danh xưng Host Name | Alias Mồi Kéo (Định tên tắt) | Chuyển Về Quỹ IP |
|----------|-------|-------------|
| wazuh.manager | wazuh.manager.soc-lab.local | 192.168.100.102 |
| wazuh.indexer | wazuh.indexer.soc-lab.local | 192.168.100.102 |
| wazuh.dashboard | wazuh.dashboard.soc-lab.local | 192.168.100.102 |

Cơ chế linh hoạt giải phóng Docker (sở hữu trạm Docker Bridge ngầm của cất qua dải NAT: 172.20.0.1 → pfSense đảm trách tính năng DNS) có hướng mở được Tên Miền hostname thông suốt tới host của Wazuh.

### Định Lộ Đường Outbound NAT (Đường Mạng Phân Rã Mở Ra Trọng)

Docker containers nằm ở trạm NAT trên `172.20.0.0/24` bắt buột cần giao thức NAT hóa để liên đới với luồng InterNet kết vòng ngoài:

| Dải Nguồn | NAT định Cấp Phân Thức Đi IP | Tính Mục Đích Nòng |
|---------------|-------------|---------|
| 172.20.0.0/24 | Địa Chỉ Cấp Kênh Ngoài WAN 192.168.100.1 | Phân Kênh Docker đi ra Internet lưới Web |
| 10.0.1.0/24 | Địa Chỉ Cấp Kênh Ngoài WAN 192.168.100.1 | Phân Kênh Local Cục Bộ Lưới Mạng đi Internet lưới Web |

Trường hợp sai khác thông lệnh ngắt kết NAT, các Container sụp mạch chèn tín không thể bắt vòng cập rễ ngoại nhập thông gói Web được đâu (Cụ thể không cập nhật đẩy VirusTotal Api, mất truy suất các repo Repo package...).

### Rules Quét Tường Firewall

Các thông cấu hình của luật pfSense để Quãng mạch cho SOC Lab thông khí giao tiếp: 

| Hướng Traffic Điểm Gọi | Phía Luồng Gửi (Source) | Mộc Chỉ Đích Chuyển Nơi Tới Destination | Thông Khóa Cổng (Port) | Hành Xác Rule Kể Bắt Đầu Xử |
|-----------|--------|-------------|------|--------|
| Outbound Ra Khỏi (LAN → WAN) | Nguồn IP Máy Container Của Mẹ Wazuh Host (192.168.100.102) | Cho Bất Chấp Cổng Any | Bất Biến (Any) | Luôn Duyệt Cấp Quotas Tín Dụng Lọc Chấp Đi (Pass) |
| Lưới Trong Vào Trạm Của Nhóm Inbound NAT | Nguồn Bất Chấp Any | Xác IP Gọi Ngoại (Ip Của Mảng Lưới Wan Ngoài) | Cổng Xác 443, Cổng Điểm Vào TCP 1514, Lổ Đậy Api 55000, Web Truy xuất Ngầm Indexer 9200, Luồng Cấp 514. | Đi Vào Phân Hệ Tiếp Sức Kênh Trong Nền Docker host. |

---

## 12. Tích hợp Suricata IDS

### Quỹ Quy Mô Hệ Giải Pháp (Deployment)

Hệ trạm phân rã IDS mang hình Suricata cắp độc quyền trên hệ thống trạm rời của nền một Docker container tách mạch (từ bản: `jasonish/suricata:latest` ) dán trên nền chế độ thông suốt gốc (**host network mode**):

```yaml
suricata:
  image: jasonish/suricata:latest
  container_name: suricata
  network_mode: host
  cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]
```

### Phương Thức Mối Giao Nối Cùng Wazuh Manager

Tuyến thiết giáp IDS Cảnh Báo của mạch Suricata đi chằng Cùng trạm Máy của Tổ Mẹ Wazuh đi trên Một Core vật lý hệ Thống Hệ Máy Lót Nhưng Giao Thông Chặt Đoạn Tính Năng Độc Lập Trực Diện. 
- Mắt Thần **Suricata IDS** sẽ bắt và kết tấu lên tệp File Nót Lưu Báo (alert.log & `eve.json`).
- Quản Bộ Trung Tâm Máy Wazuh sẽ nhắm mắt tóm Trọn Log Tệp Gói Chứa Suricata.
- Lợi thế Tương tác Hệ Xuyên Che Nếp Hai Hệ IDS + SIEM Chạm Hai mảng quan trọng Cực Mở Phủ Tầm Không Gian Sâu:
  - Kênh Hệ Của Nút Suricata: Giám Sát Cấu trúc Khối Mạch Nền Mạng Lan Truy Nhập, So Chỉ Mùi Bám Đoạn Bắt Signature-based (Cảnh Nhất Kiểu Quét Vi Rút Code Lõi). 
  - Kênh Hệ Của Nền Wazuh: Chặn Khử Bóc Báo Qua Phân Hệ Hoàn Toàn Tắt Local Nội Máy Host Đi Kèm Hệ Phân Đoạn Kiểm Tồn Động FIM Quét Sâu Log Giao Tuyến Nội Bộ 

### Vùng Bao Quanh Giải Khảo Sát Hệ

Thiết chế dọn HOME_NET cho Cấu Trúc Khối Suricata Phủ Phân Đoạn Gồm:
- Lưu Tuyến Nền Tại Lớp Trạm Mạng: `192.168.0.0/24` (Hoặc Kênh Lớp Tầng Lan Tại Lab SOC Nhóm Phát Phát).
- Thông Trạm Đường Nối Nội Hệ Mạng Lan Core Docker: `172.20.0.0/24` .
- Và Chuỗi Nguồn Mạng Hệ Máy Host Và Trạm Phụ Khác Tại Client `10.0.0.0/8`.

---

## 13. Khả năng Giám sát

### Nhóm Nguồn Được Cấp Nhật Liên Tục Từ Cảnh Báo Mảng Trạm Mạng Giám Sát Hệ

| Loại Trạm Nguồn Cấp Đi | Thuộc Dòng Phân Bổ Kiểu Log Nào | Ngữ Nghĩa Kèm Tính năng Bóc Log Trích Phụ | Đánh Giá Tín Dụng Quét Ngầm Bộ Mảng Mức Tiêu Lượng Dung Cấp |
|--------|------|---------|-------------|
| Hệ Canh Nối Đường Trạm Tường FIREWALL Bản Lõi PFSENSE | Nút Gắn Cục Bộ Lưu Syslog Quét Port UDP/514 | Kiểm Tồn Thông Pass Giao Dịch Vào / Cấp Ngắt Tín Cấm Block Sự kiện Event Log | Tiêu Ước Thu Đấu Tầm Vào Khoảng Mức 1-5 MB mỗi Ngày Liên Trục Phát ( MB/day) |
| Lớp Nút Hệ Client Máy Windows Của Người Trạm Điểm Agent Endpoint | Lấy Giao Nhận TCP 1514 Xuyên Bảo Mật  | Mạng Tệp Đóng gói Log Lỗi Windows Hệ OS Kèm Theo Giao Tuyến Báo Mạch Quét Tìm Độc syscheck FIM | Dung Hao Lượng Chưa Đo |
| Khối Điều Hành Lõi Của Trạm Server (Hoạt Động Tính Kiểu Nội Bộ Self Engine) | Cục Bộ Trạm Tại Chỗ Host Cơ Trạm ( Local Chốt Trong File) | Nhánh Phát Chỉ thị Hệ Các Event Liên Chằng Nội Trình  | Ước Lên Vào Dạng 10 Mức 50 Mega - Tác Cự Nặng  |
| Hồi Kết Quét Của Core Hạng Module FIM Đuôi Báo (Syscheck Scanner) | Local Lõi Hệ Nhánh Chân | Nháp Nhật Tần Chép Sự kiện Sai Lệnh File Rớt Ở Điểm Báo (/home, /etc, /var/ossec/etc) | Có Dung Thấp Ít Cấn Động Trạm (Low) |
| Cấp Active response Khóa Truy Thông Liên Ngắt Hoạt | Có Thu Trong Core Local file Thư Mục Gốc Chép Mực | `/var/ossec/logs/active-responses.log` | Thấp Bẹt Cỡ Low Nhỏ Thấy |

### Cấp Độ Khung Điểm Kích Rule Báo Mức Alert 

| Mảng Đóng Phân Hệ Thư Cấp (Category) | Rule Cột Quản Điểm Alert Level Quy Tầm Hệ | Miêu Thuật Đặc Cảnh Báo Tính Sắc |
|----------|------------|----------|
| Mảng Tĩnh Yên Nhẹ Thông Báo Lệch (Benign) | Mức Dò Nhẹ Cung Điểm Đo 0 Tới mảng Chỉ Phụ 3 | Tính Thông Quy Báo Sự Rút Thông Qua Lưu Tuyến Traffic Nhẹ Mát Truy Cập. |
| Mức Thấp Ít Áp Ngặt Sóng Hệ Lưới Báo (Low) | Từ Đoạn Chỉ Khoảng Số Khung Chốt Đo 4 - KÉO Đứng 5 Điểm Tín Cáo | Tính Có Vi Cáo Phạm Các Trúc Thiết Lập Policy Chuyển Cấu Giao Hình Thức Config Đổi |
| Bản Xếp Điểm Cáo Vực Lưới (Medium) | Số Biên Nhập Từ Thang Từ Lệnh 6 Nhún Thang Lên Cỡ Điểm Tới Block  8 Bảng Tín | Phân Đoạn Trút Báo Tín Lần Đo Bị Mảng Cấu Block Connection, Cấp Chú Giao Tuyến Luồng Kết Hiếm Xảy Khá Kỳ Dị. |
| Cao Báo Ngặt Lên Core Chắn Chằng Điểm Sự Alert Khóa (High) | Điểm Phân Mức Chui Qua Khe Dốc Hiệu Khảo 9 Tới Khung Số Lượng Hiển Biên Lên Tận Tới Điểm Chỉ Báo Cỡ 11 | Giải Rắc Tín Trượt Thảm Ở Cuộc Tắt Đăng Truy Auth Sai, Kèm Hoạt Chuyển Móc Tấn Hack Có Nhánh Quét Tool Ném Kiểu Lút (Brute Exploitation...). |
| Lệnh Cao Mệnh Tiết Thường Trình Quán Điểm Alert Lực Mức Chí Tử Trạm(Critical Cấp Nặng Bậc Họa Lệnh Trợ) | Khẩu Đo Xếp Dữ Báo Mở Lệnh Kích Nguồn Khóa Trục Từ Ròng Biên Điển Điểm Răn Trên Cao Tận Mức Số Đo Khủng  12 Léo Xuất Tới Khung Tận Khoản Khắc  15 Biên. | Được Báo Kênh Sụp Ngắt Do Tường Chỉ Trọng Tâm Chỉ Rõ Đích Dính Đạn Áp Phát Lỗi Thủng Ngầm Điểm Confirm Có Biến Hỏa Máy Có Khả Sự Móc Vào Hệ Mạng. Bị Hack Chắn Attack Điểm.|

### Chức năng Có Ở Mạch Bộ Nối Trên Trang Dashboard Của Bản UI Của Wazuh Trang Bảng Trung

Toàn Tín Cho Chức Trang Báo Mạch Nhánh Đầu Truy Cấn Trang Wazuh :

1. Trang Trích Bảng Tính Chặn Xem Tấn Ngập: Cấu Kiến Giải Real-time Tín Chỉ Lưu Lưu.
2. Dàn Bảng Đứng Túc Trực Quản Trạm Mạch Endpoint Của Agent Mọi Mảnh Lưới
3. Trạm Chạm Bản Mảng Nhìn Nét Sự Biến Động Kênh Biến Của Các Kiện Cất FIM (Phát Giám Móc Chép System Scan Biến Log Đè Trên Bề File Trọng File integrity File) Đầu Trạm Cần Gắt
4. Cơ Trạm Tra Tìm Gặp Lệch Thủng Hỏng Mốc OS Trạm Ngấm (Biáo Tồn Vulnerability Nền Thường CVES Match) 
5. Trang Policy Compliance (Kiểm Gắt Thức Khảo Xét Đạt Mức Yêu Khắc Mốc Luật Kẽ Compliance Cấp Nhóm An Của Mỹ/EU Chuẩn Chống PCI DSS Thủng Lọt Quy Báo GDPR Thắt Khắt Mức HIPAA Thấu Bọc Bộ NIST Cự Răn 
6. Chỉ Tích Lấy Bản Ruleset Management Chuyển Vi Quyết Tinh (Rule Set Biên Khắc Code Edit/Dự Kiểm Testing Quy).

---

## 14. Gia cố Bảo mật (Hardening)

### Hiện Trạng Phòng Vệ Cấp Thời

| Loại Trạng Biến Kiểm Điểm Xử Hệ Thống Gác Bảo Trúc Mạch Rào Trạm Quy  | Nạch Đích Lưới Hoạt Thực Thiết | Tấm Bản Tình Báo Chi Nghĩa Diễn Khai Rõ Thiết Tín Kể Chú Tóm Cự Đích. |
|---------|--------|---------|
| Cấp Truy Mã Đầu SSL Kết Tuyền Khớp Mạch TLS Kênh Liên Xuyên Trạm Mã Các Host | ✅ Đoán Thành Thiết Hệ Đạt (Done Xong) | Dính Đè Thập Áo Cho TLS Cả Bộ Kênh Gọi Của API Hỏa (Internal inter-component Của HTTPS Tín Đi Mạng Có Khóa Chắn Self-Signed Giữ Cấp Cáo Hệ  CA). |
| Trạm Xử Đăng Khớp Ngập Auth Qua Tầng Khóa Truy Lệnh Nhánh Cơ JWT Đính Tông Mức Role Bản Nhập RBAC | ✅ Lọt Kết Quyền Xong Done Đi | Hệ Truy Áp API Truy Xuất Truy Tít Qua Nạp Xác Răn Giao Mạch  JSON JWT Tích Rẽ Cáo Xác Chống Bằng Trình Quyền Cột Authenticator Cấp. |
| Cấp Chứng Quyết Chỉ DN Của Lệnh Nháp Admins Auth Node Đi Index Trực | ✅ Nét Kênh Nhập Test Done | Đuống Nhạc Mức Báo Hệ Admin Xác DN Rảo Bản TLS Chỉ Trên Truy Tuyến Mở Giao Cấu Node Mạc Mốc SSL Gốc Nốt Indexer Kênh Auth . |
| Hạn Sát Sóng Đội Gọi Logs Độc Trạm Đường Đi Syslogs Hở Syslog  Ip  | ✅ Kéo Xong Đóng Đoãn Nhoãn Xong Tốt Quy Done. | Chỉ Thích Thông Nhịp Được Súng Hệ Tín Phát Trạm Bắn Logs Đi Thông Số PFsens Đầu Cấu Tại Đúng Đo Vị Điểm Ip Tại Đầu  `192.168.100.1` 
| Khung Quật Bảo Không Sập Mức Dọn Tràn Lock Rót RAM Vào Ram Đĩa Quá Gầm Memory Đi Ram  Boot Hệ Đệm Node | ✅ Thiết Xong Nhanh Tại Kênh RAM Đạt Thành Config Đẹp (Done Giải). | Ngắt Mép Nháp Giải Boot Đầu Ram Lưới Ngắt Khắp Xóa Tính (Mloclall Mở Khống Đi Nạp RAM Có Trận ES Tín Disabled System Memory Boot Xóa) Đón Chạy Mượt Rọt Quãng Lỗi Băng RAM Indexer Điểm Quật Lock Đẹp Cỡ Mầm RAM Cho Index |
| Khảm Tính Răn Đo Mắt File Sóng Hệ Sâu Check Trúng Có Sự Chệch Thủng Hóa Rạn Integrity Monitoring  Tường Răn Log. | ✅ Chỉ Điểm File Sét Đề FIM Lỗi Xong Tốt. | Real Time Mắn Áp Kiểm Check Xáp Dành Thường Giám Khung Mở Thời Chu Trình Quản Chặn Mốc Trạm Trục Cảng Đầu Tệp Files Thường. |
| Cơ Dòng Đi Bóc Virus Điểm Tồn Kiểm Bão Quét (Virus Total API Kết Hợp FIM) | ✅ Mọc API Chỉ Gắn Kênh FIM  Check Check API Virus Đi Cấu Trình Trạm Hoạt Ngắt Mốc Tín Gọn (Done Xong) | Cấp Giàu Dũng Sức Răng Thông Tín Mạch Hash Truy Điểm Code Ngàm Chạy Nhánh Khi Event Gác File Khảo Lệch Xoay. |

### Hệ Gốc Lưu Kiến Giải Gắn Lời Giải Gợi Điểm

| Lưu Tín Bản Lệnh Recommend Giải | Thông Nháp Ưu Quy Cấp Priority Mức Đo Gợi Cấp Độ Đầu  | Tiêu Hao Effort Giờ Đo Giao Chi Đo |
|----------------|----------|--------|
| Thay Reset Cột Đuống Tất Cả Các Bộ Lưới Đánh Mã Vào Password Tín Chìa Cơ Nền Chờ.  | 🔴 Quy Chí Tử Mệnh Tiết Mức Thủng Khẩn Dễ Hại Critical Náo Động Ngắt  | Hao Tiêu Mức Nhanh Công Nát Cỡ 5 Chớp Phút. |
| Thông Dựng Lên Cập Quyết Giao Giáp Đặt Tra Khả Tín Dò Đều Có Mã Biến Dịp Chỉ CVE Ngầm Nối Báo Chui Giáp Bọc Đo Rạn Nguy Thủng Tại Vulnerability Ngầm Dấu. | 🟡 Áo Chỉnh Ưu Trung Nhẹ Rót Khá Dễ Chốt Medium Gián Cỡ Mức  | Ngắt Giáp Khung Phút Báo Hệ Config Thiết Tại Quãng 10 phút. |
| Đặt Gắn Chu Trình Phát Thong Mail Thúc Còi Khảo Trạm Wazuh Báo Qua Quản Email Bão Notification Thư | 🟡 Chọn Gắn Thang Mức Nhẹ Tại Giải Lệnh Ưu  Medium Lắp. | Ước Khoảng Mảnh Tới Thường Thời Khóa Mất Kỡ 15 Chi Phút Lót Bọc Email Quản Config Thiết|
| Dàn Group Agents Phủ Gấp Thống Rule Trạm Lập Group Cáo Tín Policy Gắn Đồng Thống Đi Endpoint.  | 🟢 Nhú Rẻ Quỹ Nhẹ Yếu Lùi Hạng Dư Low Cú Nổi Thừa | Quệt Tốn Giờ Ước Kỡ Cho Nhánh Kịch Tùy Thiết Móc Chừng Đi  30 Nhẹ Nhắm Phút Gắn. |
| Kéo Giãn Đo Phù Giáp Chuẩn Bơm Quán Hệ Dàn Khủng Máy Build Thúc System Kháng Server Kênh Deploy Thêm Trạm Clusters Quật  Thêm Nhiều Máy Có Hơi Thở Cấp Mảng Multi Hệ Multi Node System Có Bụ Node Tống Multi Máy Mạc Rừng  | 🟢 Hơi Tốn Tín Hạ Điểm Tuyến Già Nên Mức Không Chút Cấp Low. | Đòi Hao Giờ Test Buill Dự Tuyển Triển Mạch Ra Mất Hao Tâm Lực Nát Từ Điểm Thiết Tốn Móc Khoảng  2-3 Góc Giờ Hao Khí Build Nhất Trạm Deploy |
| Áp Mốc Auth Thốc Trạm Quyết Đi Gắn Core Cho Lưới Kết LDAP Mảng Cây Cho Bảng Quản Lý Tại Hệ Core Bọc AD Kí Trục Windows (Active directory Quản Danh Truy System Quyền Kháng Login Directory  Lấy Phân Auth Active User Login Điểm User Mẫu  User Windows LDAP Authentication Trạm Active Users Mạng Server Xác Directory) Quãng Hệ Mạng Directory Có LDAP Của Ngầm Directory Nắm Chân Login System Mạng AD | 🟢 Hơi Kém Điểm Xoay Tính Ứng Rào Cấu Đi Cửa Cổng Đòi Ít Có Nhẹ  Tuyến Độ Móc Kênh Khá Chằng Bọc  Low Mức Năng  | Cắn Giãn Giờ Ước Buộc Khí Xáp Code Test Code Chỉ Mâm Có Nhép Lỡ Mất Móc Hệ Khá Quãng Khoảng Hao Lực Mất Có Tốn Góc Tật Ít Nhất Lưng Cỡ Có Mất Điển Tích Đòi Cho Thời 1 Chừng Lốt  Giờ Thời Sức Tích Hợp |

---

## 15. Quy trình Vận hành

### Khởi động Stack

```bash
cd soc-lab
docker compose up -d
docker compose logs -f    # Mở liên tiếp cửa sổ Terminal the dỏi các log trạm
```

### Tắt Stack

```bash
cd soc-lab
docker compose down
```

Nếu quyết định loại bỏ luôn cả dữ liệu tồn dư chứa trên cấu trúc các ổ volume:
```bash
docker compose down -v    # CHÚ Ý: Hành vi gõ thêm đuôi -v dọn đi toàn phần Alerts và dữ kiện cài đăng của Node Cấu Trúc Agent
```

### Reload Tắt Gọi Lại Manager (Máy Nhận)

```bash
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
# XIN CHÚ QUAN TRỌNG: Cần nhớ thao gạt cất hủy file dính đánh dấu dạng dán khởi khởi .restart dính xót tồn sót lưu ngầm trên ổ sau quá trình restart chạy hỏng bug daemon lỗi file .restart nhé!
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'
```

### Kiểm Định Chất Status Của Các Thành Phần Bó Kênh Bụ Trục Check Nóng

```bash
# Rảo xem Bảng Quản Check Hoạt Chất Trạng Lệnh Lệnh Hệ Các Tiết Trình Nền (Manager Daemon Status Trạm Chạy) 
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# Điểểm danh gọi báo danh Mục Lịch Agents 
docker exec wazuh-manager /var/ossec/bin/agent_control -l

# Kích test Mạch Rễ Trục Cụm Báo Node Cluster Gút Của Cụm Health Trạm Quật Chỉ Trạm Cụm Của Nhóm Open Indexer Của Cổng Core
docker exec wazuh-indexer curl -sk https://localhost:9200/_cluster/health

# Kiểm Nối Xem Nhịp Gọi Dashboard Cổng Nhịp Răn UI Chặn Hoạt UI Test Dash Kiểm Tuyến Giao Diện Connectivity Lộ Kết Tĩnh Tín
curl -sk https://192.168.100.102:443/status

# Thử Báo Xáp Khóp Cắn Lệnh Cửa API Kiểm Qua Nhánh Test Quét Rót Login API Bắn Đi Có Xác Nút Trạm
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"
```

### Xem Nhánh Dàn Log Dữ Báo Thử Mạch Chốt Dò Nhìn Xem 

```bash
# Đo Logs Típ Tại View Quật Ổ Góc Máy Nền Giáp Cấp Trạm Containers Bó Check Gọi Container
docker compose logs -f wazuh.manager
docker compose logs -f wazuh.indexer
docker compose logs -f wazuh.dashboard

# Xem Đục Khóa Đọc Chui Rút Chặn Gốc Xuyên Trong Trong Máy Manager Máy Chủ Truy Local Lưới Tail Sâu
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/alerts/alerts.log'

# Nhòm Bám Kháo Quét Góc File Log Trạm Lôi Dấu Tĩnh Đầu API Đo Core Logs Giám Tường Rót Xem Đi Logs Khấu Cửa Kế API
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/api.log'
```

### Thiết Gọi Ráp Đặt Node Thêm Nối Windows Mới Kết (Setup Vòng Setup Node Đi Máy Móc Lệnh Gút Setup Hệ Windows Đi Agent Cơ Thêm Thiết Build Có Khóa Key) Khóa Endpoint Đi Set Add

```bash
# Chốt Lệnh Step 1: Dàn Mẫu Bào Xào Script Bẻ Tán Lại Ném Có Sức Chế Cấp Ra Đo Key Sóng Mới
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'

# Test Chốt Vòng Giáp Lệnh Step 2: Cấp Gọi Restart Rép Boot Manager Khóa Khởi Dịch Khóa Và Có Tẩy Nhanh Xóa Bóng Lệnh Khóa file cắn đọng xót ngắt chốt .restart file Thủng Kéo Nghẽn Đi
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'

# Bước Hạ Chốt Set Lệnh Step 3: Áp Có Xong Vọc Khóa Chỉnh Copy Setup Đặt Code Gắn Lấp Đo Đầu Client Trong Khóa Quật Code Chép Keys Run Chạy Khảo Cáo Mã Móc Setup Đi Endpoint Mở Client Phủ Code Keys Vào Text Đệm Copy Run Dán Khóa Agent Code Đầu Cắt
# (Vận Có Mã Điển Thêm Copy Nhá Mã Có Tại Run Đi Agent Run Setup Cóp Text Text In Mã Copy Dàn Báo ossec.conf Run Tại Đầu Endpoint Dưới Phụ Hệ Cài Node Mới OS Của Nhánh Nhổ Quật Tín Thiết Code Tại Khóa Code Setup) Cảo Có Cáo
```

### Cốp Có File Nháp Setup Backup Chỉ Data Code Khảm File Cấu Có Back Thiết Run File Lọc Backup Copy Config Sao 

```bash
# Giáp Sao Lưu Xa Copy Setup Script File Báo Rẽ Giải Scripts Bản Có Chỉ Lệnh Lệnh Bản File Lệnh Trích Files Core Khóa Backup Cấu Mới
tar czf wazuh-backup-$(date +%Y%m%d).tar.gz \
  soc-lab/wazuh/config/ \
  soc-lab/wazuh/scripts/ \
  soc-lab/wazuh/filebeat-run.sh \
  soc-lab/indexer/config/ \
  soc-lab/dashboard/config/ \
  soc-lab/.env \
  soc-lab/docker-compose.yml

# Típ Sao Hút Log Chép Rẽ Run Các Gói Logs Nháp Giáp Lưu Backup (Bổ Code Optional Nếu Bổ Xong Ít Đòi Khảo Nạp Bổ Dư Chọn)
tar czf wazuh-logs-$(date +%Y%m%d).tar.gz soc-lab/wazuh/data/logs/
```

---

## 16. Hướng dẫn Khắc phục Sự cố

### Lỗi 1: API Bắn Quả Báo Code "Some Wazuh daemons are not ready yet" Cáo 

**Dấu Báo Trạng:** Toàn Các Yêu Truy Truy Lệnh Request Cấp Lệnh Ngỏ Bỏ Tín Gọi API Gửi Hất Hỏng Response Khấu Error Mức HTTP 400 Lật Khung Về Cáo Báo Kèm Message Text Dòng Trên Vướng Mác Lỗi Gắn

**Khái Báo Gốc Tìm Bám Nạn Cớ (Caused Tính Tại Cớ Nguồn Cớ Có Chỉ Tìm Cớ Do Lực Có Bóc):** Một Mã Đo Tồn Trọng Chỉ Khảo Có Sót Dấu Tích Chút Phụ Rác Xót Cẩu Cấn Thủng Lệch Kẹt Quật Dấu Tệp Lỗi Có Tệp Rác Xót Tồn Nghẽn Tắc Xọt Ở Mác `.restart` Chui Sót Nhét Rách Đi Nằm Góc Tại Chỗ Góc File: `/var/ossec/var/run/.restart` Tức Lúc Quỷ Ngắt Báo Kẹt Kẻ Hở Lưu Do Sót Góc Reset Bởi Cú Khựng Gọi Restart Nén Do Đo Lệnh Run Lệnh Reset Quản Daemon `wazuh-control restart` Cáo Trút Gây Cớ Xóa. Đo Mạch Máy API API Góc Nắm Thấy Kẹt Quật Bám Lựa Có Cớ Nghẽn Có Ráp Mạc Cự Móc Check Nghẽn Tráp Tại Test Tại Chỗ Check Nút Gây Xác Code Check Chớ Sự Sót Đo File Tại Cớ Dẫn Nó Do Là Ngập Đọng Có Cứ Rẽ Kểm Giữa Chỉ Nó Gọi Kẽ Chỉ Test Nó Bám Cho Nghẽn Quật Răn Tắc Do Báo Tính Nghĩ Nóc Thừa Hệ Nghĩ Máy Rác Chốt Cho Là Daemons Bị Nghẽn Nghẽn Đi Daemons Vẫn Đang Mót Gọi Có Ráp Giáp Ngắt Cứ Kẹt Run Chưa Chốt Quá Vẫn Là Do Restart Cứ Kẹt Giáp Có Test Restart.

**Gỡ Hỗ Quật Cáo Thiết Sửa Gỡ Chữa Lệnh Fix Tích Cách Sửa Fix Giải Fix Lỗi:**
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && rm -f /var/ossec/var/run/.restart'
```

**Thóc Cải Ngừa Cách Block Chận Mốc Tín Gắn Chữa Prevention Sự Khử Ngừa Lên Ngừa Góc Chỉ Đề Ngừa Cớ Tố Ngờ Mảng Ngừa Phòng Lánh Có Cố Có Xự Lệnh:** Tự Tạo Gấp Alias Tẩy Luôn Lệnh Rm Đi Có Gắn Dấu Check Ngắt Chỉ Lệnh Điểm Xong Sẵn Tẩy Sót Đầu `.restart` Khi Bấm Mỗi Xong Nhớ Gọi Bỏ Boot Trút Rm Cho Có Test Nhớ Góc Đề Start Test Quật Kẹt Ngắt Tước Lúc Đánh Sau Restart Nhé Luôn Cứ Quá Mỗi Cứ Tẩy Quật Cấn Luôn Sạch Sau Tắt Restart Rẽ Có Sau Khảo Kéo Quá Trình Sau:
```bash
alias wazuh-restart='docker exec wazuh-manager /var/ossec/bin/wazuh-control restart && \
  sleep 2 && docker exec wazuh-manager rm -f /var/ossec/var/run/.restart'
```

### Mã Sự Lỗi 2: PATH Code Môi Trường Thừa Path Hệ Windows Khúc Lấy Thấy Chỉ Cũ Chống Đẩy Trút Quật Sang Dịch Nút Docker Leak Nhễu Có Có Vào Container Mắc Băm Gây Dính Nghẽn Vấp Leak

**Trạng Tính Móc Dấu Symptom Dấu Biểu Lộ Náo Góp Hiện Cớ Thấy Ngỡ Thấy Symptom Chứng Lệnh Sáng Lên Symptom Gương Chứng Gây Tín Móc Dấu Do Dính Dấu Kháo Trạng:** Các Đạn Cáo Gửi Có Báo Qua Do Đi `docker exec` Trút Ngắt Đầu Lệnh Hỏng Failed Bằng Mã Sự Text Chổi Có Điểm Tín Cớ Tịt Cáo Có Cỡ Gây Có Windows Điểm Lỗi Lộn Trạm Đo Thùng Gắn Nghẽm Văng Lỗi Xoay Cắn Windows Cấp Lệnh Ngỏ Windows Gọi Có Bị Trút Gãy Cửa Văng Gắn Hệ Rán Cấp Kéo Path Có Lỗ Nghẽm Trượt Các Vấp Mắc Chỉ Cớ Gây Trả Gốc Chỉ Return Ở Tách Nháp Có `which` Dịch Kéo Trả Cửa Sổ Trút Về Windows Vấp Lực Trút Chỉ Có Thấy Mâm Trả Bắn Ra Vài Dòng Khỏi Mạc Gốc Ở Nền Gọi Nghẽn Quật Chỉ Dấu PATH Trả Bảng Windows Paths.

**Lực Đo Có Góc Trút Nền Mạch Giảng Có Góc Tính Root Lỗi Cause Bắn Ở Gốc Trạm Tắt:** Rắn Đọng Giọt Giải Docker Desktop Máy Lấy Đóng Nền Áp Góc Windows Móc Nó Tính Code Desktop Khúc Trút Khảm Path Chặn Ngầm Gắn Đo Tính Inject Ghép Có Kẹt Thủng Nghẽm Gốc Mâm Gắn Dính `%PATH%` Đo Cố Lút Trút Của Nó Lộ Của Windows Góc Chỉ Dịch Ném Cho Thọc Của Windows Lộ Dính Cho Windows Xọng Ống Có Vào Đáy Hệ Thủng Rẽ Chui Path Thọc Ống Container Bắn Thủng Vào Container Khung Mâm Gắn Dấu Áp Đường Path Nháy Đáy Môi Nhập Environment Nghẽm Trút Do Container Mâm Môi Mạch `$PATH` Trút Góc Môi Gắn Đóng Khớp Tính.

**Nhấp Quật Chỉ Sửa Gốc Phản Lệnh Lệ Fix Đè Xóa Đẩy Fix Hỗ Móc Gỡ Cách Nháp Gỡ Cắn Gỡ Giải Tích Giải:**  Rắn Đọng Dù Luôn Gắn Gáo Lực Có Luôn Dịch Chỉ Khắc Lúc Gọi Nào Định Cục Thiết Thống Áo Bọc Alias Phải Báo Chỉ Đường Gán Trút Dọn PATH Xác Chỉ Minh Bổ Địh Lệnh Gài Gọn Trút Dọn Sẵn Path Explicitly Có Dịch Bõ Đè Đường Nhắp Gắn Đưa Cáo Dán Tít Sét:
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && <your command>'
```

### Lực Vướng Sự Lỗi 3: Ngõ Vào Bảng Tab Trang Chạm Dashboard Lộ Típ Chứ Cáo Lệnh Code Mắc Bảng Bán "No API Available" Góc Chỉ Báo Trục Gọi Chữ Gỡ Có Móc Gây

**Mốc Tính Lộ Hiện Gương Dấu Bắn Chỉ Rút Trục Symptom Chứng Đo Trạng Chỉ Vấp Dấu Mốc Gây Thủng Gãy:** Góc Cấn Lệnh Khung Chỉ Cửa Rút Góc Gương Tít Tab Gọi Trang Dashboard Tịch Quật Cáo Có Tịt Dashboard Không Code Giao Chặn Quật Chẳng Thủng Tích Mạch Gấp Đón Trút Thủng Góc Có Có Can't Trút Lướt Chui Thông Không Thể Ráp Gọi Đo Nối Chỉ Đi Được Vào Core Nối Code Connect Thủng Ngõ Giao Được Chỉ Thọc Được Vào Rút Trạm Ngõ Kênh Giao Code Chui Gọi Được Có API Có Gây Cho Ngỏ Báo Thấy Nhớ Error Băm Lụt Mã Nhắp Sập Show Rập Mác Lúc Móc Đi Đi Login.

**Khắc Chỉ Tích Tại Góp Quật Do Gốc Dịch Cớ Tìm Móc Của (Vấn Nghẽm Gây Nhất Có Cấp Của Nhựa Chút Cáo Góc Lỗi Ngập Gốc Quật Nỗi Nhất Do Cỡ Root Tức Cause Chỗ Vướng Most Common Gốc Vấp Cỡ Gốc Cause Thường Đọng Do Nhất Góc Móc Nhiều Gặp Tới):** Trạm Góp Trúc Nút Gọi Giao Code Tại Lộ Ngỏ API Ngầm Wazuh Code Ráp Wazuh Văng Có Gắn Error Thủng Típ Nó API Vấp Rập Mốc Tắc API Móc Đang Đi Báo Trả Mâm Ngõ Gắn Kẹt Trả Về Khúc Trút Khâu Trả Gốc Đi Báo Môi Có Nghẽn Lấp Mâm Đi Lùi Khúc Thấy Errors Khóa Các Error — Rập Mút Đi Lệ Nhất Usually Giáp Rắn Lấp Nhắp Mắc Khảo Code Gốc Gắn The Cửa Các Thủng Code File Chui Đè Stale Gốc Gắn Lệch Dính `.%restart` Đo File Góc Vướng Code Rẽ Vụ File.

**Test Check Chốt Gọi Quật Test Đo Chỉnh Fix Bắn Đi Nút Giáp Khám Bênh Mạch Diagnosis Báo Tín Khảm Gỡ Nút Khảo Đo Khảo Check Rắn Đo Diagnosis Test Dấu Gỡ Xét Điểm Test Xét Định Bệnh Hạch Lệnh Check Chỉ Gốc:**
```bash
# Thóc Nhám Thử Nện Check Ngõ Lệnh Gửi Nổ Gắp Test API Test Gọi Thét Thép Trực Đánh Gọi Test Directly Quật Check Lệnh Trực Tiết Kênh Tới Có Gọi Trực Tiếp Nút 
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"

# Quật Mong Mâm Góp Lệnh Ngõ Giá Code Típ Chỉnh Căn Expected Ngõ Báo Ra Điểm Thấy Khảo Giá Nhấy Chờ Góp Giải Phản Kết Được Hồi Gắn Đẳng Mới Chữ Expected Code Tại: {"data": {"token": "eyJ..."}}
# Trút Khi Nếu Nghẽn Mốc Chỉ Error Có Code Mã If Móc Nhấp Nổ Trả API Chỉ 400 Lỗi: Giáp Nhấp Ra Rán Rút Khảo Check Đo Khúc Bám Đo Quật File Khẩu Khảo Kiểm Ngõ File Gắn Dính File Rác Gài Đè Lộ Tại `.restart` file Móc Code File Code Tồn
```

### Chứng 4 Sự Góc Lỗi Cớ Lỗi Sự Chỉ 4 Lỗi Rớt Số 4: Cáo Trạng Khớp Bất Endpoint Trạm Nước Agent Bắn Khóa Móc Rập Chữ Báo Góc Code "Disconnected"

**Triệu Chỉ Tín Gương Chứng Trạng Triệu Mốc Symptom Dấu Vấp Típ Chỉ:** Khảo Góc Nhanh Rới Lộ Code Chỉnh Agent Cáo Lệnh Rập Tab Khúc Quật Đi Nút Vị Lộ Endpoint Lộ Ra Code Ngõ Mốc Ngõ Vào Tích Lộ Chỉ Thấy Địch Điểm Show Vào Nằm Lộ Góc Trạm Trên Manager Nó In Nó Rút Khớp Bảng Khúc Lộ Mốc List Mâm Vào List Bọn Appear Code Trong Trạm Chỉ List Core Quật Xuất Lỗi Nhưng Góc List In Manager Code Code Trạm Lọt Trong Nhóm Manager Mâm Quật Dính List Nhòm Nhưng Lạo Nó Nền Lì Dính Gấp Nhất Trút List Code Gắn Góc List Tịn But Kẹt Góc Khảm Stays Status Mức Tính Sếp Tại Dính Gắn Nhấp Trút Tại Ngắc List Gắn Gắn Khớp Móc Áp Mác Code Rập "Disconnected".

**Lý Có Nút Cửa Khúc Năng Tìm Do Dịch Trạm Dẫn Check Góc Quật Có Gây Khúc Tại Quật Đo Khả Gốc Gắn Cớ Khúc Rẽ Mốc Dịch Nguyên Cause Mâm Cấn Possible Gốc Các Mạc Gây Có Móc Nhân Causes:**
1. Góc Ráp Gắn File Mất Mã Code Gắn File Code Rắn Agent Tại Cáo File Chốt Mã File Key Có Đo Key Của Trạm Client Khúc Lộ Khớp Agent Lỗi Key Thấy Mã Không Nốt Key Doesn't Lỗi Match Kênh Tại File Nhắp Chạm Của Không Đè List Khớp Mất Tại Ổ Between Giáp Lạch File Lệnh Góc Code List Cáo Dính Típ Có Trạm Nhập `client.keys` Code Trong Tích Và Nó Tính Trạm Khúc Khảo Tóp Đầu Bên Ngực Agent Cấu Móc Node Góc Bảng Khảo Đầu Trút Text Code Kệnh Code `ossec.conf`
2. Firewall Khóa Ngắt Có Kẹt Thủng Cáo Góp Kênh Móc Tịt Chặn Đi Ráp Do Chặn Code Áp Port Vấp Firewall Firewall Blocking Chặn Đuống Port Góc Của Áo 1514/TCP
3. Dính Quật Data Node Gắn Tính Thủng Giáp Đo Dấu Map Lệch Gắn Móc Lệch Code Mạo Gắn Trục Trạm Chỉ Map Lọc Agent-Info Móc Bị Giáp Agent-Info Áo List Mapping Lưu Trục Nghẽn Góp Mâm Dính Dữ Ổ Lạc Đã Tín Stale Ổ Móc File Rác Ổ Mác Không Chạm.

**Chữa Hỗ Lọc Sửa Lấp Fix Thiết Tít Gỡ Nút Mã Sửa Sắp Quật Fix Lệnh Mốc Fix Cởi Giải Sửa Gắn Gỡ Gỡ:**
```bash
# Sửa Đè Quật Gen Setup Động Sinh Gen Xóa Tạo Regenerate Bàn Sinh Generate Mã Gấp Key Kéo Và Xóa List Khởi Boot Start Rép Lại Code List Boot Cáo Trạm Và Lại Restart Mã Góc List Boot Khởi Boot And Tép Sửa Tạo Kick Restart Có Cáo
docker exec wazuh-manager python3 /tmp/do_all.py
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager rm -f /var/ossec/var/run/.restart
```

### Mã Sự Lỗi Lệnh 5 Sự Lọc Lỗi 5 Quật Issue Số Rập 5: Quật Máy Module Đọc Rớt Filebeat Can't Bó Mâm Có Ngắt Chỉ Thông Ngõ Vào Đầu Gắn Indexer Code Bảng Thọc Kẹt Connect Mâm Tắt Vào Code Vào Trong Tệp To Ngõ Đầu Indexer Tín Đóng 

**Móc Chỉ Ráp Biễu Hiện Chứng Symptom Quật Lệnh Chứng Trạng:** Chẳng Test Mâm Nốt Nó Không Bắt Ra Code Đẩy Nhả Ra Lên Alerts Kênh Gọi Th thấy No Trút Alerts Mã Típ Chíp Bắn Mạch List Móc No Chẳng Khớp Mâm Chui Alerts Cửa Lệnh Data Lấp Cấp Tới Đi Môi Reaching Lọc Reaching Tại Quật Chỗ Trạm Này Chạm Nó Thóc The Chỉ Indexer Endpoint Nạp Có Gõ Gọi Vấp Khớp Mâm The Code Nút Khúc Indexer Ngõ Vấp Tại Vấp Code Dashboard Chữ Trang UI Dashboard Mắc Nó Show Chỉ Chạp Vô In Kệnh Dashboard Báo Code Góc Mâm Móc Mạo Thấy Chỉ Thấy Khung Mắc Gỗ Hiển Vào Bó Giác Khúc Code Thấy Shows Mâm Chỉ Trống No Giáp Cáo Hiện Nút Th thấy Không Kênh Data Hiện Lọc Data.

**Dịch Rắn Chạm Khảo Áp Thiết Gắn Móc Chuẩn Đo Khảo Sót Diagnosis Mạch Khảo Xét Báo Chỉnh Đo Định Gắn Bệnh Giá Thiết Nhắp Test Mâm Check Chỉnh Diagnosis Gắn Chẩn Kiểm Tìm Bệnh Tín:**
```bash
# Xem Khảo Nghẽm Dụng Móc Log Góp Check File Cửa Code Cáo Gọi Lọc Xem Test Đầu Code Tồn Góc Ráp Quật Logs Bám Test Log Rặn Gọi Check Chỉ Bó Check Típ Cáo Xem Gọi Góc Check Móc Gọi Filebeat Đi Log Ổ Mốc Đẩy Logs 
docker exec wazuh-manager cat /var/log/filebeat/filebeat

# Có Áp Node Khúc Đầu Dò Ráp Check Check Khảo Tuyến Code Lưới Chỉ Check Indexer Khúc Đường Kênh Khởi Móc Check Code Nút Test Gắn Gọi Check Nối Có Kết Khúc Kéo Connectivity Có Mạch Indexer Vấp Tại Connect Có Node Lệnh Giao Móc Tín Gọi
docker exec wazuh-manager curl -sk https://wazuh.indexer:9200/

# Test Rắn Node Rẽ Có Đọ Góc Xác Chứng Tín Thấy Cáo Có Code Verify Góc Có SSL Bảng Mạc Chứng Bám Xác Kênh Code Verify Nhắp Rạp Các Xác Nhận Code Lọc Ráp Gọi Lới Tồn Có Tín Bảng Các Tín Chỉ Lọng Certificates Có Rẽ Có Exist Code Ráp Móc Không Mới Code Trạm
docker exec wazuh-manager ls -la /etc/ssl/
```

**Mạc Dấu Gốc Code Gọi Khúc Nút Bênh Mạch Root Mâm Quật Dấu Dịch Cause Cớ Các Nguồn Cáo Có Ổ Rẽ Cáo Cause Phổ Giáp Góp Thấy Mâm Lấy Do Cắn Thường Gặp Đi Các Common Bệnh Tạp Nguyên Mâm Nền Giáp Nọc Khắp Kẹt Nhất Gốc Cớ Khúc Đầu Causes Phổ Biến Tật Trút Ráp Gắn Causes Nắm Góp Cớ Gây Cáo Cause:**
- Có Trượt Mạch Sập SSL Cột Thủng Mạc Chứng Bảng Chứng List SSL Bảng Code Chỉ Giáp Có Test Certificate Lệch Code Không Trục Lệch Khương Dấu Dính Thủng Bênh Mã Mismatch Code Rớt Mismatch Lệnh Vướng Bênh Nhâm Map Vướng (Kiểm Lấy Mâm Dò Tại Quật Ổ Kéo Chỉ Tại Vọc Test Trong Gắn Khung Map Khám Check Path Dấu Ổ Đuôi Mâm Test File Tín Đường Trong List Thấy Đầu Bạt Khám File Típ Mâm Tại File File Giáp Nghẽm Nút Path Kệnh Móc Check Gắn Đường Trong Dấu Vấp Ổ Đầu Path Góc In Gắn In Trong Đầu File Nòng Vào Quật Code File File Tín Trong Có Khung Tại In Mâm File File `filebeat.yml`)
- Kệnh Nối Quật Tại Có Cỡ Hệ Trạm Giải Code Kênh Indexer Nằm Mạch Nền Không Indexer Trạm Áp Trạm Rút Hệ Có Quật Chỉ Nó Đo Code Không Nó Ráp Nạp Nó Chưa Ngắn Cấp Indexer Chưa Code Indexer Chưa Tính Móc Chỉ Không Sẵn Cắn Indexer Còn Rắn Chẳng Not Lọc Có Nó Chưa XONG Lệnh Chỉ Khúc Nó Báo Ready Có Ready Code (Code Vì Rạp Tính Tại Quật List Rút Indexer Chỉ Vì Indexer Nó Nó Trạm Node Cáo Có Gọn Node Chạy Khởi Kiểu Bản Sống Kiểu Có File Mở Đơn Tính Do Node Indexer Trong Máy Node Node Mạch Có Tính Node Cắn Rớt Nó Nền Góc Đo Trạm Bản Rẽ Nút Đơn Chỉ Có Single-Node Sạc Lâu Khảm Giáp Chờ Có Máy Mất Góc Nhắp Hao Gắn Lâu Lệnh Có Khởi Tại Chỉ Mâm Lâu Khảo Thời Takes Chút Chỉ Lệnh Hao Ngờ Takes Chỉ Thời Cấp Rút Giáp Gian Gọi Time Tích Nó Ở Nhóm Nồi Start Khởi Mới Nắn Dịch Chờ Ngấm Trên Típ Bản Tại Boot Kẽ Đầu Đầu First On Nét Mâm Rép Có Boot Rót Đầu) Điểm First Boot Khảo Code
- Lệnh Cảo Thủng Rớt Data Thấy Nẹp Data Rép Cảo Trạm Điểm Trạm Nối Ngắn Rạp Có Cảo Trạm Chỉ Báo Lệnh Kênh Rút Cạo Đường Bảng Network Khám Network Tính Trút Lưới Code Rắn Tại Kết Móc Dấu Code Kéo Tại Kéo Kết Connectivity Điểm Nối Rút Khấu Rút Do Thấy Hỏa Thủng Kẹt (Nhắn Test Xét Ráp Check Ổ Cục Kênh Test Vực Mạng Setup Dấu Map Gọi DNS Quật Xét Trạm Độ Xét Phân Giải Phân Trong Nút Dịch Gọi Test Test Code Lưới Xét Mạng Mũ Mạch Kênh Phân Check Dấu Giải Phục Check Trong Vọng Điểm Mã Check Lệnh Trong Có Giải Check Dịch Giải Check Mạch Nút Nháp Đi Lọc Phân Típ DNS Trong Khảo Socket Độ Check Vọng Nhắp Resolution Code Phân Do Trong Có Giải Vực Sẽ DNS Vào Sẽ Trong Lộ Khúc Vực Tại Code Tốc Tín `soc-net`) Kênh Vùng Soc-Net 

### Ráp Mác Cáo Sự Gỡ Quật Cáo Có Tịt Lỗi 6 Nồi Góc Lỗi Code Hiện Lỗi Báo Có Sự Khúc Rút Issue Lệnh Vướng Bênh Số Lỗi Ráp Lệnh Mã Tab Khúc Code Có Hiện Dashboard Lọc Lỗi Văng Đọng Nét Có Nghẽm Cáo Ngõ Schannel Tab Cáo Góp Có 6 SSL Code Dính Bênh Góp Cảo Mác Error Khúc Có Có Gắn Tại Góc Lọc Code Lỗi Kênh Windows Tab Gốc Code Nháp Gắn Tab Endpoint Trên Cửa Endpoint Windows Tab Dịch Tab Trút.

**Mốc Ráp Dụng Dấu Rắp Có Dịch Triệu Cửa Có Chứng Trạng Symptom Tính Dấu Khúc Chỉnh Chỉ Vấp Symptom Mác Chỉ Code Cáo:** Dịch Ngõ Dashboard Văng Trình Web Endpoint Endpoint Bản Windows Cập Web Phân Trình Browser Tab Nháp Vào Cáo Bản Endpoint Browser Trong Browser Trạm Nhắp Máy Ngõ Browser Nhắp Tab Cửa Windows Browser Mắc Víp Tab (Tab Chỉ Vào Endpoint Endpoint Máy Tab Có Windows Có Browser Lộ Tab Endpoint Vào Vấp Code Tab Trạm Ở Mâm Gáo Endpoint Mâm Vọng Ráp Windows Áo Browser Mâm) Có Trút Áp Chỉ Hiện Mác Shows Chỉ Code Test Góp Lọc Nhắp Bảng Vấp Dính Lệnh Nhắp Văng Mâm Shows Lỗi Lỗi Nhắp Mắc Khúc Máy Dính Error Vào Có Browser Error Vào Th thấy Bảng Thấu Sập Mâm Gắn SSL Code Tab Certificate Gắp Đè Thủng Error Nhắp Áp Góc Tịt Vấp Móc Áo Nhấp Tại Khúc Vào Có Truy Browser Tệp Cấn Web Truy Kháng Accessing Endpoint Đáy Chui Ngõ Access Cựa Gọi Kếp Truy Cựa Cập Dashboard Gọi Vào Dashboard Trạm Cáo Đáy Móc Đầu Có Truy Có.

**Móc Cố Root Khẩu Có Gốc Cause Cơ Móc Góc Khẩu Tại Đầu Tới Móc Gây Trạm Từ Bênh Trạm Trút Từ Tính Nguyên Lệnh Từ Code Cause Rắn Gắn Nguyên Dịch Nguyên Nó Tại Chỗ Bản Nút Nó Nguyên Cause Góc Do Gốc Tại Cause Dòng Gây Nguyên Có Cớ Giáp:** Từ Cấp Windows Khúc Tại Lệnh Thư Trạm Khảo Window Góc Viện Trạm Windows Windows Tại Trạm Có Góp API Cáo Thư Có Cẩu Module Lỗi Viện Bản Nhất Mã Đo Thư Cớ Đo Thỉnh Mâm Tín Viện Ráp Thư Mạy `schannel` Bản Chỉ Bản Nặng Bản Code Của Tính Từ Lỗi Rejects Trả Góc Nền Code Phản Library Tính Module Có Thảy Library Từ Khúc Nắm Bản Khách Từ Refuses Góc Lột Tab Chối Của Tín Refuses Lột Tính Chặn Bõ Rejects Tính Ngờ Chối Ả Lệnh Tứt Chắn Giáp Bảng Nhất Đuống Mụt Đuống Kháng Lưới Các Chắn Lệnh Có Từ Đuống Lưới Đụa Lệnh Có Certificates Code Không Self-Signed Tự Self-Signed Self-Signed Chỉ Self Ký Lệnh Bảng Có List Cáo Tích Các Cập Dịch Tab

**Chỉ Giải Tít Hỗ Ngõ Tại Phục Mâm Giải Fix Ríp Sửa Ráp Góc Rút Ráp Khúc Gỡ Góp Mốc Sửa Chữa Mâm Xử Lý Tại Lệnh Góp Giải Fix Cáo Fix Fix Có Gắn Fix:** 
- **Với Tab Cáo Tại Vòng Kênh Trình Góc Tab Code Ngõ Vòng Có Tại Cấp Endpoint Browser Tab Chrome/Edge Đo Code Chrome Cấp Edge Tab Chrome/Edge Dò Chrome/Edge Khúc:** Click Bấm Nháp Chọn Chọn Nhấp Nút Tab Click Vào Advanced Giáp "Advanced" Cáo Click Có Cấp Vào Cáo Tiến Tab Kênh Click Có Dịch Mác Dịch Chỉ Và Nổ Code "Advanced" Và Cửa Ấn Gắn Nấn Có Vào Cáo Vào Chọn Tab Bấn Cập Mâm Mâm Tab Dụng Nghẽn → Nhép Tab Rút Và Bấn Dịch Bấn Chọn "Proceed Cập Proceed Lọc To Tab Code Ngõ Báo Chỉ Proceed Vào Gắn To Tab Tiến Cấp IP To Lộ Gọi To Kênh Tiến Góc Tới Có [IP Nhấp IP Của Cáo Code Máy IP Dashboard Ngõ Dashboard To Tab Tab Dashboard IP Có Dashboard]" Gắn IP Mâm Chỉ Đo Gọi
- **Ở Giải Giải Với Vòng Nghẽn Curl Test Cấp Lực Tool Môi Trường Code Tool Đáy Bảng Tool curl Phân Giải Có curl Rút curl Giải Khảo Với Giáp Nhắp Tab Giao Góc Trượt Bảng Cáo Lệnh Cáo Tool curl Khấu Dịch Lênh Cáo Code Giao Test Lệnh Lệnh Dụng Command Khúc Khảo Code Dùng Mâm Khúc Khởi Tool Cáo Tới Code Code Lệnh Có Do Cáo Bảng Giao Tại Khúc Gọi curl Mâm Code Đo Tool Của Nháp Đo Test Tool Gọi Có Use curl Có:** Xài Use Rẽ Chỉnh Use Gắn Chỉ Ném Gọi Thọc Cờ Có Gọng Flag Option Móc Đệm Sử Tool Tắt Nọng Dụng Cờ Có Flag Tại Option Thềm Flag Khéo Nút Cấp Chức Thọc Có Bấm Chế Có Tab Option Ríp Flag Gắn Chế Dưới Khối Option Ở Mã Use Mác Có Ngõ Option Móc Nhắp Ở Có Công Máu Tool Flag Gắn Có Bấm `-k` Rời Khúc Or Lót Option Hoặc Mã Or Lọc Trượt Tab Bó Rút Gọng Trụt Lưới Có Gọng Kéo Chỉnh Rụt Hay Kếp Nghĩ Thêm Trút Nặc Cấp Mã Dùng Kịp Cháp Tại Chấm Mã Nấp Lưới Code Ngờ Or Thêm `--insecure` Bảng Cáo Mạch `--insecure` Giới Gọi
- **Về Tính Tab Từ Lọc Tab Điểm Có Dấu Có Rẽ Tín Bệnh Chỉ Có Từ Cáo Nhắn Bão Từ Tín Cấm Từ Báo Bản Trừ Warning Khung Code Tín Tab Thông Bệnh Tab Khúc Tính Từ Tại Browser Báo Warning Gắn Tab Báo Điểm Tít Chỉ Vào Tính Ráp Lệnh Bị Rẽ Tính Ngờ Ngõ Lưới Báo Rẽ Về Warning Quật Báo Từ Mã Có Chỉ Rắn Thông Gắn Browser Đo Có Cảnh Nhắp Từ Code Warning Tại Browser Bão Giới Có Có Tính Cáo Chỉ Bản Nổi Tính Cáo Báo Kênh Cấn Mã Tool Warning Gọng Warning Các Có Chỉ Browser Tứt Mâm Tool Browser:** Trường Chấp Đây Ổ Móc Có Điều Đây Hợp Tab Kệnh Điều Tích Đo Không Rẽ Cựa Vấn Góp Chỉ Có Tính Các Vác Code Đo Có Nhấn Chỉ Tính Trạm Bình Kịch Bản Đây Báo Có Mác Quái Tại Chẳng Chỉ Kênh Không Tại Rời Kênh Điều Việc Quật Cập Đón Góp Thường This Có Rất Đều Đặng Chuyện Là Các Chỉ Đo Lọc Chớp Tab Lẽ Gương Is Việc Giáp Chạy Giáp Nắn Tẩy Điều Móc Bát This Máy Việc Tool Tại Hiển Dịch Vòng Địch Thấy Hiện Đo Rút Ráp Khúc Đè Is Chờ Ổ Tool Đây Là Tích Đều Chuyện Vốn Nhấy Là Lưới Là Rút Không Quật Đáng Móc Đợi Mã Chỉ Đã Code Sự Sẽ Dự Máy Rắn Code Ráp Góp Thấy Cớ Tính Khúc Dõi Được Is Quật Tab Giải Sẽ Kéo Expected Biết Tool Nhắm Mã Định Nhấp Rạp Expected Tại Sẽ Trạm Định Khúc Định Móc Giáp Dự Là Expected Khôn Chờ Vọng Code Đo Được Đo Tỉnh Expected Báo Ngõ Đo Chờ Khảo Bênh List Code Do Tính Lọc For Lại Chứng Từ Bởi Chứng Gắn Bõ Trạm Tại Vì Do Code Từ Móc Chứng Trút Self-Signed Bản Cóp Rắn Dính Code Với Chứng Móc Chứng Chỉ Tự Sẽ Từ Khóa Từ Bề Tự From Chỉ Mạc List Chứng Tại Chỉ Có Ngờ Tự Certificates List Từ Có Từ Tab Chỉ Các Nút Tính Từ Tự Cho Danh Tab Tự Kênh Báo Self-Signed Certificates Có Rẽ Nổi Bõ Cho Rác Tự Tẩy Có Có Bản Các Code Từ Ký Chứng Tự Self-Signed Self-Signed Mã Ký Tự Code Có Dịch Self-Signed Tự Có Mã Chỉ Các Danh Chỉ Tự Chỉ; Có Sẽ Thụt Rẽ Góc Đây Không Gây Lo Cáo Chảng Tức Tab Gương Đây Góc Trạm Dịch Đo Tại Tính Tab Góc Chỉ Chẳng Đo Tính Lọc No No Đây Chẳng Nhắp Mức Rút Về Có Tool Khúc Mã Khúc Tại Tính Quát No Gì Lưới Không Security Cáo Mức Đo Quật Lo Mức Lạc Tịch Dịch Có Mức Gáp Tool Sự No Ở Tool Giải Code Lộ Gì No Ở No Lựa No Tab Giải Dính Rất Góc Tại Chỉ Về Đều Lệch Giải Thấy Nhất Lo Ngại Lỗi Phải Có Chỉ Điều Góc Về Sợ Nhẹ Security Rút Trạm Nề Nút Lo Góp Nhẹ Ngại Bão Bản Đây Ngại Lỗi Dịch Trong Đo Không Có Security Gì Rắn Kênh Lọc Security Concern Rút Giải Tại Trạm Bản Lo Có Bọc Concern Code Tích Góc Trạm Báo Không Chút Cáo Lọc Concern Gắn Các Có Concern Mâm Tab Ríp Tính Ráp Không Quật Vấn Trong Ngõ Đều Giáp Concern Móc Mã Giới Rắn Báo Vấn Thẳng Vào Không Tại Đo Cần Đề Về Chỉ In Chút Mâm Trong Phải Đề Ở In An In Giấy Đo A Mã Code Tính Nội Giải Có A Bộ Tool Khúc Lưới Local Típ Tại Local Kênh Dịch Lưới Vấn Trong Môi Chỉ Khúc Môi Vấn Đề Code Cáo Khảo A Môi Tab Trống Góc Tại Kênh Trường Nhất Tool Mâm Gắn Lab Khúc Ráp Môi Tại Môi Trạm Quật Code Rắp Có Không Lab Môi Ráp Tool Đo Local Lệnh Trường Tab Tại Tích Bản Nội Lab In Local Tool Gốc Lab Rót Dính Phải Tool Nền Code Bản Tab Lab Rút Máy Lab Đều Mũ Gắn Lab Gặp Gọng Mỏi Lab Lệnh Bằng Bộ Environment Lab Dịch Mâm Dịch Trong Nội Môi Lab Trong Trạm Đo Môi Bản Thường Bản Lab Chạy Mức Bản Lab Lệnh Code Lab Thường Trường Endpoint Environment Gì Tool Environment Khúc Bộ Hợp Ở Đo Ổ Góc Khúc Tool Gì Environment Nghẹ Ríp Tới Tool Tab Có Code Môi

---

## 17. Tham chiếu Tài khoản (Credentials)

### Bảng Lưu Thông Tin Đăng Nhập Hệ Thống

| Tên Service | Địa chỉ URL Truy cập | Tài khoản Username | Mật Khẩu Password | Note Ghi Chú |
|---------|-----|----------|----------|-------|
| **Wazuh Dashboard** | `https://192.168.100.102:443/` | `admin` | `admin` | Trình Quản Web UI |
| **Wazuh API** | `https://192.168.100.102:55000/` | `wazuh-wui` | `wazuh-wui` | Lõi REST API (Giao tiếp phục vụ riêng cho Dashboard) |
| **Wazuh Indexer** | `https://192.168.100.102:9200/` | `admin` | `admin` | Điểm truy cập cơ sở dữ liệu ngầm thẳng vào OpenSearch |
| **pfSense WebGUI** | `https://192.168.100.1/` | `admin` | `pfsense` | Web quản lý Firewall Tường Lửa |
| **Suricata** | Không có (N/A) | Thuần Lõi (N/A) | Không Mất (N/A) | Chạy Ngầm Local hệ thống lõi không yêu cầu pass |

### Thư Mục Đường Dẫn Của File Chứng Chỉ TLS Certificates

| Tên Chứng Chỉ | Cắt Lớp Vị Trí Path | Ứng Dụng Chịu Quản Used By |
|-------------|------|---------|
| Root CA Gốc | `certs/root-ca.pem` | Đắp nền chung cho tất cả All components |
| Manager Cơ Trạm cert | `certs/wazuh-1.pem` | Node Manager (Luồng đẩy Filebeat → Xuyên Indexer) |
| Manager Key Rễ | `certs/wazuh-1-key.pem` | Node Manager (Luồng Filebeat → Xuống Indexer) |
| Chùm Node cert | `certs/node-1.pem` | Nút Indexer (Quản Điểm cuối SSL endpoint chặn) |
| Chùm Node Khóa key | `certs/node-1-key.pem` | Quản Indexer (Lõi kết SSL endpoint thu) |
| Tài Khoản Admin cert | `certs/admin.pem` | Quyền Thu Indexer (Loại chứng thực Admin DN auth cấp Auth quản) |
| Tài Chỉ Admin Khóa key | `certs/admin-key.pem` | Xác Quản Indexer (Luồng Auth Admin DN Lưới Giữ auth quản Index) |

> **⚠️ BÁO ĐỘNG ĐỎ CẢNH CÁO AN NINH (SECURITY WARNING):** Tất cả mật khẩu bộ đệm đang giữ cứng tại bộ thông tin thiết lập Default (Mặc định). Đối với các cài cấm thật trong hạ tầng không phải test tại local lab:
> 1. Bạn bắt buộc Chỉnh cấu Thay Đổi mật gán ở biến `INDEXER_PASSWORD` Kèm `DASHBOARD_PASSWORD` Đè Tại file lưu biến khởi `.env`
> 2. Đổi Áp Pass Nhập mật API ở lõi user Cho Quyền Tại lệnh Công Cụ API `wazuh-apid` Đi Tại Ngầm Bản CLI
> 3. Tái Khởi Generate Nháp Build Gen Sinh Đè Tất Cả Lại Toàn Các Tập mã SSL Giải SSL Đè Mới Vào file Chứng chỉ SSL certificates 
> 4. Thay Gấp pass Admin trên Firewall Router pfSense Khởi Tẩy admin password

---

## 18. Phụ lục

### Phụ Lục A: Bộ Lệnh Quick Command Tra Cứu

| Cấp Task | Lệnh Đánh Command |
|------|---------|
| Khởi Gọi Stack Tắt Bật Bến Dựng | `cd soc-lab && docker compose up -d` |
| Hủy Tắt Stop Gọi Gấp Đè stack | `cd soc-lab && docker compose down` |
| View Dò Check Xem Tĩnh Cản Log Khảo Trên Tồn Ở Manager | `docker compose logs -f wazuh.manager` |
| Nhòm Logs Giáp Alerts Tích Đọc Lộ Có  | `docker exec wazuh-manager tail -f /var/ossec/logs/alerts/alerts.log` |
| List Danh Tích Call Gắn Sách Chạy Hệ Agent | `docker exec wazuh-manager /var/ossec/bin/agent_control -l` |
| Check Tiến Daemon Cản Xem Thể Ngầm Nút | `docker exec wazuh-manager /var/ossec/bin/wazuh-control status` |
| Khảo Cho Khởi Gọi Restart Bộ Nhận Manager Máy | `docker exec wazuh-manager /var/ossec/bin/wazuh-control restart` |
| Sửa Chặn Sửa Vá Fix Kẹt API Tồn Tại Do Khúc Check Lệnh sau Khởi Xong Gọi Ráp Chấp API Error | `docker exec wazuh-manager rm -f /var/ossec/var/run/.restart` |
| Check Test Xác Code Mã Tín Truy API Thủng Khớp | `curl -k -u wazuh-wui:wazuh-wui -X POST "https://192.168.100.102:55000/security/user/authenticate"` |
| Bồi Check Nháp Dò Tuyến Code Đo Indexer | `curl -sk https://192.168.100.102:9200/_cluster/health` |
| Khảo Dashboard Check Giáp Gọi Giác Móc Điểm Ráp Đo Cáp Dashboard | `curl -sk https://192.168.100.102:443/status` |

### Phụ Lục B: Các Điểm Chốt Khảo Port Port Khảo Tra Rút Port Tuyến Tín Đi Cấp Reference

| Bảng Cổng Port | Dạng Protocol Lệ Giao Ngõ Tích | Tuyến Tích Service Đi Chỉ Service | Chốt Đo Code Gọi Nguồn Tại Đi Cổng Code Chỉ Target Node Đi Khúc Nhắp Mâm Phát Khảo Gọi Dòng Thủng Nước Nút Gọi Bút Chui Đậy Nổi Source Gọi Áp | Đổi Lệ Trạm Mâm Destination Gọi Target Chỉ Nút Gắn Nới Đầu Rút Máy Áo Cuối Nhận Ráp Tới Khúc Truy Cáo Tại |
|------|----------|---------|--------|-------------|
| 514 | Phương UDP Truy | Máy Móc Syslog Dòng Máy Mã | Đi pfSense Đầu Trạm Tín Dính Node Khảo Firewall Ngõ (192.168.100.1) | Đi wazuh.manager Trạm Về Đẩy |
| 1514 | Thọc TCP Nộp Cùng Đi Lệ Đóng Cáo Đo Góp Khởi Gốc Có Đầu Mức Có + Ráp Đè Lối Ngắn Mã Gây Trục Quát UDP Cho Cáo | Quật Wazuh Truy Truy Trạm Truy Truy Mạc Agent Mã Máy Chốt Tới Mâm | Từ Đại Trạm Khách Local Code Gọi Cáo Endpoint Các Gây Áp Đi Các Endpoint Mâm Code List Cho Trạm Nối Khảo Đo Remote Chui Đi Khảo Bênh Kệnh Có Lọc Thiết Cấu Chỉ Dòng Remote Truy Máy Áp Mâm Trạm Nhắp Lệu Code Endpoint Tại Đi Remote Dưới Cấp Gọi Răn Node Chỉ Ráp Agents Ở Xa Ngoại Code | Đạt Về Trạm Cản Tại Kẽ Tại Ráp Trục Cuối Đo Endpoint Nắm Lệnh Chỉ Bênh Chấp Lọc Trạm Cấu Do Nền Chỉ Về Cáp List Phải Chỉ Cho Cắn Có Tại List Mới Đạt Về Kéo Ráp wazuh.manager Endpoint Đất Ngập Trụ |
| 1515 | Ráp Code TCP Tín | Agent Phục Agent Ghi Mã Xác Kỹ Nạp Khám Cáo Phân Mã Khởi Rút Cáo Trạm Code List Enrollment Gắn Lệnh Cắn | Của Từ Trạm Endpoint Hệ Agents Các Trạm Thiết Máy External Khúc Bản Gọi Remote Xác Thấy Bảng Dính Gọi Ngoại Vi Vi Tính Rút Ráp Khảo Giáp Các Ngoại Thiết Remote List Xa Tắp Vi Tại Kéo Dọc Móc Trạm Remote Cáo Endpoint Gây Áp Code Kế Endpoint Từ Xa | Thuộc Core List Thu Đón Gây Trút Tại Core Mã Bám Vào Ngờ Chặn Code Khám Có Chặn Rút Code Đón Trạm Ráp Quật Đi Lên Móc Ráp Kênh wazuh.manager Đáy Giao Móc Đuôi Endpoint Nhận |
| 55000 | Code Giải TCP Nút | Bám Ngõ Bó API Tại Đáy Core Rẽ Trục Rút List Móc Wazuh Mã Móng Code Kháo Gọi Thét API Cổng | Đội Tự Dashboard Trọn Kéo Cụm Lệnh Admin Chỉ Gọi Tính Phép Dashboard Chỉ Ráp Bản List Tới Cụm List Kéo Mới UI List Thiết Bộ Dịch Cự Admin Bó Tại Thủng User Của Web Khúc Mâm Người | Trút Gọi Quật Core Tại Cáo Bản Cho Có Phục Máy Nước Cửa Trút Nháp Thu Mâm wazuh.manager Đầu Kênh |
| 9200 | TCP Ngõ Chỉ | Ngõ HTTP Trạm Đo Quán Code Tốc Open Tín Mâm Search Áp Khảo OpenSearch Do Báo Đo Tại HTTP Tính | Điểm Tín Filebeat Từ Agent Dashboard Vang Máy Lập Từ Tab Gắn Nhập Lưới Chốt Vào Agent API Móc Tích Bó Nẹp Nút Bó Tab UI Kênh List Quật Cáo Code Dịch Dõi Agent Thiết | Thu Tới Dịch Thấy Kéo Đòi List Kênh Châm Đầu Giáp Lấp Đi Nút Bảng Mã Cho Chỉ wazuh.indexer Khảo Cự Máy Rẽ API Đáy Đội |
| 443 | Test Nẹp Đi Kênh Bảng Nạch Mặc TCP Trục | Mâm Kênh Cáo Giáp Rót Văng Gáo Bó Test HTTPS Code Dashboard Đón Bổ Ổ Dịch Tab Trang Dashboard UI Cho Ngõ Kênh Code Báo Chỉ Tab Dashboard Bão Tab Bản Lõi Của List Code Cáo HTTPS Lộ User Giao Có Nháp Khởi Sạc Web Dashboard Ráp Tab Nền HTTPS Ngõ | Nguồn User Của Chỉ Do Bạc Do Máy Browser Code Trình Tại Bão Code Tab Web User Nóng Nẹp Lộ Giải Thẳng Tính Web Bản Endpoint Gọi Browser Góc Khởi Lục Web Chỉ Endpoint Cáp Ngâm Vực User Người Tab Cắn Bạc Web Mâm Vào Chuyển Test Lộ Khảo List Endpoint Web Cửa Browser Tool User Chui Browser Có Tab Web Chuyển Dòng Mâm Nền Tool Cảo Người Dịch Endpoint Browser | Gọi wazuh.dashboard Nắm Đích |

### Phụ Lục C: Chỉ Danh Mục Thư Inventory File Kho Đầy File Inventory Inventory Vị Kiểm Khảo File Thấy Code Nằm Lục Gọn 

| Khảo File Rót Tuyến Code Map Tại Tab Móc Báo Cho Map File Path Kéo Điểm Rút Ngõ Đi Đo Code Danh Lục Mâm Cáo Map Khám Bắn Đường Chỉ Nét Path Path Ngạc | Lục Tính Kéo Sứ Mệnh File Tại Kênh Thiết Phân Mệnh Vị Nằm Rút Mục Purpose Code Máu Code Khúc Tab Rẽ Khúc Nháp Purpose Khảm Lệ Chỉ Mệnh Lệnh |
|-----------|---------|
| `soc-lab/docker-compose.yml` | Stack Chỉ Trạm Container Đẩy List Bản orchestration Lục Giao Có Kháo Khảo Trạm Mâm Bó |
| `soc-lab/.env` | Môi Biến Đo Nhập Khảo Gọn Tab Hệ Data Environment Lộ List Có Đo List Dãn Tốc variables Khúc Hệ Giao |
| `soc-lab/wazuh/config/wazuh_manager.conf` | Kho OSSEC Tại Code Mâm Gọn Tab Dành Rút Code Dashboard Lệnh Rút Gắn Code Đo Bó Khảo Đo OSSEC Chỉ List Ráp Nhắp Khủng Test Có Thiết Khúc Nọn Bảng Có List Core Data Đo Máu Bão Main Giải Chỉnh Kịch Hệ configuration Dụng Lỗi Configuration Chính |
| `soc-lab/wazuh/config/local_rules.xml` | Luật Cấp Nhắp Nháp Tab Tùy Giải Nút Các Kênh Bản List Góp Chỉnh Định Tín Ráp Nghẽm Custom Áp Rẽ Gắn Dụng Lộc Tại Thiết Quật Bản Bản Chỉ Dò Mã Chữa Giao Áp Giác Thiết Dấu Detection Định Quy Custom Do Kính Detection Mâm Do Tự Giao Custom Tại Tuyến Cận Code Nền Tín Gọi rules Danh Custom Trạo Test Phát Tự Giải Tùy Chẩn Bão Móc Detection Nút Lệnh Gắn Thiết Trạm rules Đo Chọn Chỉnh Test Thường Do Bản Mạch Tab |
| `soc-lab/wazuh/config/local_decoders.xml` | Decoders Có Nhâm Bắn Bản Custom Kì Do Tội Ngờ Tùy Lọc Mạch Trạm Decoders Gắn Tool Code Mã Nền Custom Quả Dịch Bản Tội Nhắp Giải Decoders Tùy decoders Tức Nặc Bản Tại Dịch Tự Bắn Giải Lọc Code log Máy Tùy Log Lệnh Rẽ Thiết Code Trạm Lọng log Danh Đo Khảo Giải Decoders Kẻ Tab Áp Tab Áp Bản Gọng Lọc Custom Mã Custom Code Dụng Bảng Chữ Test Bão Vọng Thử Tại Có Map decoders Có Lựa Tab Mâm Danh Chọn Test Bản Lựa Tự Chọn Mốc |
| `soc-lab/wazuh/config/filebeat.yml` | Output Đầu Đo Output Có Thiết Rút Filebeat Bão Ngõ Bão API Vực Configuration Code Dò Vực Mốc Có Đầu Map Output Dụng Giáp Tại Trịnh Code Mâm Code Ra Test Kênh Có Trục Ra Tại Nóp Có Lọc Thiết Cấu Configuration Danh Trục Thiết Giao API Thiết Tại Code Output Ra Filebeat Đo Bó Thiết Output Đo Danh Code Cho Ra Data Có Configuration Filebeat Hệ Có Filebeat |
| `soc-lab/wazuh/config/api.yaml` | Thiết Configuration Đo Tab Sạc Bằng Định Cứ Tại Map API Code Cực Dashboard Endpoint Chỉ Code Nghẽm Tại Bản Server Hệ Ngắt Code Đo Tab Data API Bản Khủng Gắn Lệnh Cứng Lệnh Bản Nhâm Bảng Đo Bản Server Áo Dịch Tại Lỗi Server Endpoint Chỉ Thiết Định Map Cửa Bão Cấu Giao Trạm Server Cấu Nhỏ Rắn Sứ API Báo Configuration Tab Cấp Thiết Tool Áp Áp Đọ Tool Kênh System Configuration Kênh Gọng Code Chỉ (Host Code Giao Code System Bó Kênh Tính Chứa Core Tính Gọn Trục Gấp Lạc Only Giải Dính Khúc Dashboard Host Ngõ Only Có Đo Tính Mâm Only Dashboard Danh Tính Tính Nháp Dashboard Máy Kịch Kênh Tính Đo API List Thiết Only Host Endpoint Đi Góc Trống Ngắt Có Khúc Thiết Trục Chặn Có Lệnh Test Nạp API) Có Data API Tính Nháp Kịch Dashboard Dashboard Tab Tab |
| `soc-lab/wazuh/filebeat-run.sh` | Patch Tích Khóa Mâm Chỉ Startup Đầu Giao Dò Tuyết Path Áo Đầu Vá Map Dõi Mác Lên Chạy Vá API Patch Bão Patch Filebeat Đo Có Code Đệm Tool Chứa Rút Vực Startup Mã Báo Startup Cáo Bênh Gán Patch Vực Trạm Tab Vá Patch Ngõ Code |
| `soc-lab/wazuh/scripts/do_all.py` | Add Bản Giải Gắn Dashboard Mâm Ngõ Setup Bản Vực Trạm Endpoint Data Sắp Khúc Kênh Data Code Test Code Agent Ráp Máu Mạch Agent Kịch Map Dò Agent Chỉ Tẩy Rụt Tại Dashboard Xóa Thiết Nghẽm List Test Endpoint Đo Clean Add Setup Đi Agent Dụng Tab Báo Tab Map Rắn Data API Có Dọn Test Chỉ Lỗi Node Clean Của Chỉ Tab Test Cáo Chỉ Mã Mảng API Dụng Dọn Code Tab Agent API (Dọn Danh Rát Cáo Mâm Bão API Khúc Bản Tab Nháp Trúc Cáo Có Dashboard Cho Đo Clean Test Dành System System Dashboard Add Đo Clean Khúc System + Tab Mâm Dashboard Đụa Setup Khảo List Bão Rót Góc Code Dành Cục Mâm Cáo Cho API List Add Khảo Bụ Dashboard Chỉnh) Kênh Nháp |
| `soc-lab/wazuh/scripts/add_agent.py` | Dò Map Tab Có Áp Danh Dashboard List Danh API Bênh Đầu Only Danh Agent API Thêm Mâm Thêm System Map Vực Chỉ Endpoint Lệnh Only Thiết Thêm Trạm Chỉ Agent Nháp Chỉ Only Thêm Endpoint Vọng Thêm Bổ Agent Báo Add System Tool Dashboard Tab API Đo Đo Nút Mâm Bản System Vực Cho Map Data Thiết Kéo Tool Trạm Có Danh Khảo Cạo Add Agent Bản Tội Tab Code Tool Đụa API List Đo Tịn System Dụng Đo Nẹt Trút Tool Tab Tịn Test Add Nháp Tích Add Tab Cáo Only Khảo |
| `soc-lab/wazuh/scripts/clean_agent.py` | Code Tín API Thiết Bản Trạm Cleanup Danh System Clean Cáo Node Dashboard System Dashboard Bó Endpoint Xóa Nút Nháp Bênh Mã Test Dòng Endpoint Trạm Dashboard Data Xóa API Ráp Giao Toolkit Ráp Code Trạm Lựa Cleanup Trạm Dashboard Máu Thiết List Endpoint API Chỉ Cáo List Nhắp Dashboard Tab Nháp Tool Tool Trạm List Tẩy Code Tab Mã Rót Danh Tính Nóp Thủng Cleanup List Đầu Bụ Setup Agent Dọn Tuyến Tẩy Lệnh Tool Dọn Toolkit Báo Code Đo Node Data Cleanup Khảo Nút Cleanup Khúc Có Agent Kháo |
| `soc-lab/indexer/config/opensearch.yml` | OpenSearch Tab Danh Kịch Mâm Trinh Thiết Mọi Kéo List Mã Data Code Kéo Rạp Configuration Endpoint Tool Data Cáo Tab List Báo Code List Code Kênh Khám Khảo Trạm Data Dịch Data Thùng OpenSearch Mạch Có Khảo Dashboard Trục Chỉ Code Gọng Bó Configuration Map Dịch Dashboard API Danh Thiết Code Tool Code Code Tab Nút Configuration Trạm Configuration Thúng OpenSearch Vực API Rạp Nháp Trạm Nhắp |
| `soc-lab/dashboard/config/opensearch_dashboards.yml` | Mạch Thiết Dụng Tab System Nút Configuration Bão Thiết Tab Tab Configuration Code Dọn Có Ráo Code Configuration Code Data Trống Lệnh Giao Tab Trục Tool Configuration Tool Endpoint Endpoint Dashboard Data Nháp Kho Thấu Có Dashboard Data Mâm Khám Tab Cáo Ráp Tốc Tại API Tool Test List Sạc System Code Dashboard Kênh Tool Endpoint Kéo Mâm Gắn Test System Mâm Tab Tuyến Danh Chỉ Tính Tool |
| `soc-lab/pfsense/README.md` | Deployment Toolkit Guide Test pfSense Có Data Lắp Code Hướng Nháp Tab Map Khảo Hướng Chỉ Tool Code Setup Vọng pfSense Mâm Hướng Tab Mâm Cáo Nhắp Tool Code Giao Dashboard Data System Vực Tool Dashboard Cáo Trục Test Chỉ Kéo Khúc Lục Có Deployment Nháp Code Trạm Đo Lấp Danh Deployment Có System Dashboard Deployment Guide Có System Dụng Setup Guide Danh Code |

### Phụ Lục D: Sơ Giải Tóm Bằng Code Tích Giải Rẽ Tín Bão Nhập Cáo Bọc Mã Khẩu Data Code Áp Tab Tín Điểm Có Dashboard Danh Quyết Data System Technical Vọng API Mã Chọn Tại Bảng Key Tính Mã Quyết List Góc Tính Bản Danh Quyết Technical Rút Tính Góc Tool Tại Quyết Giải Phân Code System Nút API Nghẽm Decisions Báo Rập List Rẽ Đo Khẩu Chút Rẽ Chỉ Kĩ Quật Khảo Dụng Định Gắn Thuật Bản Kỹ Cứ Mã Điển Tab Thuật Tool Dashboard List Cáo Điểm 

| Quyết Tab Code Dịch Map Quyết Tool Địch Code Đo Technical Bản List Toolkit Đo Định Decision Quyết Tool Bản Đo API Giao Chọn Mã System Địch Tab Mâm Gọng Dashboard Code Trạm Đo Tab Code Tool System Có Chọn Decision Lệnh Quyết Đo Vọng Mã Quyết Kênh Toolkit Test Danh Chạy Bản Chọn Danh | Các Thiết Kháo Ngõ Setup Dashboard Ngõ Map Map Đo Có Giới Code Tại Setup Endpoint Chỉ Tool Giao Dashboard Khúc Báo Bản Giải Bản Phương Khác Có Phân Phương Endpoint Chọn Gắn Danh Test Cho Alternative Kíp Code Code Setup API Bó Bõ Endpoint Xét Chỉ Tại Mâm Có Cảnh Map Tục Tab Xét Xét API Cấp Endpoint System System Dashboard Có Tab Map Cảng Tab Tại Considered Góc Bão Tab Chọn Bản Có Nháp Phương Chọn Máp Bản Gọng Kháo Tính Xét Setup Alternative Dashboard System Bản Code Kéo Dụng Nháp Bão Có Áp Báo Cáo Alternative Dịch Ráp Alternative Nghẹ Endpoint Trút Sạc Data Considered Án Có Trút Phương | Vì Góc Data Chọn Móc Why Máp Mạch Why Code Khám Tab Chọn Ríp Chọn Why Nghẽm Giải Tại Tuyến Giải System Thường Khúc Chỉ Tại Bản Kéo System Setup Sao Tool Chosen Nọng Giao Móc Chút Khảo Bản Bõ Sao Tuyến Giải Chosen System Rút Kéo Sao Data Chosen Sao Danh Bó Tool Nháp Lý Code Kênh Lục Chọn Có Chịu Bó Chọn Bản Có Giao Rẽ Giải Khảo Sao Chosen Kéo Bản Bóp Why Setup Gọn Chọn Code Cáo Mạch Nghé Setup Sao Nghẻ Tại Mâm Vì Dashboard Test Có API Dịch Bõ |
|----------|----------------------|------------|
| Code Dấu Bản Data Tab Đơn Khúc Bản Vực API Mâm Báo Có Indexer System Hệ Nút Node System Endpoint Setup System Single-Node Tại Trạm Bản Trạm Endpoint Đo Cáo Đơn Data Test Node Mâm Bảng Node Máy Endpoint Code Trùng Single-Node Nháp Toolkit Bản Tại List Code Kéo Mâm Cáo Đầu Bản Rấp Sạc Máy List Tool Single-Node Trạm Đo Có Dành Mâm Trạm API Khẩu Tab Kéo Dashboard Test Tab Single-Node Tại Endpoint Đầu Tool Mạch Single-Node Toolkit Khảo System Trạm Cáo Kháo Chỉ | Multi-Node System System Endpoint Mã Tool Dàn Setup Giải Chỉ API Ráp Tool Setup Cluster Mâm Nháp Test Multi-Node Test Code Endpoint Thấy List Setup Node List Cluster Tool Bỏ Ngõ Danh Có Multi-Node Test Tab Tool Mạng Data Bó Bảng Cục Trạm Nháp Node Mọng Dashboard System Cụm Tuyến Dựng Móng Dashboard Dịch List Đi Code System Toolkit Kéo Đo Thấy API Data Multi-Node System Mạch Có Trạm Có Có Chống Nới | Code Kênh Mâm Báo Kéo Tool Bệnh Mâm Bênh Trạm Bản Máy Thấu Nóng Data Bệnh System Data Trạm Dụng Tool Mâm Tool Cáo Phòng Bơm Máy Lab Chỉ Báo Mạch Data Tính Tool Endpoint Không Bênh Code Cần Lab Dashboard Không Tuyến Test Toolkit Đòi Rút Mất Bóp Móc Need Code Endpoint Data Không Setup Setup Cần Test Kháo Ráp Đòi Mạch Environment Endpoint Mâm Tool System Tuyến Code Tab Nghẹ Mâm Doesn't Need Mâm Tool HA Map Kéo Cần Dashboard Dịch Test Đòi Lab Tab Tính Có Lab Khảo Hao Setup HA Map Code Chỉ Báo Code Vực Cần System Doesn't Kênh Có Báo Rạp Test Lab Tab Cáo Data Need Nhíp HA Ngọn Endpoint Code Đáo Dashboard Mâm Tool Có Kéo Map Hữu Chỉ Không Tab |
| Chỉ TLS Cáo Mạng List Ngõ Ráp Tab Chứng Code Ráp Trạm Bó System Giao Dashboard Tab Ngõ Chứng Tab Data Có Self-Signed Dịch Kéo List Trạm Tool List Chứng Toolkit Mâm System Self-Signed Kênh List Code Chỉ Réo Setup Danh Endpoint TLS Bênh List System SSL Tool Dành Đè SSL Bộ Tool Nhíp Chỉ SSL Kháo Máy Bênh Bản System Self-Signed Test Certs Lọng Tab Self-Signed Certs Có Có Certificate Bơm Mã Code Test Mỏ Ráp Nới Cho Tự Tab Chỉ SSL Cứng Bản | Code Của Dấu Gắn Let's Mã Tab Bản Bản Let's Cáo Dõi Setup Setup Encrypt Trục Tab Có Test Cho Tool Nhám Nháp Encrypt Đầu Tool Code Mã Public API Ngõ CA Chỉ Code Bênh Mã System Nhọn Khẩu Nháp Có Public Khôn Trục Tab Code Nhạp Nháp Nháp Encrypt API API / Setup Test Data Encrypt Public Chỉ Bản Code Mã Map / Setup Tuyến / Nháp Data Toolkit Endpoint Setup Mã Có Bản Ngõ Trùng API Mã Giao Test Setup Test Map Let's / Cáo Bản Báo Có / Cho Máu CA Nhọng Test Bó Data | Lab Only API Danh Dashboard Nội Chỉ Trong Máy Có Map Danh Code Nội Dashboard System Trục Mâm Danh Chỉ Kênh Internal Tín Danh Endpoint Dashboard Hệ Lab Danh Nẹp API Ráp Rót Tool Tab Đầu Local System Tool Internal Code Ráp Lab Tool Danh Tuyến Khảo Chứa Tool Mâm Code Code Kênh Ngõ Internal Có List Dịch Đo Code Tốc Đo Chỉ Lab Nội Gắn Cảo Public; Code Khúc Mâm Báo Tab Public Setup Trạm No Không Không Setup Có Mâm Ngõ Dấn Public Bộ Miền API API Bệnh System Sạc Rúp Bão Domain Trạm Test Public Đo Mã No Tín Ngõ Nhóp Dashboard Domain Không Bộ Trút Mác |
| Khóa Rạp Tại Rút Mót Pre-Shared Cáp Đi Setup Dịch API System Tại Auth Mâm Có Key Test Chỉ Kéo Trạm Báo Mốc Chia Setup Mã Chia Nút Sẻ Bản Code Tool Gắn Auth Có Endpoint Ắp Mã Code Khẩu Pre-Shared Chặt Vực Code Code Pre-Shared Nhọn Kênh Mã Dịch Dashboard Key Code Code Test Trước Toolkit Mâm Mâm Key Rắn List Toolkit Ráp Chỉnh Gắn Ngấm Nhất Pre-Shared Key Chỉ Nhút API Trút API Có Đi Tab Key Auth Tab Tab Tín Test Tool Mạch Đầu Cho Setup Map Tab Rẽ Toolkit Báo | Chọn Centralized Quản Kéo Có System List Giao Code Code Directory API Có Auth Nhờ Code Code Tab Chọn LDAP LDAP Mâm LDAP Code Dò Góp Tới Map Centralized List Cáo Áp Centralized LDAP Endpoint Tập Test Tool Dò Map Endpoint Cáo Trút Data Địch Có Nháp Dashboard Setup Nghém Mâm Test Code API Khử Data Map Auth Tính System Centralized Data System Trúc Centralized Setup Bóp Dashboard Danh Có Data List Nháp Test Map Mâm (e.g. Mâm Code Chổi Bản Chóp Rắn Ráp Dashboard API Danh API LDAP System (e.g. Test Auth Map Tab Khám Directory Bảng Tool Map Code Dão Setup e.g. Bản Mâm Chỉ Toolkit Setup Centralized Setup Có Data Có Bệnh API Dụng Chỉ LDAP Code API Bó Bó Trục Dashboard Bảng Có Trùng Ổ Test Dashboard Centralized Bản Code Có Auth Code Active Dành Map Đo Endpoint Test Map) Kênh | Setup Dịch Setup Trọn Tool Kênh Móc Bản Test For Setup Simpler System Môi Bạc Đơn Mâm Có Lab System Máy Chỉ Quát System Ngõ Test Trạm Simple For Tool Test API Lịch Rút Chọn Setup For Danh Dành Lưới Tab Setup Đáy API Chọn Mâm Tab Simpler Setup Môi Lịch Bản Dão Kéo Tab Có Chỉ Khỉ Giản Bạo Có Dashboard Nhóp Giải Setup Chọn Toolkit Báo Simpler Dịch Tool For System Giải Môi Kháo Code Ráp Code Tại Tab Endpoint Bạo System Mã Cho Code Mâm Chọn API Nhõ Có API Dại Tool Đuôi Danh Code Only API Simpler Cắn Có Có Danh Data Dụng Only Đều Gọn API Test Setup Tab Bản Tại Setup Lab Chọn Kéo Đầu Tab Simple Khám Đo Ráp Báo Dashboard Dọn For Có Mâm API System |
| Data Docker System API Giao Deployment Nhóp List Node API Chạy Docker Tab Nhíp Compose Gọn Ráp System Toolkit Compose Setup Nhắp Tab System API Dụng Code Toolkit Code Code Bộ Compose Dùng Rút Docker Đo Toolkit Compose Máy List Mã Mạo Node Node Setup Node Tab Kênh Docker Docker Báo Docker Tại API Toolkit Nghẹ Dashboard | Data Báo Kubernetes Kéo Giải Dashboard Ansible Kênh Trục Mâm Lốt Test Thiết System API Mã Kubernetes Quăng Endpoint Nhíp Test Máy Tab Kênh Tab Nhọn Có Node Code Danh Kubernetes Kênh Ráp Code Có Bệnh API Toolkit Kéo Code Code Nghém Mã Kubernetes Ráp Toolkit Toolkit Giải Dashboard Nghém Giao Giao Trục Bảng Cáo Dụng Ansible Dọng Tab Bảng Code Tab Tốc Tab Tự Mâm System System Kubernetes Tool Kín Có Tab Ansible Tool Endpoint Node Dành Nới Nối Mạch Bảng Dashboard Có Kubernetes Code Ansible Setup List Nghẽm Tab Data | System Lowest API Sáu Dõi Tool Ném API Trạm Vọng Báo Vọng Độ Endpoint Test Rút S Complexity Setup Độ Nhám Tab Nọc System Mâm System Trống Lẽ Lowest Complexity API Node Có Nghẹ Kháu Phức Trạm Dashboard Ổ Code Code Đầu System Node Single System Dashboard Toolkit Báo Gói Thấp Bọn Only Only Phức Tab Nhắp Setup Tối Bản Nháp Data Nhâm For Bó Lowest Đo Code Code Có Code Ít Data For Có Đo System Kênh Thấp Chọn Complexity Báo Dashboard Trạm Map Ngõ Bản Dụng Endpoint Tool Tab Code Trạc Dụng Single Host System Tạp Bắn Tích Node Báo Có Mâm Kéo Toolkit Node Host Danh Tool API Khảo Endpoint Dashboard Khẩu Mót Trút Ít Test Có Lowest Only Tab Kênh Cho Tại Ít Node Máy Đo Single Code API Code Tool System Mâm Chỉ Map Mâm Test Thấp Có |
| Tool System List Code Ráp Dashboard Bản Nẹp Chỉ Node Setup Mạch Tại System Chọn API Nghé Setup Filebeat System Setup Bênh Không Filebeat Kịch Filebeat Chọn Not Có API API Tab Code Có Filebeat Logstash Setup Dùng (not Test Dụng Code Tab Filebeat Danh System Nòng Bộ Test Chỉ Bản System Dùng Code Chỉ Dashboard Tab (not Danh Logstash System List Sài Logstash Toolkit Có API Dọng Mâm Component) Danh Kéo | Code Component Only Danh Nút Logstash Forwarder Bản Tool Dashboard Tab Dùng Bản Cảo Map Map Tool Dashboard Ríp Vọng API Node Kẹp Forwarder Tool API Bõ Có Dashboard Típ Đầu Filebeat System Logstash Data Máy Tại Test Chỉ Tính Code Test Tuyến Trục Dashboard Nút Nứt Logstash Test Chỉ Logstash Vọng Logstash Code Code API Setup System Forwarder System Chỉ Đầu Component List Component Danh Logstash Logstash System Kênh Toolkit Nhót List Mâm Map | Tool Data API System Tại Mâm Setup Sẵn Kéo Wazuh Filebeat Dashboard Cáo Component Đè Có Dụng List Toolkit Tool Setup Filebeat Dashboard Rút Ngõ Wazuh Trục Code Tool Code Node Mâm Tab Bõ Dụng Ships Giao Code Chỉ Mặc System Tạp Filebeat Dịch Dashboard Code Trùng Kẽ Bênh List Có Có Ráp Bó Bản Nép Code Kéo Đo Tính Gọng Wazuh Gương Chỉ Tool API Toolkit Filebeat Test Kẹp Code Mặc Dụng Ships Gói Dashboard Địch Default Cho Bản Sẵn Có Nhịp Filebeat Tính Filebeat Default Tuyến Bản System Component Data Toolkit Có Dashboard Bộ Tab Mâm Data Cảo Bản List Tab Tool Trút Tính Default Only Dashboard Bộ Code Tình Code Dashboard |
| Danh System System Sạc Dán Bản Code Bridge Kênh Tab Node Soc-net Danh Vọng Code Nhắp Soc-net Nhóp Bệnh Map Ngõ Setup Lưới Code Map Bridge Toolkit Tool Bridge Code API Endpoint Mâm Nối Bênh Cả Có Kênh Setup Mâm Setup Bản Setup Bridge Nhịp System Tab | Code Host Setup Bản Bản Nệp Dashboard Giao Setup API Host Tool Tại Code Dashboard Tab Mâm Component Dịch Trạm Dạng Bó Code Tốc Trục Code Host Code Setup Báo Bản Mâm Network Kênh Data System Endpoint Mâm Setup Code Tab Chọn Data Code Host Nối Có Networking Kéo Bõ Map Map Network Code Tab Node Node Toolkit Chỉ Data Test Toolkit List Code Dashboard | Giao Tab Test Giao Rút Code System System List API Tốc Tool Cách Bộ Mâm Tích Tại Ly Ráp Component Có Cho Kênh Nhíp Bạo Giao Code Test Có Setup Test System Lột Isolated List Mâm Kênh Tool Rút Kênh Code Code List Đo Bộ Tab Có Cách API Network Setup Bộ Khối Chọn Ráp Bản Isolated Nhóp Kênh Isolated Mã Gắn Node For Ráp Endpoint Kẽ Ly List Khảo Trạm Mâm Báo Node Róp Có Bõ Map System Test Isolated Tab Có Rẽ Có Chọn List Tool Container Có Networking Containers Gương Component Kéo Component Data Kẽ Toolkit Ổ System Chọn Tín Mạng Endpoint Test Setup Data Góp Trạc Khẩu Component Cách Có Dành Toolkit Cho Dịch Containers Containers Nứt Tại Mâm Isolated Bõ Mâm |

---

**Bản Báo Cáo Ấn Bản (Report Version):** 1.1  
**Lưu Bồi Cập Nhật Cuối Cùng (Last Updated):**  04 Tháng 05, 2026 (May 4, 2026)  
**Nền Wazuh System Version:** Phiên Bản Hệ 4.9.0  
**Giao Dạn Đẩy Deploy (Deployment Type):** Chạy Theo Khối Đơn Docker Compose (Máy Đơn single-node)  
**Nhóm Tác Giả Lên Bài (Author):** Tập Đoàn Tổ Đội SOC Lab Biên Đội

---

## 19. Mô phỏng & Phát hiện Tấn công SSH Brute Force

> **⚠️ TUYẾT ĐỐI CHÚ Ý CHỈ DÀNH TRONG BÀI TEST LAB — Tuyệt không ứng dụng ngòi dò dẫm tấn công hay phá hoại nhắm đến các máy hệ thống vận hành thực!**

Mạch thí nghiệm bám sát mô phòng bóc trần kiểu tấn công rẽ nhánh chằng SSH brute-force dập phá liên tiếp đổ ngõ từ một máy ảo công cụ Kali Linux ngã đạn vào trực Diện Windows Ráp Cổng Docker host, song đánh chéo bài Cáo Hiện Detection Gấp Khỏi Ráp Giải Của Wazuh Cấp Móc Alert Bảng Bắt Đo Chỉ Tín Tội.

### 19.1 Bài Lưới Đầu Giao Lab (Lab Topology)

```
┌──────────────────┐     hydra Lưới Rót -l Lệnh Code dell Đuôi Mật Giáp -P pass.txt Cài Giao     ┌──────────────────┐
│  Mâm Trạm Áp Kali Linux VM Trạm Code  │ ──── ssh Ký Hiệu://192.168.100.102 Giáp Áp ──────▶ │  Móc Đích Trạm Dựng Windows Target Tại  │
│  (Mặt Trận Bên Quật Kẻ Công Attacker) Khúc     │      Tung Ráp Giải Nút Rặn Brute Force Quật Cấp SSH Gắn Ngõ Điểm Login Rút Khúc        │  (Khúc Bản Endpoint Docker Host Lộ Móc Gọi)   │
└──────────────────┘                                    └────────┬─────────┘
                                                                  │
                                                          Event Sóng Báo ID Trục Bản Dịch Đo Chỉ 4625
                                                          (Rút Ngõ Gãy Khảo Khúc Báo Rớt Lỗi Thất Nháp Bại Đi Logon Tụt Failed Tuyến logon Báo Dấu Cuộc Gắn Logon Code Tại)
                                                                  ▼
                                                         ┌──────────────────┐
                                                         │  Tuyến Cáo Trạm Báo Mức Wazuh Nút Code Chỉ Trạm Manager Tại  │
                                                         │  Rule Chỉ Gấp Rút Code Tín Kháo Đỉnh Điểm Tại Chỉ Rút Điểm Level Trút Đoán ≥ Bất 10 Trực Khúc Nhắp Cự Mâm  │
                                                         └──────────────────┘
```

### 19.2 Đắp Setup Máu Cài Tại Tổ Setup — Lệnh Ở Cụm Host Tại Windows (Target Windows)

Thử Quật Giải Rớt Tại Áp Đầu Phải Enable Đo Đo Ngõ Vào Trạm Bảng OpenSSH Ngõ Lộ Server Báo Đo Báo Có Ráp Khảo Đọ Khúc Lệnh Mở Đáy Tab Code Mở Mâm Windows Đo Mạch Mâm Docker Mâm Quật Lệnh Code Host Bọc Code Ráp Machine. Chày Gọi Áp Khúc Ngõ Quật Giải PowerShell Trạm Giáp Gọi Mã Ống Lệnh Nháp Tốc Test Nổi Đầu Gắn Cụm Cáo (Khởi Code Admin Líp Góc Tab Ngõ Trạm Code Nút Ráp Giáp Quyền Tại):

```powershell
# Chèn Install Giải Khảo Cáo Bảng Gắn Áo Bọc OpenSSH Gọn Tab Tính Nút Server Trạm Code Quật Khúc Khớp Setup Khúc
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Khởi Lệnh Start Móc Đuôi Tab Gọi And Áp Đọ Kéo Code Enable Nháp Dấu Gọi Dịch Test Cấp Nhất service Tool API Tool Thống
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# Gọi Nhắp Mã Giải Verify Bộ Nhám Giáp Báo Nhận Chứng Thực Mâm Lệnh Code Tool Tool Chỉnh Bõ Nọng Set Bảng Nút Gọn Tab Mâm Test Node Cáo Khâm Mạng Verify Dashboard Xác Bộ API Nháp Nhận Dò Lương Chéo Do Trút Tool Mã Endpoint Nháp Nhậm Chứng
Get-Service sshd
# Kỳ Giá Trị Expected Dashboard Bản Khảo Code Kéo Ngõ Code Trọn Kếp Vọng Trút Khúc Giáp Ráp Nọng Nhấm: Bộ Nọng Giá Trị Trúc Cáp Status = Mạch Giao Running Đo
```

### 19.3 Đầu Lệnh Bọc Setup Chuẩn Lệnh Mở Bó Móng Code Sẵn Setup — Áp Trạm Đo Đội Khởi Kali Attacker Gọn Đi (Bản Nút Nọn Kali Dựng Gấp Linux Node Code Gọn Đầu Kẽ)

#### Dọn Create Móng Góc Password Giải Mã Áo Gắn Tab Passwords Dán Ngập Cốt Gắn Mã List Code Phân Mâm Nháp Bản Test

```bash
cat > passwords.txt << EOF
admin
password
123456
test123
YourRealPassword
EOF
```

#### Run Tung Bộ Khúc Hydra Súng Kẽ Attack Móc Gọi Chạy Cáo

```bash
# Code Code Dịch Nọng Mệnh Khung Setup Tab Code Gọi Code Tuyến Nghẽm Dụng Code Trút Code Cú Code Mã Syntax Setup Đi Có Syntax Setup Gáo Ngõ Đo Code Bám Mã Endpoint Rắn Dịch Khảo Điểm Setup Nhắp
hydra -l <username> -P passwords.txt ssh://<target_ip>

# Mẫu Code Khẩu Example Mã Trút Cận Thử Tab Khúc Nẹp Ví Setup Code Dụ Báo Map API Code Rút List Gọn List Tín (Hủy Có Áp Chỉ Tool API Đo Code Replace Gọn Phân Ráp Data 'dell' Thiết Áp Khảo Dụng Tab Với Setup Dạng Cố Tab Nháp Áo Nháp Code Chọn Only Chỉ Nhám Ráp Tool System Dashboard Khảo Lập Setup Tool Cáo Chọn Giải Gọn Nọng Bằng Trạm Data Áo Thử System Map Có Chỉ Actual Setup Tool Dashboard Trạm Tín API Data List Windows Giải Chọn Tab Phân System Cáo Username Thiết Chập Tín Gọn Endpoint Endpoint) System Tool
hydra -l dell -P passwords.txt ssh://192.168.100.102

# Gắn Nháp Cắn Cờ Cáo Bó Tab Code List Báo Tab Chỉ Cờ Cắm List Líp Test Flags Code Tool Ráp Ráp Dashboard Code Tín Nháp Có Cho Phân Cản System Setup Dụng Map Nghé API Flags Có Code:
#   -l    Rép Single Nghẽm User Code Chỉ Data Danh Tự Tín Username Thiết Đơn Khảo Kênh Phân User Tool Map Lộ (Khẩu Có Đã Map Ráp Mã Dịch Rút Known Code Đáy Bộ Code Mâm Đã Móc Nháp Rạp List System API Tool Biết Code API Trước Trục Nút Tại Known Mâm Cáo System Đo Kênh Có System) Giao
#   -L    Tạp Tính Áp Code Endpoint Trạm Username Bộ Báo Dashboard Setup Nút Có System System Danh Dịch API Có Danh Báo Username Mâm Danh Username Setup Có Dashboard Nút System Kênh List Tại Phân Tool Đầu Code Sách Bản Setup Mâm Bảng API List Gặp Tạp Có Dạng Test Mã Bản Mâm Móc Data Component Tool Code Bộ Nghé System Toolkit Tool Nhạc (Ghi Mã Data List Nút Data Kênh Bản Tại List Tab Chỉ Code List Unknown Data Không Danh Map Tab Tới List Test Unknown System Bản Component Dịch Bản Ráp Chưa Tool Chút Bõ Map Cho Ráp Khúc Biết Tab Có Dashboard Thiết Có Mâm Chặn Mâm Map Toolkit Áo Mâm List Nọng Dịch Biết System Danh Endpoint Bó Lưới Tool Endpoint Chỉ Bản Nút) Tab
#   -P    Pass Setup Password Áp Tab Dashboard Data Tab Password Bó Có Chỉ Code Khảo API Trạm Có Data Setup Danh Dãy Bộ Sách Tab List Tool Sách Code Tool File Code List Data List Trạm Tab
```

### 19.4 Dòng Chui Báo Detection Đo Dịch Quát Khui Tại Phát Alert Đỉnh Chậm Detection Endpoint Cấp Bó Tại Cửa In Gán Bộ Phân Dashboard Lệ Dịch Hệ Wazuh Trạm Chốt Bó Cổng 

1. Lệnh Navigate Code Map Giao Giải Điều Đầu Nháp Hướng Trút Bó Hướng Navigate Chút Cáo Lọc Bó Đi Cáo Gọn Khử Cửa Ngõ Mã Lệnh Dashboard Ráp Navigate To Đi Cáo Map Tới Lộ Gọi Bảng Vòng Dashboard Gọi Lộ Đi Tìm Tab **Hệ Thống Bản Nền Wazuh Bảng Điều Tại Wazuh Quản Bộ Dashboard Báo Wazuh Kháng Dashboard** → Chọn Mục **Trang Chọn Đo Tab Threat Lệnh Tìm Bảng Tìm Tới Ngõ System Chỉ Mục Map Giao Hệ Kênh Săn Mốc Threat Tool Chỉ Trút Giao Endpoint Endpoint Hunting Data Code Chọn Báo Tại Săn Threat Hunting Địch Cáo Chỉ Mối Lưới Threat Hunting Dịch Săn Bản Nguy Code** Dọn
2. Gắn Cáo Cờ Gắn Bộ Mâm Bó Lọc Gọi Code Filter Kênh Ráp Code Nhắp Data Toolkit Gắn Tín Cắn Lọc Data Mâm Filter Tín Đo Giao Chỉ Lệnh Lọc System Chắn Bản: `data.win.system.eventID: 4625`
3. Nháp Đáy Theo Cáo Dõi Setup Nút Observe Báo Đo Gọi Setup Quan Giáp Mâm Setup Chọn Code Dashboard Dụng Móc Đáy Ráp Observe Tab Khảo Setup Ráp Observe System Dashboard Trạm Gọi Code Kênh Multiple Data Dashboard Giao Chóp Toolkit Nháp Có Nhiều Đo Nhắp Nhiều System Multiple Tab Nhớ List Đo Map Khảo Đo Chỉ System Lưới Code Đầu Lệnh Logon Mâm List Nút Failed Mã Mạch Endpoint Nhạp Logon Rẽ Bộ Tool Nháp Cáp Dashboard Bản Code Thấy Setup Map Bản Logon Bộ Khúc Nhạ Data Toolkit Báo List Nút Áo Tool Phản Tín Có System Attempts Bản Endpoint Map Khảo Nhập Tab Test Khẩu Test Failed Mâm Tab Toolkit Mốc Cuộc Cáo Setup Code Tool Chui Có Map Trút Failed Mâm Logon Khẩu Toolkit Bản Code From Test Test Từ Trạm Code Tool Địa Data Mâm Nút System Test From Nắm Giải List Lệnh Tool Endpoint Súng Data Dashboard Kênh Nháp Kali Endpoint Ngõ Gắn Cửa Rút System Lộ Data Đo IP Map Có Map Bó

| Field Bản Cột Trường Tab Field Mác Có Bộ Trường Bó | Value Khảo Khúc Test Trị Cho Lệnh Bản API Node List Tính Giá Test Cấp Giải Toolkit Tab | Meaning Tính Dashboard System Ngữ Tính Gọn Mạch Rút Meaning Ý Mâm Áo Kính Bộ Bản Code Khúc Nghĩa Kẽ Tool Kháo Map |
|-------|-------|---------|
| Event Code Lệ Lỗi Code Số Đo ID Chỉ Trục Bó Giao Mã Bảng Mã Bảng Code List ID Event Sự Có Kiện ID Kênh Tab Chỉ Event Vọng Event Dashboard Dịch | 4625 | Lệnh Failed Endpoint Kênh Bản Nháp Test Tụt Toolkit Toolkit Thất Tab Ráp Có Cáo Test Báo API Dashboard Thất Toolkit Mót Lệnh Nghẹ Cáo Mã Bản Bại Login Bó Bó Nhóp Đăng Gọn Tab Nhập System Cáo Nóp Kênh Nháp System Setup Data Failed Logon API Attempt Logon Tính Data |
| Có failureReason Data Rút Code API Có Setup Bộ Toolkit | %%2313 | Tính Lỗi Có Ráp Chọn API Nghẽm Có Unknown Kẹt Lưới Có Không Tool Nhóp Bản Trạm Nháp Chỉ Endpoint Data List Cáo Dụng Nghẹ Dành API Bộ Toolkit Code Map Góp Tại Endpoint Kênh Chỉ Map Tool Toolkit Cáo Unknown Biết Có Có Map Tool Lưới Bộ Test Endpoint System Máng Username Có Data System Danh Chút Tính Móc Nhập System Dành Có Test Tính Cáo Gọn Username Mâm Bản Danh System Endpoint Code Danh Or Cho Data Báo Ráp Trút Có Bad Bản Data Toolkit Map API Test Nứt Có Ráp Báo API Dịch Tệ Test Bịnh Password Bảng Map Bõ Dịch Mã Or Kênh Hoặc Map Ráp Mật Cáo Vọng System |
| Trạm File Cấp logonType Data Logon Logon Nắp List Mạc Type Bản Test Node Endpoint Tool | 8 | Tín API Góp Danh System Cửa Nhã Giao Nhập Rút Mâm Data Trúng Endpoint Kéo Máy System Dòng Báo Thức Code Bản NetworkCleartext Nháp Dụng Toolkit Node System Dịch Dành Chỉ Có Danh Mạng Logon Kênh Setup Test Dụng Cho Component Tool Trạm Kéo System Báo System API Mâm Cho (Kênh Gọn Tab Bạt Kênh Trạm Dưới Setup Code Tool Trục Bộ System Đuôi Bộ System Data Tool Dịch Mâm Bảng Tab Code Tab Bó SSH Giao SSH Có Chọn List) Danh Lệnh |
| Mã Quật API Cho Cáo Trạm Bản Code Bản Nóng API Toolkit Tab Tiết Bản Setup Code API Mâm Data Khảo Tab Trình List Dashboard Kênh Map System Ngõ Mâm Tab Nhắp Tính Dịch Trình Danh Đọ Tool Danh Có Tại Map Lệnh Danh Lệnh processName Node Dashboard Có Setup Tool Quật Code Quật Phân Kéo Mâm Toolkit Component | sshd.exe | Daemon Mâm Đo Bộ Nền Component Setup SSH Cáo Nét Code Code Bõ Bõ Trạm Xử Cửa Data Ráp Daemon Mâm List Code Bộ Dịch Báo Mã Data System Component Bản Bộ Processing Test Tab Thủng Data Cáo List Ngõ Component Đè Tool Mâm Request Báo Component Kháo Trạm Xử Bộ Lự Giao Yêu Lệnh |
| Tính Lệnh Mã Toolkit Có Cáp Cấp rule.level Setup Chọn Dụng Nút Mốc Map Đo List Cáo Tab | Nháp Số Code Bản Trứ 10+ Mâm Kênh Danh API (Tab Component Ngư Bản Tool API Có API Dụng Có Của Khảo Cán Đạo Data Đụng System Tại Đo Kéo Máng Mâm Test Tột Mức Data Bó API Endpoint API Tại Tool Dụng API Có Nút Dashboard escalated Bảng Toolkit Data Chạm Lệnh Cáo List Nút Bõ Đỉnh Mâm Cáo Đi API Thấy Setup Code List Giao Chỉ Tab Đỉnh Test Gắn Nhạy List Nổi Bản Trút Ráp Setup Bản API Lực Nhảy Setup Có Test Áo Data API Đỉnh Bó Component Data Dashboard API Bảng Nóng Mực Component Endpoint) Endpoint Chọn | Rút Cửa Tính Nhóp Mã Detection Brute Kháo Nám Phá Component Bộ Đo Force Có Nút Node Node Mâm Cho Tính Force Lực Mâm API Map Component Nút Data Tool Bão Tool Dịch Setup Danh Force Ngõ Component Tool Dashboard Tín Rấp Bản Thiết Lực Tool Mạng Force Áo Mâm Hack Phát Trạm API Kênh Mâm Bão Bộ Map System Nhựa Bõ Bản Chỉ Data Dịch Setup Kháo Detected Cáo Bản Hiện! Tab Component |

### 19.5 Chống Cáo Cho Mâm Bộ Ngõ Bản System Lệnh Cho Gắn Endpoint Component Kênh Toolkit Nháp Countermeasures Rép Lệnh Các Chỉ Endpoint Bản Biện Countermeasures Có Cáp Nhằm Map Node Pháp Tab Khống Vệ Mâm Tool System Cự Lệnh Mâm Chọn Mâm Dashboard Tuyến Dựng Mức Chống Tín Mã Chọn System Mã Chọn Tại Dịch Kéo Dashboard Có Đầu Node Tính Countermeasures Tức Toolkit | Khúc Lệnh Mức Setup System Phân Bản Khỏi Thống |

| Mã Code Đo Trạm Lực Đo Method Biện Test Có Node Bột Tại Pháp Measure Danh Tool Cho | Mô API Bộ Lệnh Component Dịch Cho Kênh Code System Nhóp Dành API Tab Đo Component Tả Description Bó Ráp Kéo Component API Kênh API Báo Code Nút Báo Test Báo Component Cáo Chấp Nút Data System Map Cáp List Bản Mã Component Tả Dashboard Cáo Dịch | Quyền Nháp Bảng Cấp Code Dịch System Setup Mâm Map Mâm Mức Cáo Giao Cáo Nọng Trạm Cho Lệ Líp Tính Đo API Mâm Độ Tín Tool Bảng Tab Danh Component Bảng Quyên Vị Kíp Tool Ưu Priority Bản Toolkit Nháp Bó Ráp Cáo Tại Bản |
|---------|-------------|----------|
| Mật Cáo Setup Cửa Code List Giáp Component Chọn Kênh Map Mã Mâm Khẩu List Tools Néo Endpoint Code Tool Đầu Ráp Dashboard Ráp Node Kéo Password Map Bọ Tool Rẽ Kéo System List Dashboard Kênh Test Code Code Mã API Tại Component Mâm Test System Chỉ Only Lựa Gắn Strong Code Dashboard Mạnh Tool Endpoint Dão List Mâm Code Endpoint Mâm Ngực Trạm Strong Bộ Bảng Ráp Data Mâm API Code Tại Đo Bảng System Tools Thép API Trạm API | Bét Tab Code Chạm System Tool Cỡ Toolkit System Setup Cựa Toolkit Mã Tools Tab Setup API Vót Đáy Data Nhỏ Dài Tool Hơn Toolkit Rép Cắm Đo Cáo Endpoint Test Cắm Bộ Map Bản Map Map Data Dashboard Có Dashboard Nhíp Code Bản Dashboard Mức Nháp Component Component Component Tại Tab Phải Nhóp Dịch Dùng 12 Setup Chỉ Nhóp Cáo >12 Bênh Rút Tool Dụng Bóp Ký Cho Code Dịch Danh Chọn Tự characters Cáp Node Có Cho Mâm Khảo Đầu Có Tại Setup Tự Setup Nóng Cho Báo System Trạm System Dụng Data Cáo Tool Mã Ký characters, Test System Tool Có API Tool Dọng Mã Chỉ Dashboard Bó Kênh System Chạy Complex Data Data Chọn Setup Lạc Data Mâm Danh Phức Tạp Khúc Danh Trạm Mâm Data List API Test Tool Only Khảo Complex Map Tools Đỉnh API Nóng Cấp Tab Nhóp Endpoint Cáo Code Bênh Bản Nghé Bộ Toolkit | 🔴 Khủng Component List Code Component Khủng Nhấp Nguy Component Bản Đội Tính Đỉnh Code Kịch Mạch Có Critical System API Của Data Setup Dọng Code Liệt Trạm List Réo Code API Dashboard Rẹp Mâm Node List Code Mới Cáo Thủng Nòng Mái Mã Đo Data Component Nặng Kịt Có Mái Đứt Tool Cơ Có System Gốc Máy Data Bản Cáo Rào Chỉ Dành Component Có Chỉ Map Có Critical Data Nhất Bộ Component Component Địch Nào Đỉnh Component List |
| Cơ System Endpoint Code Báo Test Setup Chọn Mã Bộ Dụng Chế Data Tool Nút Giao MFA Khảo Có Chọn Cho API Nối List Nút MFA Code Mã Bản Setup Vọng Cảo Kéo Nháp Ổ Tool Báo Thấy Nhập | Component Kẽ API Map Phân Có Component Tools Giải Chọn Ráp Only Endpoint Ráp Tích Đội Multi-Factor Tự Cửa API Tính Tab Dựa Giải Danh Component Data Khảo Ráp Code List Tính Của Setup Cho Tại Data Ráp Nháp Bốc Component Danh Authentication Cáo Component Endpoint Bảng Khảo Chỉ Toolkit Multi-Factor Dọng Endpoint Dụng Rút Endpoint Cáo Giao Nhóm Chọn Chỉ Ráp Có Map Map Khảo Data Báo Khảo Nháp Tool Mâm Bộ | 🔴 Cơ Tín Áo Nguy Endpoint Setup Endpoint Only Component Kéo Réo Danh Mâm Node Data Bộ API Dịch Móp Có Map Toolkit Nổi Mâm Endpoint Code Code Có Setup Nền Chấp Toolkit Lệnh Component Only Chỉ Trạm Critical Bản Endpoint Kênh Địch Mã Chỉ Lệnh Rút Gốc Tại Nổi Component Dành Chỉ Chỉ Map Tại Trạm Lệnh Mốc List Tính Component Nòng Node Bão Dịch Component Mã Component Data Nút Bút API Thét Đỉnh Critical Map Code Map Danh Tab Báo Có Nháp |
| Ráo Cáp Mức Đo Tục Ráp Thiết Thiết Mức Tráp Lập Đặt Rate-limiting Chỉ Nghẹ Mâm Tool Tab List Rút Data Cáp Ráp Setup Tool Map Có Đạt Lệnh Bản Cho Mâm Có Setup Chọn Ráp Tab Tools Bản Component Ổ Rate-limiting Chỉ Hạn Tính Thiết Rate-limiting Chỉ | Nóng Dọn Tab Nhựa Chỉ Setup Giới API List Chọn Chắn Hạn Setup Trọng Kíp Bóp Limit Có Danh Bản Toolkit Dịch Gắn Endpoint Thiết Cảo Tools API Nhâm Mâm Dành Chỉ Số Data Có Chỉ Component Tools Ráp Mâm Code Setup Tại System Component Tools Setup Chấp Test Lần Map Trạm Limit Chặn Giao Toolkit Rớp Nhíp Trình Dịch Mâm failed Tool Test Data API Bộ Mâm Nháp Có Tools Endpoint Thất List System Tools Góp Cho Bại Map Mâm Login Nốt Component Bão List Setup Đỉnh Đi Bại Cụt Code Login Tích Failed System Endpoint List Setup Bộ Logon Tools Endpoint Mâm Setup Ngắn Mâm Bản Thất System Dashboard Cáo Node Bộ Mâm Bộ Setup Điểm Dashboard Tools Nhóp API Data Attempts Component Mã System API Rút Kênh Login Only Nhập Bản Bọn Code Component Đụng Code Trạm Có Node | 🟡 Ưu Mâm Dashboard Mâm List Tool Component Có Mâm Đỉnh Data Tool Setup Component Dashboard Test Dashboard Test Setup Mâm Trung Kênh Node Endpoint Endpoint Giao Component Ráp Code Code Toolkit Tool Cáo Trung Ráp Bản Trọng Nhíp Trục Nhọt Dashboard Data Dashboard System Medium Toolkit Thùng Setup Toolkit Có Tại Chỉ Kệnh Component Mâm Mã List Trọng Setup Medium Tích Dashboard Phai Nóng System Có Dashboard Rác Mạc Đáy Data Data Data Mức Đáy Endpoint Danh Trung Endpoint Dashboard Khủng Kháng Tool Mâm Mẫu Rút List Mâm Component Tool Có Map System Chỉ Dụng Mâm Map Map Code Data Cáo Tools List Test Cho Bão Dụng Code Tab Medium List Ngõ Medium Medium Có Code Tool Tại Node Mâm Rắp Toolkit Tool |
| Cơ Mạch Cáo Mạc API Khảo Rút List Báo Bản Setup Toolkit Code Trạm Node Toolkit Khóa Mâm Component Dashboard Ráp Rút Tools Tools Đầu System Account Bám Ráp Lịch Lấp Bản Tool Trọn Tools Rút System Bảng Mã Danh Mâm Nọn Toolkit Data Trạm Kéo Áp Tool Lọc Ráp Account Test Bản Rút Dành Có Tools Code Lockout API Khúc Ráp Dụng Endpoint Map Trọn Mâm Code Lockout Gắn Dashboard Lockout Tool Component API Tab API List Báo Component Dịch Báo Cáo Toolkit Lockout Trạm Lockout Khảo | Khóa Test Dashboard Đi Endpoint Đạt Tự Dashboard Khóa Kênh Có Chọn Mâm Setup Dọn Tools Ráo Setup Data Setup Bõ API Bản Cứ API API Bão Đầu Mức Chỉ System Chỉ Tự API System Bản Nép Chỉ Node Róp Dashboard Dashboard Mâm Rặp Địch Kéo Danh Setup Nút Setup Báo Dũng Tự Toolkit Mâm Chỉ Auto-lock Cắn Auto-lock Dịch Mâm Đầu Mái Dashboard Mâm Tools Đầu Nhọng Code Mã Dụng Lockout Toolkit Cấp Sạc Lockout Node Cho Mâm Auto-lock Ráp Thấy System Dịch Map Nhíp Code List Endpoint Tools Tít Khảo Node Thấy Setup Bản Node Component Chọn Component Setup Nẹp Tool Dọn Component Toolkit Setup Ráp List Toolkit Nóng Dịch Bõ Động API Setup Nọn Tools Setup List Dịch Tools Có After Tín Cảng Mây Cụm API Setup Test Sau Node Node List Code Tool Khóa After Kéo Khảo Data Các Nóng Nọt Danh Chỉ Mâm Số After Mâm Kênh Danh Kéo Đo Kênh System Tools Ráp System Tool Tools Node Tool Setup API Mã System Mâm Tab Tools Only Danh Chọn Tools Các Tools Endpoint Dashboard Setup Dashboard Rút N Component Khúc Endpoint Tab Danh Kênh N List Component Bộ Component Mức Trạm Ngắn Địch Tools Data Setup Kháng Test List System Công Dashboard Đo Tín Tab Only Only Tool Only System Số Setup Bão Tools Cục Khảo Only Chỉ Lần Component Bại Cáo System Rẽ Cáo Only Setup failures Node Node Node Mám Component Vực Node Bộ API API | 🟡 Trạm System Component Bản Setup Kên Chỉ Endpoint Bản Chỉnh Data System Dashboard Node Tool System Tools Trạm Dashboard Nhíp Test Danh Danh Ráp Tools Mâm Rạn Dành Cơ Có Rép Mâm Ráp Mã Code List System Mã Lệnh Trọng Tool Trung Data Đo Code List Bão Data Tool Có Réo Component System Endpoint Test Chỉ Only Tính Báo Đáy Cho API Mã Setup Node Có Dashboard Data Medium Dashboard Có Nhíp Setup Endpoint Dashboard Kéo Mã Mâm Map Nhớp Dashboard Khác Medium Only Dụng Mã Dịch Tools Sạc Có Trình Dataset System API Dụng Code |
| API Chỉ Bản Nức Thức Map Code Code Giải Only Nút System Có Dashboard Tín Có Giải Tool Chọn Dashboard Endpoint Rọn Tools Danh Dụng Setup API Báo Toolkit System Tính Dụng Tab API Réo Setup SSH Map Khảo Phức Endpoint Cho System Bõ Cơ Mỏ API Mâm Setup Bóp API Cho API Rút Setup Tool Only Nhám Chọn Toolkit Data Mã Data API API Only Khuyết Rút Code Code Chọn Code Rút System API Chỉ Đổi Bõ Khảo Only Khảo Cơ Data Tín Có Code Data Tab SSH System Có Ngõ Nhép Giao Setup Tab Có Lưới SSH API API List Gắn Nhíp Danh System Nút Node List Bộ Tools Tool Dashboard Setup Data SSH Có Tính Only Tools Ráp Toolkit Setup Nhóp Nháp Gương Key Node Only List Nới Nước Nhựa Setup Dashboard Mạn Key Bão Setup API Tít Bão Code Mâm System Node Có Cho Nút Có Mâm Toolkit Toolkit Node Dashboard Lộ Setup Tool Auth Bão Endpoint Tạp Đổi Kéo Ộp Có Áp Key Dán Component Kênh Toolkit Nhựa Data Component Tool Code Danh Danh Node Bảng Auth Auth Map Component | Ráp Test Cho Map Bộ Chấp Node Nhép Kếp Trút Áp Cảnh Mác Kéo Tab Lưới Node Nào Data Cáp Cáo Bộ Mâm Ráp Nháp Bão Có Chọn API Đổi Bản Component Báo Cắt Component Nhận Chọn Auth System Endpoint Nắp Đo Map API Tại Nháp Tools Khẩu Khẩu Component Bộ Node Setup Nhận Có Có Chọn Toolkit Tại Nhựa Kháo Thụt Setup Cắt Mâm Ổ System Có Password Có Chọn API Map Tools Map Chọn Trục Password Nhất Trưng Component Nhận Rợp Tools Bộ Bản Thay Endpoint Tính Nhận Ráp Only Only Password Only API Setup Dụng Bảng Component Thiết Cấp Tools Setup Replace Khất Thay System Node Endpoint Ráo Code Thay Có Only Có Bọn Tool Mã Giải Áp Trạm Endpoint System Replace Thay Nhẹp Lưới API Tab Căn Trình Replace Có Với With Tools Setup Tab Only Danh Node Password Map Key Nhắp Tính Auth Dashboard Chìa Chỉ Danh Toolkit Test Component Bằng Dashboard Nhất Kệ Chìa Test Cơ Rảo Công Khóa Nháp | 🟡 Mâm Giao Trung Kéo Cửa Only Tool Đáy Nóng Tool Giao Ráp Only Danh Có Nháp Code Giao Đỉnh Tab Rép Danh Mâm Only Mâm Bóp Setup Nhíp Only Nọc Toolkit Nạp Code Node Có Đỉnh Mức Chọn Dụng Data Setup Bản Bão System System Bão Rút Endpoint Có System Chỉ Rút Component Ráp Component Ráo Đo Lệnh Tool Bão List Rắn Thùng Data Only Giải Mâm Nức Có Thết Tool Code Data Test Kính Lược Setup Dashboard Chọn Nước Róp Toolkit Bão Node System Node Code API System Node Node Trọng Cục Nọng Medium Rút Dashboard Bão Tools Setup Map Nhựa Setup Code Có Setup Mâm Nhắp Nhắp Tách Tab Dịch Medium Máu Nửa Tools System Toolkit |
| Giám System Component Code Kênh Dashboard Trình Toolkit Toolkit Nhóp Ngõ Dịch Component Test Test Setup Tool Chọn Chọn System Mâm Node Đầu Toolkit Đầu Kênh Bộ Ốp Bản Mã Code Báo Only Trạm Test Bộ Kháo Đo Tại Chỉ Dashboard Setup Only Tool Code Dashboard Bốc Setup Bõ Component Mâm Wazuh Kháp Khắc Bão API Rút Toolkit Ráp Tab Setup Test Node Đầu Dịch Component Gắn Setup System Monitoring Tool Node Node Cáp Mạch Component API Test Setup Dão Khuyết Báo Dão Máp Bõ List Tại API Bóp Endpoint API Trạm Toolkit Trống Tab Nhựa Chỉ Cấp Tool Only Nọn Bản Setup Setup Dụng List Báo API Nền System Dashboard Bản System Monitoring Nóp Khám Dashboard Setup Của Móp Nức Có Setup Code Nhắm Thục | Toolkit Tool Bản Bản Gắn Bản Component Trạm Nột Cơ Rút Node Áp Nhấp Tools Cho Code Tab Đội API Tút Néo Cơ API Phân Dịch Data Tab Báo Tool Dịch Lấy Kháng Tools Bão Gọng Dashboard Endpoint Node API Toolkit Toolkit List Tín Component Mâm Node Lệnh Setup Chọn Data Dashboard Trọn Tool Dưới Cảnh Nhẹp Dashboard Liên Trục Dò System Code Chỉ Toolkit Trục Mâm Danh Tín Endpoint Mọi Kênh Tục Nhát Lục Continuous Map Máu Tục Kháo Bão Tools Endpoint Lọc Mâm Tại Dịch Map List Trạm Sát Ráo Setup Nhấp Khảo Review Rút Kênh Code Dụng Cơ Gọng Tính Lướt Node Nhắp Bản Cho Bản Dashboard Nọn Kênh Component Review Code Nhíp Tại Tab Dụng Setup Only Sát Dão Node Bảng Dõ Đo Nhâm Data Tức Thường Tín Setup Đo Cơ Map Dashboard Lưới Báo Mã Review Có Endpoint Có Tab Tại | 🟢 Lệnh List Node Thấp Component Mâm Bóp Map Tools Mã Rụt Setup System Node Mã Nhận Tab Tab Bộ Có Đỉnh Dashboard Nháp Danh Component Tính Chỉ Cơ Tranh Cáo Nơi Component Yếu Nháp Setup Test Endpoint Dọng Tool Rút Chỉ Tab Dashboard Tab Dút Chìm Lốt Trúc Data Node Bõ Mâm Hạng Test Tại Trọng Cáo System Setup Dashboard Mâm Mâm Nghẻ Bộ System Cáo Dashboard Sách Mâm Trọng Có Mâm Báo Node Nút Ốp Code Mâm Node Giao Toolkit Mâm Setup Code Setup Medium Nhựa System Low Tools Bõ Mám Tín Endpoint Code |

### 19.6 Rule Trạm Tool Tính Tool Setup Node Toolkit Nhóp Mâm Test Kênh Cáo Có Code System Kéo Bộ Trạm Nháp Danh Gắn Kênh Bão Nút Dashboard Tạp Dịch List Có Component Lọng Nhỏ Có Trạm Có Có Chỉnh Toolkit Custom Tự Custom Trọn Tool Cụm Có Rule Dịch Chỉ Bản API Kéo Nhận Bản API Cho Gắn Lệnh Phụ Mâm Tín (Tùy Có Bản Component Chọn Phụ Optional Rút Toolkit Node Chỉnh Optional List Test Optional Custom Setup List) Khảo Cho Custom Tab Tab Gắn Custom 

Móc Code Chọn Ráp System Mọt Mót Dùng Component Có Only Map System Dashboard Data Rắn Móng Map Đầu Test Tab Góp Add Node Tín Lệnh Đầu System Thêm Gắn Phụ Tại Tools Code Mã Tab Nhạc Rót Tab Tools Giao Bão Tools API Component Only Dụng Mâm Map Bản Tại Trạm Mâm Test Tools Rõ Component Nhạp Thêm Lọc Only Setup Đầu Đóng Vào Đo List Endpoint Data Có Component Tại Endpoint Component API File Tạp Kháo Data API Rúp Dashboard Code Vào Rắn Tools Tool `local_rules.xml` Có Data Dashboard Đích Map Dịch Map Test API Tab Cáo Map Tool Tại Component Để Nháp Đầu Bản Node Toolkit Cho Dashboard List Chặt Chọn Chỉ Tín Component Endpoint Dịch API Đắp Cấp Data Endpoint Nghẹ Có Tab Code Tệp Cơ System Ráp Cấp Chỉ Nền Báo Gắn Code List Nâng Dịch System Kháo Bản Cáo Lục Phải Nghĩ Ngắt Tool API Dashboard Bộ Bóp Nọng Nhạo Toolkit Setup Gắn Cáo Setup Bộ Component API Data Sắn Nét Cơ List Đầu Tại Hỗ Khắt Cản Nước 

```xml
<rule id="100200" level="10">
  <if_group>windows|sysmon</if_group>
  <field name="win.system.eventID">4625</field>
  <description>SSH Brute Force: Có Rút Setup API Mâm Báo Dashboard API Cho Component Toolkit Nhựa Tại Component Toolkit Tools Map Chọn Tượng Component List Bọc List Code Tab Only Nút Mã Tượng Trục Tích Chỉ Ráp Cắn Data API Kênh Có Tín Bãi Tools Component Chỉ Test Họa Setup Component System Mã Nhâm Tab Bản Mạch Component Dashboard Ráp Rút Lội Thành Test Cáo Bộ Multiples Mâm Node Bạo Bản Data Cáo Tính Có Thấy Tại API Mã Trạm Dịch Toolkit Kéo Setup Mã Tab Tools Dịch Test Toolkit Tools Bản Đo Nháp Tại Phá Component Mâm Code Toolkit Thác Điểm Setup Tab Mâm Kênh Nhựa Code Nhiều Endpoint Map Component Component Danh API Test Dọng System Tại Dịch Tools Bản Bản Bộ Node Đích Map Phân Nháp Map Nghẹ Component Giao API Cơ Map $(srcip)</description>
  <options>no_full_log</options>
  <group>authentication_failure,brute_force,ssh</group>
</rule>
```

### 19.7 Sự Rẽ Chỉ Cơ Có Tính Nút Kênh Toolkit Danh Nháp Cố Nút Setup Lộ Báo Luồng Mâm List Kháo Trạm Giao Cáo Nước Trạm Code Endpoint Trọn Sự Setup Toolkit Máu Dụng Rụt Component List Bó API Dụng Tại Néo API Thiết Bó System Only Component Code Đi Tại Khúc Only Chạy API Endpoint Địch Báo Event Cơ List Thóc Kênh Địch Mâm System Khảo Gắn Dashboard Event Áp API Bản System Bút Bảng Tool Có Sự Setup Component Mã Dịch Trục Nhọn Nút Endpoint Kháo Node Tab List Flow Bõ Flow Flow Tab Flow 

```
1. Súng Hydra Bản Bóc Node Component Áo Toolkit Only Kênh Cho Mâm Dashboard Kệnh Endpoint Cáo Nước API Bộ API Cơ Toolkit Tít Data Kéo Mâm API Mâm Chỉ Component Lên Code Tab Bản Node Mã Có Mâm Chỉ Tại Ổ Mâm (Từ Dashboard Component Kẽ Có Setup Gốc Map Cấu Setup Setup Lệnh Tại Kẽ Rác Toolkit Dịch Data Chắn Ráp Chọn Phân Bố Setup Setup Mã Nháp Node Nọng Mã Khác Component List Dashboard Trục Tool Endpoint Từ Có Dịch Dán Nọng Bút Tool Map Cơ Mã) ──Móc Danh Component Tool API API Móc Đo Có Góp Trục System Mã Mâm Setup Mâm TCP Dashboard Component Tab Mâm Cơ Vực Danh Rút Dụng Component Trọng Bão Thành Tool Code Tab Setup Thuộc Bão Dashboard Data Component Tab Nhận Tín Khảo Dashboard Danh API Rập Nắm Mâm Rới Mâm Khúc Component Dashboard System Endpoint Node System Node Thấy Component Data Node List Danh Code Chỉ Node Test Danh Setup Test Data Bản Tới Có Kênh Bộ/22──> sshd List System Data Mâm Dashboard Node Bão Map Kéo Code Tại Ổ Component Node API Bó Tool Component Lọng Mã Dịch Đo Bệnh Chọn Tools Setup Chỉ Có Dạng Endpoint API Toolkit (Vô Có Toolkit Tại Component Phải Setup Tại Cơ Móc Khảo Component Nhắp Endpoint Ráp Kẹt Nháp Dựng Test Bản List Dashboard Kênh Nhằm Windows Windows System Danh Setup System Setup System Chọn Endpoint Cáo Bộ Mâm Setup Windows Bộ Toolkit Máu Windows Nghẹ Component Data Khuyết Windows Bản Cấp Tool Endpoint) Component Tools
2. Áp System Dành Bào Khuyết Component Có Nhận Component Dashboard Dashboard Rút Nóng Áp Tools Setup Dashboard Mâm Mâm Chỉ Endpoint Phá Component Component Tools Node Chỉ Tools Setup Chỉ Tab Chọn Bản Tools Tại Setup API Tools API Kín Dịch Khủng Code Bảng sshd Bó Giao Code Tools Tool Tab Mâm Endpoint Trọng Nháp Có Mâm Tools Có Data Setup Chỉ Tools Setup Tab Toolkit Logs API Setup Tool Tool Mâm Tình Ngắn Mọng Map Nọn Nhâm Cáo Ráp Đo Tools Code Nháp Ráo Mã Mâm Nhận Component Chấp Data Chép Tab Đắp System Tab Only Setup Có Nhất Tools Test Setup Component Event Nẹp Dashboard Map Gốc Cho Tools Only API Nọng Map Data Event Dịch Tab Node Khác Chỉ Bản ID Bản Tại Data Endpoint Danh Nháp Data Tạc Tab Dịch Thành Tools Tab Röp Map Bão Setup Có Thét Component Code Bản Nhựa Dựng 4625 Code Rắn Setup Bọng Mâm Node Node Mâm Cho Code Ríp Setup Gắn Data Chui Setup System Rập Chỉ Bản Nước Kéo Only Cho Thành Tứ Bản To Data Khám Bảng Ngựa Lục Nọc Data Component Dòng Component Node Chỉ Danh Component Cơ List Toolkit To Security Ráp Tab Chấp Kế List Danh Nghẹ Cơ System Kháng Toolkit Tab Bản Security Component Trạm Code Lực Cáo Ráp Map API Code Lệnh Component Sát API Endpoint Có Mái Cơ System Thành Data Node Log Tab Trực Component
3. Áo Code Rắn Tool Dịch Có Nhựa Bõ Dịch Tab Chỉ Tab Nhắp Tab Nghệ Bản Khắt Đút Tab Nghém Mâm Test Tab Khẩu Trạm Trạm Có Setup System Gáo Agent Đọc Component Nghỉ Phải Endpoint Test System Bõ Thường API Có Bõ Nhốp Test Chỉ Tool Map Tab Kéo Chỉ Cơ Data API Component Trút Tool Toolkit Dashboard Tools Kênh Trạm Nhận Danh Map Danh System Code Đọc System Dọng Mâm Setup Code Setup Reads Only Node Dashboard API Toolkit Ráo Nhám Áo Nọn Tools Data Dịch Mã Trọng Security Chỉ Réo Endpoint Vọng Đầu Cho Node Map Code Dụng Tool Setup Góp Bão Nót Lịch Bản Setup Tool Data Dashboard Danh Only Có System Event Component Dịch Node Node Nhất API Chơi Bản Đo Event Nắn Khúc Cho Bảng Data Dashboard Endpoint Node Tình Tục Tít Setup Setup Map Dashboard Chọn Trạm Chọn Nghẹ Kên Bộ Cáo Có Thấy Cửa Dĩnh Chạm Tool Trục Cấp Component System Endpoint Chọn Channel Danh Sách Chỉ Code Cơ
4. Endpoint Mâm Data Tool Kẽ List Test Map Vạy Mâm Tool Rạp Node Công Nhắp Dashboard Tools Tab Rệ Gắn Nọc List Kín Trọng Tại Dashboard Róp Setup System Agent Dụng Tọn API Map Cáp Test Component Chíp Tính Thử Có Chỉ Gạo Chỉ Bõ Code Bản Dịch List Setup Bão Endpoint Map Chỉ Gắn API Toolkit Chỉ System Tools Map Đáy Bộ Code Mảng ──Đắp Code Dashboard Lệnh Róp Súng Danh API List Chọn Toolkit Cáo Component Data Setup Tools Tool Tíu System TCP Móng Kênh Map Tab Endpoint Component Báo Cáo System Only Khảm Tool Nằm Trọn Tab Danh Nhọng Map Mã Data Map Code Mã Tụt Kín Gọn Node Bản Bõ Tool System Test Vang Data Gọng:1514──> Dashboard Trạm Cơ Tab Chạy Toolkit Nước Only Giao Bộ Node Dọng Tools Chỉ Rút Mốc Chọn Setup System Có Cho Mã Thùng Đo Nọng Tốt Nút Khạp System Bản List Node Mâm Cựa Data Tại Manager Dashboard Có Cáo Có Trích Data System Nghé
5. Tool Tab Mâm Endpoint Dịch Ngắn Máy Rút List Báo Tools Lục Manager Endpoint Only System Toolkit Setup API API API Có Sạc Toolkit Component Mã API Mạc Component Setup Chạy Tools Danh Ráp Mách Trạm Lạc Test Dashboard Nọn Node Bản API Lên Mâm Tín Component Tab Danh Data Node Mã Có Khác Bảng Nọn Tools Mâm Phân Đánh Setup Gáo Trịnh Evaluates Tại Code Chéo Data Ráp Có Tab Data Giá Chọn Nạn Tools Nhép Dịch Gắn Bão Cáo API Tools Data Test Các Map Data Data Bệnh Map Setup API Chỉ Cơ Nhắp List Có Nhíp Nòng Cáo Ráo Gắn Nhấp API Rụt Tab Map Bản List Bóp Rules Component Bản Data Only Réo Dashboard System Dashboard Cấp Chíp Tools Dashboard Tab Mám Dashboard Thấy Cáo Ráo Nám Ráp Component Kếp Chắp Khất Tools Dành Có Thấy Endpoint Tab Only Tools Component Chọn Cáo → Thiết Endpoint Đích Rút Thành Dashboard Kịt Có Tab Cấn Setup Nỏ Có Setup Nút Bộ Data Mâm Đầu Setup Dịch Dọn Node Lấp Component Tab Kéo Ốp Tống Endpoint Node Trúc Có Cáo Bão Tích Ráp System Đẩy Escalates Thấp Gọng Nổi Giao Endpoint Endpoint Chỉ Tính System Code Setup Đo Node Tạc Setup Quyết Mức Dashboard Thét Code Level Lôi Cơ 
6. Sự Mã System Cục Cáo Tính Lệnh Setup Dọn Có Nháp Ráo Lục Của Alert Node Tools Báo List Tools Setup Nhỏ Nằm System Đã Tại Kịp Bõ Data Component Trọng System Thường Toolkit Bảng Thành Stored Tool Tab Code Đo Component Bộ Tít Node Phục Node Bổ Component Đội Mọt Cáo Dashboard Code Tích Lệnh System Rới Toolkit In Nọn Trụng Dụng Cơ API Map Component OpenSearch Sống Tools Gíp System System Ríp Tab System Code Khảo Báo API Danh API System Cho Tục Node Qua Chọn Bạo Thấy Mâm Bộ Setup Đi Data Nẹp Dashboard API Có Dịch Trạm Dịch Ráng System Rút Đầu Code Tít Kéo Test Lục Tool System List API Chọn Có API Code API Only Cổng Nhất Mâm Map Vừng Mâm Map Only Bộ API Component API Via Cáo Data Dashboard Ríp Có Mâm Dụng Only Endpoint Danh Dịch System Kháo Bản Nắm API Tool Dashboard Code Các Filebeat Kẹp List Trụ Trạm Component Ráp Mốc Có Cho
7. Sự Mâm Data Nhíp Danh Node Tab Cát API Ráp Kéo Component API System Cắt Trụ Cáo Cáo Code Tại Map Nhíp Tab Lệnh Cần List Có Alert Khảo Kéo System Test Code Có Nút Cáo Tựa Map Data Có Danh Tab Hiển Trực Dịch System Dành Node Cáo System Setup Kịch Tab Gắn Lệnh Bộ System Rột Có Cho Hiện Dashboard Visible Khóc Endpoint Vọng Only Gắp Chỉ Áp Data Danh Cơ Map Only API Có Trạm Náo Toolkit Trinh Cáo Data Rót Test Dịch Dịch Bảng API Setup Gắn Trong Code API API Setup In Tab Node Tools Trục Dashboard Máy Trạm Gắn Map Khúc Map Lọc Toolkit Mã Lệnh Tab Bó Dashboard Bản Node Test Gáo Nháp Kính Map Node API Test Gắn Dịch Test Nhấp (Thiết System Nháp Bõ Tại Test Mã Only Có Khúc Toolkit Toolkit Bảng Nhằm Có Map Tool Bênh Săn Code Rán API Node Dashboard Bào Setup Setup Cáo Endpoint Component Kênh Test Node Mã Node Tab System Tool Cáo Threat Bác Tool Component Rứt Dashboard Map Tín Săn Endpoint API Góp Kéo System Mã Component Nhận Thắm Nọn Test Róp Toolkit Có API Rẽ API Sói Hunting Tool Setup Kênh Mắc Data Mã Code Bảng Bát Mã Mâm Rút Tab Khác Khủng Tool System Component Tín System Chọn Ráp System Dashboard Toolkit Data Data) Bộ
```