import pandas as pd
from sqlalchemy import create_engine, text, inspect

# 1. Your Render External Database URL
cloud_db_url = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"
engine = create_engine(cloud_db_url)

# 2. Your Data
# I've included several possible column names (email, contact, etc.)
# The script will only use the ones that actually exist in your database.
companies_data = [
    {'id': 1, 'name': 'Greenwood International', 'contact_email': 'admin@greenwood.com', 'email': 'admin@greenwood.com'},
    {'id': 2, 'name': 'St. Marys School', 'contact_email': 'info@stmarys.com', 'email': 'info@stmarys.com'},
]

branches_data = [
    {'name': 'North Campus', 'company_id': 1},
    {'name': 'South Campus', 'company_id': 1},
    {'name': 'Main Branch', 'company_id': 2},
]

def smart_upload(table_name, data):
    try:
        # Get actual columns from the cloud table
        inst = inspect(engine)
        columns = [c['name'] for c in inst.get_columns(table_name)]
        print(f"🔎 Cloud '{table_name}' table has columns: {columns}")

        # Filter our data to only include columns that exist in the cloud
        filtered_data = []
        for entry in data:
            filtered_entry = {k: v for k, v in entry.items() if k in columns}
            filtered_data.append(filtered_entry)

        if filtered_data:
            df = pd.DataFrame(filtered_data)
            df.to_sql(table_name, engine, if_exists='append', index=False)
            print(f"✅ Successfully uploaded to {table_name}!")
        else:
            print(f"⚠️ No matching columns found for {table_name}. Check your data keys.")

    except Exception as e:
        print(f"❌ Error uploading to {table_name}: {e}")

# Run the upload
if __name__ == "__main__":
    with engine.connect() as conn:
        # 1. Upload Companies First
        smart_upload('companies', companies_data)
        
        # 2. Upload Branches Second
        smart_upload('branches', branches_data)

        # 3. Reset the ID counter so the next web entry doesn't crash
        try:
            conn.execute(text("SELECT setval('companies_id_seq', (SELECT MAX(id) FROM companies));"))
            conn.commit()
            print("✅ ID Sequence reset.")
        except:
            pass

    print("\n🚀 DONE! Check your dashboard: https://fleettrackpro-7017f.web.app/")