import psycopg2
from flask import Flask
# ⚠️ We import db and User specifically to control the connection
from app import app, db, User
from werkzeug.security import generate_password_hash

# 🌍 YOUR RENDER EXTERNAL DATABASE URL
CLOUD_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

def force_fix():
    print("🚀 TARGET: Render PostgreSQL Cloud")
    
    # 1. Manual Clean via psycopg2
    try:
        conn = psycopg2.connect(CLOUD_URL)
        conn.autocommit = True
        cur = conn.cursor()
        print("🧨 Nuking 'users' table in the CLOUD...")
        cur.execute("DROP TABLE IF EXISTS users CASCADE;")
        cur.close()
        conn.close()
        print("✅ Cloud table dropped.")
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return

    # 2. Rebuild using the Cloud URL
    with app.app_context():
        # 🔥 CRITICAL: We force the app to use the Cloud URL right now
        app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_URL
        
        print("🏗️ Rebuilding Cloud tables...")
        db.create_all()
        
        print("🔑 Creating Super Admin in the Cloud...")
        admin = User(
            username="admin_mansoor",
            name="Mansoor Admin",
            role="super_admin",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
        print("🎊 SUCCESS! DATABASE IS REPAIRED IN THE CLOUD!")

if __name__ == "__main__":
    force_fix()