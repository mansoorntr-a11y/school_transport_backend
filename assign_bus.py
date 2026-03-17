from app import app, db
from models import Child, BusRoutes, PickupDropPoint

def assign_bus_to_rohan():
    print("🚌 BUS ASSIGNMENT SCRIPT STARTED...")

    with app.app_context():
        # 1. Find the Child (Rohan)
        # We search by the specific name we created earlier
        rohan = Child.query.filter_by(student_name="Rohan").first()
        
        if not rohan:
            print("❌ Error: Could not find student 'Rohan'. Run fix_parent_data.py first!")
            return

        print(f"✅ Found Student: {rohan.student_name}")

        # 2. Assign Route Details (The text shown on the card)
        rohan.route_no = "Route 5"
        rohan.pickup_route_name = "Morning Pickup"
        rohan.pick_up_point = "Main Gate, Yelahanka"
        rohan.drop_point = "Main Gate, Yelahanka"
        rohan.grade_div = "5A"  # Just ensuring this is set

        # 3. Save changes
        db.session.commit()
        print(f"🎉 SUCCESS! Assigned {rohan.student_name} to 'Route 5' at 'Main Gate'.")

if __name__ == "__main__":
    assign_bus_to_rohan()