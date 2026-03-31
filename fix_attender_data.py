import sqlite3
import os

def fix_data():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🛠️ Syncing Attender Branch Names...")

    # We are setting the branch_id column to match the TEXT name 
    # so your 'func.upper' filter in app.py works perfectly.
    
    # Update Shamitha
    cursor.execute("UPDATE users SET branch_id = 'FLEETONE' WHERE name = 'shamitha' OR username = 'shamitha'")
    
    # Update Sumithra
    cursor.execute("UPDATE users SET branch_id = 'FLEETTWO' WHERE name = 'sumithra' OR username = 'sumithra'")

    conn.commit()
    print("✅ Shamitha -> FLEETONE")
    print("✅ Sumithra -> FLEETTWO")
    conn.close()

if __name__ == "__main__":
    fix_data()