import sqlite3
import pandas as pd
from sqlalchemy import create_engine
import os

# 1. Corrected Path: Since you are already in the 'school_transport_backend' folder
local_db = 'instance/v4_transport.db' 

# 2. Your External Database URL
cloud_db_url = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

# Ensure correct prefix for SQLAlchemy
if cloud_db_url.startswith("postgres://"):
    cloud_db_url = cloud_db_url.replace("postgres://", "postgresql://", 1)

local_conn = None # Initialize to avoid NameError

try:
    # Check if the file actually exists before trying to open it
    if not os.path.exists(local_db):
        print(f"❌ Error: Could not find the file at {local_db}")
        print("Make sure you are running this from the 'school_transport_backend' folder.")
    else:
        print("✅ Found local database. Connecting...")
        local_conn = sqlite3.connect(local_db)
        
        print("Connecting to Cloud PostgreSQL...")
        cloud_engine = create_engine(cloud_db_url)

        # Tables to migrate
        tables = ['clients', 'branches', 'admins', 'schools', 'users']

        for table in tables:
            print(f"🔄 Migrating {table}...")
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", local_conn)
                
                if df.empty:
                    print(f"ℹ️ {table} is empty locally. Skipping.")
                    continue

                # Push to Cloud
                df.to_sql(table, cloud_engine, if_exists='append', index=False)
                print(f"✅ {table} moved successfully ({len(df)} rows)!")
            except Exception as table_err:
                # This usually happens if the table doesn't exist in SQLite yet
                print(f"⚠️ Skipping {table}: {table_err}")

        print("\n🚀 DATA MIGRATION COMPLETE!")
        print("Refresh: https://fleettrackpro-7017f.web.app/")

except Exception as e:
    print(f"❌ Migration failed: {e}")
finally:
    if local_conn:
        local_conn.close()