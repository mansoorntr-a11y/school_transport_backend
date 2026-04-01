import os
from sqlalchemy import create_engine, text

# Your Render Database URL
DB_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

engine = create_engine(DB_URL)

def reset_database():
    print("\n⚠️  WARNING: This will DELETE EVERYTHING in the Render Cloud Database.")
    confirm = input("Type 'YES' to confirm you want a total wipe: ")
    
    if confirm == "YES":
        try:
            with engine.connect() as conn:
                print("🧹 Cleaning the cloud...")
                # We wrap the command in text() for SQLAlchemy 2.0 compatibility
                conn.execute(text("TRUNCATE companies, branches, users, buses, students RESTART IDENTITY CASCADE;"))
                conn.commit()
                print("✨ SUCCESS: Cloud Database is now EMPTY and FRESH!")
        except Exception as e:
            print(f"❌ ERROR during wipe: {e}")
    else:
        print("❌ Wipe cancelled. No data was harmed.")

if __name__ == "__main__":
    reset_database()