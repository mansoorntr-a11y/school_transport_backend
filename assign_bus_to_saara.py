from app import app, db, Student, Bus  # 👈 Use Student and Bus models

def assign_bus_to_saara():
    print("🚌 BUS ASSIGNMENT SCRIPT STARTED...")

    with app.app_context():
        # 1. Find the Child (TEST SAARA)
        # Match the name currently showing in your app
        saara = Student.query.filter_by(name="TEST SAARA").first()
        
        if not saara:
            print("❌ Error: Could not find student 'TEST SAARA'.")
            return

        print(f"✅ Found Student: {saara.name}")

        # 2. Find a Bus to link to (Important for the GPS ID)
        # We need an actual Bus ID so the button turns Green
        any_bus = Bus.query.first()
        if not any_bus:
            print("❌ Error: No buses found in the database. Create a bus first!")
            return

        # 3. Assign Route & Bus ID
        saara.bus_id = any_bus.id  # 🌟 THIS enables the "Track" button!
        saara.branch = "TESTONE"
        saara.grade = "5"
        saara.last_status = "On Bus" # 🟢 This makes the badge Green!
        
        # 4. Save changes
        db.session.commit()
        print(f"🎉 SUCCESS! Linked {saara.name} to Bus {any_bus.bus_no}.")
        print(f"📡 'bus_gps_id' will now be: {any_bus.id}")

if __name__ == "__main__":
    assign_bus_to_saara()