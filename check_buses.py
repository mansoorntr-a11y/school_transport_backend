import sqlite3
conn = sqlite3.connect('instance/v4_transport.db')
cursor = conn.cursor()

print("📋 CURRENT BUSES IN DATABASE:")
cursor.execute("SELECT id, bus_no, branch FROM buses")
rows = cursor.fetchall()
for row in rows:
    print(f"ID: {row[0]} | Number: {row[1]} | Branch: '{row[2]}'")
conn.close()