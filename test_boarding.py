import requests

# 📝 Configuration
# Make sure this Tag exists in your student table!
STUDENT_TAG = "RF8877" 
BUS_NO = "KA05AP1124"
BASE_URL = "http://127.0.0.1:5000/api/simulate/tap/tag"

print(f"📇 Simulating Student Tap...")

try:
    # This tells the backend: "Student just got on the bus!"
    response = requests.get(f"{BASE_URL}/{STUDENT_TAG}/{BUS_NO}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"✅ SUCCESS: {data['student']} has BOARDED {BUS_NO}")
        print("📍 NOW: Check your Flutter Map. You should see the Student Icon!")
    else:
        print(f"❌ Error: {response.json().get('error')}")
except Exception as e:
    print(f"❌ Connection Error: {e}")