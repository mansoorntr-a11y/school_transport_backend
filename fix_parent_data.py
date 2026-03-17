import sys
from app import app, db
from models import Parent, Child, User, Branch # Import other models to ensure tables are created

def fix_parent_data():
    print("🔥🔥🔥 FIX SCRIPT STARTED: Resetting DB & Adding Parent... 🔥🔥🔥")
    
    with app.app_context():
        # 1. This creates all tables (Parent, Child, etc.) if they are missing
        # This replaces the need to type commands in the terminal manually!
        db.create_all()
        print("✅ Database tables checked/created.")
        
        # 2. Setup the test data
        target_mobile = '9999999999'
        target_pin = '1234'
        
        print(f"🔧 Checking for Parent {target_mobile}...")

        # 3. Check if parent exists using the NEW field 'mobile'
        parent = Parent.query.filter_by(mobile=target_mobile).first()

        if not parent:
            print("   -> Parent NOT found. Creating new Parent...")
            parent = Parent(
                mobile=target_mobile, 
                pin=target_pin
            )
            db.session.add(parent)
            db.session.commit()
            print(f"✅ Created Parent {target_mobile} with PIN {target_pin}")
        else:
            print("   -> Parent found. Updating PIN...")
            parent.pin = target_pin
            db.session.commit()
            print("✅ PIN updated to 1234.")

        # 4. Ensure a Child exists and is linked
        print("🔗 Linking to a child...")
        child = Child.query.first()
        
        if not child:
            # Create a dummy child if none exists
            print("   -> No child found. Creating dummy child 'Rohan'...")
            # We need a branch/admin for the foreign keys, creating dummies if needed
            # (In a real app, you'd likely already have these)
            child = Child(
                student_name="Rohan",
                admission_no="A101",
                grade_div="5A",
                dob="2015-01-01",
                parent_id=1,    # Assumes admin user 1 exists
                branch_id=1     # Assumes branch 1 exists
            )
            # Handle potential foreign key errors gracefully in this script by skipping if strict
            try:
                db.session.add(child)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"⚠️ Could not create dummy child (Foreign Key issue): {e}")
                return

        # 5. Link the child to this mobile parent using the NEW relationship
        if child and child.mobile_parent != parent:
            child.mobile_parent = parent
            db.session.commit()
            print(f"✅ Linked child '{child.student_name}' to Parent {target_mobile}")
        elif child:
            print(f"✅ Child '{child.student_name}' is already linked.")

if __name__ == "__main__":
    fix_parent_data()