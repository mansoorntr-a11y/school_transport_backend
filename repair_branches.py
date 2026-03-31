import sqlite3
import os

def repair_data():
    db_path = os.path.join('instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 🏫 Move original students back to TESTONE
        cursor.execute("UPDATE students SET branch = 'TESTONE' WHERE id IN (1, 2, 9)")
        
        # 🏫 Keep/Move the others in TESTTWO
        cursor.execute("UPDATE students SET branch = 'TESTTWO' WHERE id IN (3, 4)")
        
        conn.commit()
        print("✅ REPAIR COMPLETE: Students have been moved back to their correct branches.")
        
        # 🔍 Double check
        cursor.execute("SELECT id, name, branch FROM students WHERE company_id = 1")
        for row in cursor.fetchall():
            print(f"ID: {row[0]} | Name: {row[1]} | Branch: {row[2]}")

    except Exception as e:
        print(f"❌ Repair Error: {e}")
    finally:
        conn.close()

repair_data()