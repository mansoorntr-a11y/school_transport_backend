import sqlite3
import os

def set_school():
    db_path = os.path.join('instance', 'v4_transport.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 🏫 Update testtwo branch with school coordinates
        # Note: We use .lower() and .upper() checks to be safe
        cursor.execute("""
            UPDATE branches 
            SET latitude = 13.1187, longitude = 77.5752 
            WHERE UPPER(name) = 'TESTTWO'
        """)
        
        if cursor.rowcount == 0:
            print("⚠️ Warning: No branch named 'testtwo' was found to update.")
        else:
            conn.commit()
            print(f"✅ Success! School location set for 'testtwo' ({cursor.rowcount} row updated).")
            
    except Exception as e:
        print(f"❌ SQL Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    set_school()