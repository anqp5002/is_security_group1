# pfSense Configuration for SOC Lab

> **Firewall & Router setup for the Wazuh + Suricata SOC Lab**

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                  ┌────┴────┐
                  │  pfSense  │  (192.168.100.1)
                  │ Firewall  │
                  └────┬────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │  Docker  │   │ Windows  │   │  Other   │
    │  Host    │   │ Agent    │   │ Devices  │
    │ .100.102 │   │ .xxx     │   │ .xxx     │
    └─────────┘   └─────────┘   └─────────┘
```

### Network Details

| Parameter | Value |
|-----------|-------|
| **WAN Interface** | `192.168.100.1/24` (or ISP-assigned) |
| **LAN Interface** | `10.0.1.1/24` (internal lab network) |
| **Docker Subnet** | `172.20.0.0/24` (bridge network) |
| **pfSense WebGUI** | `https://192.168.100.1` |
| **pfSense Admin** | `admin` / `pfsense` (change on first login) |

---

## 1. Installation

### Prerequisites

- **Hardware:** Dedicated PC/mini-PC with **2+ NICs** (e.g., Protectli, Dell Wyse, or old desktop)
- **Storage:** 16GB+ SSD
- **RAM:** 2GB+ (4GB recommended)
- **USB** or **CD-ROM** for installation media

### Steps

