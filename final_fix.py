import sqlite3
import os

# 📂 Define the path to your database
db_path = os.path.join('instance', 'school_transport.db')

if not os.path.exists(db_path):
    print(f"❌ Error: Could not find database at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 🔍 1. Let's find out what your table is actually named
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"📁 Found tables: {tables}")

    # 🚀 2. Identify the correct table (usually 'student' or 'students')
    target_table = None
    if 'student' in tables:
        target_table = 'student'
    elif 'students' in tables:
        target_table = 'students'

    if target_table:
        # 💳 3. Mark your test tags as PAID
        tags = ('CARD123', 'CARD124', 'CARD125')
        query = f"UPDATE {target_table} SET payment_status = 'Paid' WHERE rfid_tag IN (?, ?, ?)"
        cursor.execute(query, tags)
        conn.commit()
        print(f"✅ SUCCESS: Updated {cursor.rowcount} students in '{target_table}' table!")
    else:
        print("❌ Error: Could not find a 'student' or 'students' table.")

    conn.close()