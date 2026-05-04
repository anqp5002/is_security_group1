#!/usr/bin/env python3
import sqlite3, os, hashlib, random, string

db_path = "/var/ossec/queue/db/global.db"

# Generate random key
key = hashlib.sha256(os.urandom(64)).hexdigest()
print("Generated key:", key)

# Determine next ID
with sqlite3.connect(db_path) as conn:
    cur = conn.cursor()
    cur.execute('SELECT MAX(CAST("id" AS INTEGER)) FROM agent')
    max_id = cur.fetchone()[0]
    if max_id is None:
        max_id = 0
    new_id = max_id + 1
    print("New agent ID:", new_id)

    # Insert into global.db
    import time
    now = int(time.time())
    cur.execute('''
        INSERT INTO agent (
            "id", "name", "ip", "register_ip", "internal_key",
            "date_add", "last_keepalive", "group", "group_hash",
            "group_sync_status", "sync_status", "connection_status",
            "disconnection_time", "group_config_status", "status_code"
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, 'MSI', 'any', 'any', key, now, now, 'default', '',
          'synced', 'synced', 'active', 0, 'synced', 0))
    conn.commit()

# Write client.keys
with open('/var/ossec/etc/client.keys', 'w') as f:
    f.write(f"{new_id} MSI any {key}\n")

print("Agent MSI added with ID", new_id)
print("Key:", key)
print("client.keys:", new_id, "MSI any", key)
