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

### Reload (Khởi động lại) Wazuh Manager

```bash
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
# LƯU Ý QUAN TRỌNG: Cần xóa file .restart bị kẹt để tránh lỗi daemon không khởi động được
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'
```

### Kiểm tra Trạng thái Hệ thống

```bash
# Kiểm tra trạng thái các daemon của Manager
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# Liệt kê danh sách Agents
docker exec wazuh-manager /var/ossec/bin/agent_control -l

# Kiểm tra trạng thái Cluster của OpenSearch Indexer
docker exec wazuh-indexer curl -sk https://localhost:9200/_cluster/health

# Kiểm tra kết nối đến Dashboard
curl -sk https://192.168.100.102:443/status

# Kiểm tra xác thực API
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"
```

### Xem Log Hệ thống

```bash
# Xem log trực tiếp từ Docker container
docker compose logs -f wazuh.manager
docker compose logs -f wazuh.indexer
docker compose logs -f wazuh.dashboard

# Xem log cảnh báo (alerts) trực tiếp trên Manager
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/alerts/alerts.log'

# Xem log API của Manager
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/api.log'
```

### Thêm Agent Mới (Windows Endpoint)

```bash
# Bước 1: Chạy script tạo Key mới cho Agent
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'

# Bước 2: Khởi động lại Manager và xóa file .restart
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'

# Bước 3: Copy chuỗi Key được sinh ra và dán vào quá trình cài đặt Wazuh Agent trên Windows
# (Thêm IP của Manager 192.168.100.102 vào file ossec.conf trên Windows Agent)
```

### Sao lưu (Backup) Cấu hình và Log

```bash
# Sao lưu thư mục cấu hình và script
tar czf wazuh-backup-$(date +%Y%m%d).tar.gz \
  soc-lab/wazuh/config/ \
  soc-lab/wazuh/scripts/ \
  soc-lab/wazuh/filebeat-run.sh \
  soc-lab/indexer/config/ \
  soc-lab/dashboard/config/ \
  soc-lab/.env \
  soc-lab/docker-compose.yml

# Sao lưu thư mục logs (Tùy chọn)
tar czf wazuh-logs-$(date +%Y%m%d).tar.gz soc-lab/wazuh/data/logs/
```

---

## 16. Hướng dẫn Khắc phục Sự cố

### Lỗi 1: Cảnh báo "Some Wazuh daemons are not ready yet"

**Triệu chứng:** Toàn bộ các yêu cầu gọi API đều thất bại và trả về HTTP 400 kèm theo thông báo lỗi trên.

**Nguyên nhân:** Thường do tệp `.restart` còn sót lại trong `/var/ossec/var/run/`. Khi Manager khởi động lại (restart) bị gián đoạn, tệp này không được tự động dọn dẹp, khiến API lầm tưởng các daemon vẫn đang trong quá trình khởi động.

**Cách khắc phục:**
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && rm -f /var/ossec/var/run/.restart'
```

**Phòng ngừa:** Luôn xóa tệp `.restart` sau khi chạy lệnh restart.
```bash
alias wazuh-restart='docker exec wazuh-manager /var/ossec/bin/wazuh-control restart && \
  sleep 2 && docker exec wazuh-manager rm -f /var/ossec/var/run/.restart'
```

### Lỗi 2: Xung đột biến môi trường PATH trên Windows khi chạy lệnh Docker

**Triệu chứng:** Các lệnh `docker exec` thất bại với thông báo lỗi đường dẫn từ Windows, không tìm thấy lệnh trong container.

**Nguyên nhân:** Biến môi trường `%PATH%` của Windows bị inject thẳng vào container, ghi đè lên `$PATH` chuẩn của Linux.

**Cách khắc phục:** Khai báo lại PATH chuẩn của Linux trước mỗi lệnh `docker exec`:
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && <câu lệnh của bạn>'
```

### Lỗi 3: Dashboard báo "No API Available"

**Triệu chứng:** Truy cập Dashboard thành công nhưng hiển thị lỗi không thể kết nối tới Wazuh API.

**Nguyên nhân phổ biến nhất:** Wazuh API đang bị treo do lỗi tương tự **Lỗi 1** (tồn tại tệp `.restart`).

**Kiểm tra và khắc phục:**
```bash
# Thử kết nối API trực tiếp từ Manager
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"

# Nếu nhận lỗi HTTP 400, hãy xóa tệp .restart như hướng dẫn ở Lỗi 1
```

### Lỗi 4: Endpoint (Agent) báo trạng thái "Disconnected"

