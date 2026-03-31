import sqlite3
import os

def fix_students():
    db_path = os.path.join('instance', 'v4_transport.db')
    if not os.path.exists(db_path):
        print("❌ Database not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 🕵️ 1. Find out the REAL column names
        cursor.execute("PRAGMA table_info(students)")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"📊 Columns found in 'students' table: {columns}")

        # Determine if it's 'name' or 'student_name'
        name_col = 'name' if 'name' in columns else 'student_name'

        # 🔄 2. Update students for the testtwo demo
        # We'll set the branch to 'TESTTWO' (uppercase matches your POST logic)
        cursor.execute(f"UPDATE students SET branch = 'TESTTWO' WHERE company_id = 1")
        conn.commit()
        
        # 🔍 3. Show the results
        cursor.execute(f"SELECT id, {name_col}, branch FROM students")
        rows = cursor.fetchall()
        
        print("\n✅ DATA UPDATED SUCCESSFULLY:")
        for row in rows:
            print(f"ID: {row[0]} | Name: {row[1]} | Branch set to: {row[2]}")

    except Exception as e:
        print(f"❌ Error during update: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    fix_students()