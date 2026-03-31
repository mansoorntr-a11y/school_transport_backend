import sqlite3
import os

def check_branches():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔎 Investigating Duplicate 'TESTONE' Branches...\n")
    
    # 1. Get all branches named TESTONE
    cursor.execute("SELECT id, name, company_id FROM branches WHERE name = 'TESTONE'")
    branches = cursor.fetchall()

    for b_id, name, c_id in branches:
        # 2. Count students for each branch ID
        cursor.execute("SELECT COUNT(*) FROM students WHERE branch = ?", (name,))
        # Note: In your current DB, students are linked by NAME string, not ID.
        # Let's check which users are linked to which ID
        cursor.execute("SELECT username FROM users WHERE branch_id = ?", (str(b_id),))
        users = cursor.fetchall()
        
        print(f"📍 Branch ID: {b_id}")
        print(f"   - Company ID: {c_id}")
        print(f"   - Linked Users: {[u[0] for u in users]}")
        print(f"   - Recommendation: {'KEEP THIS' if users else 'SAFE TO DELETE'}\n")

    conn.close()

if __name__ == "__main__":
    check_branches()