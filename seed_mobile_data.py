from app import app, db
from models import Parent, Child, Bus, BusLocation
from werkzeug.security import generate_password_hash
import datetime

def seed_data():
    with app.app_context():
        print("🌱 Seeding Mobile App Data...")

        # 1. Create a Test Parent (Mobile Login)
        test_phone = "9999999999"
        test_pin = "1234" # Simple PIN for app
        
        # Check if exists
        if Parent.query.filter_by(phone_number=test_phone).first():
            print(f"⚠️ Parent {test_phone} already exists. Skipping creation.")
            mobile_parent = Parent.query.filter_by(phone_number=test_phone).first()
        else:
            mobile_parent = Parent(
                parent_name="Test Father",
                phone_number=test_phone,
                password_hash=test_pin # In real app, hash this!
            )
            db.session.add(mobile_parent)
            db.session.commit()
            print(f"✅ Created Mobile Parent: {test_phone} (PIN: {test_pin})")

        # 2. Link a Child to this Parent
        # We try to find ANY child in the system
        child = Child.query.first()
        if child:
            child.mobile_parent_id = mobile_parent.id
            db.session.commit()
            print(f"✅ Linked Child '{child.student_name}' to Parent {test_phone}")
        else:
            print("❌ No children found in DB to link! Create a child in Admin Panel first.")

        # 3. Add Dummy GPS Data for the Bus
        bus = Bus.query.first()
        if bus:
            print(f"📍 Adding GPS data for Bus {bus.bus_number}...")
            # Create a location near Bangalore (Yelahanka area)
            loc = BusLocation(
                bus_id=bus.id,
                latitude=13.1007, 
                longitude=77.5963,
                speed=45.5,
                timestamp=datetime.datetime.utcnow()
            )
            db.session.add(loc)
            db.session.commit()
            print("✅ GPS Data Added!")
        else:
            print("❌ No Bus found to add GPS data.")

        print("\n🎉 Data Seeding Complete! You can now test the Mobile Login.")

if __name__ == "__main__":
    seed_data()