**Triệu chứng:** Agent hiển thị trong danh sách của Manager nhưng có trạng thái "Disconnected".

**Nguyên nhân có thể:**
1. Khóa chia sẻ (key) giữa Agent và Manager không khớp (file `client.keys` trên Manager và `ossec.conf` trên Agent).
2. Tường lửa (Firewall) chặn port 1514/TCP.
3. Dữ liệu map của agent bị lệch hoặc tồn tại rác trong thư mục `agent-info`.

**Cách khắc phục:**
```bash
# Chạy lại kịch bản sinh key mới, xóa agent cũ và khởi động lại
docker exec wazuh-manager python3 /tmp/do_all.py
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager rm -f /var/ossec/var/run/.restart
```
Sau đó cập nhật lại key mới cho Agent và khởi động lại dịch vụ Wazuh trên Windows.

### Lỗi 5: Filebeat không thể kết nối tới Indexer

**Triệu chứng:** Không thấy dữ liệu cảnh báo (Alerts) hiển thị trên Dashboard.

**Kiểm tra chẩn đoán:**
```bash
# Xem log của Filebeat
docker exec wazuh-manager cat /var/log/filebeat/filebeat

# Kiểm tra kết nối tới Indexer
docker exec wazuh-manager curl -sk https://wazuh.indexer:9200/

# Kiểm tra sự tồn tại của chứng chỉ SSL
docker exec wazuh-manager ls -la /etc/ssl/
```

**Nguyên nhân phổ biến:**
- **Lỗi chứng chỉ SSL:** Thiếu hoặc sai lệch chứng chỉ (file `filebeat.yml` cấu hình sai đường dẫn).
- **Indexer chưa sẵn sàng:** Indexer chạy ở chế độ Single-Node có thể mất nhiều thời gian để khởi động trong lần đầu tiên. Hãy kiên nhẫn chờ đợi.
- **Lỗi mạng (Network):** Phân giải DNS của Docker bridge (soc-net) bị lỗi, khiến `wazuh.indexer` không thể được phân giải thành IP.

### Lỗi 6: Lỗi SSL/Schannel khi truy cập Dashboard trên Windows

**Triệu chứng:** Trình duyệt (Chrome/Edge) hiện cảnh báo bảo mật khi truy cập Dashboard.

**Nguyên nhân:** Do hệ thống đang sử dụng chứng chỉ tự ký (Self-Signed Certificates) thay vì chứng chỉ từ các tổ chức CA (Certificate Authority).

**Cách khắc phục:** 
- **Trên trình duyệt:** Bấm vào "Advanced" (Nâng cao) và chọn "Proceed to 192.168.100.102 (unsafe)".
- **Khi sử dụng công cụ dòng lệnh (như curl):** Thêm tham số `-k` hoặc `--insecure` để bỏ qua việc xác minh chứng chỉ.

