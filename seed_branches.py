# seed.py
from app import app, db, Branch

def seed():
    with app.app_context():
        # Update PSBN
        psbn = Branch.query.filter_by(name='PSBN').first()
        if psbn:
            psbn.latitude, psbn.longitude = 13.1187, 77.5752
        
        # ✅ Match the name 'TEST' from your database
        test_branch = Branch.query.filter_by(name='TEST').first()
        if test_branch:
            test_branch.latitude, test_branch.longitude = 13.0735, 77.5938
            
        db.session.commit()