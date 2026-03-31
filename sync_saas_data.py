import sqlite3

conn = sqlite3.connect('instance/v4_transport.db')
cursor = conn.cursor()

# 1. Ensure all buses in 'TESTONE' belong to Company 1 (testschool)
cursor.execute("UPDATE buses SET company_id = 1 WHERE branch = 'TESTONE'")

# 2. Ensure all buses in 'FLEETONE' belong to Company 2 (fleetschool)
cursor.execute("UPDATE buses SET company_id = 2 WHERE branch = 'FLEETONE'")

# 3. Double check: Assign the correct branch_id to your test users
cursor.execute("UPDATE users SET branch_id = 'TESTONE' WHERE username = 'testone_incharge'")

conn.commit()
print("✅ SaaS Data Synced! Buses are now linked to their correct Companies.")
conn.close()