from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from app import db, User 

# 🌍 YOUR RENDER EXTERNAL DATABASE URL
CLOUD_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

def total_cloud_reset():
    print("🛰️ Connecting to Render PostgreSQL for a TOTAL RESET...")
    engine = create_engine(CLOUD_URL)
    
    try:
        # 1. Drop EVERYTHING
        print("🧨 Nuking ALL existing tables in the Cloud...")
        db.metadata.drop_all(bind=engine)
        print("✅ Cloud database is now empty.")

        # 2. Rebuild EVERYTHING fresh
        print("🏗️ Rebuilding all tables with the latest schema...")
        db.metadata.create_all(bind=engine)
        print("✅ All tables (Users, Buses, Students, etc.) created successfully.")
        
        # 3. Create the Admin
        Session = sessionmaker(bind=engine)
        session = Session()
        
        print("🔑 Injecting Super Admin...")
        admin = User(
            username="admin_mansoor",
            name="Mansoor Admin",
            role="super_admin",
            password_hash=generate_password_hash("admin123")
        )
        session.add(admin)
        session.commit()
        session.close()
        
        print("\n🎊 TOTAL RESET COMPLETE! The Cloud is now perfectly synced with your code.")
        print("👉 Go to: https://fleettrackpro-7017f.web.app")

    except Exception as e:
        print(f"\n❌ RESET ERROR: {e}")

if __name__ == "__main__":
    total_cloud_reset()