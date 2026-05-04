#!/usr/bin/env python3
"""Clean MSI agent from global.db, add fresh key, clear client.keys"""
import sqlite3, os, hashlib, time

db_path = "/var/ossec/queue/db/global.db"

# Kill wazuh-db to release lock
os.system("killall wazuh-db 2>/dev/null")
time.sleep(2)

# Connect
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
