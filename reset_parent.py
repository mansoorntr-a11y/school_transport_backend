import sqlite3
from werkzeug.security import generate_password_hash

db_path = 'instance/v4_transport.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 📝 Credentials
USERNAME = "9845931891"
PASSWORD = "1234"
HASHED_PW = generate_password_hash(PASSWORD)

try:
    # 1. Get the Student ID for CARD123
    cursor.execute("SELECT id, branch, company_id FROM students WHERE rfid_tag = 'CARD123'")
    student = cursor.fetchone()
    
    if student:
        s_id, branch, c_id = student
        
        # 2. Check if user already exists
        cursor.execute("SELECT id FROM user WHERE username = ?", (USERNAME,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Update existing user
            cursor.execute("UPDATE user SET password = ?, role = 'parent', student_id = ? WHERE username = ?", 
                           (HASHED_PW, s_id, USERNAME))
            print(f"🔄 SUCCESS: User {USERNAME} updated with password '1234'")
        else:
            # Insert new user
            cursor.execute("INSERT INTO user (username, password, role, branch, company_id, student_id) VALUES (?, ?, 'parent', ?, ?, ?)",
                           (USERNAME, HASHED_PW, 'parent', branch, c_id, s_id))
            print(f"✅ SUCCESS: New Parent account created for {USERNAME}")
            
        conn.commit()
    else:
        print("❌ Error: CARD123 not found in students table.")

except Exception as e:
    print(f"⚠️ Error: {e}")
finally:
    conn.close()