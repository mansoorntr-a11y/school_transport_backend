from sqlalchemy import create_engine, inspect

DB_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"
engine = create_engine(DB_URL)

def check_user_table():
    inspector = inspect(engine)
    columns = inspector.get_columns('users')
    print("\n🔍 The 'users' table has these columns:")
    for col in columns:
        print(f"  - {col['name']}")

if __name__ == "__main__":
    check_user_table()