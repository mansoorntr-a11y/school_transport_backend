import sqlite3
import os

def universal_sync():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 Standardizing all Branch IDs to Names...")

    # 1. Update FLEET School Incharges
    cursor.execute("UPDATE users SET branch_id = 'FLEETONE' WHERE username = 'fleetone'")
    cursor.execute("UPDATE users SET branch_id = 'FLEETTWO' WHERE username = 'fleettwo'")

    # 2. Update TEST School Incharges
    cursor.execute("UPDATE users SET branch_id = 'TESTONE' WHERE username = 'testone'")
    cursor.execute("UPDATE users SET branch_id = 'TESTTWO' WHERE username = 'testtwo'")

    conn.commit()
    print("✅ All Branch Incharges synced to Branch Names.")
    conn.close()

if __name__ == "__main__":
    universal_sync()