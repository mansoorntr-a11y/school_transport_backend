import sqlite3
import os

# List of all the database files found in your instance folder
db_files = [
    'instance/transport.db',
    'instance/school_transport.db',
    'instance/schooltransport.db',
    'instance/v4_transport.db'
]

def repair_specific_file(file_path):
    if not os.path.exists(file_path):
        return

    print(f"\n🔍 Checking: {file_path}")
    conn = sqlite3.connect(file_path)
    cursor = conn.cursor()

    # Check if 'buses' table actually exists in this file
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buses'")
    if not cursor.fetchone():
        print(f"  Empty file (no tables found). Skipping.")
        conn.close()
        return

    print(f"  ✨ Found your data! Repairing this file...")

    # List of columns to add
    updates = [
        ("buses", "route_id", "INTEGER"),
        ("buses", "attender_id", "INTEGER"),
        ("students", "route_id", "INTEGER")
    ]

    for table, col, col_type in updates:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
            print(f"  ✅ Added {col} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"  ℹ️ {col} already exists in {table}")
            else:
                print(f"  ❌ Error on {table}: {e}")

    conn.commit()
    conn.close()
    print(f"  🎉 This file is now fixed and your data is safe!")

# Run the check on every file
for db in db_files:
    repair_specific_file(db)

print("\n🚀 All done! You can now restart app.py.")