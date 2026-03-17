from app import app, db, Company, User

def fix_identities():
    with app.app_context():
        # 1. Fix Company 1 (Default)
        co1 = db.session.get(Company, 1)
        if co1:
            co1.name = "FleetTrack Central"
            print("✅ Company 1 renamed to FleetTrack Central")

        # 2. Fix Company 2 (The one testone belongs to)
        co2 = db.session.get(Company, 2)
        if co2:
            co2.name = "testschool"
            print("✅ Company 2 renamed to testschool")
        else:
            new_co = Company(id=2, name="testschool")
            db.session.add(new_co)
            print("✅ Company 2 created as testschool")

        # 3. Ensure testone is linked to Company 2
        user = User.query.filter_by(username='testone').first()
        if user:
            user.company_id = 2
            print(f"✅ User {user.username} locked to Company 2")

        db.session.commit()
        print("🚀 Database Identity Sync Complete!")

if __name__ == "__main__":
    fix_identities()