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
    # 1. Check columns in 'users' to see how to insert
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [c[1] for c in cursor.fetchall()]
    print(f"📊 'users' table columns: {user_cols}")

    # 2. Check if the user already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (USERNAME,))
    exists = cursor.fetchone()

    if exists:
        # Update existing user
        cursor.execute("UPDATE users SET password = ?, role = 'parent' WHERE username = ?", 
                       (HASHED_PW, USERNAME))
        print(f"🔄 SUCCESS: Password for {USERNAME} updated to '1234'.")
    else:
        # Insert new user (We only use columns we know exist)
        # We assume columns: username, password, role, branch, company_id
        cols_to_use = ['username', 'password', 'role']
        vals = [USERNAME, HASHED_PW, 'parent']
        
        if 'branch' in user_cols:
            cols_to_use.append('branch')
            vals.append('testone')
        if 'company_id' in user_cols:
            cols_to_use.append('company_id')
            vals.append(1)

        query = f"INSERT INTO users ({', '.join(cols_to_use)}) VALUES ({', '.join(['?' for _ in vals])})"
        cursor.execute(query, vals)
        print(f"✅ SUCCESS: Created new Parent account: {USERNAME}")

    conn.commit()

except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()