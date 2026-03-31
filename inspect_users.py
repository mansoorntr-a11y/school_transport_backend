import sqlite3

# 📂 Always point to the 'v4' database now
db_path = 'instance/v4_transport.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # 🔍 1. Find the table name
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"📁 Tables in DB: {tables}")

    # 🔍 2. Check the users
    # We try 'user' then 'users'
    table_name = 'user' if 'user' in tables else 'users'
    
    cursor.execute(f"SELECT id, username, role, student_id FROM {table_name}")
    users = cursor.fetchall()
    print(f"\n👥 Current Users in '{table_name}':")
    for u in users:
        print(f"ID: {u[0]} | Username: {u[1]} | Role: {u[2]} | Linked Student ID: {u[3]}")

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()