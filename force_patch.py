from app import app, db
from sqlalchemy import text

def force_patch():
    with app.app_context():
        # Using raw SQL to ensure the column is added regardless of model state
        with db.engine.connect() as conn:
            try:
                print("🛠️ Attempting to add company_id to fee_zones...")
                conn.execute(text("ALTER TABLE fee_zones ADD COLUMN company_id INTEGER"))
                conn.commit()
                print("✅ Column company_id added!")
            except Exception as e:
                print(f"ℹ️ Note: {e}")

            try:
                print("📝 Updating existing zones to Company ID 2...")
                conn.execute(text("UPDATE fee_zones SET company_id = 2 WHERE company_id IS NULL"))
                conn.commit()
                print("✅ Records updated!")
            except Exception as e:
                print(f"❌ Update failed: {e}")

if __name__ == "__main__":
    force_patch()