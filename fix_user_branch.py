import sqlite3
conn = sqlite3.connect('instance/v4_transport.db')
cursor = conn.cursor()

# Update the user to have the NAME of the branch, not just the ID
cursor.execute("UPDATE users SET branch_id = 'TESTONE' WHERE username = 'testone'")
conn.commit()
print("✅ User 'testone' updated to use branch name 'TESTONE' instead of ID.")
conn.close()