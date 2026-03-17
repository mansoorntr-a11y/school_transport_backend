import requests

# 🔗 Your local backend URL
URL = "http://127.0.0.1:5000/api/hardware/rfid"

# 🎒 Enter an RFID tag that exists in your database
test_tag = input("Enter Student RFID Tag to simulate scan: ")

try:
    response = requests.post(URL, json={"rfid_tag": test_tag})
    if response.status_code == 200:
        data = response.json()
        print(f"🔔 SUCCESS: Student {data['student']} is now {data['status']}")
    else:
        print(f"❌ ERROR: {response.json().get('error', 'Unknown error')}")
except Exception as e:
    print(f"🔥 CONNECTION FAILED: {e}")