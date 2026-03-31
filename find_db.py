import os

print("🔍 Searching for your database file...")
for root, dirs, files in os.walk("."):
    for file in files:
        if file.endswith(".db"):
            print(f"✅ FOUND: {os.path.join(root, file)}")