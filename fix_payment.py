import sqlite3
import os

# 📂 Ensure we are looking at the right file
db_path = 'instance/school_transport.db'

if not os.path.exists(db_path):
    print(f"❌ Error: Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 🚀 Try 'student' (singular) first, then 'students'
        tags = ('CARD123', 'CARD124', 'CARD125')
        
        # We'll try to update 'student' table
        cursor.execute("UPDATE student SET payment_status = 'Paid' WHERE rfid_tag IN (?, ?, ?)", tags)
        
        conn.commit()
        print(f"✅ SUCCESS: {cursor.rowcount} students marked as PAID in 'student' table!")
        
    except sqlite3.OperationalError:
        # If 'student' fails, try 'students' (plural)
        try:
            cursor.execute("UPDATE students SET payment_status = 'Paid' WHERE rfid_tag IN (?, ?, ?)", tags)
            conn.commit()
            print(f"✅ SUCCESS: {cursor.rowcount} students marked as PAID in 'students' table!")
        except Exception as e:
            print(f"❌ Failed again: {e}")
            
    conn.close()