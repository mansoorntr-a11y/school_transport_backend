import sqlite3
import os

# 1. Try to find the database in the two most common locations
db_paths = ['instance/transport.db', 'transport.db']
db_file = None

for path in db_paths:
    if os.path.exists(path):
        db_file = path
        break

if not db_file:
    print("❌ ERROR: Could not find transport.db. Make sure you are in the backend folder.")
    exit()

print(f"🛠️ Found database at: {os.path.abspath(db_file)}")

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

def add_column(table, column, type):
    try:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {type}")
        print(f"✅ Added {column} to {table}")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print(f"ℹ️ {column} already exists in {table}")
        else:
            print(f"❌ Error on {table}.{column}: {e}")

# 2. Force add the missing columns
add_column("buses", "route_id", "INTEGER")
add_column("buses", "attender_id", "INTEGER")
add_column("students", "route_id", "INTEGER")

conn.commit()
conn.close()
print("\n🎉 Repair Complete! Restart app.py now.")