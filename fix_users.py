from app import app, db, User

with app.app_context():
    # 1. Put testtwo back where they belong (ID: 1)
    t2 = User.query.filter_by(username='testtwo').first()
    if t2:
        t2.company_id = 1
        print("✅ testtwo moved back to TEST SCHOOL (ID: 1)")

    # 2. Ensure fleetadmin is locked to FLEET SCHOOL (ID: 2)
    fa = User.query.filter_by(username='fleetadmin').first()
    if fa:
        fa.company_id = 2
        print("✅ fleetadmin locked to FLEET SCHOOL (ID: 2)")

    db.session.commit()