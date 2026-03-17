from app import app, db, Bus

with app.app_context():
    # 1. Find the specific missing bus
    missing_bus = Bus.query.filter_by(bus_no='KA05AP1102').first()
    
    if missing_bus:
        # Give it a coordinate near the others so you can see it
        missing_bus.last_lat = 13.1160 
        missing_bus.last_lng = 77.5790
        missing_bus.status = 'Stopped'
        print(f"✅ Fixed KA05AP1102! Coordinates set to {missing_bus.last_lat}, {missing_bus.last_lng}")
    else:
        print("❌ Could not find KA05AP1102. Check if the 'bus_no' matches exactly in DB.")

    # 2. Safety Check: Fix ANY other bus that might be hiding
    all_buses = Bus.query.all()
    fixed_count = 0
    for b in all_buses:
        if not b.last_lat or b.last_lat == 0.0:
            b.last_lat = 13.1180
            b.last_lng = 77.5750
            b.status = 'Stopped'
            fixed_count += 1
            
    db.session.commit()
    print(f"🚀 Safety Sweep: Fixed {fixed_count} additional buses with empty locations.")