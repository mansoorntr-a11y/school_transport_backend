import sqlite3
import os

# 📂 These are the files we found
db_files = [
    'instance/schooltransport.db',
    'instance/school_transport.db',
    'instance/transport.db',
    'instance/v4_transport.db'
]

tags = ('CARD123', 'CARD124', 'CARD125')

print("🚀 Starting Universal Payment Fix...")

for db_path in db_files:
    if not os.path.exists(db_path):
        continue
        
    print(f"\n🔎 Checking: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all table names in this specific file
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall()]
        
        # Determine the table name (singular or plural)
        target = next((t for t in tables if 'student' in t.lower()), None)
        
        if target:
            query = f"UPDATE {target} SET payment_status = 'Paid' WHERE rfid_tag IN (?, ?, ?)"
            cursor.execute(query, tags)
            conn.commit()
            if cursor.rowcount > 0:
                print(f"✅ SUCCESS! Updated {cursor.rowcount} students in {db_path} ({target} table)")
            else:
                print(f"ℹ️ Found table '{target}' in {db_path}, but those RFID tags weren't in it.")
        else:
            print(f"❌ No student table found in {db_path}")
            
    except Exception as e:
        print(f"⚠️ Error checking {db_path}: {e}")
    finally:
        conn.close()

print("\n🏁 Process Finished!")