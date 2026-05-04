#!/usr/bin/env python3
import sqlite3, os

db_path = "/var/ossec/queue/db/global.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Discover columns and quote them
cur.execute("PRAGMA table_info(agent)")
columns = ['"' + col[1] + '"' for col in cur.fetchall()]
print("Columns:", columns)

# List all agents
query = "SELECT " + ",".join(columns) + " FROM agent"
cur.execute(query)
rows = cur.fetchall()
print("Current agents:")
for r in rows:
    print(" ", r)

# Delete agent named MSI
cur.execute('DELETE FROM agent WHERE "name" = \'MSI\'')
print("Deleted", cur.rowcount, "agent(s) named 'MSI'")
conn.commit()

# Verify
cur.execute(query)
remaining = cur.fetchall()
print("Remaining:", len(remaining))
conn.close()

# Clear client.keys
os.system("> /var/ossec/etc/client.keys")
print("Cleared client.keys")
