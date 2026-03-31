import sqlite3
import os

def audit_database():
    # 🚀 The "Magic" Path: Look inside the instance folder
    db_path = os.path.join('instance', 'v4_transport.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Still can't find it at: {db_path}")
        return

    print(f"✅ FOUND IT! Auditing: {db_path}")
    print("-" * 30)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence': continue
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 Table: {table_name.ljust(15)} | Rows: {count}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    audit_database()