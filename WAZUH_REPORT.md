# Wazuh SOC Lab Deployment Report

> **Comprehensive report on the Wazuh 4.9.0 SIEM stack deployment** for the Network Intrusion Detection System (IDS) SOC Lab.
> Covers Docker-based architecture, component configuration, integration with pfSense and Suricata, agent management, and operational procedures.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Architecture & Network Topology](#2-architecture--network-topology)
3. [Docker Compose Stack](#3-docker-compose-stack)
4. [Wazuh Manager Configuration](#4-wazuh-manager-configuration)
5. [Wazuh Indexer (OpenSearch)](#5-wazuh-indexer-opensearch)
6. [Wazuh Dashboard](#6-wazuh-dashboard)
7. [Filebeat & OpenSearch Compatibility Fix](#7-filebeat--opensearch-compatibility-fix)
8. [Custom Rules & Decoders for pfSense](#8-custom-rules--decoders-for-pfsense)
9. [Agent Management](#9-agent-management)
10. [VirusTotal Integration](#10-virustotal-integration)
11. [pfSense Integration Details](#11-pfsense-integration-details)
12. [Suricata IDS Integration](#12-suricata-ids-integration)
13. [Monitoring Capabilities](#13-monitoring-capabilities)
14. [Security Hardening](#14-security-hardening)
15. [Operational Procedures](#15-operational-procedures)
16. [Troubleshooting Guide](#16-troubleshooting-guide)
17. [Credentials Reference](#17-credentials-reference)
18. [Appendices](#18-appendices)

---

## 1. Executive Summary

### Purpose

This report documents the deployment of **Wazuh 4.9.0** — an open-source SIEM (Security Information and Event Management) platform — as the central logging and analysis engine for the SOC Lab. The Wazuh stack runs entirely in Docker containers on a dedicated host (192.168.100.102) and serves as the aggregation point for:

- **pfSense firewall logs** (via syslog/UDP)
- **Windows endpoint telemetry** (via Wazuh agent)
- **File integrity monitoring** (FIM) on the manager itself
- **VirusTotal threat intelligence** enrichment
- **Suricata IDS alerts** (co-deployed on same host)

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Docker Compose deployment | Reproducible, portable, easy to restart/reconfigure |
| Single-node Indexer | Lab environment — no clustering needed |
| Self-signed certificates | Internal lab use only |
| Filebeat + OpenSearch compatibility patch | Wazuh 4.9 ships Filebeat 7.x; OpenSearch 2.x removed `_type` support |
| Pre-shared key agent auth | Simpler than centralized auth for a lab environment |

### Stack Status

| Component | Status | Uptime |
|-----------|--------|--------|
| wazuh-manager | Running | ~46 minutes |
| wazuh-indexer | Running | ~5 hours |
| wazuh-dashboard | Running | ~5 hours |
| suricata | Running | ~5 hours |

---

## 2. Architecture & Network Topology

### High-Level Architecture

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
│  │                   │   suricata    │  (host network mode)          │
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

### Network Addressing

#### Physical Network (pfSense LAN)

| Entity | IP Address | Description |
|--------|------------|-------------|
| pfSense WAN | 192.168.100.1/24 | Gateway, firewall, DNS/DHCP server |
| Docker Host | 192.168.100.102 | Host machine running all containers |
| pfSense LAN | 10.0.1.1/24 | Internal lab subnet (agents, endpoints) |

#### Docker Bridge Network (soc-net — 172.20.0.0/24)

| Container | IP Address | Hostname | Exposed Ports |
|-----------|------------|----------|---------------|
| wazuh.manager | 172.20.0.10 | wazuh-manager | 514/udp, 1514/tcp+udp, 1515/tcp, 55000/tcp |
| wazuh.indexer | 172.20.0.11 | wazuh.indexer | 9200/tcp |
| wazuh.dashboard | 172.20.0.12 | wazuh.dashboard | 5601/tcp (mapped to host 443) |

#### Host Port Mapping

| Host Port | Container Port | Service | Protocol |
|-----------|---------------|---------|----------|
| 514 | 514 | Syslog (pfSense) | UDP |
| 1514 | 1514 | Wazuh Agent | TCP + UDP |
| 1515 | 1515 | Agent enrollment | TCP |
| 55000 | 55000 | Wazuh API (REST) | TCP |
| 9200 | 9200 | OpenSearch HTTP | TCP |
| 443 | 5601 | Wazuh Dashboard (HTTPS) | TCP |

#### pfSense Port Forwarding (WAN → Docker Host)

| External Port | Protocol | Forward To | Purpose |
|---------------|----------|------------|---------|
| 443 | TCP | 192.168.100.102:443 | Dashboard access |
| 1514 | TCP+UDP | 192.168.100.102:1514 | Agent connections |
| 55000 | TCP | 192.168.100.102:55000 | API access |
| 9200 | TCP | 192.168.100.102:9200 | Indexer direct access |
| 514 | UDP | 192.168.100.102:514 | Syslog from pfSense |

### Data Flow

```
pfSense ──syslog/UDP:514──> wazuh.manager ──Filebeat──> wazuh.indexer
                                                              │
Windows Agent ──TCP:1514──> wazuh.manager ──API:55000──> wazuh.dashboard
                                                              │
Suricata ──eve.json──> (mounted volume) ──> wazuh.manager     │
                                                              │
User Browser ──HTTPS:443──> wazuh.dashboard ──REST──> wazuh.manager
```

---

## 3. Docker Compose Stack

### Stack Definition

The entire stack is defined in `soc-lab/docker-compose.yml` with 4 services:

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

### Volume Structure

```
soc-lab/
├── docker-compose.yml          ← Stack definition
├── .env                        ← Environment variables
├── certs/                      ← SSL certificates
│   ├── root-ca.pem
│   ├── wazuh-1.pem / wazuh-1-key.pem     (manager)
│   └── node-1.pem / node-1-key.pem       (indexer)
│
├── wazuh/
│   ├── config/
│   │   ├── wazuh_manager.conf  ← OSSEC config (mounted to /var/ossec/etc/ossec.conf)
│   │   ├── local_rules.xml     ← Custom detection rules
│   │   ├── local_decoders.xml  ← Custom log decoders
│   │   ├── filebeat.yml        ← Filebeat output config
│   │   └── api.yaml            ← API server config (host only, NOT mounted)
│   ├── data/
│   │   ├── logs/               ← Persistent logs (alerts, archives, API)
│   │   └── etc/                ← Shared agent configuration
│   ├── scripts/                ← Agent management utilities
│   │   ├── do_all.py
│   │   ├── add_agent.py
│   │   └── clean_agent.py
│   ├── filebeat-run.sh         ← Filebeat startup patch script
│   └── README.md               ← Component-level documentation
│
├── indexer/
│   └── config/opensearch.yml   ← OpenSearch configuration
│
└── dashboard/
    └── config/opensearch_dashboards.yml  ← Dashboard configuration
```

### Environment Variables (`.env`)

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

## 4. Wazuh Manager Configuration

### Main OSSEC Configuration

The manager configuration (`wazuh_manager.conf`) defines:

#### 4.1. Remote Connections (Inputs)

**Syslog input — pfSense firewall logs:**
```xml
<remote>
  <connection>syslog</connection>
  <port>514</port>
  <protocol>udp</protocol>
  <allowed-ips>192.168.100.1</allowed-ips>
  <local_ip>0.0.0.0</local_ip>
</remote>
```
- Listens on UDP 514 for syslog messages
- Only accepts connections from pfSense (192.168.100.1)
- Processes pfSense filterlog messages through the custom decoder

**Agent connection channel — encrypted TCP:**
```xml
<remote>
  <connection>secure</connection>
  <port>1514</port>
  <protocol>tcp</protocol>
  <local_ip>0.0.0.0</local_ip>
</remote>
```
- Encrypted TCP channel for Wazuh agent communications
- All Wazuh agents connect here

#### 4.2. File Integrity Monitoring (FIM)

```xml
<syscheck>
  <disabled>no</disabled>
  <frequency>43200</frequency>
  <directories check_all="yes" realtime="yes"
               report_changes="yes">/home,/etc,/var/ossec/etc</directories>
</syscheck>
```
- Scans every 12 hours (43200 seconds)
- Real-time monitoring on key directories
- Reports file content changes (not just metadata)

#### 4.3. Agent Auto-Enrollment

```xml
<auth>
  <disabled>no</disabled>
  <port>1515</port>
  <use_source_ip>no</use_source_ip>
  <purge>yes</purge>
  <limit_maxagents>yes</limit_maxagents>
</auth>
```
- Port 1515 for enrollment requests
- `use_source_ip=no`: allows agents behind NAT to enroll
- `purge=yes`: removes agents that have been disconnected too long

#### 4.4. Daemon Status

| Daemon | Function | Status |
|--------|----------|--------|
| wazuh-analysisd | Log analysis & rule matching | Running |
| wazuh-remoted | Agent communication | Running |
| wazuh-authd | Agent enrollment | Running |
| wazuh-db | Agent registry database | Running |
| wazuh-modulesd | External integrations (VirusTotal, etc.) | Running |
| wazuh-monitord | Log rotation & monitoring | Running |
| wazuh-logcollector | Local log collection | Running |
| wazuh-syscheckd | File integrity monitoring | Running |
| wazuh-execd | Active response execution | Running |
| wazuh-integratord | External integration dispatch | Running |
| wazuh-apid | REST API server | Running |
| wazuh-clusterd | Multi-node clustering | Not running (single-node) |
| wazuh-maild | Email alerts | Not running (not configured) |

### API Configuration

The Wazuh API (`wazuh-apid`) runs as a Python ASGI application via uvicorn on port 55000:

- **Default protocol:** HTTPS (self-signed certificate)
- **Authentication:** JWT tokens issued via `/security/user/authenticate`
- **RBAC backend:** SQLite database at `/var/ossec/api/configuration/security/rbac.db`
- **Default users:** `wazuh` and `wazuh-wui` (both have administrator role)

#### RBAC Database Structure

The `rbac.db` contains:

| Table | Purpose |
|-------|---------|
| `users` | API users with scrypt-hashed passwords |
| `roles` | Role definitions (administrator, readonly, etc.) |
| `user_roles` | User-to-role mapping |
| `roles_rules` | Role-to-rule access control |
| `roles_policies` | Role-to-policy access control |

**Critical note:** The `api.yaml` file on the Docker host is **NOT mounted** into the container — the container uses the default `api.yaml` packaged in the image.

---

## 5. Wazuh Indexer (OpenSearch)

### Configuration

The indexer uses OpenSearch 2.x as the backend for alert/event storage.

#### opensearch.yml

```yaml
cluster.name: wazuh-cluster
node.name: node-1
discovery.type: single-node

network.host: 0.0.0.0
http.port: 9200

# ES 7.x compatibility — allows Filebeat 7.x _type in bulk requests
compatibility:
  override_main_response_version: true

# SSL/TLS — HTTPS only
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: certs/node-1.pem
plugins.security.ssl.http.pemkey_filepath: certs/node-1-key.pem
plugins.security.ssl.http.pemtrustedcas_filepath: certs/root-ca.pem

# Admin certificate DN
plugins.security.authcz.admin_dn:
  - CN=admin,OU=Wazuh,O=Wazuh,L=California,C=US
```

### Key Configuration Details

| Setting | Value | Purpose |
|---------|-------|---------|
| discovery.type | single-node | No cluster formation needed |
| bootstrap.memory_lock | true | Prevents swapping, critical for performance |
| heap size | 1GB | Configurable via INDEXER_HEAP_SIZE |
| SSL | HTTPS only | All traffic encrypted |
| ES compatibility | override_main_response_version: true | Allows Filebeat 7.x bulk format |

### Administrator Certificate

The indexer authenticates administrative operations via SSL client certificate:
```
Subject: CN=admin, OU=Wazuh, O=Wazuh, L=California, C=US
```

This certificate DN is authorized via `plugins.security.authcz.admin_dn`.

---

## 6. Wazuh Dashboard

### Configuration

The dashboard provides the web UI (Kibana/OpenSearch Dashboards + Wazuh plugin).

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

### Key Configuration Details

| Setting | Value | Purpose |
|---------|-------|---------|
| opensearch.hosts | https://wazuh.indexer:9200 | Backend for data queries |
| ssl.verificationMode | none | Accepts self-signed certs |
| server.port | 5601 | Internal HTTP port |
| Host port mapping | 443:5601 | External HTTPS access |
| SERVER_SSL_ENABLED | true | Dashboard serves HTTPS |
| WAZUH_API_URL | https://wazuh.manager | Connects to Wazuh API on port 55000 |

### Dashboard Access Flow

```
User Browser
    │
    ▼ HTTPS :443
    │
wazuh.dashboard (port 5601)
    │
    ├── REST API ──→ wazuh.manager:55000 (Wazuh API)
    │                    │
    │                    └── RBAC auth (wazuh-wui user)
    │
    └── OpenSearch ──→ wazuh.indexer:9200 (data queries)
                         │
                         └── SSL cert auth (admin user)
```

---

## 7. Filebeat & OpenSearch Compatibility Fix

### Problem Statement

Wazuh 4.9.0 ships with **Filebeat 7.x** which generates Elasticsearch 7.x bulk API format. **OpenSearch 2.x** removed support for the `_type` parameter in bulk request action/metadata lines.

Without the fix, Filebeat fails with:
```
Action/metadata line [1] contains an unknown parameter [_type]
```

### Fix Implementation

The fix is applied at **two layers**:

#### Layer 1: Filebeat Output Configuration

In `filebeat.yml`:
```yaml
output.elasticsearch:
  document_type: ""
```

This strips the `_type` field from the action line in bulk requests:
```json
// Before (broken):
{"index": {"_index": "wazuh-alerts", "_type": "wazuh"}}

// After (fixed):
{"index": {"_index": "wazuh-alerts"}}
```

#### Layer 2: OpenSearch Compatibility Mode

In `opensearch.yml`:
```yaml
compatibility:
  override_main_response_version: true
```

Tells OpenSearch to accept ES 7.x-compatible requests.

#### Layer 3: Startup Patch Script

The `filebeat-run.sh` script automatically applies the `document_type: ""` fix at container startup:

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

This ensures the fix survives:
- Container restarts
- Image updates
- Config file regeneration

---

## 8. Custom Rules & Decoders for pfSense

### pfSense Decoder

The custom decoder (`local_decoders.xml`) identifies pfSense firewall log messages by matching the program name:

```xml
<decoder name="pfsense">
  <program_name>filterlog</program_name>
</decoder>
```

pfSense sends firewall events via syslog with the `filterlog` tag. This decoder ensures Wazuh correctly parses the syslog messages into structured fields (source IP, destination IP, port, protocol, action).

### pfSense Detection Rules

Two custom rules (`local_rules.xml`) trigger on pfSense events:

```xml
<group name="pfsense,firewall,">
  <rule id="100114" level="7">
    <if_sid>100111</if_sid>
    <match>block</match>
    <description>pfSense: Blocked traffic from $(srcip) to $(dstip)</description>
  </rule>

  <rule id="100115" level="10">
    <if_sid>100111</if_sid>
    <match>authentication error</match>
    <description>pfSense: Auth error from $(srcip)</description>
  </rule>
</group>
```

| Rule ID | Level | Trigger | Description | Response |
|---------|-------|---------|-------------|----------|
| 100114 | 7 (Medium) | pfSense blocks a connection | Blocked outbound/inbound attempt | Log review |
| 100115 | 10 (Critical) | Authentication failure | Possible brute-force/credential stuffing | Immediate investigation |

Both rules inherit from the base syslog rule `100111` (pfSense syslog catch-all).

---

## 9. Agent Management

### Current Agents

| Agent ID | Name | IP | Status | Type |
|----------|------|----|--------|------|
| 000 | wazuh-manager | 127.0.0.1 | Active/Local | Server self-monitoring |
| 001 | MSI | any | Active | Windows endpoint |

### How Agent Authentication Works

```
Agent ──connect:1514/TCP──> wazuh-remoted
                                    │
                                    ▼
                            Check client.keys
                            (pre-shared key)
                                    │
                           ┌────────┴────────┐
                           │ Match?           │
                           └────────┬────────┘
                                YES │              NO
                                   ▼               ▼
                            Accept agent    Reject connection
                                   │
                                   ▼
                            Update global.db
                            (last_keepalive, connection_status)
```

### Agent Enrollment — Manual Key Method

When a Windows MSI agent is installed, it needs a pre-shared key that matches the manager's `client.keys` and `global.db`.

#### Quick Setup Script: `do_all.py`

This utility script (in `soc-lab/wazuh/scripts/`) performs the complete agent setup:

```python
1. Kill wazuh-db to release SQLite lock on global.db
2. Delete old MSI agent entry from global.db
3. Generate new SHA-256 key
4. Insert new agent record with connection_status='active'
5. Write client.keys file
6. Print key for agent configuration
```

**Usage:**
```bash
# Copy script to container
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/

# Run inside container (PATH must be reset)
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'
```

**Output:**
```
Deleted 1 MSI agent(s)
New key: <sha256-hex>
Agent MSI added with ID 2
client.keys written
=== COPY THIS KEY ===
2 MSI any <sha256-hex>
```

#### Script Reference

| Script | Function | Use Case |
|--------|----------|----------|
| `do_all.py` | Clean + generate + insert + write | First-time agent setup |
| `add_agent.py` | Generate key + insert only | Adding additional agents |
| `clean_agent.py` | Delete from global.db + clear keys | Removing stale agents |

#### Agent Configuration (Windows ossec.conf)

The Windows agent's `ossec.conf` must specify:
```xml
<client>
  <server>
    <address>192.168.100.102</address>
    <port>1514</port>
    <protocol>tcp</protocol>
  </server>
</client>
```

### Database Location

Both the agent registry and agent-info mapping are stored on a persistent Docker volume:

| Data | Path on Container | Storage |
|------|-------------------|---------|
| Agent registry | `/var/ossec/queue/db/global.db` | wazuh-data volume |
| Agent-info mapping | `/var/ossec/queue/agent-info/001` | wazuh-data volume |
| Agent keys | `/var/ossec/etc/client.keys` | Ephemeral (regenerated by scripts) |

---

## 10. VirusTotal Integration

### Configuration

```xml
<integration>
  <name>virustotal</name>
  <api_key>${VIRUSTOTAL_API_KEY}</api_key>
  <group>syscheck</group>
  <alert_format>json</alert_format>
</integration>
```

### How It Works

1. **FIM (syscheck)** detects a file change on monitored directories
2. The manager computes the SHA-256 hash of the changed file
3. The hash is sent to VirusTotal's API
4. VirusTotal returns reputation data (malicious count, detection ratio, etc.)
5. The original alert is enriched with this intelligence data
6. The enriched alert is stored in OpenSearch and displayed in the Dashboard

### Scope

| Parameter | Value |
|-----------|-------|
| Trigger | Syscheck file change events |
| API Key | Environment variable `${VIRUSTOTAL_API_KEY}` |
| Rate Limit | VirusTotal free tier: 4 requests/minute |
| Alert Format | JSON enrichment appended to original alert |

---

## 11. pfSense Integration Details

### Syslog Forwarding

pfSense is configured to send firewall events to the Wazuh manager:

| pfSense Setting | Value |
|-----------------|-------|
| Syslog server | 192.168.100.102 |
| Port | 514 |
| Transport | UDP |
| Facility | Local0 (default) |
| Events forwarded | Firewall pass/block, authentication |

### DNS Resolution (Unbound)

pfSense runs the Unbound DNS resolver with custom host overrides:

| Hostname | Alias | Resolves To |
|----------|-------|-------------|
| wazuh.manager | wazuh.manager.soc-lab.local | 192.168.100.102 |
| wazuh.indexer | wazuh.indexer.soc-lab.local | 192.168.100.102 |
| wazuh.dashboard | wazuh.dashboard.soc-lab.local | 192.168.100.102 |

This allows Docker containers (which use the Docker bridge gateway 172.20.0.1 → pfSense as DNS) to resolve Wazuh hostnames.

### Outbound NAT

Docker containers on 172.20.0.0/24 need NAT to reach the internet:

| Source Subnet | NAT Address | Purpose |
|---------------|-------------|---------|
| 172.20.0.0/24 | 192.168.100.1 (pfSense WAN) | Docker internet access |
| 10.0.1.0/24 | 192.168.100.1 (pfSense WAN) | LAN clients internet access |

Without this, containers fail to reach external hosts (VirusTotal API, package repos, etc.).

### Firewall Rules

pfSense rules governing SOC Lab traffic:

| Direction | Source | Destination | Port | Action |
|-----------|--------|-------------|------|--------|
| Outbound (LAN→WAN) | 192.168.100.102 | Any | Any | Pass |
| Inbound NAT | Any | (WAN IP) | 443, 1514, 55000, 9200, 514 | Forward to Docker host |

---

## 12. Suricata IDS Integration

### Deployment

Suricata runs as a separate Docker container (`jasonish/suricata:latest`) in **host network mode**:

```yaml
suricata:
  image: jasonish/suricata:latest
  container_name: suricata
  network_mode: host
  cap_add: [NET_ADMIN, NET_RAW, SYS_NICE]
```

### Integration with Wazuh

Suricata and Wazuh are co-deployed on the same host but operate independently:

- **Suricata** generates alerts in `eve.json` format
- **Wazuh** can ingest Suricata logs if configured as a log source
- The two systems provide complementary visibility:
  - Suricata: Network-level threat detection (signature-based)
  - Wazuh: Host-level monitoring, log analysis, file integrity

### Network Monitoring Scope

Suricata's HOME_NET includes:
- 192.168.1.0/24
- 192.168.100.0/24
- 172.20.0.0/24
- 10.0.0.0/8

---

## 13. Monitoring Capabilities

### Current Monitoring Sources

| Source | Type | Details | Data Volume |
|--------|------|---------|-------------|
| pfSense firewall | Syslog/UDP:514 | Pass/block events | ~1-5 MB/day |
| Windows agent | TCP:1514 | Windows events, syscheck | TBD |
| Manager (self) | Local | Internal events | ~10-50 MB/day |
| FIM (syscheck) | Local | File changes on /home, /etc, /var/ossec/etc | Low |
| Active responses | Local file | `/var/ossec/logs/active-responses.log` | Low |

### Alert Categories

| Category | Rule Level | Examples |
|----------|------------|----------|
| Benign | 0-3 | Normal traffic, informational |
| Low | 4-5 | Policy violations, configuration changes |
| Medium | 6-8 | Blocked connections, unusual patterns |
| High | 9-11 | Authentication failures, exploitation attempts |
| Critical | 12-15 | Confirmed compromise, active attacks |

### Dashboard Features

The Wazuh Dashboard provides:

1. **Security Events** — Real-time alert visualization
2. **Agent Status** — Connection health, OS inventory
3. **FIM Dashboard** — File change monitoring
4. **Vulnerability Detection** — Known CVE matching (if enabled)
5. **Policy Compliance** — PCI DSS, GDPR, HIPAA, NIST frameworks
6. **Ruleset Management** — Rule editing and testing

---

## 14. Security Hardening

### Current Security Measures

| Measure | Status | Details |
|---------|--------|---------|
| TLS/SSL encryption | ✅ Done | All inter-component HTTPS, self-signed CA |
| RBAC authentication | ✅ Done | API requires JWT authentication |
| Admin DN certificate | ✅ Done | Indexer admin auth via SSL client cert |
| Syslog IP restriction | ✅ Done | Only pfSense (192.168.100.1) can send syslog |
| Memory locking | ✅ Done | Indexer mloclall disabled |
| File integrity monitoring | ✅ Done | Real-time monitoring on key directories |
| VirusTotal enrichment | ✅ Done | File hash lookup on syscheck events |

### Recommendations

| Recommendation | Priority | Effort |
|----------------|----------|--------|
| Change all default passwords | 🔴 Critical | 5 min |
| Enable vulnerability detection | 🟡 Medium | 10 min (config change) |
| Add email alerts (wazuh-maild) | 🟡 Medium | 15 min |
| Enable agent group policies | 🟢 Low | 30 min |
| Deploy multi-node cluster | 🟢 Low | 2-3 hours |
| Integwith Active Directory/LDAP | 🟢 Low | 1 hour |

---

## 15. Operational Procedures

### Starting the Stack

```bash
cd soc-lab
docker compose up -d
docker compose logs -f    # Watch all logs
```

### Stopping the Stack

```bash
cd soc-lab
docker compose down
```

To also remove persistent data:
```bash
docker compose down -v    # WARNING: deletes all alerts and agent data
```

### Restarting the Manager

```bash
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
# IMPORTANT: Remove stale .restart file after restart!
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'
```

### Checking Component Health

```bash
# Manager daemon status
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# Agent list
docker exec wazuh-manager /var/ossec/bin/agent_control -l

# Indexer cluster health
docker exec wazuh-indexer curl -sk https://localhost:9200/_cluster/health

# Dashboard connectivity
curl -sk https://192.168.100.102:443/status

# API authentication test
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"
```

### Viewing Logs

```bash
# Container logs
docker compose logs -f wazuh.manager
docker compose logs -f wazuh.indexer
docker compose logs -f wazuh.dashboard

# Inside the manager
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/alerts/alerts.log'

# API logs
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && tail -f /var/ossec/logs/api.log'
```

### Setting Up a New Windows Agent

```bash
# Step 1: Generate new agent key
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && python3 /tmp/do_all.py'

# Step 2: Restart manager and remove .restart file
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager sh -c 'rm -f /var/ossec/var/run/.restart'

# Step 3: Install Windows agent with the generated key
# (Use the printed key in Windows ossec.conf)
```

### Backing Up Configuration

```bash
# Backup config files and scripts
tar czf wazuh-backup-$(date +%Y%m%d).tar.gz \
  soc-lab/wazuh/config/ \
  soc-lab/wazuh/scripts/ \
  soc-lab/wazuh/filebeat-run.sh \
  soc-lab/indexer/config/ \
  soc-lab/dashboard/config/ \
  soc-lab/.env \
  soc-lab/docker-compose.yml

# Backup logs (optional)
tar czf wazuh-logs-$(date +%Y%m%d).tar.gz soc-lab/wazuh/data/logs/
```

---

## 16. Troubleshooting Guide

### Issue 1: API Returns "Some Wazuh daemons are not ready yet"

**Symptom:** All API requests return HTTP 400 with this message.

**Root cause:** A stale `.restart` file at `/var/ossec/var/run/.restart` left over from `wazuh-control restart`. The API checks for this file as a signal that daemons are restarting.

**Fix:**
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && rm -f /var/ossec/var/run/.restart'
```

**Prevention:** Always remove `.restart` after restart:
```bash
alias wazuh-restart='docker exec wazuh-manager /var/ossec/bin/wazuh-control restart && \
  sleep 2 && docker exec wazuh-manager rm -f /var/ossec/var/run/.restart'
```

### Issue 2: Windows PATH Leaks Into Container

**Symptom:** Commands run via `docker exec` fail with Windows error messages; `which` returns Windows paths.

**Root cause:** Docker Desktop on Windows injects the Windows `%PATH%` into the container's `$PATH` environment.

**Fix:** Always reset PATH explicitly:
```bash
docker exec wazuh-manager sh -c \
  'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && <your command>'
```

### Issue 3: Dashboard Shows "No API Available"

**Symptom:** Wazuh Dashboard cannot connect to the API; shows error on login.

**Root cause (most common):** The Wazuh API is returning errors — usually the stale `.restart` file issue.

**Diagnosis:**
```bash
# Test API directly
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"

# Expected: {"data": {"token": "eyJ..."}}
# If 400: check .restart file
```

### Issue 4: Agent Shows "Disconnected"

**Symptom:** Agent appears in manager but stays disconnected.

**Possible causes:**
1. Agent key doesn't match between `client.keys` and agent's `ossec.conf`
2. Firewall blocking port 1514/TCP
3. Agent-info mapping stale

**Fix:**
```bash
# Regenerate key and restart
docker exec wazuh-manager python3 /tmp/do_all.py
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager rm -f /var/ossec/var/run/.restart
```

### Issue 5: Filebeat Can't Connect to Indexer

**Symptom:** No alerts reaching the indexer; Dashboard shows no data.

**Diagnosis:**
```bash
# Check Filebeat logs
docker exec wazuh-manager cat /var/log/filebeat/filebeat

# Check indexer connectivity
docker exec wazuh-manager curl -sk https://wazuh.indexer:9200/

# Verify certificates exist
docker exec wazuh-manager ls -la /etc/ssl/
```

**Common causes:**
- SSL certificate mismatch (check file paths in filebeat.yml)
- Indexer not ready (single-node takes time on first boot)
- Network connectivity (check soc-net DNS resolution)

### Issue 6: Dashboard Schannel SSL Error on Windows

**Symptom:** Browser (Windows) shows SSL certificate error when accessing Dashboard.

**Root cause:** Windows `schannel` library rejects self-signed certificates.

**Fix:**
- **Chrome/Edge:** Click "Advanced" → "Proceed to [IP]"
- **curl:** Use `-k` or `--insecure` flag
- **Browser warning:** This is expected for self-signed certs; no security concern in a lab environment

---

## 17. Credentials Reference

### Authentication Table

| Service | URL | Username | Password | Notes |
|---------|-----|----------|----------|-------|
| **Wazuh Dashboard** | `https://192.168.100.102:443/` | `admin` | `admin` | Web UI |
| **Wazuh API** | `https://192.168.100.102:55000/` | `wazuh-wui` | `wazuh-wui` | REST API (used by Dashboard) |
| **Wazuh Indexer** | `https://192.168.100.102:9200/` | `admin` | `admin` | OpenSearch direct access |
| **pfSense WebGUI** | `https://192.168.100.1/` | `admin` | `pfsense` | Firewall admin |
| **Suricata** | N/A | N/A | N/A | No authentication (host-local) |

### File Locations

| Certificate | Path | Used By |
|-------------|------|---------|
| Root CA | `certs/root-ca.pem` | All components |
| Manager cert | `certs/wazuh-1.pem` | Manager (Filebeat → Indexer) |
| Manager key | `certs/wazuh-1-key.pem` | Manager (Filebeat → Indexer) |
| Node cert | `certs/node-1.pem` | Indexer (SSL endpoint) |
| Node key | `certs/node-1-key.pem` | Indexer (SSL endpoint) |
| Admin cert | `certs/admin.pem` | Indexer (admin DN auth) |
| Admin key | `certs/admin-key.pem` | Indexer (admin DN auth) |

> **⚠️ SECURITY WARNING:** All passwords are set to defaults. For any environment beyond a local lab:
> 1. Change `INDEXER_PASSWORD` and `DASHBOARD_PASSWORD` in `.env`
> 2. Update the API user passwords via `wazuh-apid` CLI
> 3. Regenerate all SSL certificates
> 4. Change pfSense admin password

---

## 18. Appendices

### Appendix A: Quick Command Reference

| Task | Command |
|------|---------|
| Start stack | `cd soc-lab && docker compose up -d` |
| Stop stack | `cd soc-lab && docker compose down` |
| View manager logs | `docker compose logs -f wazuh.manager` |
| View alerts | `docker exec wazuh-manager tail -f /var/ossec/logs/alerts/alerts.log` |
| List agents | `docker exec wazuh-manager /var/ossec/bin/agent_control -l` |
| Check daemons | `docker exec wazuh-manager /var/ossec/bin/wazuh-control status` |
| Restart manager | `docker exec wazuh-manager /var/ossec/bin/wazuh-control restart` |
| Fix API after restart | `docker exec wazuh-manager rm -f /var/ossec/var/run/.restart` |
| Test API auth | `curl -k -u wazuh-wui:wazuh-wui -X POST "https://192.168.100.102:55000/security/user/authenticate"` |
| Check indexer | `curl -sk https://192.168.100.102:9200/_cluster/health` |
| Test Dashboard | `curl -sk https://192.168.100.102:443/status` |

### Appendix B: Port Reference

| Port | Protocol | Service | Source | Destination |
|------|----------|---------|--------|-------------|
| 514 | UDP | Syslog | pfSense (192.168.100.1) | wazuh.manager |
| 1514 | TCP+UDP | Wazuh Agent | Remote agents | wazuh.manager |
| 1515 | TCP | Agent enrollment | Remote agents | wazuh.manager |
| 55000 | TCP | Wazuh API | Dashboard, admin | wazuh.manager |
| 9200 | TCP | OpenSearch HTTP | Filebeat, Dashboard | wazuh.indexer |
| 443 | TCP | Dashboard HTTPS | User browser | wazuh.dashboard |

### Appendix C: File Inventory

| File Path | Purpose |
|-----------|---------|
| `soc-lab/docker-compose.yml` | Stack orchestration |
| `soc-lab/.env` | Environment variables |
| `soc-lab/wazuh/config/wazuh_manager.conf` | OSSEC main configuration |
| `soc-lab/wazuh/config/local_rules.xml` | Custom detection rules |
| `soc-lab/wazuh/config/local_decoders.xml` | Custom log decoders |
| `soc-lab/wazuh/config/filebeat.yml` | Filebeat output configuration |
| `soc-lab/wazuh/config/api.yaml` | API server configuration (host only) |
| `soc-lab/wazuh/filebeat-run.sh` | Filebeat startup patch |
| `soc-lab/wazuh/scripts/do_all.py` | Agent setup (clean + add) |
| `soc-lab/wazuh/scripts/add_agent.py` | Agent add only |
| `soc-lab/wazuh/scripts/clean_agent.py` | Agent cleanup |
| `soc-lab/indexer/config/opensearch.yml` | OpenSearch configuration |
| `soc-lab/dashboard/config/opensearch_dashboards.yml` | Dashboard configuration |
| `soc-lab/pfsense/README.md` | pfSense deployment guide |

### Appendix D: Key Technical Decisions

| Decision | Alternative Considered | Why Chosen |
|----------|----------------------|------------|
| Single-node indexer | Multi-node cluster | Lab environment doesn't need HA |
| Self-signed SSL certs | Let's Encrypt / public CA | Internal lab; no public domain |
| Pre-shared key auth | Centralized auth (e.g., LDAP) | Simpler setup for lab |
| Docker Compose | Kubernetes, Ansible | Lowest complexity for single host |
| Filebeat (not Logstash) | Logstash forwarder | Wazuh ships Filebeat by default |
| soc-net bridge | Host networking | Isolated network for containers |

---

**Report Version:** 1.0  
**Last Updated:** May 4, 2026  
**Wazuh Version:** 4.9.0  
**Deployment Type:** Docker Compose (single-node)  
**Author:** SOC Lab Team
