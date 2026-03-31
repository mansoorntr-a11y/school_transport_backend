import requests
import time
import random

# ✅ These are the exact GPS IDs from your project
BUS_IDS = ["352592577999675", "352592575602115", "352592578043119"]
BASE_URL = "http://127.0.0.1:5000/api/hardware/gps"

# Initial starting points around your school in Yelahanka
locations = [
    {"lat": 13.1187, "lng": 77.5752}, # KA05AP1124
    {"lat": 13.1140, "lng": 77.5810}, # KA51AK3560
    {"lat": 13.1100, "lng": 77.5720}  # KA51AK3546
]

print("🚀 GPS Simulator Started! Press Ctrl+C to stop.")
print(f"📡 Simulating {len(BUS_IDS)} buses...")

while True:
    for i, device_id in enumerate(BUS_IDS):
        # Create a small movement (about 20-30 meters)
        locations[i]["lat"] += random.uniform(-0.0004, 0.0004)
        locations[i]["lng"] += random.uniform(-0.0004, 0.0004)
        
        payload = {
            "device_id": device_id,
            "lat": locations[i]["lat"],
            "lng": locations[i]["lng"],
            "speed": random.randint(20, 50) # Random speed in km/h
        }
        
        try:
            # Send the "Hardware Signal" to your backend
            response = requests.post(BASE_URL, json=payload)
            if response.status_code == 200:
                print(f"✅ Bus {device_id} moved to {locations[i]['lat']:.4f}")
            else:
                print(f"⚠️ Device {device_id} error: {response.text}")
        except Exception as e:
            print(f"❌ Could not connect to backend: {e}")

    print("-" * 30)
    time.sleep(5) # Wait 5 seconds before the next move