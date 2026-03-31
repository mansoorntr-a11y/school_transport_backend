import sqlite3
import os

def final_fix():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🛠️ Fixing User 'testone' (Changing string to ID)...")
    # 1. Find the actual ID for the 'TESTONE' branch
    cursor.execute("SELECT id FROM branches WHERE name = 'TESTONE' AND company_id = 1")
    branch_row = cursor.fetchone()
    
    if branch_row:
        branch_id = branch_row[0]
        # Update the user to use the Integer ID instead of the string 'TESTONE'
        cursor.execute("UPDATE users SET branch_id = ? WHERE username = 'testone'", (branch_id,))
        print(f"✅ User 'testone' updated to Branch ID: {branch_id}")
    else:
        print("❌ ERROR: Could not find a branch named 'TESTONE' for Company 1")

    print("\n🛠️ Force-Syncing Students for Company 1...")
    # 2. Ensure students 1, 2, 9 are exactly 'TESTONE'
    cursor.execute("UPDATE students SET branch = 'TESTONE' WHERE id IN (1, 2, 9)")
    # 3. Ensure students 3, 4 are exactly 'TESTTWO'
    cursor.execute("UPDATE students SET branch = 'TESTTWO' WHERE id IN (3, 4)")

    conn.commit()
    conn.close()
    print("\n✨ ALL SYSTEMS ALIGNED! Try logging in as 'testone' now.")

if __name__ == "__main__":
    final_fix()