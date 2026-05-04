#!/usr/bin/with-contenv sh
# Patches filebeat.yml before starting Filebeat.
# Fixes: "Action/metadata line [1] contains an unknown parameter [_type]"
# when connecting to OpenSearch 2.x (which removed _type support).
# OpenSearch 2.x rejects ES 7 bulk format that includes _type in action metadata.
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
