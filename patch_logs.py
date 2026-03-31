import sqlite3
import os

def deep_clean_database():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'v4_transport.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🧹 Performing Deep Clean (Removing spaces & forcing Upper)...")
    
    # Clean Students Table
    cursor.execute("UPDATE students SET branch = UPPER(TRIM(branch)) WHERE branch IS NOT NULL")
    
    # Clean Branches Table
    cursor.execute("UPDATE branches SET name = UPPER(TRIM(name)) WHERE name IS NOT NULL")
    
    # Clean Attendance Logs
    cursor.execute("UPDATE attendance_logs SET branch = UPPER(TRIM(branch)) WHERE branch IS NOT NULL")

    conn.commit()
    conn.close()
    print("✅ Database is now surgically clean!")

if __name__ == "__main__":
    deep_clean_database()