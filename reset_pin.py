from app import app, db
from models import Parent

def reset_parent_pin():
    with app.app_context():
        # Find the test parent
        phone = "9999999999"
        parent = Parent.query.filter_by(phone_number=phone).first()
        
        if parent:
            print(f"Found Parent: {parent.parent_name}")
            print(f"Old PIN Hash: {parent.password_hash}")
            
            # FORCE RESET to simple text "1234" for testing
            parent.password_hash = "1234" 
            db.session.commit()
            
            print(f"✅ SUCCESS: PIN for {phone} has been reset to '1234'")
        else:
            print(f"❌ ERROR: Parent {phone} not found in database!")

if __name__ == "__main__":
    reset_parent_pin()