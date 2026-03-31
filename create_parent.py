import sqlite3
import os
from werkzeug.security import generate_password_hash

# 📂 Use the 'v4_transport.db' since that's the one we updated!
db_path = 'instance/v4_transport.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 📝 Credentials for your demo
username = "parent1"
password = "password123"
hashed_pw = generate_password_hash(password)

try:
    # 1. Find the student ID for CARD123
    cursor.execute("SELECT id, branch, company_id FROM students WHERE rfid_tag = 'CARD123'")
    student = cursor.fetchone()
    
    if student:
        s_id, branch, c_id = student
        # 2. Create the Parent User linked to this student
        cursor.execute("""
            INSERT INTO user (username, password, role, branch, company_id, student_id) 
            VALUES (?, ?, 'parent', ?, ?, ?)
        """, (username, hashed_pw, branch, c_id, s_id))
        
        conn.commit()
        print(f"✅ SUCCESS: Parent account created!")
        print(f"👤 Username: {username}")
        print(f"🔑 Password: {password}")
    else:
        print("❌ Error: Could not find student with tag 'CARD123'.")

except Exception as e:
    print(f"⚠️ Error: {e} (Account might already exist)")

finally:
    conn.close()