from app import app, db, User, Student

with app.app_context():
    # Let's check User ID 9 (from your logs)
    user = db.session.get(User, 9)
    if not user:
        print("❌ User with ID 9 not found!")
    else:
        print(f"✅ Found User: {user.username}")
        
        # Check if any student matches this username
        students = Student.query.filter_by(parent_mobile=user.username).all()
        if not students:
            print(f"❌ DATABASE GAP: No students found with parent_mobile = '{user.username}'")
            print("To fix this, update the Student record to match the Parent's mobile number.")
        else:
            for s in students:
                print(f"⭐ Success! Found Student: {s.name} linked to this parent.")