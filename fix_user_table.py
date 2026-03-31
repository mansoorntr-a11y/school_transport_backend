import sqlite3
import os

db_path = 'instance/v4_transport.db' # Path from your app.py

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        print("🛠️ Adding branch column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN branch TEXT")
        conn.commit()
        print("✅ Success!")
    except sqlite3.OperationalError:
        print("ℹ️ Branch column already exists.")
    conn.close()
else:
    print("❌ Database not found at", db_path)