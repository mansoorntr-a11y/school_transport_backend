from app import app, db, Stop

with app.app_context():
    # Update all stops that say 'TEST1' to 'TESTONE'
    updated = Stop.query.filter_by(branch='TEST1').update({Stop.branch: 'TESTONE'})
    db.session.commit()
    print(f"✅ Success! Moved {updated} stops from TEST1 to TESTONE.")