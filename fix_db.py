import sqlite3
import os

def fix_v4_database():
    # 🎯 TARGET: The exact path from your app.py config
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'v4_transport.db')

    if os.path.exists(db_path):
        print(f"🔎 Found database at: {db_path}")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 1. Check if the column already exists
            cursor.execute("PRAGMA table_info(attendance_logs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'company_id' not in columns:
                print(f"➕ Adding company_id column to attendance_logs...")
                # We add the column and default it to 1 so existing data stays linked
                cursor.execute("ALTER TABLE attendance_logs ADD COLUMN company_id INTEGER DEFAULT 1")
                conn.commit()
                print("✅ Success! The column was added.")
            else:
                print("ℹ️ The company_id column already exists in v4_transport.db.")
            
            conn.close()
        except Exception as e:
            print(f"❌ Error: {e}")
    else:
        print(f"🚫 Error: Could not find {db_path}. Please check your folder structure.")

if __name__ == "__main__":
    fix_v4_database()