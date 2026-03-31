from app import app, db, Student

with app.app_context():
    student = Student.query.filter_by(name="TEST SAARA").first()
    if student:
        student.payment_status = "Paid"
        student.last_status = "On Bus" # This makes the badge green!
        student.total_fee = 20.0
        db.session.commit()
        print("✅ SUCCESS: TEST SAARA is now PAID and ON BUS.")
    else:
        print("❌ Student not found. Check the name in your database.")