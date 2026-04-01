import sqlite3
import os

def find_my_data():
    # This looks through your folders for any database files
    db_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db") and ".venv" not in root:
                db_files.append(os.path.join(root, file))

    if not db_files:
        print("❌ No .db files found in this folder.")
        return

    for db_path in db_files:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Check if the 'companies' table exists and has rows
            cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='companies'")
            if cursor.fetchone()[0] > 0:
                cursor.execute("SELECT COUNT(*) FROM companies")
                count = cursor.fetchone()[0]
                if count > 0:
                    print(f"🌟 FOUND IT! '{db_path}' has {count} schools/clients.")
                else:
                    print(f"📁 '{db_path}' exists but the companies table is empty.")
            else:
                print(f"📁 '{db_path}' exists but doesn't have a 'companies' table.")
            conn.close()
        except Exception as e:
            print(f"⚠️ Could not check {db_path}: {e}")

print("🔎 Scanning for the file with your data...")
find_my_data()
print("Scan finished.")