from app import app, db, Bus

with app.app_context():
    # 🕵️‍♂️ Find all buses that have no coordinates
    missing_buses = Bus.query.filter((Bus.last_lat == None) | (Bus.last_lat == 0.0)).all()
    
    if not missing_buses:
        print("✅ All buses already have coordinates!")
    else:
        print(f"🛠️ Found {len(missing_buses)} buses needing location fixes...")
        for bus in missing_buses:
            # Give them a default location near your school
            bus.last_lat = 13.1145 + (bus.id * 0.001) # Slightly offset so they don't stack
            bus.last_lng = 77.5890 + (bus.id * 0.001)
            bus.status = 'Stopped'
            print(f"📍 Updated {bus.bus_no} at {bus.last_lat}, {bus.last_lng}")
        
        db.session.commit()
        print("🚀 SUCCESS: All 4 buses are now ready for the map!")