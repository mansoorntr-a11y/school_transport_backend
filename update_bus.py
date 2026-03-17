from app import app, db, Bus
from sqlalchemy import func

with app.app_context():
    target_no = 'KA51AK3560'
    
    # 🔍 1. Try a Case-Insensitive search with spaces stripped
    bus = Bus.query.filter(func.lower(Bus.bus_no).contains(target_no.lower())).first()

    if not bus:
        # 📂 2. If STILL not found, let's see what IS in the database
        all_buses = [b.bus_no for b in Bus.query.all()]
        print(f"🕵️‍♂️ Could not find '{target_no}'. Here are the buses I DID find: {all_buses}")
    else:
        # ✅ 3. We found it! Now let's fix the data
        print(f"🎯 Found Bus: {bus.bus_no} (ID: {bus.id})")
        
        bus.last_lat = 13.1145
        bus.last_lng = 77.5890
        bus.status = 'Stopped'
        
        db.session.commit()
        print(f"🚀 SUCCESS: {bus.bus_no} is now updated and ready for the map!")