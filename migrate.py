import sqlite3

def add_column():
    conn = sqlite3.connect('instance/schooltransport.db')
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE students ADD COLUMN division TEXT')
        print("✅ Column 'division' added successfully!")
    except sqlite3.OperationalError:
        print("ℹ️ Column 'division' already exists.")
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column()