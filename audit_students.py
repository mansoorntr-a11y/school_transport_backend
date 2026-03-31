import sqlite3
import os

def check_students():
    db_path = os.path.join('instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 AUDITING STUDENTS...")
    cursor.execute("SELECT id, student_name, branch, company_id FROM students")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]} | Name: {row[1]} | Branch: '{row[2]}' | CoID: {row[3]}")
    
    conn.close()

check_students()