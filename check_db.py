import sqlite3
import os

def scan_for_data():
    # Look for all .db files in the current folder and subfolders
    db_files = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db") and ".venv" not in root:
                db_files.append(os.path.join(root, file))

    if not db_files:
        print("❌ No database files found!")
        return

    print(f"🔎 Found {len(db_files)} database files. Checking for rows...")
    
    for db_path in db_files:
        print(f"\n--- Checking: {db_path} ---")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Corrected table fetching
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            rows = cursor.fetchall()
            tables = [r[0] for r in rows]
            
            if not tables:
                print("  Empty file (no tables).")
                continue

            has_data = False
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    if count > 0:
                        print(f"  ✅ Table '{table}' has {count} rows.")
                        has_data = True
                except:
                    continue
            
            if not has_data:
                print("  No data rows found in any table.")
            
            conn.close()
        except Exception as e:
            print(f"  Error reading file: {e}")

scan_for_data()