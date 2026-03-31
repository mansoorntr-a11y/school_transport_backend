import sqlite3
import os

def add_column():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔧 Adding 'name' column to users table...")
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
        conn.commit()
        print("✅ Column added successfully!")
    except Exception as e:
        print(f"ℹ️ Note: {e} (It might already exist)")
    
    conn.close()

if __name__ == "__main__":
    add_column()