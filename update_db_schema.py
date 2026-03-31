import sqlite3

def update_schema():
    # Path to your database
    db_path = 'instance/v4_transport.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🚀 Starting Database Update...")

    # 1. Update 'buses' table for multi-shift support
    try:
        print("Adding shift columns to 'buses' table...")
        cursor.execute("ALTER TABLE buses ADD COLUMN morning_route_id INTEGER REFERENCES routes(id)")
        cursor.execute("ALTER TABLE buses ADD COLUMN noon_route_id INTEGER REFERENCES routes(id)")
        cursor.execute("ALTER TABLE buses ADD COLUMN evening_route_id INTEGER REFERENCES routes(id)")
        cursor.execute("ALTER TABLE students ADD COLUMN morning_route_id INTEGER REFERENCES routes(id)")
        cursor.execute("ALTER TABLE students ADD COLUMN noon_route_id INTEGER REFERENCES routes(id)")
        cursor.execute("ALTER TABLE students ADD COLUMN evening_route_id INTEGER REFERENCES routes(id)")
        print("✅ 'buses' table updated.")
    except sqlite3.OperationalError:
        print("⚠️ Shift columns already exist in 'buses' table.")

    # 2. Update 'routes' table for shift tracking
    try:
        print("Adding 'shift' column to 'routes' table...")
        cursor.execute("ALTER TABLE routes ADD COLUMN shift TEXT")
        print("✅ 'routes' table updated.")
    except sqlite3.OperationalError:
        print("⚠️ 'shift' column already exists in 'routes' table.")

    conn.commit()
    conn.close()
    print("🏁 Database Schema is now in sync with your Python code!")

if __name__ == "__main__":
    update_schema()