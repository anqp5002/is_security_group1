#!/bin/sh
# Apply OpenSearch 2.x compatibility setting to allow Filebeat 7.x _type in bulk requests.
# Fixes: "Action/metadata line [1] contains an unknown parameter [_type]"
curl -sk -u admin:admin -X PUT "https://localhost:9200/_cluster/settings" \
  -H "Content-Type: application/json" \
  -d '{"persistent":{"compatibility":{"override_main_response_version":"true"}}}'
