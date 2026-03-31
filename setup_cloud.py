from app import app, db, User
from werkzeug.security import generate_password_hash

# 🚀 YOUR RENDER EXTERNAL DATABASE URL
CLOUD_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_URL

with app.app_context():
    print("🧨 Dropping old tables to fix schema...")
    db.drop_all() # 👈 This wipes the old, broken tables
    
    print("🏗️ Rebuilding tables with new columns (including 'name')...")
    db.create_all() # 👈 This creates them fresh with the 'name' column
    
    # 🔑 Create the Super Admin again
    admin = User(
        username="admin_mansoor",
        name="Mansoor Admin", # 👈 Now this column actually exists!
        role="super_admin",
        password_hash=generate_password_hash("admin123")
    )
    db.session.add(admin)
    db.session.commit()
    print("✅ DATABASE IS NOW 100% CORRECT AND LIVE!")