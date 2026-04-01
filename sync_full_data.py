import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

# 1. PATH: Change this to the path the scanner found!
local_db = 'instance/v4_transport.db' 
cloud_db_url = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

engine = create_engine(cloud_db_url, pool_pre_ping=True)

tables_to_sync = [
    'companies', 'branches', 'users', 'fee_zones', 
    'routes', 'stops', 'buses', 'students', 
    'notice', 'bus_history', 'fee_records', 'attendance_logs'
]

def migrate():
    try:
        local_conn = sqlite3.connect(local_db)
        print(f"✅ Connected to local: {local_db}")
        
        with engine.begin() as cloud_conn:
            print("🧹 Clearing cloud tables...")
            cloud_conn.execute(text(f"TRUNCATE TABLE {', '.join(tables_to_sync)} RESTART IDENTITY CASCADE;"))
            
            for table in tables_to_sync:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", local_conn)
                    if df.empty:
                        print(f"  ℹ️ {table} is empty. Skipping.")
                        continue
                    
                    print(f"  🚀 Uploading {table} ({len(df)} rows)...")
                    # Added 'multi' and 'chunksize' to prevent hanging
                    df.to_sql(table, engine, if_exists='append', index=False, method='multi', chunksize=100)
                    print(f"  ✅ {table} Done.")
                except Exception as e:
                    print(f"  ⚠️ Error on {table}: {e}")

        print("\n✨ SYNC FINISHED! Check your live dashboard now.")

    except Exception as e:
        print(f"❌ Critical Error: {e}")
    finally:
        local_conn.close()

migrate()