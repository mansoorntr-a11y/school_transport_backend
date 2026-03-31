from app import app, db, User

with app.app_context():
    print("\n--- DATABASE USER CHECK ---")
    users = User.query.all()
    for u in users:
        school_name = u.company.name if u.company else "GLOBAL/SUPERADMIN"
        print(f"👤 {u.username.ljust(15)} | Role: {u.role.ljust(10)} | School: {school_name} (ID: {u.company_id})")
    print("---------------------------\n")