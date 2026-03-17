from app import app, db, Bus
ctx = app.app_context()
ctx.push()

# Try finding by registration_no or bus_no
bus = Bus.query.filter((Bus.registration_no == 'KA51AK3560') | (Bus.bus_no == 'KA51AK3560')).first()

if bus:
    # Set coordinates (using getattr to be safe again)
    if hasattr(bus, 'last_lat'):
        bus.last_lat = 13.1145
        bus.last_lng = 77.5890
    else:
        bus.last_latitude = 13.1145
        bus.last_longitude = 77.5890
        
    bus.status = 'Stopped'
    db.session.commit()
    print("✅ Successfully updated Bus KA51AK3560!")
else:
    print("❌ Still couldn't find that bus. Check the registration number spelling!")