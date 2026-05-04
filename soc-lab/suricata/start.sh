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
