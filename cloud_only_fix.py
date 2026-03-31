from sqlalchemy import create_engine, text
from app import db, User, Bus, Student, Client, Branch # Import all your models
from werkzeug.security import generate_password_hash

# 🌍 YOUR RENDER EXTERNAL DATABASE URL
CLOUD_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

def total_repair():
    print("🛰️ Connecting to Render PostgreSQL...")
    engine = create_engine(CLOUD_URL)
    
    try:
        with engine.connect() as conn:
            print("🧨 DROPPING ALL OLD TABLES (Cleaning the slate)...")
            # This wipes everything: users, buses, students, clients, etc.
            conn.execute(text("DROP TABLE IF EXISTS students, buses, bus_locations, branches, clients, users CASCADE;"))
            conn.commit()
            print("✅ Cloud database is now empty.")

        print("🏗️ Rebuilding entire SaaS structure from models...")
        db.metadata.create_all(bind=engine)
        
        # 🔑 Create the Super Admin
        from sqlalchemy.orm import sessionmaker
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🔑 Injecting Master Super Admin...")
        admin = User(
            username="admin_mansoor",
            name="Mansoor Admin",
            role="super_admin",
            password_hash=generate_password_hash("admin123")
        )
        session.add(admin)
        session.commit()
        session.close()
        
        print("\n🎊 TOTAL REPAIR COMPLETE! Everything is synced.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    total_repair()