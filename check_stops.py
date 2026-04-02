import pandas as pd
from app import app, db, Stop

with app.app_context():
    stops = Stop.query.all()
    print("\n" + "="*50)
    print(f"📊 DATABASE REPORT: {len(stops)} TOTAL STOPS FOUND")
    print("="*50)
    
    if len(stops) == 0:
        print("❌ The database is empty!")
    else:
        for s in stops:
            # This helps us see if the Branch or Company ID is the problem
            print(f"ID: {s.id} | Name: {s.stop_name} | Branch: [{s.branch}] | CoID: {s.company_id}")
    print("="*50 + "\n")