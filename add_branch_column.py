import sqlite3
import os

def add_column():
    # 📂 Path to your specific database
    db_path = os.path.join('instance', 'v4_transport.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Error: Could not find the database at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 💉 The SQL injection (adding the missing column)
        cursor.execute("ALTER TABLE routes ADD COLUMN branch_id INTEGER")
        
        conn.commit()
        conn.close()
        print("✅ SUCCESS: The 'branch_id' column has been added to the routes table!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Info: The column already exists, you're all set!")
        else:
            print(f"❌ SQL Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_column()