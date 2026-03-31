import sqlite3
import os

def fix_names():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔧 Fixing existing attenders with empty names...")
    # This copies the current 'contact_number' or 'username' into the 'name' column 
    # for any record where name is empty, so it's not blank.
    # After this, you can manually edit them in the app to set the real name!
    cursor.execute("UPDATE users SET name = 'New Attender' WHERE name IS NULL AND role = 'attender'")
    
    conn.commit()
    conn.close()
    print("✅ Done! Now edit the attenders in the app to set their correct names.")

if __name__ == "__main__":
    fix_names()