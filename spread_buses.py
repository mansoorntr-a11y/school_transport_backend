import sqlite3
import os

def spread_buses():
    # 📂 Path to your database
    db_path = os.path.join('instance', 'v4_transport.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Could not find database at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 🚐 Bus 1: Find the first bus in TESTTWO and move it slightly North
        cursor.execute("""
            UPDATE buses 
            SET last_lat = 13.1195, last_lng = 77.5765 
            WHERE id = (SELECT id FROM buses WHERE branch = 'TESTTWO' LIMIT 1)
        """)
        
        # 🚐 Bus 2: Find the second bus (OFFSET 1) and move it slightly South
        cursor.execute("""
            UPDATE buses 
            SET last_lat = 13.1180, last_lng = 77.5745 
            WHERE id = (SELECT id FROM buses WHERE branch = 'TESTTWO' LIMIT 1 OFFSET 1)
        """)
        
        conn.commit()
        print("✅ Success! The two buses are now at different locations.")
        
    except Exception as e:
        print(f"❌ SQL Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    spread_buses()