from app import app, db, User
from werkzeug.security import generate_password_hash

# 🚀 PASTE YOUR RENDER EXTERNAL DATABASE URL HERE
CLOUD_URL = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

# 🛡️ Force the app to use the Cloud URL instead of Local SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = CLOUD_URL

with app.app_context():
    print("📡 Connecting to Render PostgreSQL...")
    
    # 🏗️ Create the tables in the cloud
    db.create_all()
    print("✅ Cloud Tables Created Successfully!")

    # 🔑 Create your Master Access
    admin_exists = User.query.filter_by(username="admin_mansoor").first()
    if not admin_exists:
        admin = User(
            username="admin_mansoor",
            role="super_admin",
            password_hash=generate_password_hash("admin123")
        )
        db.session.add(admin)
        db.session.commit()
        print("✅ Super Admin 'admin_mansoor' created in the Cloud!")
    else:
        print("ℹ️ Admin already exists in the Cloud.")