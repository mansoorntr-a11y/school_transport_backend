import sqlite3
import os

def final_sync():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🕵️‍♂️ Fixing Sumithra's Branch assignment...")

    # We use LIKE '%Sumithra%' to handle any case sensitivity or spaces
    cursor.execute("""
        UPDATE users 
        SET branch_id = 'FLEETTWO' 
        WHERE name LIKE '%Sumithra%' OR username LIKE '%6360%'
    """)

    conn.commit()
    count = cursor.rowcount
    print(f"✅ Successfully updated {count} record(s).")
    
    # Let's double check what is actually in the DB now
    cursor.execute("SELECT name, branch_id FROM users WHERE branch_id = 'FLEETTWO'")
    rows = cursor.fetchall()
    print(f"📍 Current FLEETTWO Staff: {rows}")

    conn.close()

if __name__ == "__main__":
    final_sync()