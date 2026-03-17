from app import app, db, Bus

with app.app_context():
    # 1. Target the missing bus specifically
    # Using 'KA05AP1102' as the bus_no
    missing_bus = Bus.query.filter_by(bus_no='KA05AP1102').first()
    
    if missing_bus:
        missing_bus.last_lat = 13.1160 
        missing_bus.last_lng = 77.5790
        missing_bus.status = 'Stopped'
        print(f"✅ Fixed KA05AP1102! Coordinates set.")
    else:
        print("❌ Could not find KA05AP1102. Check the spelling in your database.")

    # 2. Safety Sweep for ALL buses
    all_buses = Bus.query.all()
    fixed_count = 0
    for b in all_buses:
        # If coordinates are missing, 0.0, or None
        if not b.last_lat or b.last_lat == 0.0:
            b.last_lat = 13.1180
            b.last_lng = 77.5750
            b.status = 'Stopped'
            fixed_count += 1
            
    db.session.commit()
    print(f"🚀 Safety Sweep: Fixed {fixed_count} total buses with empty locations.")