from app import app, db, Stop

with app.app_context():
    # Find all stops that accidentally got labeled 'TEST1'
    stops_to_fix = Stop.query.filter_by(branch='TEST1').all()
    
    for s in stops_to_fix:
        s.branch = 'TESTONE'
    
    db.session.commit()
    print(f"✅ Successfully moved {len(stops_to_fix)} stops to TESTONE!")