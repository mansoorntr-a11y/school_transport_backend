import sqlite3

def patch():
    # 1. Connect to your database file
    conn = sqlite3.connect('instance/school_transport.db') # Check your filename!
    cursor = conn.cursor()

    try:
        # 2. Add the missing column
        print("Adding company_id to fee_zones...")
        cursor.execute('ALTER TABLE fee_zones ADD COLUMN company_id INTEGER REFERENCES companies(id)')
        
        # 3. Assign existing zones to your main company (usually ID 1 or 2)
        # Check your 'companies' table to see what ID 'TEST SCHOOL' has.
        cursor.execute('UPDATE fee_zones SET company_id = 2') 
        
        conn.commit()
        print("✅ Database patched successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch()