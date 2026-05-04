# Wazuh SOC Lab — Deployment Report

> **Wazuh 4.9.0 SIEM Stack** deployed via Docker Compose as part of the Network Intrusion Detection SOC Lab.
> Integrated with pfSense firewall (syslog), Suricata IDS, and VirusTotal threat intelligence.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Network Topology](#2-network-topology)
3. [Component Configuration](#3-component-configuration)
4. [Wazuh Manager](#4-wazuh-manager)
5. [Wazuh Indexer (OpenSearch)](#5-wazuh-indexer-opensearch)
6. [Wazuh Dashboard](#6-wazuh-dashboard)
7. [Filebeat & OpenSearch Compatibility](#7-filebeat--opensearch-compatibility)
8. [Custom Rules & Decoders](#8-custom-rules--decoders)
9. [Agent Management](#9-agent-management)
10. [VirusTotal Integration](#10-virustotal-integration)
11. [pfSense Integration](#11-pfsense-integration)
12. [Security Considerations](#12-security-considerations)
13. [Troubleshooting](#13-troubleshooting)
14. [Credentials Reference](#14-credentials-reference)
15. [Scripts Reference](#15-scripts-reference)

---

## 1. Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Host                                │
│                      192.168.100.102                               │
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ wazuh.manager │  │wazuh.indexer │  │wazuh.dashboard│           │
│  │  172.20.0.10  │  │ 172.20.0.11  │  │  172.20.0.12  │           │
│  │               │  │              │  │              │            │
│  │  Wazuh 4.9.0  │  │ OpenSearch   │  │  Dashboard    │           │
│  │  + Filebeat   │  │   2.x        │  │  + Wazuh UI   │           │
│  └───────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│          │                 │                 │                     │
│          └─────────────────┼─────────────────┘                     │
│                            │                                       │
│                    ┌───────┴───────┐                               │
│                    │   suricata    │  (host network mode)           │
│                    │  IDS Engine   │                               │
│                    └───────────────┘                               │
└──────────────────────────┬────────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   pfSense   │ 192.168.100.1
                    │  Firewall   │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  Internet   │
                    └─────────────┘
```

### Component Roles

| Component | Purpose | Docker IP | Host Ports |
|-----------|---------|-----------|------------|
| **wazuh.manager** | SIEM engine — agent management, log analysis, alerting | 172.20.0.10 | 514/udp, 1514/tcp+udp, 1515/tcp, 55000/tcp |
| **wazuh.indexer** | Threat data storage & search (OpenSearch 2.x) | 172.20.0.11 | 9200/tcp |
| **wazuh.dashboard** | Web UI — Kibana/OpenSearch Dashboards + Wazuh plugin | 172.20.0.12 | 443/tcp (->5601) |
| **suricata** | Network IDS — packet inspection & alerting | host mode | N/A |

---

## 2. Network Topology

### IP Addressing

| Entity | IP Address | Purpose |
|--------|------------|---------|
| pfSense WAN | 192.168.100.1/24 | Gateway & firewall |
| pfSense LAN | 10.0.1.1/24 | Internal lab network |
| Docker Host | 192.168.100.102 | Host for all containers |
| wazuh.manager | 172.20.0.10 | Docker bridge (soc-net) |
| wazuh.indexer | 172.20.0.11 | Docker bridge (soc-net) |
| wazuh.dashboard | 172.20.0.12 | Docker bridge (soc-net) |
| Docker subnet | 172.20.0.0/24 | soc-net bridge |

### Docker Network

```yaml
networks:
  soc-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

All Wazuh containers communicate over the `soc-net` bridge network. Suricata uses `host` networking mode to capture physical interface traffic.

### Port Forwarding (pfSense)

pfSense forwards these ports from WAN to Docker Host (192.168.100.102):

| External Port | Protocol | Internal IP | Internal Port | Service |
|---------------|----------|-------------|---------------|---------|
| 443 | TCP | 192.168.100.102 | 443 | Wazuh Dashboard (HTTPS) |
| 1514 | TCP+UDP | 192.168.100.102 | 1514 | Wazuh Agent connection |
| 55000 | TCP | 192.168.100.102 | 55000 | Wazuh API |
| 9200 | TCP | 192.168.100.102 | 9200 | Wazuh Indexer (OpenSearch) |
| 514 | UDP | 192.168.100.102 | 514 | Syslog (pfSense logs) |

> **Agents connect to:** `192.168.100.102:1514/TCP` (the Docker host IP, not the container IP)

---

## 3. Component Configuration

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

## 4. Wazuh Manager

### Container Configuration

- **Image:** `wazuh/wazuh-manager:4.9.0`
- **Hostname:** `wazuh-manager`
- **Container IP:** `172.20.0.10`

### Volume Mounts

| Host Path | Container Path | Purpose |
|-----------|---------------|---------|
| `./wazuh/config/wazuh_manager.conf` | `/var/ossec/etc/ossec.conf` | Main OSSEC config |
| `./wazuh/config/local_rules.xml` | `/var/ossec/etc/rules/local_rules.xml` | Custom rules (pfSense) |
| `./wazuh/config/local_decoders.xml` | `/var/ossec/etc/decoders/local_decoders.xml` | Custom decoders (pfSense) |
| `./wazuh/data/logs` | `/var/ossec/logs` | Persistent logs |
| `./wazuh/data/etc` | `/var/ossec/etc/shared` | Shared agent config |
| `./certs` | `/etc/ssl` | SSL certificates (read-only) |
| `./wazuh/filebeat-run.sh` | `/etc/services.d/filebeat/run` | Filebeat startup patch (read-only) |
| `wazuh-data` volume | `/var/ossec/queue` | Agent queue data |

### Main Configuration (`wazuh_manager.conf`)

```xml
<ossec_config>
  <!-- Syslog from pfSense -->
  <remote>
    <connection>syslog</connection>
    <port>514</port>
    <protocol>udp</protocol>
    <allowed-ips>192.168.100.1</allowed-ips>
    <local_ip>0.0.0.0</local_ip>
  </remote>

  <!-- Agent connections (TCP, encrypted) -->
  <remote>
    <connection>secure</connection>
    <port>1514</port>
    <protocol>tcp</protocol>
    <local_ip>0.0.0.0</local_ip>
  </remote>

  <!-- VirusTotal Integration -->
  <integration>
    <name>virustotal</name>
    <api_key>${VIRUSTOTAL_API_KEY}</api_key>
    <group>syscheck</group>
    <alert_format>json</alert_format>
  </integration>

  <!-- File Integrity Monitoring -->
  <syscheck>
    <disabled>no</disabled>
    <frequency>43200</frequency>
    <directories check_all="yes" realtime="yes"
                 report_changes="yes">/home,/etc,/var/ossec/etc</directories>
  </syscheck>

  <!-- Agent auto-enrollment -->
  <auth>
    <disabled>no</disabled>
    <port>1515</port>
    <use_source_ip>no</use_source_ip>
    <purge>yes</purge>
    <limit_maxagents>yes</limit_maxagents>
  </auth>
</ossec_config>
```

### Manager Daemon Status (Active)

| Daemon | Status |
|--------|--------|
| wazuh-modulesd | running |
| wazuh-monitord | running |
| wazuh-logcollector | running |
| wazuh-remoted | running |
| wazuh-syscheckd | running |
| wazuh-analysisd | running |
| wazuh-execd | running |
| wazuh-db | running |
| wazuh-authd | running |
| wazuh-integratord | running |
| wazuh-apid | running |
| wazuh-clusterd | not running |
| wazuh-maild | not running |

---

## 5. Wazuh Indexer (OpenSearch)

### Container Configuration

- **Image:** `wazuh/wazuh-indexer:4.9.0`
- **Hostname:** `wazuh.indexer`
- **Container IP:** `172.20.0.11`
- **Heap:** 1GB (configurable via `INDEXER_HEAP_SIZE`)

### Configuration (`opensearch.yml`)

```yaml
cluster.name: wazuh-cluster
node.name: node-1
node.master: true
node.data: true
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node

# ES 7.x compatibility for Filebeat
compatibility:
  override_main_response_version: true

# SSL (HTTPS)
plugins.security.ssl.http.enabled: true
plugins.security.ssl.http.pemcert_filepath: certs/node-1.pem
plugins.security.ssl.http.pemkey_filepath: certs/node-1-key.pem
plugins.security.ssl.http.pemtrustedcas_filepath: certs/root-ca.pem

# Admin DN
plugins.security.authcz.admin_dn:
  - CN=admin,OU=Wazuh,O=Wazuh,L=California,C=US
```

### Key Settings

- **Single-node discovery** — no clustering
- **HTTPS only** — all transport encrypted with self-signed certificates
- **ES 7.x compatibility mode** — allows Filebeat 7.x `_type` parameter in bulk requests
- **Memory lock** — `bootstrap.memory_lock: true` to prevent swapping

---

## 6. Wazuh Dashboard

### Container Configuration

- **Image:** `wazuh/wazuh-dashboard:4.9.0`
- **Hostname:** `wazuh.dashboard`
- **Container IP:** `172.20.0.12`
- **Port mapping:** `443:5601` (external 443 -> internal 5601)

### Configuration (`opensearch_dashboards.yml`)

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

### Key Settings

- **HTTPS enabled** via `SERVER_SSL_ENABLED=true` environment variable
- **Connects to API** via `WAZH_API_URL=https://wazuh.manager` (port 55000)
- **Default route** set to Wazuh home (`/app/wz-home`)
- **SSL verification mode** set to `none` for self-signed certificates

---

## 7. Filebeat & OpenSearch Compatibility

### The Problem

Wazuh 4.9.0 ships with Filebeat 7.x which uses Elasticsearch 7.x bulk API format. OpenSearch 2.x removed support for the `_type` parameter in bulk request action/metadata lines. This causes:

```
Action/metadata line [1] contains an unknown parameter [_type]
```

### The Fix: Two Layers

**Layer 1 — Filebeat config (`filebeat.yml`):**

```yaml
output.elasticsearch:
  document_type: ""
```

Strips the `_type` field from bulk request action lines.

**Layer 2 — OpenSearch config (`opensearch.yml`):**

```yaml
compatibility:
  override_main_response_version: true
```

Tells OpenSearch to accept ES 7.x format requests.

### Startup Patch (`filebeat-run.sh`)

The `filebeat-run.sh` script applies the `document_type: ""` fix automatically at container startup if it's not already present in filebeat.yml. This ensures the fix survives container restarts and image updates.

---

## 8. Custom Rules & Decoders

### pfSense Decoder (`local_decoders.xml`)

```xml
<decoder name="pfsense">
  <program_name>filterlog</program_name>
</decoder>
```

Matches syslog messages from pfSense's `filterlog` process (firewall logs).

### pfSense Rules (`local_rules.xml`)

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

| Rule ID | Level | Description | Severity |
|---------|-------|-------------|----------|
| 100114 | 7 | pfSense blocked traffic | Medium — blocked connection attempt |
| 100115 | 10 | pfSense authentication error | Critical — possible brute-force attack |

---

## 9. Agent Management

### Registered Agents

| ID | Name | IP | Status |
|----|------|----|--------|
| 000 | wazuh-manager | 127.0.0.1 | Active (local) |
| 001 | MSI | any | Active |

### Agent Enrollment Flow

1. Agent connects to manager at `192.168.100.102:1514/TCP`
2. Manager authenticates via `client.keys` (pre-shared key)
3. Agent appears in manager's `global.db` database
4. Manager maintains `agent-info` mapping in `/var/ossec/queue/agent-info/`

### Manual Agent Key Management

For Windows MSI agents, the key can be pre-generated using the scripts in `soc-lab/wazuh/scripts/`:

1. **`clean_agent.py`** — Removes old MSI agent from `global.db` and clears `client.keys`
2. **`add_agent.py`** — Generates new SHA-256 key and inserts agent into `global.db`
3. **`do_all.py`** — Combined: cleanup + generate key + insert agent + write `client.keys`

> **Important:** The scripts kill `wazuh-db` to release the SQLite lock on `global.db`. After running, the manager daemons must be restarted via `wazuh-control restart`.

---

## 10. VirusTotal Integration

The manager uses the VirusTotal API to enrich file hash alerts from the File Integrity Monitoring (FIM) module.

```xml
<integration>
  <name>virustotal</name>
  <api_key>${VIRUSTOTAL_API_KEY}</api_key>
  <group>syscheck</group>
  <alert_format>json</alert_format>
</integration>
```

- **Scope:** Files monitored by syscheck (FIM)
- **Trigger:** When syscheck detects file changes, the SHA-256 hash is looked up in VirusTotal
- **Format:** Alerts are enriched with VirusTotal reputation data in JSON format
- **API Key:** Set via `VIRUSTOTAL_API_KEY` environment variable

---

## 11. pfSense Integration

### Syslog Forwarding

pfSense sends firewall logs to the Wazuh manager via UDP syslog:

| pfSense Setting | Value |
|-----------------|-------|
| Syslog server | 192.168.100.102 |
| Port | 514 |
| Protocol | UDP |
| Log content | Firewall events (pass/block) |

### DNS Resolution

For containers to resolve Wazuh hostnames, pfSense DNS Resolver (Unbound) has host overrides:

| Hostname | IP |
|----------|-----|
| wazuh.manager.soc-lab.local | 192.168.100.102 |
| wazuh.indexer.soc-lab.local | 192.168.100.102 |
| wazuh.dashboard.soc-lab.local | 192.168.100.102 |

### Outbound NAT

pfSense performs NAT for Docker subnet traffic:

| Source | NAT Address |
|--------|-------------|
| 172.20.0.0/24 | 192.168.100.1 (pfSense WAN) |
| 10.0.1.0/24 | 192.168.100.1 (pfSense WAN) |

Without this, Docker containers cannot reach the internet through pfSense.

---

## 12. Security Considerations

### SSL Certificates

All inter-component communication uses SSL/TLS with self-signed certificates:

- **Certificate Authority:** `root-ca.pem`
- **Node certificates:** `wazuh-1.pem` + `wazuh-1-key.pem` (manager), `node-1.pem` + `node-1-key.pem` (indexer)
- **Location:** `./certs/` directory
- **Verification:** Filebeat uses `verification_mode: full`; Dashboard uses `verificationMode: none`

### Network Segmentation

- All Wazuh containers communicate over isolated `soc-net` bridge (172.20.0.0/24)
- Only necessary ports are exposed to the host: 514, 1514-1515, 55000, 9200, 443
- Suricata runs in host network mode (requires raw socket access for packet capture)

### Authentication

| Service | Username | Authentication |
|---------|----------|---------------|
| Wazuh API (55000) | wazuh-wui | Password (scrypt-hashed in RBAC DB) |
| Wazuh Indexer (9200) | admin | Password (internal) |
| Wazuh Dashboard (443) | admin | Password (via Indexer) |
| Agent enrollment | N/A | Pre-shared key in `client.keys` |

---

## 13. Troubleshooting

### API Returns "Some Wazuh daemons are not ready yet"

**Cause:** A stale `.restart` file exists at `/var/ossec/var/run/.restart` after `wazuh-control restart`.

**Fix:**
```bash
docker exec wazuh-manager sh -c 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && rm -f /var/ossec/var/run/.restart'
```

### Windows PATH Leaks Into Container

**Symptom:** Commands inside container fail with Windows paths in PATH.

**Fix:** Always reset PATH when running `docker exec`:
```bash
docker exec wazuh-manager sh -c 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && <command>'
```

### Agent Shows "Disconnected"

**Possible causes:**
1. Agent key in `client.keys` doesn't match agent's `ossec.conf` key
2. Firewall blocking port 1514/TCP
3. Agent-info mapping stale — restart manager daemon

**Fix:** Re-generate agent key using scripts, or restart the Wazuh manager:
```bash
docker exec wazuh-manager sh -c 'export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin && /var/ossec/bin/wazuh-control restart'
# Then remove the stale .restart file
```

### Dashboard Returns "No API Available"

**Cause:** Wazuh API is unreachable or returning errors (e.g., stale `.restart` file).

**Check API directly:**
```bash
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://localhost:55000/security/user/authenticate"
```

**Check API status:**
```bash
curl -k "https://localhost:55000/"
```

### Filebeat Cannot Connect to Indexer

**Check SSL certificates:**
```bash
docker exec wazuh-manager sh -c 'ls -la /etc/ssl/'
```

**Check indexer health:**
```bash
docker exec wazuh-indexer sh -c 'curl -sk https://localhost:9200/_cluster/health'
```

### Dashboard Schannel SSL Error (Windows)

**Symptom:** `schannel` error when accessing Dashboard in browser on Windows.

**Cause:** Windows `schannel` rejects self-signed certificates.

**Fix:** Click "Advanced" -> "Proceed to website" in the browser, or use `curl -sk` from command line.

---

## 14. Credentials Reference

| Service | URL | Username | Password |
|---------|-----|----------|----------|
| Wazuh Dashboard | `https://192.168.100.102:443` | `admin` | `admin` |
| Wazuh API | `https://192.168.100.102:55000` | `wazuh-wui` | `wazuh-wui` |
| Wazuh Indexer | `https://192.168.100.102:9200` | `admin` | `admin` |
| pfSense WebGUI | `https://192.168.100.1` | `admin` | `pfsense` |

> **⚠️ WARNING:** These are default/dev credentials. Change all passwords before any production use.

---

## 15. Scripts Reference

### Agent Management Scripts

All scripts in `soc-lab/wazuh/scripts/` run inside the `wazuh-manager` container:

```bash
# Copy script to container
docker cp soc-lab/wazuh/scripts/do_all.py wazuh-manager:/tmp/

# Run inside container
docker exec wazuh-manager python3 /tmp/do_all.py
```

| Script | Function | When to Use |
|--------|----------|-------------|
| `do_all.py` | Clean old MSI + generate new key + insert to global.db + write client.keys | Setting up a fresh Windows agent |
| `add_agent.py` | Generate key + add agent to global.db | Adding a new agent without cleanup |
| `clean_agent.py` | Delete MSI agent from global.db + clear client.keys | Removing a stale agent entry |

---

## Appendix A: Quick-Start Commands

```bash
# Start the stack
cd soc-lab
docker compose up -d

# Check status
docker compose ps
docker exec wazuh-manager /var/ossec/bin/wazuh-control status

# View logs
docker compose logs -f wazuh.manager

# Check agent list
docker exec wazuh-manager /var/ossec/bin/agent_control -l

# Check indexer health
docker exec wazuh-indexer curl -sk https://localhost:9200/_cluster/health

# Test API authentication
curl -k -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.102:55000/security/user/authenticate"

# Restart manager (then remove .restart file!)
docker exec wazuh-manager /var/ossec/bin/wazuh-control restart
docker exec wazuh-manager rm -f /var/ossec/var/run/.restart

# Stop the stack
docker compose down
```

---

## Appendix B: File Reference

| File | Container Path | Purpose |
|------|---------------|---------|
| `wazuh_manager.conf` | `/var/ossec/etc/ossec.conf` | Main manager configuration |
| `local_rules.xml` | `/var/ossec/etc/rules/local_rules.xml` | Custom detection rules (pfSense) |
| `local_decoders.xml` | `/var/ossec/etc/decoders/local_decoders.xml` | Custom log decoders (pfSense) |
| `filebeat.yml` | `/etc/filebeat/filebeat.yml` | Filebeat output to Indexer |
| `filebeat-run.sh` | `/etc/services.d/filebeat/run` | Filebeat startup script (with patch) |
| `opensearch.yml` | `/usr/share/wazuh-indexer/opensearch.yml` | OpenSearch configuration |
| `opensearch_dashboards.yml` | `/usr/share/wazuh-dashboard/config/opensearch_dashboards.yml` | Dashboard configuration |
| `.env` | N/A (project root) | Environment variables |
| `global.db` | `/var/ossec/queue/db/global.db` | Agent registry database |
| `client.keys` | `/var/ossec/etc/client.keys` | Agent authentication keys |
| `rbac.db` | `/var/ossec/api/configuration/security/rbac.db` | API user/role database |
| `api.yaml` | `/var/ossec/api/configuration/api.yaml` | API server configuration |

---

## Appendix C: Monitoring Sources

The Wazuh manager currently monitors:

| Source | Type | Details |
|--------|------|---------|
| pfSense firewall | Syslog/UDP (port 514) | Firewall pass/block events from 192.168.100.1 |
| Windows MSI agent | TCP (port 1514) | Agent ID 001 — endpoint monitoring |
| Manager itself | Local | ID 000 — internal events |
| File changes (FIM) | Syscheck | /home, /etc, /var/ossec/etc — every 12 hours |
| Active responses | Local file | `/var/ossec/logs/active-responses.log` |
| VirusTotal | Integration API | File hash enrichment for syscheck events |

---

**Last Updated:** May 4, 2026  
**Wazuh Version:** 4.9.0  
**Deployment:** Docker Compose (single-node)
