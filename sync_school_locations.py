from app import app, db, Branch

# 🏫 Real GPS Coordinates for your school branches
BRANCH_DATA = {
    "PSBN": {
        "lat": 13.1187, 
        "lng": 77.5752, 
        "address": "Singanayakanahalli, Bengaluru"
    },
    "PSBE": {
        "lat": 13.0182, 
        "lng": 77.6534, 
        "address": "Kasturi Nagar, Bengaluru"
    }
}

def sync_branches():
    with app.app_context():
        print("🔄 SYNCING SCHOOL LOCATIONS...")
        for name, info in BRANCH_DATA.items():
            # Find the existing branch entry
            branch = Branch.query.filter_by(name=name).first()
            if branch:
                # ✅ Update the missing Lat/Lng values
                branch.latitude = info['lat']
                branch.longitude = info['lng']
                branch.location = info['address']
                print(f"✅ Updated {name} with Coordinates.")
            else:
                # Create it if it doesn't exist
                new_branch = Branch(
                    name=name, 
                    latitude=info['lat'], 
                    longitude=info['lng'], 
                    location=info['address']
                )
                db.session.add(new_branch)
                print(f"🆕 Created {name} with Coordinates.")
        
        db.session.commit()
        print("🎉 ALL BRANCHES SYNCED SUCCESSFULLY!")

if __name__ == "__main__":
    sync_branches()