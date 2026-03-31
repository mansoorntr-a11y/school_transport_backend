import sqlite3

def update_students_table():
    db_path = 'instance/v4_transport.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 Adding multi-shift columns to Students table...")
    columns = [
        "morning_route_id INTEGER REFERENCES routes(id)",
        "noon_route_id INTEGER REFERENCES routes(id)",
        "evening_route_id INTEGER REFERENCES routes(id)"
    ]

    for col in columns:
        try:
            cursor.execute(f"ALTER TABLE students ADD COLUMN {col}")
            print(f"✅ Added {col.split()[0]}")
        except sqlite3.OperationalError:
            print(f"⚠️ Column {col.split()[0]} already exists.")

    conn.commit()
    conn.close()
    print("🏁 Students table is now updated!")

if __name__ == "__main__":
    update_students_table()