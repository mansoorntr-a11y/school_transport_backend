import sqlite3
import os

def rescue():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. See what we have
    cursor.execute("SELECT id, name, branch, company_id FROM students")
    rows = cursor.fetchall()
    print(f"📊 Current Database State ({len(rows)} students):")
    for r in rows:
        print(r)

    print("\n🛠️ Fixing Company IDs...")
    # 2. Force all students to Company 1 for testing (since your logs show CoID=1)
    cursor.execute("UPDATE students SET company_id = 1 WHERE company_id IS NULL OR company_id = 0")
    
    # 3. Force all branch names to match the expected 'TESTONE'
    cursor.execute("UPDATE students SET branch = 'TESTONE' WHERE branch LIKE '%test%' OR branch LIKE '%TEST%'")

    conn.commit()
    conn.close()
    print("✅ Rescue complete! Restart server and check now.")

if __name__ == "__main__":
    rescue()