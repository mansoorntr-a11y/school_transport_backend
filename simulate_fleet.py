import time
import random
from app import app, db, Bus, BusHistory

def move_fleet():
    with app.app_context():
        print("🚀 Starting Multi-Bus Simulation...")
        buses = Bus.query.all()
        
        if not buses:
            print("❌ No buses found to simulate!")
            return

        while True:
            for bus in buses:
                # 1. Create a tiny random movement
                move_lat = (random.random() - 0.5) * 0.001 
                move_lng = (random.random() - 0.5) * 0.001
                
                bus.last_lat += move_lat
                bus.last_lng += move_lng
                bus.status = 'moving'
                bus.speed = random.randint(20, 50)

                # 2. SAVE to History Table (This is for the Polyline!)
                new_point = BusHistory(
                    bus_id=bus.id, 
                    lat=bus.last_lat, 
                    lng=bus.last_lng
                )
                db.session.add(new_point)
                
            db.session.commit()
            print(f"📡 Update: {len(buses)} buses moved & logged.")
            time.sleep(5) # Update every 5 seconds for a smooth demo

if __name__ == "__main__":
    move_fleet()