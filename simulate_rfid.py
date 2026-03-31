import requests

# 📝 Using your specific tag
STUDENT_TAG = "CARD123" 
BUS_NO = "KA05AP1124" # Or any bus that is currently moving
BASE_URL = "http://127.0.0.1:5000/api/simulate/tap/tag"

print(f"📇 Simulating Tap for {STUDENT_TAG} on Bus {BUS_NO}...")

try:
    response = requests.get(f"{BASE_URL}/{STUDENT_TAG}/{BUS_NO}")
    if response.status_code == 201:
        print(f"✅ SUCCESS: Student {STUDENT_TAG} is now on the bus!")
        print("📍 OPEN FLUTTER: The Student Icon should appear now.")
    else:
        print(f"⚠️ Error: {response.text}")
except Exception as e:
    print(f"❌ Connection Error: {e}")