1. **Download pfSense** from [pfsense.org/download](https://www.pfsense.org/download/)
   - Architecture: AMD64
   - Installer: USB Memstick Installer or CD-ROM ISO

2. **Create bootable USB** with Rufus (Windows) or `dd` (Linux)

3. **Boot target machine** from USB → select Installer

4. **Partitioning:**
   - Auto (ZFS) — recommended for stability
   - Or Auto (UFS) — simpler, slightly faster

5. **Reboot** → remove USB → pfSense boots to console

---

## 2. Initial Interface Assignment

At the console after first boot:

```
Should VLANS be set up now? [y/N]: N
Enter the WAN interface name: em0
Enter the LAN interface name: em1
```

> **Note:** Interface names (`em0`, `em1`, etc.) depend on your NIC hardware. Use `_` to identify which is which.

### Assign IPs via Console (Option 2)

| Interface | IP | Purpose |
|-----------|-----|---------|
| **WAN** | `192.168.100.1/24` | Host network access |
| **LAN** | `10.0.1.1/24` | Internal lab network |

---

## 3. WebGUI Configuration

After assigning IPs, access the WebGUI:

```
URL:    https://192.168.100.1
User:   admin
Pass:   pfsense    (change immediately!)
```

### 3.1. Login → System → General Setup

| Setting | Value |
|---------|-------|
| **Hostname** | `pfsense` |
| **Domain** | `soc-lab.local` |
| **DNS Servers** | `1.1.1.1`, `8.8.8.8` |
| **Timezone** | `Asia/Ho_Chi_Minh` (UTC+7) |

### 3.2. Change Admin Password

- **System** → **User Manager** → Edit `admin`
- Set a strong password

---

## 4. Firewall Rules

### 4.1. Allow Docker Host Access to WAN

Navigate to **Firewall** → **Rules** → **WAN**

Add a rule (if not already present):

| Protocol | Source | Port | Destination | Port | Description |
|----------|--------|------|-------------|------|-------------|
| TCP | `192.168.100.102` | `*` | `WAN net` | `*` | Docker host outbound |

> **Default WAN rule blocks all inbound.** No inbound ports needed unless you want remote access.

### 4.2. LAN → WAN Outbound (Auto-created)

```
Protocol  Source      Port  Destination  Port  Description
IPv4 *    10.0.1.0/24 *     *            *     LAN outbound
```

### 4.3. Port Forwarding for SOC Lab Services

**Firewall** → **NAT** → **Port Forward**

| Protocol | Source | Dest. Port | Redirect IP | Redirect Port | Description |
|----------|--------|-----------|-------------|---------------|-------------|
| TCP | `*` | `443` | `192.168.100.102` | `443` | Wazuh Dashboard |
| TCP | `*` | `1514` | `192.168.100.102` | `1514` | Wazuh Agent TCP |
| UDP | `*` | `1514` | `192.168.100.102` | `1514` | Wazuh Agent UDP |
| TCP | `*` | `55000` | `192.168.100.102` | `55000` | Wazuh API |
| TCP | `*` | `9200` | `192.168.100.102` | `9200` | Wazuh Indexer |
| TCP | `*` | `514` | `192.168.100.102` | `514` | Syslog |

### 4.4. Associated Filter Rules

When adding port forwards, pfSense will prompt:
> **"Create associated filter rule?"** → **YES** (for each rule)

---

## 5. NAT Configuration

### 5.1. Outbound NAT (Automatic)

Navigate to **Firewall** → **NAT** → **Outbound** → **Automatic**

pfSense will automatically translate LAN/Docker traffic to the WAN IP.

### 5.2. Manual Outbound NAT (if Docker traffic drops)

If Docker containers can't reach the internet, switch to:

- **Firewall** → **NAT** → **Outbound** → **Manual (Hybrid)**

Add:

| Interface | Source | Source Port | Dest. Port | NAT IP |
|-----------|--------|-------------|------------|--------|
| WAN | `172.20.0.0/24` | `*` | `*` | `192.168.100.1` |
| WAN | `10.0.1.0/24` | `*` | `*` | `192.168.100.1` |

---

## 6. DHCP Server

### 6.1. LAN DHCP (10.0.1.x)

**Services** → **DHCP Server** → **LAN**

| Setting | Value |
|---------|-------|
| **Enable** | ✓ |
| **Range** | `10.0.1.100` - `10.0.1.200` |
| **Subnet mask** | `/24` |
| **Gateway** | `10.0.1.1` |
| **DNS** | `1.1.1.1`, `8.8.8.8` |

### 6.2. DHCP Static Mappings

**Services** → **DHCP Server** → **LAN** → **Static Mapping**

| Hostname | IP | MAC (if known) |
|----------|-----|--------|
| `docker-host` | `192.168.100.102` | (host MAC) |

---

## 7. DNS Resolver (Unbound)

By default, pfSense runs Unbound on the LAN interface.

**Services** → **DNS Resolver** → **General**

| Setting | Value |
|---------|-------|
| **Enable DNS Resolver** | ✓ |
| **Network Interfaces** | LAN |
| **Outgoing Network Interfaces** | WAN |

### Custom Host Overrides

**Services** → **DNS Resolver** → **Host Overrides**

Add internal DNS records:

| Host | Domain | IP |
|------|--------|----|
| `wazuh.manager` | `soc-lab.local` | `192.168.100.102` |
| `wazuh.indexer` | `soc-lab.local` | `192.168.100.102` |
| `wazuh.dashboard` | `soc-lab.local` | `192.168.100.102` |

This allows containers to resolve hostnames via the Docker DNS (`172.20.0.1` → pfSense resolver).

---

## 8. Traffic Mirroring (SPAN) for Suricata

> **Optional — required only if running Suricata on a separate IDS host.**

Most managed switches support port mirroring (SPAN).

### Example: Cisco SG-Series

```
configure
monitor session 1 source interface gi1/0/1 both
monitor session 1 destination interface gi1/0/24
end
copy running-config startup-config
```

### Example: TP-Link/Omada

1. Navigate to **Switching** → **Mirroring**
2. **Mirror Port:** Port connected to IDS host
3. **Mirrored Port:** Port connected to WAN/LAN uplink

### pfSense as Bridge (Alternative)

If you have 3 NICs available:

| NIC | Role |
|-----|------|
| `em0` | WAN (to ISP) |
| `em1` | LAN (to internal switch) |
| `em2` | Mirror (copy of all traffic) |

> **pfSense does not have native SPAN.** For true traffic mirroring, use a managed switch.

---

## 9. VLAN Segmentation (Optional)

If your switch supports VLANs, segment the lab network:

| VLAN | ID | Subnet | Purpose |
|------|----|--------|---------|
| **Management** | 10 | `10.0.10.0/24` | pfSense, Docker host admin |
| **Servers** | 20 | `10.0.20.0/24` | Wazuh stack, Suricata |
| **Clients** | 30 | `10.0.30.0/24` | Windows agents, endpoints |
| **DMZ** | 99 | `10.0.99.0/24` | Public-facing services |

### VLAN Setup in pfSense

1. **Interfaces** → **Assignments** → **VLANs** → Add each VLAN
2. **Interfaces** → **Assignments** → Assign VLAN as new interface
3. **Interfaces** → **{VLAN_IF}** → Enable + configure IPv4
4. **Firewall** → **Rules** → Create inter-VLAN rules

---

## 10. Integration Verification

### 10.1. Verify pfSense Connectivity

```bash
# From Docker host
ping 192.168.100.1
curl -sk https://192.168.100.1/   # Should get pfSense WebGUI redirect
```

### 10.2. Verify Container Internet Access

```bash
# From inside any container
docker exec wazuh-manager ping -c 2 1.1.1.1
docker exec wazuh-manager curl -s https://google.com | head -3
```

### 10.3. Verify Port Forwards

```bash
# From pfSense or another machine on the WAN network
curl -sk https://192.168.100.1:443    # Should reach Wazuh Dashboard
curl -sk -u wazuh-wui:wazuh-wui \
  -X POST "https://192.168.100.1:55000/security/user/authenticate"
```

### 10.4. Check Firewall Logs

**Status** → **System Logs** → **Firewall**

Look for:
- Passed connections from Docker host → WAN
- Blocked inbound attempts (expected)
- NAT translations for forwarded ports

---

## 11. Security Hardening

| Action | How | Priority |
|--------|-----|----------|
| **Change admin password** | System → User Manager | 🔴 Critical |
| **Disable SSH WAN access** | System → Advanced → SSH | 🟡 High |
| **Limit WebGUI access** | System → Advanced → WebGUI → Listen on LAN only | 🟡 High |
| **Enable pfBlockerNG** | Package Manager → pfBlockerNG (DNS blocking) | 🟢 Medium |
| **Enable Snort/Suricata** | Package Manager or external IDS | 🟢 Medium |
| **Harden SSH** | Use key auth only, change port | 🟢 Medium |
| **Auto-updates** | System → Auto Update Check | 🟢 Medium |
| **Backup config** | Diagnostics → Backup & Restore → Download | 🟢 Medium |

---

## 12. Troubleshooting

| Problem | Solution |
|---------|----------|
| **Can't access WebGUI** | Check `https://192.168.100.1` (not `http`). Default cert is self-signed → proceed anyway |
| **Docker containers can't reach internet** | Check Outbound NAT (Section 5.2). Ensure `172.20.0.0/24` is included |
| **Wazuh agent won't connect** | Verify port forward 1514/TCP+UDP. Check pfSense firewall logs for blocked packets |
| **pfSense dashboard shows high CPU** | Disable unnecessary packages. Check for traffic spikes |
| **Windows curl returns SSL error** | `schannel` on Windows rejects self-signed certs. Use `-sk` flag or add `--ssl-no-revoke` |
| **Lost internet after pfSense install** | Check WAN interface: `pfSense console → Option 1 → Assign Interfaces`. Ensure correct NIC as WAN |
| **pfSense not passing DHCP** | If modem is in bridge mode, WAN should get IP via DHCP. Check `Status → Interfaces` |

---

## 13. Quick-Start Checklist

- [ ] pfSense installed & booted
- [ ] WAN/LAN interfaces assigned correctly
- [ ] WebGUI accessible at `https://192.168.100.1`
- [ ] Admin password changed
- [ ] WAN firewall rules allow Docker host traffic
- [ ] Port forwards created for Wazuh services (443, 1514, 55000, 9200)
- [ ] Outbound NAT includes Docker subnet (`172.20.0.0/24`)
- [ ] DNS Resolver enabled for LAN
- [ ] DNS host overrides added for `wazuh.manager`, `wazuh.indexer`
- [ ] Docker containers can reach internet
- [ ] Windows Wazuh agent connects successfully
- [ ] Firewall logs reviewed for blocked traffic
- [ ] Config backed up (`Diagnostics → Backup & Restore`)

---

## References

- [pfSense Documentation](https://docs.netgate.com/pfsense/en/latest/)
- [Wazuh Documentation](https://documentation.wazuh.com/current/)
- [Suricata User Guide](https://suricata.readthedocs.io/)
- [pfSense Port Forwarding Guide](https://docs.netgate.com/pfsense/en/latest/nat/port-forwards.html)
- [pfSense VLAN Configuration](https://docs.netgate.com/pfsense/en/latest/vlan/index.html)

---

*Last Updated: May 4, 2026*
