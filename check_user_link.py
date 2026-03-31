import sqlite3
import os

def check_link():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🕵️ Checking User-to-Branch Link...")
    
    # 1. Check the User
    cursor.execute("SELECT username, branch_id, company_id FROM users WHERE role LIKE '%incharge%'")
    users = cursor.fetchall()
    for u in users:
        username, b_id, c_id = u
        print(f"\n👤 User: {username}")
        print(f"   - Assigned Branch ID: {b_id}")
        print(f"   - Company ID: {c_id}")

        # 2. Check the Branch Name for that ID
        cursor.execute("SELECT name FROM branches WHERE id = ?", (b_id,))
        branch = cursor.fetchone()
        if branch:
            print(f"   - 📍 This ID points to Branch Name: '{branch[0]}'")
            
            # 3. See if students exist for that name
            cursor.execute("SELECT count(*) FROM students WHERE branch = ? AND company_id = ?", (branch[0], c_id))
            count = cursor.fetchone()[0]
            print(f"   - 🎓 Students found for this branch name: {count}")
        else:
            print(f"   - ❌ ERROR: Branch ID {b_id} does not exist in the branches table!")

    conn.close()

if __name__ == "__main__":
    check_link()