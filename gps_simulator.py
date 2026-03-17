import requests
import time
import random

# CONFIGURATION
SERVER_URL = "http://127.0.0.1:5000/api/hardware/gps"
DEVICE_ID = "352592577999675" # ✅ Matches your uploaded Bus KA05AP1124

# Route points for TEST1 area
route_points = [
    (13.1187, 77.5752), 
    (13.1200, 77.5760),
    (13.1220, 77.5780),
    (13.1240, 77.5800),
    (13.1225, 77.5749)
]

def simulate_drive():
    print(f"🚀 Starting Bus {DEVICE_ID} Simulation...")
    
    while True:
        for lat, lng in route_points:
            # Add noise for realism
            current_lat = lat + random.uniform(-0.0005, 0.0005)
            current_lng = lng + random.uniform(-0.0005, 0.0005)
            speed = random.randint(25, 45)

            payload = {
                "device_id": DEVICE_ID,
                "lat": current_lat,
                "lng": current_lng,
                "speed": speed
            }

            try:
                response = requests.post(SERVER_URL, json=payload)
                if response.status_code == 200:
                    print(f"✅ GPS SENT: {current_lat:.4f}, {current_lng:.4f} | Speed: {speed}")
                else:
                    print(f"❌ Server Error: {response.status_code}")
            except Exception as e:
                print(f"⚠️ Connection Failed: {e}")

            time.sleep(3)

if __name__ == "__main__":
    simulate_drive()