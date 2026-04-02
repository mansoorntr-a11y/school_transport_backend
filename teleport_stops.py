from app import app, db, Stop

with app.app_context():
    # Find all stops where the branch is empty or null
    homeless_stops = Stop.query.filter((Stop.branch == "") | (Stop.branch == None)).all()
    
    for s in homeless_stops:
        s.branch = "TESTONE"
    
    db.session.commit()
    print(f"✅ RESCUED: Moved {len(homeless_stops)} homeless stops to TESTONE!")