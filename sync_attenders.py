import sqlite3

def sync():
    # Update this path to your actual DB path
    conn = sqlite3.connect('instance/v4_transport.db')
    cursor = conn.cursor()

    print("🛰️ Syncing Attender Branch Names...")

    # We update the branch_id COLUMN to hold the NAME string
    # This makes it work with your func.upper() filter in app.py
    
    # For FLEET SCHOOL (Company 2)
    cursor.execute("UPDATE users SET branch_id = 'FLEETONE' WHERE username = 'shamitha'")
    cursor.execute("UPDATE users SET branch_id = 'FLEETTWO' WHERE username = 'sumithra'")

    conn.commit()
    print("✅ Shamitha -> FLEETONE")
    print("✅ Sumithra -> FLEETTWO")
    conn.close()

if __name__ == "__main__":
    sync()