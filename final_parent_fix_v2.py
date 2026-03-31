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
    # 1. Check if the user already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
    exists = cursor.fetchone()

    if exists:
        # Update existing user using the correct 'password_hash' column
        cursor.execute("UPDATE users SET password_hash = ?, role = 'parent' WHERE username = ?", 
                       (HASHED_PW, USERNAME))
        print(f"🔄 SUCCESS: User {USERNAME} updated with password '1234'.")
    else:
        # Insert new user with the specific columns found in your DB
        # Columns: id, company_id, username, password_hash, role, branch_id, contact_number, branch
        query = """
            INSERT INTO users (username, password_hash, role, branch, company_id) 
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (USERNAME, HASHED_PW, 'parent', 'testone', 1))
        print(f"✅ SUCCESS: Created new Parent account: {USERNAME}")

    conn.commit()

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()