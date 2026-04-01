from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash

DB_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"
engine = create_engine(DB_URL)

def create_admin():
    hashed_pw = generate_password_hash("admin123")
    # 🚀 CHANGED 'password' TO 'password_hash' BELOW
    query = text("""
        INSERT INTO users (username, password_hash, role) 
        VALUES ('admin', :pw, 'super_admin')
    """)
    
    try:
        with engine.connect() as conn:
            conn.execute(query, {"pw": hashed_pw})
            conn.commit()
            print("👑 SUPER ADMIN CREATED: User: admin | Pass: admin123")
    except Exception as e:
        print(f"❌ Still failing! Error: {e}")

if __name__ == "__main__":
    create_admin()