import requests

# 1. Your LIVE Render URL
BASE_URL = "https://school-transport-backend-d0sg.onrender.com"

# 2. The Admin details you want
admin_data = {
    "username": "admin_mansoor",
    "password": "your_password_here",  # Change this to something you'll remember!
    "role": "super_admin",
    "branch": "Main Office"
}

def create_admin():
    print(f"📡 Connecting to {BASE_URL}...")
    try:
        # Note: If this gives a 401 error, you need to temporarily disable
        # @jwt_required in your backend's app.py for this specific route.
        response = requests.post(f"{BASE_URL}/api/admin/users", json=admin_data)
        
        # ✅ FIXED: Changed statusCode to status_code
        if response.status_code == 201:
            print("✅ SUCCESS! Your Super Admin is created.")
            print(f"Go to https://fleettrackpro-7017f.web.app and log in!")
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    create_admin()