Đây là điều bình thường trong môi trường Lab. Khuyến nghị sử dụng chứng chỉ hợp lệ (ví dụ Let's Encrypt) nếu triển khai thực tế.

---
---

## 17. Tham chiếu Tài khoản (Credentials)

### Thông tin Đăng nhập Hệ thống

| Dịch vụ | URL Truy cập | Username | Password | Ghi chú |
|---------|-----|----------|----------|-------|
| **Wazuh Dashboard** | `https://192.168.100.102:443/` | `admin` | `admin` | Giao diện quản trị Web UI |
| **Wazuh API** | `https://192.168.100.102:55000/` | `wazuh-wui` | `wazuh-wui` | REST API |
| **Wazuh Indexer** | `https://192.168.100.102:9200/` | `admin` | `admin` | Truy cập trực tiếp cơ sở dữ liệu OpenSearch |
| **pfSense WebGUI** | `https://192.168.100.1/` | `admin` | `pfsense` | Web quản lý Tường lửa pfSense |

### Đường dẫn Chứng chỉ TLS (Certificates)

| Chứng chỉ | Đường dẫn (Path) | Mục đích sử dụng |
|-------------|------|---------|
| Root CA | `certs/root-ca.pem` | Nền tảng chung cho tất cả các thành phần |
| Manager Cert | `certs/wazuh-1.pem` | Node Manager |
| Manager Key | `certs/wazuh-1-key.pem` | Node Manager |
| Indexer Cert | `certs/node-1.pem` | Node Indexer |
| Indexer Key | `certs/node-1-key.pem` | Node Indexer |
| Admin Cert | `certs/admin.pem` | Xác thực Admin cho Indexer |
| Admin Key | `certs/admin-key.pem` | Xác thực Admin cho Indexer |

> **⚠️ CẢNH BÁO BẢO MẬT:** Tất cả mật khẩu đang ở chế độ mặc định. Đối với môi trường thực tế (production):
> 1. Bắt buộc thay đổi `INDEXER_PASSWORD` và `DASHBOARD_PASSWORD` trong file `.env`.
> 2. Thay đổi mật khẩu API của `wazuh-apid`.
> 3. Tạo lại toàn bộ chứng chỉ SSL mới.
> 4. Thay đổi mật khẩu admin của pfSense.

---

## 18. Phụ lục

### Phụ lục A: Danh sách Lệnh nhanh

| Tác vụ | Câu lệnh |
|------|---------|
| Khởi động Stack | `cd soc-lab && docker compose up -d` |
| Tắt Stack | `cd soc-lab && docker compose down` |
| Xem log Manager | `docker compose logs -f wazuh.manager` |
| Xem log Cảnh báo (Alerts) | `docker exec wazuh-manager tail -f /var/ossec/logs/alerts/alerts.log` |
| Danh sách Agent | `docker exec wazuh-manager /var/ossec/bin/agent_control -l` |
| Kiểm tra trạng thái Daemon | `docker exec wazuh-manager /var/ossec/bin/wazuh-control status` |
| Khởi động lại Manager | `docker exec wazuh-manager /var/ossec/bin/wazuh-control restart` |
| Xóa file .restart | `docker exec wazuh-manager rm -f /var/ossec/var/run/.restart` |

### Phụ lục B: Thông tin Cổng (Ports)

| Cổng | Giao thức | Dịch vụ | Nguồn | Đích |
|------|----------|---------|--------|-------------|
| 514 | UDP | Syslog | pfSense (192.168.100.1) | wazuh.manager |
| 1514 | TCP/UDP | Wazuh Agent | Windows Endpoint | wazuh.manager |
| 1515 | TCP | Cấp phát Agent Key | Windows Endpoint | wazuh.manager |
| 55000 | TCP | Wazuh API | Wazuh Dashboard | wazuh.manager |
| 9200 | TCP | OpenSearch HTTP | Wazuh Dashboard / Filebeat | wazuh.indexer |
| 443 | TCP | HTTPS Dashboard | Trình duyệt người dùng | wazuh.dashboard |

---

## 19. Mô phỏng & Phát hiện Tấn công SSH Brute Force

### Kịch bản Tấn công

Kẻ tấn công sử dụng công cụ `hydra` trên máy Kali Linux để dò mật khẩu SSH (Brute Force) vào một máy tính Windows (hoặc Linux) trong mạng LAN.

- **Kẻ tấn công (Kali Linux):** Chạy lệnh tấn công `hydra`
- **Mục tiêu:** Máy tính đã được cài đặt Wazuh Agent
- **Công cụ phát hiện:** Wazuh Manager (thông qua log từ Agent)

### Các bước thực hiện

**1. Khởi chạy tấn công từ Kali Linux:**
```bash
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://192.168.100.10
```

**2. Quá trình phát hiện trên Wazuh:**
- Wazuh Agent liên tục thu thập log xác thực thất bại (Failed Logon) từ hệ điều hành và gửi về Manager.
- Wazuh Manager (thông qua `wazuh-analysisd`) so khớp các log này với bộ quy tắc (ruleset) hiện có.
- Khi số lượng đăng nhập sai vượt ngưỡng cho phép trong thời gian ngắn, Manager sẽ kích hoạt Rule phát hiện Brute Force.

### Phân tích Cảnh báo (Alert) trên Dashboard

Truy cập **Wazuh Dashboard -> Security events**, bạn sẽ thấy các cảnh báo được sinh ra:

- **Rule ID:** `5712` (SSHD brute force trying to get access to the system).
- **Mức độ (Level):** `10` (High - Cảnh báo mức độ cao).
- **Thông tin chi tiết:** Hiển thị IP của kẻ tấn công, tài khoản bị tấn công, và thời gian diễn ra.

Nếu tích hợp với công cụ phản hồi tự động (Active Response), Wazuh có thể cấu hình để lập tức chặn IP của kẻ tấn công bằng tường lửa host-based hoặc báo cáo về pfSense để chặn ở mức gateway.

---

**Báo cáo Phiên bản:** 1.1  
**Ngày cập nhật cuối:** 04/05/2026  
**Phiên bản Wazuh:** 4.9.0  
**Môi trường:** Docker Compose (Single-node)

