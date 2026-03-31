import sqlite3
import os

def audit_database():
    db_file = 'v4_transport.db' # Ensure this matches your config
    
    if not os.path.exists(db_file):
        print(f"❌ ERROR: File '{db_file}' does not exist in this folder!")
        print(f"Current folder files: {os.listdir('.')}")
        return

    print(f"🔎 Auditing: {db_file}")
    print("-" * 30)
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        if not tables:
            print("⚠️ The database is EMPTY (no tables found).")
            return

        for table in tables:
            table_name = table[0]
            if table_name == 'sqlite_sequence': continue
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"📊 Table: {table_name.ljust(15)} | Rows: {count}")
            
        conn.close()
    except Exception as e:
        print(f"❌ Script Error: {e}")

if __name__ == "__main__":
    audit_database()