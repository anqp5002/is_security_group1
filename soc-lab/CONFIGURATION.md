# SOC Lab — Cấu Hình Chi Tiết (Detailed Configuration)

> **Comprehensive configuration reference** for the Wazuh + Suricata + pfSense SOC Lab stack.
> Based on the current project (D:\dev\is_security_group1) with supplementary reference from SOC Lab deployment guides.
> **Nguyên tắc:** Nếu có khác biệt giữa DOCX hướng dẫn và dự án hiện tại, **ưu tiên cấu hình dự án hiện tại**.

---

## Table of Contents

1. [Network Configuration](#1-network-configuration)
2. [Docker Compose Stack](#2-docker-compose-stack)
3. [Environment Variables (.env)](#3-environment-variables-env)
4. [Wazuh Manager Config](#4-wazuh-manager-config)
5. [Wazuh Indexer (OpenSearch) Config](#5-wazuh-indexer-opensearch-config)
6. [Wazuh Dashboard Config](#6-wazuh-dashboard-config)
7. [Filebeat Config](#7-filebeat-config)
8. [Wazuh API Config](#8-wazuh-api-config)
9. [Custom Rules & Decoders](#9-custom-rules--decoders)
10. [Suricata IDS Config](#10-suricata-ids-config)
11. [pfSense Integration Config](#11-pfsense-integration-config)
12. [Agent Scripts](#12-agent-scripts)
13. [Filebeat Startup Patch](#13-filebeat-startup-patch)
14. [SSL Certificates](#14-ssl-certificates)
15. [Agent Configuration (Windows)](#15-agent-configuration-windows)
16. [Deployment Checklist](#16-deployment-checklist)
17. [Differences from Reference Guides](#17-differences-from-reference-guides)
18. [Quick Command Reference](#18-quick-command-reference)
19. [SSH Brute Force Simulation](#19-ssh-brute-force--simulation--detection)
20. [Sysmon Log Ingestion](#20-sysmon-log-ingestion)
21. [Suricata IDS trên Windows](#21-suricata-ids-trên-windows)

---

## 1. Network Configuration

### Physical Network

| Entity | IP Address | Subnet | Gateway | Role |
|--------|------------|--------|---------|------|
| pfSense WAN | 192.168.100.1 | /24 | ISP | Gateway, Firewall, DHCP, DNS |
| pfSense LAN | 10.0.1.1 | /24 | — | Internal lab network |
| Docker Host | 192.168.100.102 | /24 | 192.168.100.1 | Host for all containers |

### Docker Bridge Network — `soc-net`

| Parameter | Value |
|-----------|-------|
| Subnet | 172.20.0.0/24 |
| Driver | bridge |
| Gateway | 172.20.0.1 (auto) |

### Container IP Assignments

| Container | IP Address | Hostname | DNS Alias |
|-----------|------------|----------|-----------|
| wazuh.manager | 172.20.0.10 | wazuh-manager | wazuh.manager |
| wazuh.indexer | 172.20.0.11 | wazuh.indexer | wazuh.indexer |
| wazuh.dashboard | 172.20.0.12 | wazuh.dashboard | wazuh.dashboard |
| suricata | host network | suricata | — |

### Port Mapping (Host → Container)

| Host Port | Container Port | Protocol | Service | Source |
|-----------|---------------|----------|---------|--------|
| 514 | 514 | UDP | Syslog (pfSense) | pfSense |
| 1514 | 1514 | TCP+UDP | Wazuh Agent | Remote agents |
| 1515 | 1515 | TCP | Agent enrollment | Remote agents |
| 55000 | 55000 | TCP | Wazuh API | Dashboard, admin |
| 9200 | 9200 | TCP | OpenSearch HTTP | Filebeat, debug |
| 443 | 5601 | TCP | Dashboard HTTPS | User browser |

### pfSense Port Forwarding (WAN → Docker Host)

| From Port | Protocol | Forward To | Purpose |
|-----------|----------|------------|---------|
| 443 | TCP | 192.168.100.102:443 | Dashboard external access |
| 1514 | TCP+UDP | 192.168.100.102:1514 | Remote agent connection |
| 55000 | TCP | 192.168.100.102:55000 | API external access |
| 9200 | TCP | 192.168.100.102:9200 | Indexer direct query |
| 514 | UDP | 192.168.100.102:514 | Syslog from pfSense |

---

## 2. Docker Compose Stack

> **File:** `docker-compose.yml`

### Networks & Volumes

```yaml
networks:
  soc-net:
    driver: bridge
    ipam:
      config:
        - subnet: ${DOCKER_SUBNET}    # 172.20.0.0/24

volumes:
  wazuh-data:
  indexer-data:
```

### Wazuh Manager Service

```yaml
wazuh.manager:
  image: wazuh/wazuh-manager:${WAZUH_VERSION}
  container_name: wazuh-manager
  restart: unless-stopped
  hostname: wazuh-manager
  ports:
    - '1514:1514/tcp'
    - '1514:1514/udp'
    - '1515:1515/tcp'
    - '514:514/udp'
    - '55000:55000/tcp'
  volumes:
    - ./wazuh/config/wazuh_manager.conf:/var/ossec/etc/ossec.conf:rw
    - ./wazuh/config/local_rules.xml:/var/ossec/etc/rules/local_rules.xml:rw
    - ./wazuh/config/local_decoders.xml:/var/ossec/etc/decoders/local_decoders.xml:rw
    - ./wazuh/data/logs:/var/ossec/logs:rw
    - ./wazuh/data/etc:/var/ossec/etc/shared:rw
    - ./certs:/etc/ssl:ro
    - ./wazuh/filebeat-run.sh:/etc/services.d/filebeat/run:ro
    - wazuh-data:/var/ossec/queue
  env_file:
    - ./.env
  environment:
    - INDEXER_URL=https://wazuh.indexer:9200
    - INDEXER_USERNAME=${INDEXER_USERNAME}
    - INDEXER_PASSWORD=${INDEXER_PASSWORD}
    - FILEBEAT_SSL_VERIFICATION_MODE=full
    - SSL_CERTIFICATE_AUTHORITIES=/etc/ssl/root-ca.pem
    - SSL_CERTIFICATE=/etc/ssl/wazuh-1.pem
    - SSL_KEY=/etc/ssl/wazuh-1-key.pem
    - VIRUSTOTAL_API_KEY=${VIRUSTOTAL_API_KEY}
  networks:
    soc-net:
      ipv4_address: 172.20.0.10
```

### Wazuh Indexer Service

```yaml
wazuh.indexer:
  image: wazuh/wazuh-indexer:${WAZUH_VERSION}
  container_name: wazuh-indexer
  restart: unless-stopped
  hostname: wazuh.indexer
  ports:
    - '9200:9200/tcp'
  volumes:
    - ./indexer/config/opensearch.yml:/usr/share/wazuh-indexer/opensearch.yml:ro
    - ./indexer/data:/var/lib/wazuh-indexer:rw
    - ./certs:/usr/share/wazuh-indexer/certs:ro
  environment:
    - 'OPENSEARCH_JAVA_OPTS=-Xms${INDEXER_HEAP_SIZE} -Xmx${INDEXER_HEAP_SIZE}'
    - INDEXER_PASSWORD=${INDEXER_PASSWORD}
    - bootstrap.memory_lock=true
  ulimits:
    memlock: { soft: -1, hard: -1 }
    nofile:  { soft: 65536, hard: 65536 }
  networks:
    soc-net:
      ipv4_address: 172.20.0.11
```

### Wazuh Dashboard Service

```yaml
wazuh.dashboard:
  image: wazuh/wazuh-dashboard:${WAZUH_VERSION}
  container_name: wazuh-dashboard
  restart: unless-stopped
  depends_on: [wazuh.indexer]
  ports:
    - '443:5601/tcp'
  volumes:
    - ./dashboard/config/opensearch_dashboards.yml:/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml:ro
    - ./certs:/usr/share/wazuh-dashboard/certs:ro
  env_file:
    - ./.env
  environment:
    - DASHBOARD_USERNAME=${DASHBOARD_USERNAME}
    - DASHBOARD_PASSWORD=${DASHBOARD_PASSWORD}
    - WAZUH_API_URL=https://wazuh.manager
    - SERVER_SSL_ENABLED=true
  networks:
    soc-net:
      ipv4_address: 172.20.0.12
```

> **Lưu ý:** `WAZUH_API_URL` không có port — mặc định là 55000. Không thêm `:55000` vào URL này.

### Suricata Service

```yaml
suricata:
  image: jasonish/suricata:latest
  container_name: suricata
  restart: unless-stopped
  network_mode: host
  cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]
  volumes:
    - ./suricata/config/suricata.yaml:/etc/suricata/suricata.yaml:rw
    - ./suricata/rules:/etc/suricata/rules:rw
    - ./suricata/logs:/var/log/suricata:rw
    - ./suricata/start.sh:/start.sh:ro
  command: /start.sh
```

---

## 3. Environment Variables (.env)

> **File:** `.env`

```env
# ── Wazuh ──────────────────────────────────────────────
WAZUH_VERSION=4.9.0
WAZUH_MANAGER_IP=0.0.0.0

# ── Wazuh Indexer (OpenSearch) ──────────────────────────
INDEXER_USERNAME=admin
INDEXER_PASSWORD=admin
INDEXER_HEAP_SIZE=1g

# ── Wazuh Dashboard ─────────────────────────────────────
DASHBOARD_USERNAME=admin
DASHBOARD_PASSWORD=admin

# ── VirusTotal ──────────────────────────────────────────
VIRUSTOTAL_API_KEY=6b11135c44a5dd582b70370d2dea969636e2eb274cf7f99c5451a47fee14401d

# ── Network (adjust to your host IP) ───────────────────
HOST_IP=192.168.100.102
PFSENSE_IP=192.168.100.1
DOCKER_SUBNET=172.20.0.0/24
```

> ⚠️ **Security:** Change all default passwords (`admin`/`admin`) before production use. The VirusTotal API key should also be kept secret.

---

## 4. Wazuh Manager Config

> **File:** `soc-lab/wazuh/config/wazuh_manager.conf`
> **Mount:** `/var/ossec/etc/ossec.conf`

```xml
<ossec_config>
  <!-- ── Syslog input from pfSense ────────────────────────── -->
  <remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>udp</protocol>
    <allowed-ips>192.168.100.1</allowed-ips>
    <local_ip>0.0.0.0</local_ip>
  </remote>

  <!-- ── Agent connections (TCP encrypted) ────────────────── -->
  <remote>
    <connection>secure</connection>
    <port>1514</port>
    <protocol>tcp</protocol>
    <local_ip>0.0.0.0</local_ip>
  </remote>

  <!-- ── VirusTotal Integration ────────────────────────────── -->
  <integration>
    <name>virustotal</name>
    <api_key>${VIRUSTOTAL_API_KEY}</api_key>
    <group>syscheck</group>
    <alert_format>json</alert_format>
  </integration>

  <!-- ── File Integrity Monitoring ─────────────────────────── -->
  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <directories check_all="yes" realtime="yes" report_changes="yes">
      /home,/etc,/var/ossec/etc
    </directories>
  </syscheck>

  <!-- ── Local Log Analysis ───────────────────────────────── -->
  <localfile>
    <log_format>syslog</log_format>
    <location>/var/ossec/logs/active-responses.log</location>
  </localfile>

  <!-- ── Agent Auto-Enrollment ────────────────────────────── -->
  <auth>
    <disabled>no</disabled>
    <port>1515</port>
    <use_source_ip>no</use_source_ip>
    <force>
      <enabled>yes</enabled>
    </force>
    <purge>yes</purge>
    <use_password>no</use_password>
    <limit_maxagents>yes</limit_maxagents>
  </auth>
</ossec_config>
```

### Configuration Details

| Block | Key Settings | Purpose |
|-------|-------------|---------|
| `<remote>` syslog | port=514, protocol=udp, allowed-ips=192.168.100.1 | Nhận firewall logs từ pfSense |
| `<remote>` secure | port=1514, protocol=tcp | Kênh liên lạc mã hóa với agents |
| `<integration>` | virustotal, group=syscheck, alert_format=json | Enrich file hash alerts |
| `<syscheck>` | frequency=43200, realtime=yes | FIM scan mỗi 12 giờ, real-time monitoring |
| `<auth>` | port=1515, use_source_ip=no | Cho phép agent đăng ký từ xa (kể cả sau NAT) |

---

## 5. Wazuh Indexer (OpenSearch) Config

> **File:** `soc-lab/indexer/config/opensearch.yml`
> **Mount:** `/usr/share/wazuh-indexer/opensearch.yml`

```yaml
cluster.name: wazuh-cluster
node.name: node-1
node.master: true
node.data: true

path.data: /var/lib/wazuh-indexer
path.logs: /var/log/wazuh-indexer

network.host: 0.0.0.0
http.port: 9200

discovery.type: single-node

# ES 7.x compatibility — allows Filebeat 7.x _type in bulk requests
compatibility:
  override_main_response_version: true

# SSL Transport
plugins.security.ssl.transport.pemcert_filepath: certs/node-1.pem
plugins.security.ssl.transport.pemkey_filepath: certs/node-1-key.pem
plugins.security.ssl.transport.pemtrustedcas_filepath: certs/root-ca.pem

# SSL HTTP (HTTPS for REST API)
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: certs/node-1.pem
plugins.security.ssl.http.pemkey_filepath: certs/node-1-key.pem
plugins.security.ssl.http.pemtrustedcas_filepath: certs/root-ca.pem

plugins.security.ssl.transport.enforce_hostname_verification: false
plugins.security.ssl.transport.resolve_hostname: false

# Admin certificate DN for authentication
plugins.security.authcz.admin_dn:
  - CN=admin,OU=Wazuh,O=Wazuh,L=California,C=US

plugins.security.nodes_dn:
  - CN=*

action.auto_create_index: "true"
bootstrap.memory_lock: true
```

### Key Configuration Notes

| Setting | Value | Why |
|---------|-------|-----|
| discovery.type | single-node | Lab environment — không cần cluster |
| compatibility.override_main_response_version | true | Cho phép Filebeat 7.x gửi _type parameter |
| plugins.security.ssl.http.enabled | true | Bắt buộc HTTPS cho mọi kết nối |
| plugins.security.authcz.admin_dn | CN=admin,... | Xác thực admin bằng SSL client certificate |
| bootstrap.memory_lock | true | Chống swap, critical for OpenSearch performance |
| OPENSEARCH_JAVA_OPTS | -Xms1g -Xmx1g | Heap 1GB (qua environment variable) |

---

## 6. Wazuh Dashboard Config

> **File:** `soc-lab/dashboard/config/opensearch_dashboards.yml`
> **Mount:** `/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml`

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

### Environment Overrides

Set via `docker-compose.yml` `environment:` block:

| Variable | Value | Purpose |
|----------|-------|---------|
| DASHBOARD_USERNAME | admin | Dashboard login user |
| DASHBOARD_PASSWORD | admin | Dashboard login password |
| WAZUH_API_URL | https://wazuh.manager | URL to Wazuh API (port 55000 mặc định) |
| SERVER_SSL_ENABLED | true | Bật HTTPS cho Dashboard |

> **Important:** `WAZUH_API_URL=https://wazuh.manager` (không có port) — Dashboard tự động thêm port 55000.

---

## 7. Filebeat Config

> **File:** `soc-lab/wazuh/config/filebeat.yml`
> **Mount:** `/etc/filebeat/filebeat.yml` (qua filebeat-run.sh)

```yaml
filebeat.modules:
  - module: wazuh
    alerts:
      enabled: true
    archives:
      enabled: false

setup.template.json.enabled: true
setup.template.overwrite: true
setup.template.json.path: '/etc/filebeat/wazuh-template.json'
setup.template.json.name: 'wazuh'
setup.ilm.enabled: false

output.elasticsearch:
  hosts: ['https://wazuh.indexer:9200']
  username: 'admin'
  password: 'admin'
  ssl.verification_mode: 'full'
  ssl.certificate_authorities: ['/etc/ssl/root-ca.pem']
  ssl.certificate: '/etc/ssl/wazuh-1.pem'
  ssl.key: '/etc/ssl/wazuh-1-key.pem'
  document_type: ""

logging.metrics.enabled: false

seccomp:
  default_action: allow
  syscalls:
  - action: allow
    names:
    - rseq
```

### Critical: `document_type: ""`

Dòng này **bắt buộc** cho OpenSearch 2.x compatibility. Filebeat 7.x mặc định gửi `_type` trong bulk request metadata — OpenSearch 2.x reject field này. Empty string `""` strip `_type` khỏi action line.

```json
// Before (sẽ bị reject):
{"index": {"_index": "wazuh-alerts", "_type": "wazuh"}}

// After (fixed):
{"index": {"_index": "wazuh-alerts"}}
```

---

## 8. Wazuh API Config

> **File:** `soc-lab/wazuh/config/api.yaml` (host only — **KHÔNG mounted** vào container)

```yaml
# Wazuh API configuration
host: 0.0.0.0
port: 55000

# Access control
access:
  max_login_attempts: 50
  max_request_per_minute: 300
  block_time: 300

# Cross-origin resource sharing
cors:
  enabled: yes
  source_route: "*"
  expose_headers: "*"
  allow_headers: "*"
  allow_credentials: yes
```

> **Note:** File này chỉ tồn tại trên host để tham khảo. Container dùng default `api.yaml` từ image. Muốn thay đổi API config thật, cần mount file này vào container hoặc exec vào container để sửa.

### API Authentication

- **Endpoint:** `POST /security/user/authenticate`
- **Default users:** `wazuh` / `wazuh-wui` (both admin role)
- **Password hash:** scrypt (lưu trong RBAC SQLite database)
- **Token:** JWT

**Test API:**
```bash
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"
```

---

## 9. Custom Rules & Decoders

### pfSense Decoder

> **File:** `soc-lab/wazuh/config/local_decoders.xml`
> **Mount:** `/var/ossec/etc/decoders/local_decoders.xml`

```xml
<decoder name="pfsense">
  <program_name>filterlog</program_name>
</decoder>
```

Nhận diện log từ pfSense `filterlog` process (firewall events gửi qua syslog).

### pfSense Detection Rules

> **File:** `soc-lab/wazuh/config/local_rules.xml`
> **Mount:** `/var/ossec/etc/rules/local_rules.xml`

```xml
<group name="pfsense,firewall,">
  <!-- Level 7: pfSense blocked traffic -->
  <rule id="100114" level="7">
    <if_sid>100111</if_sid>
    <match>block</match>
    <description>pfSense: Blocked traffic from $(srcip) to $(dstip)</description>
  </rule>

  <!-- Level 10: Authentication error (critical) -->
  <rule id="100115" level="10">
    <if_sid>100111</if_sid>
    <match>authentication error</match>
    <description>pfSense: Auth error from $(srcip)</description>
  </rule>
</group>
```

| Rule ID | Level | Match | Ý nghĩa |
|---------|-------|-------|---------|
| 100114 | 7 (Medium) | `block` trong pfSense log | Kết nối bị firewall chặn |
| 100115 | 10 (Critical) | `authentication error` | Brute-force hoặc credential stuffing |

---

## 10. Suricata IDS Config

### suricata.yaml

> **File:** `soc-lab/suricata/config/suricata.yaml`
> **Mount:** `/etc/suricata/suricata.yaml`

```yaml
%YAML 1.1
---
# Network interface
af-packet:
  - interface: lo
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes
    ring-size: 2048
    rollover: yes

vars:
  address-groups:
    HOME_NET: "[192.168.1.0/24,192.168.100.0/24,172.20.0.0/24,10.0.0.0/8]"
    EXTERNAL_NET: "!$HOME_NET"
    DNS_SERVERS: "$HOME_NET"
    SMTP_SERVERS: "$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    SQL_SERVERS: "$HOME_NET"
    TELNET_SERVERS: "$HOME_NET"
  port-groups:
    HTTP_PORTS: "80,443,8080,8443"
    SHELLCODE_PORTS: "!80"
    ORACLE_PORTS: "1521"
    SSH_PORTS: "22"

app-layer:
  protocols:
    modbus: { enabled: yes }
    dnp3:   { enabled: yes }

outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert: { payload: yes, metadata: yes }
        - dns
        - http: { extended: yes }
        - tls: { session-fields: yes }
        - ssh
        - smtp
        - flow
        - netflow
        - stats

  - fast:
      enabled: yes
      filename: fast.log
      append: yes

  - stats:
      enabled: yes
      filename: stats.log
      interval: 30

logging:
  default-log-level: info
  outputs:
    - level: info
      type: file
      filename: suricata.log

rule-files:
  - /etc/suricata/rules/*.rules
```

### start.sh (Entrypoint)

> **File:** `soc-lab/suricata/start.sh`
> **Mount:** `/start.sh`

```bash
#!/bin/bash
set -e

RULES_DIR="/etc/suricata/rules"
UPDATED_RULES="/var/lib/suricata/rules/suricata.rules"

# Run suricata-update to fetch/enable rules
suricata-update

# Copy updated rules to the Suricata config directory
cp -f "$UPDATED_RULES" "$RULES_DIR/suricata.rules"
cp -f /var/lib/suricata/rules/classification.config "$RULES_DIR/"

exec suricata -c /etc/suricata/suricata.yaml -i lo --af-packet
```

> **⚠️ KNOWN ISSUE:** Suricata dùng interface `lo` (loopback). Trên môi trường thật, cần đổi thành interface mạng thật (vd: `eth0`) để bắt được traffic thực tế.
> - Sửa trong `start.sh`: đổi `-i lo` thành `-i eth0` (hoặc tên interface phù hợp)
> - Sửa trong `suricata.yaml`: đổi `interface: lo` thành `interface: eth0`

### HOME_NET Configuration

Suricata giám sát các dải mạng:

| Subnet | Description |
|--------|-------------|
| 192.168.1.0/24 | Reserved / phụ |
| 192.168.100.0/24 | Mạng chính (Docker host, pfSense) |
| 172.20.0.0/24 | Docker bridge network |
| 10.0.0.0/8 | pfSense LAN network |

---

## 11. pfSense Integration Config

### Syslog Forwarding

Trên pfSense WebGUI (`https://192.168.100.1`):

**Status → System Logs → Settings:**

| Setting | Value |
|---------|-------|
| Enable Remote Logging | ☑ ON |
| Remote log servers | 192.168.100.102:514 |
| System Events | ☑ |
| Firewall Events | ☑ |
| DNS Events | ☑ |
| DHCP Events | ☑ |
| VPN Events | ☑ |

### DNS Resolver (Unbound) Host Overrides

**Services → DNS Resolver → Host Overrides:**

| Host | Domain | IP |
|------|--------|----|
| wazuh.manager | soc-lab.local | 192.168.100.102 |
| wazuh.indexer | soc-lab.local | 192.168.100.102 |
| wazuh.dashboard | soc-lab.local | 192.168.100.102 |

### Outbound NAT (Manual Hybrid)

**Firewall → NAT → Outbound:**

| Interface | Source | NAT IP |
|-----------|--------|--------|
| WAN | 172.20.0.0/24 | 192.168.100.1 |
| WAN | 10.0.1.0/24 | 192.168.100.1 |

### Firewall Rules

**WAN rules:**

| Protocol | Source | Port | Destination | Description |
|----------|--------|------|-------------|-------------|
| TCP | 192.168.100.102 | * | WAN net | Docker host outbound |

**LAN rules (auto-created):**

| Protocol | Source | Port | Destination | Description |
|----------|--------|------|-------------|-------------|
| IPv4 * | 10.0.1.0/24 | * | * | LAN outbound |

**Port Forwards (Firewall → NAT → Port Forward):**

| Protocol | Source | Dest. Port | Redirect IP | Redirect Port |
|----------|--------|-----------|-------------|---------------|
| TCP | * | 443 | 192.168.100.102 | 443 |
| TCP | * | 1514 | 192.168.100.102 | 1514 |
| UDP | * | 1514 | 192.168.100.102 | 1514 |
| TCP | * | 55000 | 192.168.100.102 | 55000 |
| TCP | * | 9200 | 192.168.100.102 | 9200 |
| TCP | * | 514 | 192.168.100.102 | 514 |

---

## 12. Agent Scripts

> Tất cả scripts trong `soc-lab/wazuh/scripts/` chạy **bên trong container** `wazuh-manager`.

### do_all.py — Full Agent Setup

**Chức năng:** Xóa agent cũ + tạo key mới + ghi vào global.db + client.keys

```python
#!/usr/bin/env python3
"""Clean MSI agent from global.db, add fresh key, clear client.keys"""
import sqlite3, os, hashlib, time

db_path = "/var/ossec/queue/db/global.db"

# Kill wazuh-db to release lock
os.system("killall wazuh-db 2>/dev/null")
time.sleep(2)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Clean old MSI
cur.execute('DELETE FROM agent WHERE "name" = \'MSI\'')
print("Deleted", cur.rowcount, "MSI agent(s)")

# Generate new key
key = hashlib.sha256(os.urandom(64)).hexdigest()
print("New key:", key)

# Get max ID
cur.execute('SELECT MAX(CAST("id" AS INTEGER)) FROM agent')
max_id = cur.fetchone()[0] or 0
new_id = max_id + 1

# Insert new agent
now = int(time.time())
cur.execute('''
    INSERT INTO agent ("id","name","ip","register_ip","internal_key","date_add",
        "last_keepalive","group","group_hash","group_sync_status","sync_status",
        "connection_status","disconnection_time","group_config_status","status_code")
    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
''', (new_id, 'MSI', 'any', 'any', key, now, now, 'default', '',
      'synced', 'synced', 'active', 0, 'synced', 0))
conn.commit()
conn.close()
print("Agent MSI added with ID", new_id)

# Write client.keys
with open('/var/ossec/etc/client.keys', 'w') as f:
    f.write(f"{new_id} MSI any {key}\n")
print("client.keys written")
print("\n=== COPY THIS KEY ===")
print(f"{new_id} MSI any {key}")
```

### add_agent.py — Add Agent Only

```python
#!/usr/bin/env python3
import sqlite3, os, hashlib, time

db_path = "/var/ossec/queue/db/global.db"
key = hashlib.sha256(os.urandom(64)).hexdigest()
print("Generated key:", key)

with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute('SELECT MAX(CAST("id" AS INTEGER)) FROM agent')
    max_id = cur.fetchone()[0]
    new_id = (max_id or 0) + 1

    now = int(time.time())
    cur.execute('''
        INSERT INTO agent ("id","name","ip","register_ip","internal_key",
            "date_add","last_keepalive","group","group_hash",
            "group_sync_status","sync_status","connection_status",
            "disconnection_time","group_config_status","status_code")
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', (new_id, 'MSI', 'any', 'any', key, now, now, 'default', '',
          'synced', 'synced', 'active', 0, 'synced', 0))
    conn.commit()

with open('/var/ossec/etc/client.keys', 'w') as f:
    f.write(f"{new_id} MSI any {key}\n")
print(f"Agent MSI added with ID {new_id}, Key: {key}")
```

### clean_agent.py — Remove Agent Only

```python
#!/usr/bin/env python3
import sqlite3, os

db_path = "/var/ossec/queue/db/global.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# List all agents
cur.execute("PRAGMA table_info(agent)")
columns = ['"' + col[1] + '"' for col in cur.fetchall()]
query = "SELECT " + ",".join(columns) + " FROM agent"
cur.execute(query)
print("Current agents:", cur.fetchall())

# Delete MSI
cur.execute('DELETE FROM agent WHERE "name" = \'MSI\'')
print("Deleted", cur.rowcount, "agent(s)")
conn.commit()

# Clear client.keys
os.system("> /var/ossec/etc/client.keys")
print("Cleared client.keys")
```

### Usage

```bash
# Copy và chạy bên trong container
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'

# Sau đó restart manager và remove .restart file
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'
```

---

## 13. Filebeat Startup Patch

> **File:** `soc-lab/wazuh/filebeat-run.sh`
> **Mount:** `/etc/services.d/filebeat/run`

```bash
#!/usr/bin/with-contenv sh
# Patches filebeat.yml before starting Filebeat.
# Fixes: "Action/metadata line [1] contains an unknown parameter [_type]"
# when connecting to OpenSearch 2.x (which removed _type support).
set -e

FB_CONF="/etc/filebeat/filebeat.yml"

# Apply the fix only if document_type is not already present
if grep -q '^  document_type:' "$FB_CONF" 2>/dev/null; then
    echo >&2 "[filebeat-patch] document_type already set"
else
    sed -i '/^output\.elasticsearch:/a\  document_type: ""' "$FB_CONF"
    echo >&2 "[filebeat-patch] Added document_type: \"\" to output.elasticsearch"
fi

echo >&2 "[filebeat-patch] Starting Filebeat with patched config"
exec /usr/share/filebeat/bin/filebeat -e -c /etc/filebeat/filebeat.yml \
    -path.home /usr/share/filebeat \
    -path.config /etc/filebeat \
    -path.data /var/lib/filebeat \
    -path.logs /var/log/filebeat
```

Script này tự động patch `document_type: ""` vào filebeat.yml mỗi khi container start. Đảm bảo fix tồn tại qua restart.

---

## 14. SSL Certificates

> **Directory:** `soc-lab/certs/`

### Certificate Files

| File | Used By | Purpose |
|------|---------|---------|
| `root-ca.pem` | All components | Root Certificate Authority |
| `root-ca.key` | CA only | Root CA private key |
| `wazuh-1.pem` | wazuh.manager | Filebeat → Indexer client cert |
| `wazuh-1-key.pem` | wazuh.manager | Filebeat client key |
| `node-1.pem` | wazuh.indexer | OpenSearch HTTPS cert |
| `node-1-key.pem` | wazuh.indexer | OpenSearch HTTPS key |
| `admin.pem` | Admin tools | Admin DN authentication |
| `admin-key.pem` | Admin tools | Admin DN private key |

### Certificate Subjects

```
Root CA:     CN=Wazuh, OU=Wazuh, O=Wazuh, L=California, C=US
Admin cert:  CN=admin, OU=Wazuh, O=Wazuh, L=California, C=US
Node cert:   CN=node-1, OU=Wazuh, O=Wazuh, L=California, C=US
```

### Generate New Certificates

Nếu cần tạo lại certificates:
```bash
cd soc-lab
curl -sO https://packages.wazuh.com/4.9/wazuh-certs-tool.sh
curl -sO https://packages.wazuh.com/4.9/config.yml
# Sửa config.yml cho đúng IP:
#   nodes.indexer[0].ip = 172.20.0.11
#   nodes.manager[0].ip = 172.20.0.10
#   nodes.dashboard[0].ip = 172.20.0.12
bash wazuh-certs-tool.sh -A
cp -r wazuh-certificates/* ./certs/
```

---

## 15. Agent Configuration (Windows)

> **File:** `C:\Program Files (x86)\ossec-agent\ossec.conf`
> Đây là cấu hình **thực tế** từ Windows agent.

### Install Windows Agent

```powershell
# PowerShell (Admin)
Invoke-WebRequest -Uri 'https://packages.wazuh.com/4.x/windows/wazuh-agent-4.9.0-1.msi' `
  -OutFile $env:tmp\wazuh-agent.msi

msiexec.exe /i $env:tmp\wazuh-agent.msi /q `
  WAZUH_MANAGER='192.168.100.102' `
  WAZUH_REGISTRATION_SERVER='192.168.100.102' `
  WAZUH_AGENT_NAME='MSI'

NET START WazuhSvc
```

### Complete Windows ossec.conf

```xml
<!--
  Wazuh - Agent - Default configuration for Windows
  More info at: https://documentation.wazuh.com
-->

<ossec_config>

  <!-- ═══════════════════════════════════════════════════════
       AGENT CONNECTION
       ═══════════════════════════════════════════════════════ -->
  <client>
    <server>
      <address>192.168.100.102</address>    <!-- Manager IP (Docker host) -->
      <port>1514</port>
      <protocol>tcp</protocol>
    </server>
    <crypto_method>aes</crypto_method>
    <notify_time>10</notify_time>
    <time-reconnect>60</time-reconnect>
    <auto_restart>yes</auto_restart>
  </client>

  <!-- Agent buffer: chống mất log khi mất kết nối -->
  <client_buffer>
    <disabled>no</disabled>
    <queue_size>5000</queue_size>
    <events_per_second>500</events_per_second>
  </client_buffer>

  <!-- ═══════════════════════════════════════════════════════
       LOG ANALYSIS — Event Channels & Files
       ═══════════════════════════════════════════════════════ -->

  <!-- Windows Application event log -->
  <localfile>
    <location>Application</location>
    <log_format>eventchannel</log_format>
  </localfile>

  <!-- Windows Security event log (filtered for critical events) -->
  <localfile>
    <location>Security</location>
    <log_format>eventchannel</log_format>
    <query>Event/System[EventID != 5145 and EventID != 5156 and EventID != 5447 and
      EventID != 4656 and EventID != 4658 and EventID != 4663 and EventID != 4660 and
      EventID != 4670 and EventID != 4690 and EventID != 4703 and EventID != 4907 and
      EventID != 5152 and EventID != 5157]</query>
  </localfile>

  <!-- Suricata EVE JSON (mounted từ Docker host) -->
  <localfile>
    <log_format>json</log_format>
    <location>D:\dev\is_security_group1\soc-lab\suricata\logs\eve.json</location>
  </localfile>

  <!-- Windows System event log -->
  <localfile>
    <location>System</location>
    <log_format>eventchannel</log_format>
  </localfile>

  <!-- Sysmon event log -->
  <localfile>
    <location>Microsoft-Windows-Sysmon/Operational</location>
    <log_format>eventchannel</log_format>
  </localfile>

  <!-- Active responses log -->
  <localfile>
    <location>active-response\active-responses.log</location>
    <log_format>syslog</log_format>
  </localfile>

  <!-- ═══════════════════════════════════════════════════════
       POLICY MONITORING
       ═══════════════════════════════════════════════════════ -->
  <rootcheck>
    <disabled>no</disabled>
    <windows_apps>./shared/win_applications_rcl.txt</windows_apps>
    <windows_malware>./shared/win_malware_rcl.txt</windows_malware>
  </rootcheck>

  <!-- Security Configuration Assessment (disabled) -->
  <sca>
    <enabled>no</enabled>
    <scan_on_start>no</scan_on_start>
    <interval>12h</interval>
    <skip_nfs>yes</skip_nfs>
  </sca>

  <!-- ═══════════════════════════════════════════════════════
       FILE INTEGRITY MONITORING (FIM)
       ═══════════════════════════════════════════════════════ -->
  <syscheck>
    <!-- User folders (real-time) -->
    <directories check_all="yes" report_changes="yes" realtime="yes">
      C:\Users\CYBORG\Desktop
    </directories>
    <directories check_all="yes" report_changes="yes" realtime="yes">
      C:\Users\CYBORG\Downloads
    </directories>

    <disabled>no</disabled>
    <frequency>43200</frequency>    <!-- 12 giờ -->

    <!-- Critical Windows binaries -->
    <directories recursion_level="0" restrict="regedit.exe$|system.ini$|win.ini$">%WINDIR%</directories>
    <directories recursion_level="0" restrict="at.exe$|attrib.exe$|cacls.exe$|cmd.exe$|eventcreate.exe$|ftp.exe$|lsass.exe$|net.exe$|net1.exe$|netsh.exe$|reg.exe$|regedt32.exe|regsvr32.exe|runas.exe|sc.exe|schtasks.exe|sethc.exe|subst.exe$">%WINDIR%\SysNative</directories>
    <directories recursion_level="0">%WINDIR%\SysNative\drivers\etc</directories>
    <directories recursion_level="0" restrict="WMIC.exe$">%WINDIR%\SysNative\wbem</directories>
    <directories recursion_level="0" restrict="powershell.exe$">%WINDIR%\SysNative\WindowsPowerShell\v1.0</directories>
    <directories recursion_level="0" restrict="winrm.vbs$">%WINDIR%\SysNative</directories>

    <!-- 32-bit programs -->
    <directories recursion_level="0" restrict="at.exe$|attrib.exe$|cacls.exe$|cmd.exe$|eventcreate.exe$|ftp.exe$|lsass.exe$|net.exe$|net1.exe$|netsh.exe$|reg.exe$|regedit.exe$|regedt32.exe$|regsvr32.exe$|runas.exe$|sc.exe$|schtasks.exe$|sethc.exe$|subst.exe$">%WINDIR%\System32</directories>
    <directories recursion_level="0">%WINDIR%\System32\drivers\etc</directories>
    <directories recursion_level="0" restrict="WMIC.exe$">%WINDIR%\System32\wbem</directories>
    <directories recursion_level="0" restrict="powershell.exe$">%WINDIR%\System32\WindowsPowerShell\v1.0</directories>
    <directories recursion_level="0" restrict="winrm.vbs$">%WINDIR%\System32</directories>

    <!-- Startup folder (real-time) -->
    <directories realtime="yes">%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup</directories>
    <ignore>%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs\Startup\desktop.ini</ignore>
    <ignore type="sregex">.log$|.htm$|.jpg$|.png$|.chm$|.pnf$|.evtx$</ignore>

    <!-- Windows registry monitoring -->
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\batfile</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\cmdfile</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\comfile</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\exefile</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\piffile</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\AllFilesystemObjects</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\Directory</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Classes\Folder</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Classes\Protocols</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Policies</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Security</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Internet Explorer</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\Session Manager\KnownDLLs</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\SecurePipeServers\winreg</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnce</windows_registry>
    <windows_registry>HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnceEx</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\URL</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Policies</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\Windows</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Windows NT\CurrentVersion\Winlogon</windows_registry>
    <windows_registry arch="both">HKEY_LOCAL_MACHINE\Software\Microsoft\Active Setup\Installed Components</windows_registry>

    <!-- Registry ignores -->
    <registry_ignore>HKEY_LOCAL_MACHINE\Security\Policy\Secrets</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\Security\SAM\Domains\Account\Users</registry_ignore>
    <registry_ignore type="sregex">\Enum$</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\AppCs</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\PortKeywords\DHCP</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\PortKeywords\IPTLSIn</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\PortKeywords\IPTLSOut</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\PortKeywords\RPC-EPMap</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\MpsSvc\Parameters\PortKeywords\Teredo</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\PolicyAgent\Parameters\Cache</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\RunOnceEx</registry_ignore>
    <registry_ignore>HKEY_LOCAL_MACHINE\System\CurrentControlSet\Services\ADOVMPPackage\Final</registry_ignore>

    <!-- ACL checking frequency (seconds) -->
    <windows_audit_interval>60</windows_audit_interval>
    <process_priority>10</process_priority>
    <max_eps>50</max_eps>

    <!-- DB sync -->
    <synchronization>
      <enabled>yes</enabled>
      <interval>5m</interval>
      <max_eps>10</max_eps>
    </synchronization>
  </syscheck>

  <!-- ═══════════════════════════════════════════════════════
       SYSTEM INVENTORY (syscollector)
       ═══════════════════════════════════════════════════════ -->
  <wodle name="syscollector">
    <disabled>yes</disabled>
    <interval>1h</interval>
    <scan_on_start>yes</scan_on_start>
    <hardware>yes</hardware>
    <os>yes</os>
    <network>yes</network>
    <packages>yes</packages>
    <ports all="no">yes</ports>
    <processes>yes</processes>
    <synchronization>
      <max_eps>10</max_eps>
    </synchronization>
  </wodle>

  <!-- ═══════════════════════════════════════════════════════
       CIS POLICIES EVALUATION
       ═══════════════════════════════════════════════════════ -->
  <wodle name="cis-cat">
    <disabled>yes</disabled>
    <timeout>1800</timeout>
    <interval>1d</interval>
    <scan-on-start>yes</scan-on-start>
    <java_path>\\server\jre\bin\java.exe</java_path>
    <ciscat_path>C:\cis-cat</ciscat_path>
  </wodle>

  <!-- ═══════════════════════════════════════════════════════
       OSQUERY INTEGRATION
       ═══════════════════════════════════════════════════════ -->
  <wodle name="osquery">
    <disabled>yes</disabled>
    <run_daemon>yes</run_daemon>
    <bin_path>C:\Program Files\osquery\osqueryd</bin_path>
    <log_path>C:\Program Files\osquery\log\osqueryd.results.log</log_path>
    <config_path>C:\Program Files\osquery\osquery.conf</config_path>
    <add_labels>yes</add_labels>
  </wodle>

  <!-- ═══════════════════════════════════════════════════════
       ACTIVE RESPONSE
       ═══════════════════════════════════════════════════════ -->
  <active-response>
    <disabled>no</disabled>
    <ca_store>wpk_root.pem</ca_store>
    <ca_verification>yes</ca_verification>
  </active-response>

  <!-- Internal log format -->
  <logging>
    <log_format>plain</log_format>
  </logging>

</ossec_config>
```

### Key Configuration Highlights

| Module | Status | Purpose |
|--------|--------|---------|
| **Client connection** | ✅ Active | AES encryption, reconnect 60s, auto-restart |
| **Client buffer** | ✅ Active | Queue 5000 events, 500 EPS |
| **Security event log** | ✅ Active | Filtered: trừ các EventID ồn (5145, 5156, etc.) |
| **Suricata EVE JSON** | ✅ Active | Đọc từ host path `D:\dev\is_security_group1\soc-lab\suricata\logs\eve.json` |
| **Sysmon** | ✅ Active | `Microsoft-Windows-Sysmon/Operational` |
| **FIM** | ✅ Active | Desktop, Downloads real-time + Windows binaries + Registry |
| **Rootcheck** | ✅ Active | Malware + ứng dụng không mong muốn |
| **Syscollector** | ❌ Disabled | Inventory (hardware, OS, network, packages) |
| **CIS-CAT** | ❌ Disabled | CIS policy evaluation |
| **Osquery** | ❌ Disabled | Osquery integration |
| **SCA** | ❌ Disabled | Security configuration assessment |

### Restart Agent After Changes
```powershell
Restart-Service -Name WazuhSvc
```

---

## 16. Deployment Checklist

### Pre-Deployment

- [ ] Docker Engine ≥ 24.x installed (`docker --version`)
- [ ] Docker Compose v2 plugin installed (`docker compose version`)
- [ ] `vm.max_map_count` ≥ 262144 (`sysctl vm.max_map_count`)
  - Fix: `sudo sysctl -w vm.max_map_count=262144`
- [ ] Project directory structure created
- [ ] `.env` file configured with correct IPs and passwords
- [ ] SSL certificates generated in `certs/`
- [ ] Ports 514, 1514-1515, 55000, 9200, 443 không bị chiếm dụng

### Deployment

- [ ] `docker compose up -d` — stack khởi động
- [ ] Indexer health: `curl -sk https://localhost:9200/_cluster/health`
- [ ] Manager daemons: `docker exec wazuh-manager /var/ossec/bin/wazuh-control status`
- [ ] API accessible: `curl -k -u wazuh-wui:wazuh-wui -X POST "https://localhost:55000/security/user/authenticate"`
- [ ] Dashboard accessible: `curl -sk https://192.168.100.102:443/status`

### Integration

- [ ] pfSense syslog forwarding configured → Wazuh receives firewall logs
- [ ] pfSense DNS host overrides added
- [ ] pfSense Outbound NAT includes Docker subnet
- [ ] pfSense port forwards created
- [ ] Windows Wazuh agent installed and connected (Status: Active)
- [ ] Suricata running and generating alerts
- [ ] VirusTotal API key configured

### Post-Deployment

- [ ] Admin passwords changed from defaults
- [ ] Dashboard WebGUI limited to LAN (optional)
- [ ] SSH WAN access disabled on pfSense
- [ ] Config backup created
- [ ] Firewall logs reviewed

---

## 17. Differences from Reference Guides

So sánh giữa DOCX hướng dẫn tham khảo và dự án hiện tại:

| Hạng mục | DOCX Reference | Dự Án Hiện Tại | ✅ Dùng |
|-----------|---------------|----------------|---------|
| **WAZUH_API_URL** | `https://wazuh.manager:55000` (có port) | `https://wazuh.manager` (không port) | Dự án |
| **Certs mount (manager)** | `./certs/root-ca.pem:/etc/ssl/root-ca.pem` (1 file) | `./certs:/etc/ssl:ro` (cả thư mục) | Dự án |
| **Agent auth block** | Không có | Có `<auth>` với đầy đủ options | Dự án |
| **filebeat-run.sh** | Không có | Có patch startup script | Dự án |
| **local_decoders.xml** | Không có | Có custom pfSense decoder | Dự án |
| **Suricata entrypoint** | `suricata-update && suricata -c ... -i eth0` | `start.sh` với `-i lo` | Dự án (cần fix interface) |
| **Agent name** | `MyWindowsPC` | `MSI` | Dự án |
| **.env INDEXER_PASSWORD** | `SecureP@ss1234!` | `admin` | Dự án |
| **filebeat.yml** | Không mount riêng | Mount và patch đầy đủ | Dự án |
| **opensearch.yml admin_dn** | Không đề cập | `CN=admin,OU=Wazuh,...` | Dự án |
| **Dashboard env vars** | Thiếu `DASHBOARD_USERNAME/PASSWORD` | Có đầy đủ | Dự án |
| **Ngoài ra từ DOCX:** | Hướng dẫn cài Suricata trên Windows, Sysmon, SSH brute-force sim | Đã bổ sung SSH brute-force, Sysmon, Suricata Win | ✅ Đã bổ sung |

### Identified Issues in Current Project (từ so sánh)

| Issue | File | Current | Should Be |
|-------|------|---------|-----------|
| Suricata interface loopback | `start.sh`, `suricata.yaml` | `-i lo` | `-i eth0` (hoặc interface thật) |
| api.yaml không mounted | `docker-compose.yml` | Không có mount | Muốn chỉnh API config trong container cần thêm mount |
| Dashboard WAZUH_API_URL format | `docker-compose.yml` | `https://wazuh.manager` | Không port — **đúng**, nhưng dễ gây nhầm lẫn |

---

## 18. Quick Command Reference

### Stack Management

| Task | Command |
|------|---------|
| Start all services | `cd soc-lab && docker compose up -d` |
| Stop all services | `cd soc-lab && docker compose down` |
| Restart manager | `docker compose restart wazuh.manager` |
| Restart dashboard | `docker compose restart wazuh.dashboard` |
| View logs (all) | `docker compose logs -f` |
| View logs (manager) | `docker compose logs -f wazuh.manager` |
| View logs (suricata) | `docker compose logs -f suricata` |

### Health Checks

| Task | Command |
|------|---------|
| Container status | `docker compose ps` |
| Manager daemons | `docker exec wazuh-manager /var/ossec/bin/wazuh-control status` |
| Agent list | `docker exec wazuh-manager /var/ossec/bin/agent_control -l` |
| Indexer health | `curl -sk https://192.168.100.102:9200/_cluster/health` |
| API test | `curl -k -u wazuh-wui:wazuh-wui -X POST "https://192.168.100.102:55000/security/user/authenticate"` |
| Dashboard status | `curl -sk https://192.168.100.102:443/status` |

### Inside Containers

| Task | Command |
|------|---------|
| Exec into manager | `docker exec -it wazuh-manager bash` |
| Exec into indexer | `docker exec -it wazuh-indexer bash` |
| Exec into dashboard | `docker exec -it wazuh-dashboard bash` |
| View alerts | `docker exec wazuh-manager tail -f /var/ossec/logs/alerts/alerts.log` |
| View API log | `docker exec wazuh-manager tail -f /var/ossec/logs/api.log` |

### Agent Management

| Task | Command |
|------|---------|
| Setup agent key | `docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/ && docker exec wazuh-manager sh -c 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'` |
| Restart manager | `docker exec wazuh-manager /var/ossec/bin/wazuh-control restart && sleep 2 && docker exec wazuh-manager rm -f /var/ossec/var/run/.restart` |

### Resource Usage

| Task | Command |
|------|---------|
| Container stats | `docker stats` |
| Indexer disk usage | `du -sh soc-lab/indexer/data/` |
| Wazuh logs size | `du -sh soc-lab/wazuh/data/logs/` |

---

---

## 19. SSH Brute Force — Simulation & Detection

> **⚠️ CHỈ THỰC HIỆN TRONG LAB ENVIRONMENT!** Không tấn công hệ thống ngoài!

Module này hướng dẫn mô phỏng tấn công brute-force SSH từ Kali Linux vào Windows target, và phát hiện trên Wazuh Dashboard.

### 19.1 Architecture

```
┌──────────────────┐          Brute Force SSH           ┌──────────────────┐
│  Kali Linux VM   │ ──── hydra -l dell -P pass.txt ──▶ │  Windows Target  │
│  (Attacker)      │       ssh://192.168.100.102         │  (Docker Host)   │
└──────────────────┘                                     └────────┬─────────┘
                                                                  │
                                                          Event ID 4625
                                                                  ▼
                                                         ┌──────────────────┐
                                                         │  Wazuh Manager   │
                                                         │  Rule Level 10   │
                                                         └──────────────────┘
```

### 19.2 Chuẩn Bị Target — Enable OpenSSH Server trên Windows (Docker Host)

Mở **PowerShell (Admin)** trên máy chạy Docker:

```powershell
# Cài OpenSSH Server
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start service
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic

# Kiểm tra
Get-Service sshd
# Phải thấy: Status = Running
```

### 19.3 Chuẩn Bị Attacker — Kali Linux VM

#### Tạo Password List

Trên Kali Linux:

```bash
# Tạo file passwords.txt
cat > passwords.txt << EOF
admin
password
123456
test123
YourRealPassword   ← Thêm password đúng để test thành công
EOF
```

#### Chạy Hydra Attack

```bash
# Syntax:
hydra -l <username> -P passwords.txt ssh://<target_ip>

# Ví dụ thực tế (thay 'dell' bằng username thật trên Windows target):
hydra -l dell -P passwords.txt ssh://192.168.100.102

# -l = username cụ thể (biết trước)
# -L = file chứa list username (không biết trước)
# -P = file chứa list password
```

### 19.4 Phát Hiện Trên Wazuh Dashboard

1. Vào **Wazuh Dashboard** → **Threat Hunting**
2. Filter: `data.win.system.eventID: 4625`
3. Phải thấy nhiều **Failed logon attempts** từ IP Kali

| Field | Value | Ý Nghĩa |
|-------|-------|---------|
| Event ID | 4625 | Failed logon attempt |
| failureReason | %%2313 | Unknown username or bad password |
| logonType | 8 | NetworkCleartext (SSH) |
| processName | sshd.exe | SSH daemon xử lý request |
| rule.level | 10+ (nếu nhiều lần) | Brute force detected! |

### 19.5 Defensive Countermeasures

| Biện Pháp | Mô Tả | Mức Ưu Tiên |
|-----------|-------|-------------|
| Strong password | >12 ký tự, phức tạp | 🔴 Critical |
| MFA | Multi-Factor Authentication | 🔴 Critical |
| Rate-limiting | Giới hạn số lần đăng nhập sai | 🟡 Medium |
| Account lockout | Tự động khóa sau N lần fail | 🟡 Medium |
| SSH key | Dùng SSH key thay vì password | 🟡 Medium |
| Wazuh monitoring | Theo dõi Dashboard thường xuyên | 🟢 Low |

### 19.6 Wazuh Detection Rule

Wazuh tự động phát hiện brute-force qua rule mặc định:

- **Event ID 4625** → Windows security event: failed logon
- Nhiều lần fail từ cùng IP trong thời gian ngắn → **rule.level escalation** lên 10+
- Có thể tạo custom rule để tăng độ nhạy:

```xml
<rule id="100200" level="10">
  <if_group>windows|sysmon</if_group>
  <field name="win.system.eventID">4625</field>
  <description>SSH Brute Force: Multiple failed logon attempts từ $(srcip)</description>
  <options>no_full_log</options>
  <group>authentication_failure,brute_force,ssh</group>
</rule>
```

---

---

## 20. Sysmon Log Ingestion

> **Sysmon (System Monitor)** — Công cụ của Microsoft Sysinternals, ghi lại chi tiết hoạt động hệ thống: process creation, network connections, file changes, registry modifications.

### 20.1 Download & Install Sysmon

Tải Sysmon từ [Microsoft Sysinternals](https://docs.microsoft.com/sysinternals/downloads/sysmon).

```powershell
# PowerShell (Admin) trên Windows Agent

# Giải nén Sysmon.zip, cd vào thư mục đã giải nén

# Cách 1: Cài với default config
.\sysmon.exe -i -accepteula

# Cách 2 (Khuyên dùng): Cài với SwiftOnSecurity config
# Download sysmon-config.xml từ:
# https://github.com/SwiftOnSecurity/sysmon-config
.\sysmon.exe -i sysmonconfig.xml -accepteula
```

### 20.2 Kiểm Tra Sysmon Running

```powershell
Get-Service Sysmon
# Phải thấy: Status = Running

# Xem events trong Event Viewer:
# Applications and Services Logs → Microsoft → Windows → Sysmon → Operational
```

### 20.3 Wazuh Agent Config (ossec.conf)

Phần này đã được cấu hình sẵn trong **Section 15** (Windows Agent Config). Wazuh Agent thu thập Sysmon logs qua event channel:

```xml
<localfile>
  <location>Microsoft-Windows-Sysmon/Operational</location>
  <log_format>eventchannel</log_format>
</localfile>
```

### 20.4 Xem Sysmon Events trên Wazuh Dashboard

1. Vào **Wazuh Dashboard** → **Threat Hunting**
2. Filter: `data.win.system.channel: Microsoft-Windows-Sysmon/Operational`
3. Phải thấy events từ Sysmon

### 20.5 Key Sysmon Event IDs

| Event ID | Tên | Mô Tả | Giá trị |
|----------|-----|-------|---------|
| 1 | Process Create | Tiến trình mới được tạo | Phát hiện thực thi mã độc |
| 3 | Network Connect | Kết nối mạng được tạo | Phát hiện C2 beaconing |
| 7 | Image Loaded | DLL được load vào process | Phát hiện DLL injection |
| 11 | File Created | File được tạo mới | Phát hiện malware drop |
| 13 | Registry Value Set | Registry thay đổi | Phát hiện persistence |

### 20.6 Restart Wazuh Agent Sau Khi Config

```powershell
Restart-Service -Name WazuhSvc
```

---

## 21. Suricata IDS trên Windows

> Hướng dẫn cài đặt và cấu hình Suricata IDS chạy trực tiếp trên Windows (không qua Docker), gửi log về Wazuh Manager qua Wazuh Agent.

### 21.1 Download & Install Suricata

1. Vào [suricata.io/download](https://suricata.io/download/)
2. Download Windows installer (`.msi`)
3. Cài đặt với default settings

```
C:\Program Files\Suricata\
├── suricata.exe      ← executable
├── suricata.yaml     ← config file
├── rules\            ← rule files
└── log\              ← log output (eve.json, fast.log)
```

### 21.2 Install Npcap (Bắt Buộc)

Suricata trên Windows cần Npcap để capture network traffic.

1. Download từ [npcap.com](https://npcap.com/#download)
2. Khi cài đặt:
   - ☑ **Enable WinPcap API-compatible mode**
   - ☑ **Enable startup at boot**

```powershell
# Kiểm tra Npcap service
Get-Service -Name npcap
# Phải thấy: Status = Running

# Nếu không chạy:
Start-Service -Name npcap
```

### 21.3 Configure suricata.yaml

Mở file: `C:\Program Files\Suricata\suricata.yaml`

**Fix HOME_NET / EXTERNAL_NET:**

```yaml
# Đầu file (sau %YAML 1.1)
vars:
  address-groups:
    HOME_NET: "[192.168.100.0/24]"  # Dải mạng của bạn
    EXTERNAL_NET: "!$HOME_NET"
    DNS_SERVERS: "$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    SQL_SERVERS: "$HOME_NET"
    SMTP_SERVERS: "$HOME_NET"
```

> **⚠️ QUAN TRỌNG:** Phải định nghĩa `HOME_NET`, nếu không rules sẽ bị disabled!

**Định nghĩa Interface:**

```powershell
# PowerShell — tìm tên interface
Get-NetAdapter | Select Name, Status
```

```yaml
# suricata.yaml — af-packet section
af-packet:
  - interface: Ethernet  # Thay bằng tên adapter thực tế
```

**Enable EVE JSON Output:**

```yaml
# suricata.yaml — outputs section
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
```

### 21.4 Run Suricata

```powershell
# PowerShell (Admin)
cd 'C:\Program Files\Suricata\'
suricata -c suricata.yaml -i Ethernet
# Thay 'Ethernet' bằng tên adapter thực tế
```

### 21.5 Integrate Suricata với Wazuh Agent

Thêm vào `ossec.conf` của Wazuh Agent (file: `C:\Program Files (x86)\ossec-agent\ossec.conf`):

```xml
<localfile>
  <log_format>json</log_format>
  <location>C:\Program Files\Suricata\log\eve.json</location>
</localfile>
```

```powershell
# Restart Agent
Restart-Service -Name WazuhSvc
```

### 21.6 Test Suricata

```powershell
# Generate network traffic
ping google.com
curl https://www.google.com

# Xem eve.json có log không
Get-Content 'C:\Program Files\Suricata\log\eve.json' -Tail 10
```

### 21.7 Xem Alerts trên Wazuh Dashboard

Vào **Wazuh Dashboard** → **Threat Hunting** → Filter by Suricata để xem alerts.

> **Lưu ý:** Nếu đã chạy Suricata trong Docker container (dự án hiện tại), không cần cài Suricata trên Windows riêng. Phần này chỉ dành cho các máy Windows không có Docker.

---

> **File Version:** 1.2
> **Last Updated:** May 4, 2026
> **Project:** is_security_group1 — SOC Lab
> **References:** [SOC_Lab_Tiep_Tuc_AtoZ.docx](https://github.com/), [SOC_HomeLab_Docker_AZ.docx](https://github.com/)
