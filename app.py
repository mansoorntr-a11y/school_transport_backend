from sqlalchemy import cast, Float # 👈 MAKE SURE THIS IS AT THE TOP OF app.py
from flask import Flask, jsonify, request, send_file
from sqlalchemy import func
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import pandas as pd
import io
import time
import random
from datetime import datetime
import openpyxl
import sqlite3
import threading

import firebase_admin
from firebase_admin import credentials, firestore
import json


# ==========================================
# 🚀 SMART FIREBASE INITIALIZATION
# ==========================================
firebase_key = os.environ.get('FIREBASE_SERVICE_ACCOUNT_KEY')

try:
    if firebase_key:
        # This part runs on RENDER (Cloud)
        cred_dict = json.loads(firebase_key)
        cred = credentials.Certificate(cred_dict)
        print("☁️ Using Render Cloud Firebase Key")
    else:
        # This part runs on your LAPTOP (Local)
        # It looks for the file you just renamed
        cred = credentials.Certificate('serviceAccountKey.json')
        print("💻 Using Local serviceAccountKey.json")

    # Initialize ONLY if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    
    fb_db = firestore.client()
    print("✅ Firebase Cloud connected!")

except Exception as e:
    print(f"⚠️ Firebase Initialization failed: {e}")
    fb_db = None

# 🚀 RUN THIS ONCE TO PATCH YOUR DATABASE WITHOUT DELETING IT
def patch_database():
    try:
        # 1. Connect to your existing database file
        # Check if your file is named 'school_transport.db' or something else
        conn = sqlite3.connect('school_transport.db') 
        cursor = conn.cursor()
        
        # 2. Add the missing column manually
        cursor.execute("ALTER TABLE routes ADD COLUMN branch_id INTEGER")
        
        conn.commit()
        conn.close()
        print("✅ DATABASE PATCHED: branch_id column added to routes table!")
    except sqlite3.OperationalError:
        print("ℹ️ Info: branch_id column already exists or table not found.")
    except Exception as e:
        print(f"❌ Patch Error: {e}")

# Call it here so it runs when you start the server
patch_database()


def get_safe_id(id_val):
    if id_val is None or str(id_val).lower() == 'null' or str(id_val).strip() == '':
        return None
    try:
        return int(id_val)
    except:
        return None


# 1️⃣ MOVE THIS TO THE TOP (Below your imports)
def get_safe_attr(obj, attr_list, default=0):
    """Helper to find the first existing attribute from a list of possible names"""
    for attr in attr_list:
        if hasattr(obj, attr):
            # Check if it's a property or a value
            val = getattr(obj, attr)
            return val if val is not None else default
    return default

app = Flask(__name__)

uri = os.environ.get('DATABASE_URL')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)
# ==========================================
# 🚀 RENDER-SPECIFIC DATABASE CONFIG
# ==========================================
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'instance', 'v4_transport.db')

# ==========================================
# 🚀 1. DATABASE CONFIGURATION
# ==========================================
# Use the EXTERNAL URL from your Render Dashboard
RENDER_DB = "postgresql://school_transport_db_bq52_user:teywdg2RlIx8TBIVJ5Vs0Ud2fiZNXwRR@dpg-d6t6iop5pdvs73bi4cag-a.oregon-postgres.render.com/school_transport_db_bq52"

if os.environ.get('DATABASE_URL'):
    # Render provides 'postgres://', SQLAlchemy needs 'postgresql://'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace("postgres://", "postgresql://", 1)
    print("🚀 RUNNING ON RENDER CLOUD")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = RENDER_DB
    print("🌐 LOCAL DEV: CONNECTED TO RENDER POSTGRES")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-123')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')

# ==========================================
# 🚀 2. INITIALIZE PLUGINS (MUST HAPPEN BEFORE VERIFICATION)
# ==========================================
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# ==========================================
# 🚀 3. VERIFY CONNECTION (NOW 'db' EXISTS!)
# ==========================================
from sqlalchemy import text # Ensure this is imported at the top of your file
with app.app_context():
    try:
        db.session.execute(text('SELECT 1'))
        print("✅ DATABASE CONNECTION VERIFIED: CLOUD IS LIVE")
    except Exception as e:
        print(f"❌ DATABASE CONNECTION FAILED: {e}")

# ==========================================
# 🚀 4. HELPER FUNCTIONS
# ==========================================
def get_safe_attr(obj, attr_list, default=0):
    for attr in attr_list:
        if hasattr(obj, attr):
            val = getattr(obj, attr)
            return val if val is not None else default
    return default

# ==========================================
# 📝 DATABASE MODELS
# ==========================================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # 🚀 THE CRITICAL ADDITION:
    name = db.Column(db.String(100)) # This is for "Shilpa", "Maria", etc.
    
    username = db.Column(db.String(80), unique=True, nullable=False) # This is the Phone/Login ID
    password_hash = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    branch_id = db.Column(db.String(50)) 
    contact_number = db.Column(db.String(20)) 
    license_info = db.Column(db.String(50))

    company = db.relationship('Company', backref='users')

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role.upper(),
            "company_name": self.company.name if self.company else "Unknown School",
            "branch_id": self.branch_id,
            "company_id": self.company_id,
            
            # 🚀 ADD THE NAME HERE FOR FLUTTER:
            "name": self.name or self.username, # Fallback to username if name is empty
            
            "phone": self.contact_number or "", 
            "contact_number": self.contact_number or "",
            "license_info": self.license_info or "No ID Entered"
        }

class Company(db.Model):
    __tablename__ = 'companies'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255))
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(20))
    bank_name = db.Column(db.String(100))
    account_no = db.Column(db.String(50))
    ifsc_code = db.Column(db.String(20))
    upi_id = db.Column(db.String(100)) 

    # 🛑 REMOVED the 'users = db.relationship' line from here!

    def to_dict(self):
      return {
        "id": self.id,
        "name": self.name,             # Match Flutter 'name'
        "logo_url": self.logo_url,     # Match Flutter 'logo_url'
        "address": self.address,
        "phone": self.phone_number,    # Match Flutter 'phone'
        "upi_id": self.upi_id,         # Match Flutter 'upi_id'
        "bank_name": self.bank_name,   # Match Flutter 'bank_name'
        "account_no": self.account_no, # Match Flutter 'account_no'
        "ifsc_code": self.ifsc_code    # Match Flutter 'ifsc_code'
    }


class Branch(db.Model):
    __tablename__ = 'branches'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    location = db.Column(db.String(200))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    def to_dict(self):
        return {
            "id": self.id, 
            "branch_name": self.name,  # 🚀 ADD THIS: Flutter screens expect this!
            "name": self.name,         # Keep this for the Map/Other logic
            "location": self.location or "No address set",
            "latitude": self.latitude, 
            "longitude": self.longitude
        }

class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String(50), nullable=False) 
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    chassis_no = db.Column(db.String(50))
    seater_capacity = db.Column(db.Integer, default=30)
    gps_device_id = db.Column(db.String(50))
    sim_no = db.Column(db.String(20))
    rfid_reader_id = db.Column(db.String(50))
    branch = db.Column(db.String(50)) # Matches the User.branch_id
    status = db.Column(db.String(20), default='stopped') 
    last_lat = db.Column(db.Float)
    last_lng = db.Column(db.Float)
    morning_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    noon_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    evening_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    speed = db.Column(db.Float, default=0.0)
    
    # 🛣️ Route Connection
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    route = db.relationship('Route', backref='buses_assigned', foreign_keys=[route_id])
    
    # 👩‍🏫 Attender Connection
    attender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    attender = db.relationship('User', foreign_keys=[attender_id])
    morning_route = db.relationship('Route', foreign_keys=[morning_route_id])
    noon_route = db.relationship('Route', foreign_keys=[noon_route_id])
    evening_route = db.relationship('Route', foreign_keys=[evening_route_id])

    def to_dict(self):
        return {
            "id": self.id,
            "bus_number": self.bus_no,
            "chassis_no": self.chassis_no or "N/A",
            "seater_capacity": self.seater_capacity or 0,
            "gps_device_id": self.gps_device_id or "N/A",
            "sim_no": self.sim_no or "N/A",
            "rfid": self.rfid_reader_id or "N/A", 
            "branch": self.branch,
            "morning_route_name": self.morning_route.route_name if self.morning_route else "Not Assigned",
            "noon_route_name": self.noon_route.route_name if self.noon_route else "Not Assigned",
            "evening_route_name": self.evening_route.route_name if self.evening_route else "Not Assigned",
            "morning_route_id": self.morning_route_id,
            "noon_route_id": self.noon_route_id,
            "evening_route_id": self.evening_route_id,
            "status": self.status,
            "last_lat": self.last_lat,
            "last_lng": self.last_lng,
            "speed": self.speed,
            "route_id": self.route_id,
            "attender_id": self.attender_id,
            "route_name": self.route.route_name if self.route else "Not Assigned",
            "attender_name": self.attender.username if self.attender else "Not Assigned"
        }

class Stop(db.Model): # 🚀 Changed name to 'Stop' to match the Controller
    __tablename__ = 'stops'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    stop_name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), default="General") 
    km = db.Column(db.Float, nullable=False, default=0.0)
    latitude = db.Column(db.Float, default=0.0)
    longitude = db.Column(db.Float, default=0.0)
    branch = db.Column(db.String(50))
    # 🔗 Links to FeeZone for auto-calculation
    fee_zone_id = db.Column(db.Integer, db.ForeignKey('fee_zones.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 
            'stop_name': self.stop_name, 
            'zone': self.zone,
            'km': self.km, 
            'latitude': self.latitude, 
            'longitude': self.longitude, 
            'branch': self.branch,
            'company_id': self.company_id, # ✅ Added for SaaS debugging
            'fee_zone_id': self.fee_zone_id
        }

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # 👈 Added missing name column
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    admission_no = db.Column(db.String(50), unique=True, nullable=False)
    grade = db.Column(db.String(20))
    division = db.Column(db.String(20)) # ✅ ADD THIS LINE
    parent_mobile = db.Column(db.String(20))
    rfid_tag = db.Column(db.String(50))
    branch = db.Column(db.String(50), default="PSBN")
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'))
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id')) 
    pickup_stop_id = db.Column(db.Integer, db.ForeignKey('stops.id'))
    drop_stop_id = db.Column(db.Integer, db.ForeignKey('stops.id'))
    total_fee = db.Column(db.Float, default=0.0)
    payment_status = db.Column(db.String(20), default="Pending")
    last_status = db.Column(db.String(50))
    route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    # 🛣️ MULTI-SHIFT STUDENT ROUTES
    morning_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    noon_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))
    evening_route_id = db.Column(db.Integer, db.ForeignKey('routes.id'))

    # Relationships
    morning_route = db.relationship('Route', foreign_keys=[morning_route_id])
    noon_route = db.relationship('Route', foreign_keys=[noon_route_id])
    evening_route = db.relationship('Route', foreign_keys=[evening_route_id])

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.name,
            "admission_no": self.admission_no,
            "morning_route_name": self.morning_route.route_name if self.morning_route else "Not Assigned",
            "noon_route_name": self.noon_route.route_name if self.noon_route else "Not Assigned",
            "evening_route_name": self.evening_route.route_name if self.evening_route else "Not Assigned",
            "grade": self.grade or "",
            "division": self.division or "", # ✅ ADD THIS LINE
            "parent_mobile": self.parent_mobile or "",
            "rfid_tag": self.rfid_tag or "",
            "branch": self.branch,
            "bus_id": self.bus_id,
            "pickup_stop_id": self.pickup_stop_id, # ✅ Add this
            "drop_stop_id": self.drop_stop_id,     # ✅ Add this
            "total_fee": self.total_fee or 0,
            "payment_status": self.payment_status or "Pending"
        }
    
# 💰 FEE PAYMENT MODEL
class FeeRecord(db.Model):
    __tablename__ = 'fee_records'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False) 
    amount = db.Column(db.Float, nullable=False)
    due_date = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="Pending")
    payment_date = db.Column(db.DateTime, nullable=True)
    transaction_id = db.Column(db.String(50), nullable=True)

    student = db.relationship('Student', backref=db.backref('fees', lazy=True))

class AttendanceLog(db.Model):
    __tablename__ = 'attendance_logs'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    student_name = db.Column(db.String(100)) # ✅ Add this line
    status = db.Column(db.String(50))
    branch = db.Column(db.String(50))
    timestamp = db.Column(db.String(50))
    bus_number = db.Column(db.String(50)) # Add if missing
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)

    # 🔗 This link allows us to get the name without a separate column
    student = db.relationship('Student', backref='logs')

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else "Unknown", # ✅ Gets name from relationship
            "company_id": self.company_id,
            "status": self.status,
            "branch": self.branch,
            "timestamp": self.timestamp,
            "bus_number": self.bus_number or "N/A"
        }

# 1. DATABASE MODEL
class FeeZone(db.Model):
    __tablename__ = 'fee_zones'
    id = db.Column(db.Integer, primary_key=True)
    zone_name = db.Column(db.String(50), nullable=False) # 👈 Changed from 'name'
    min_km = db.Column(db.Float, default=0.0)
    max_km = db.Column(db.Float, default=0.0)
    price = db.Column(db.Float, nullable=False)
    branch = db.Column(db.String(50), default='Main')
    term = db.Column(db.String(50), default='Annual')
    mode = db.Column(db.String(50), default='Two-Way')
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'zone_name': self.zone_name, # 🚀 Must match Flutter zone['zone_name']
            'min_km': self.min_km,
            'max_km': self.max_km,
            'price': self.price,
            'branch': self.branch,
            'term': self.term,
            'mode': self.mode
        }

# 📢 NOTICE/CIRCULAR MODEL
class Notice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    file_path = db.Column(db.String(255))
    # 🚀 ADD THESE TWO LINES for SaaS isolation
    branch = db.Column(db.String(100), default='GLOBAL') 
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'))
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)


class BusHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_id = db.Column(db.Integer, db.ForeignKey('buses.id'), nullable=False)
    lat = db.Column(db.Float, nullable=False)
    lng = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to easily find the bus
    bus = db.relationship('Bus', backref=db.backref('history', lazy=True))

def calculate_student_fee(stop_name, company_id):
    """
    Finds the correct fee based on a stop name and the school's fee zones.
    """
    # 1. Find the stop to get the distance (KM)
    stop = Stop.query.filter_by(name=stop_name, company_id=company_id).first()
    
    if not stop:
        print(f"⚠️ Stop '{stop_name}' not found. Defaulting fee to 0.")
        return 0.0

    distance = stop.distance or 0.0

    # 2. Find which FeeZone this distance falls into
    # We look for: min_km <= distance <= max_km
    zone = FeeZone.query.filter(
        FeeZone.company_id == company_id,
        FeeZone.min_km <= distance,
        FeeZone.max_km >= distance
    ).first()

    if zone:
        print(f"✅ Match: Stop {stop_name} ({distance}km) -> {zone.zone_name} @ ₹{zone.price}")
        return zone.price
    
    print(f"⚠️ No fee zone covers {distance}km. Defaulting fee to 0.")
    return 0.0

class Route(db.Model):
    __tablename__ = 'routes'
    id = db.Column(db.Integer, primary_key=True)
    route_name = db.Column(db.String(100), nullable=False)
    shift = db.Column(db.String(20)) 
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    
    # 🚀 ADD THIS LINE NOW:
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True) 
    
    stop_ids = db.Column(db.Text, nullable=True) 

    def to_dict(self):
        return {
            'id': self.id,
            'route_name': self.route_name,
            "shift": self.shift or "General",
            "display_name": f"{self.route_name} ({self.shift or 'General'})",
            'company_id': self.company_id,
            'branch_id': self.branch_id, # 👈 Add this here too
            'stop_ids': self.stop_ids
        }

# ==========================================
# 🔐 AUTH & USER MGMT (Fixed for SaaS ID)
# ==========================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    
    if user and check_password_hash(user.password_hash, data.get('password')):
        # 🔍 1. Fetch Branch Name Safely
        branch_name = "testone" 
        if user.branch_id:
            branch_obj = db.session.get(Branch, user.branch_id)
            if branch_obj:
                branch_name = branch_obj.name
        
        # 🛡️ 2. Fetch Company Name Safely
        company_name = "Super Admin Control"
        if user.company_id:
            company = db.session.get(Company, user.company_id)
            if company:
                company_name = company.name
        
        # 🚀 3. THE MASTER FIX: Include IDs in the response
        return jsonify({
            "access_token": create_access_token(identity=str(user.id)),
            "user_id": user.id,             # ✨ ADD THIS LINE!
            "role": user.role,
            "branch": branch_name,          
            "branch_id": user.branch_id,    
            "company_name": company_name,
            "company_id": user.company_id   
        }), 200

    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
@jwt_required()
def handle_admin_users():
    if request.method == 'OPTIONS':
        return _cors_response()

    current_user_id = get_jwt_identity()
    admin_user = db.session.get(User, int(current_user_id))

    # 🛡️ 1. THE SECURITY GUARD: Check if the role is allowed
    # We include 'school_admin' (testadmin) and 'admin' (regular school admin)
    allowed_roles = ['super_admin', 'school_admin', 'admin']
    
    if not admin_user or admin_user.role.lower() not in allowed_roles:
        print(f"🚫 Access Denied for role: {admin_user.role if admin_user else 'None'}")
        return jsonify({"error": "Unauthorized"}), 403

    # ✍️ 2. POST LOGIC: Creating a new user
    if request.method == 'POST':
        try:
            data = request.json
            if User.query.filter_by(username=data.get('username')).first():
                return jsonify({"error": "Username already exists"}), 400

            # Determine company isolation
            if admin_user.role == 'super_admin':
                target_company_id = data.get('company_id') 
            else:
                target_company_id = admin_user.company_id

            new_user = User(
                name=data.get('name'), # Ensure 'name' is being sent from Flutter
                username=data.get('username'),
                password_hash=generate_password_hash(data.get('password', '1234')),
                role=data.get('role', 'admin'),
                company_id=target_company_id,
                branch_id=data.get('branch_id'),
                contact_number=data.get('contact_number')
            )
            
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": f"User {new_user.username} created successfully"}), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # 📂 3. GET LOGIC: Fetching the list
    if admin_user.role == 'super_admin':
        # Super Admin can filter by company_id in URL or see everyone
        cid = request.args.get('company_id')
        if cid:
            users = User.query.filter_by(company_id=cid).all()
        else:
            users = User.query.all()
    else:
        # School Admin (testadmin) ONLY sees users from their own school
        users = User.query.filter_by(company_id=admin_user.company_id).all()
        
    return jsonify([u.to_dict() for u in users]), 200


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_admin_user(user_id):
    if request.method == 'OPTIONS':
        return _cors_response()

    current_user = db.session.get(User, int(get_jwt_identity()))
    
    # 1. Find the target user
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"error": "User not found"}), 404

    # 🛡️ 2. SAFETY LOCKS
    # A. Don't let someone delete themselves
    if current_user.id == target_user.id:
        return jsonify({"error": "You cannot delete your own account!"}), 400

    # B. Permission Check
    if admin_user.role == 'super_admin':
        # Super Admin can delete anyone
        pass 
    elif admin_user.role in ['admin', 'school_admin'] and admin_user.company_id == target_user.company_id:
        # School Admin can only delete users in their own school
        pass
    else:
        return jsonify({"error": "Unauthorized"}), 403

    # This 'try' block must be at the same level as the 'if'
    try:
        db.session.delete(target_user)
        db.session.commit()
        print(f"🗑️ User {target_user.username} deleted by {admin_user.username}")
        return jsonify({"message": "User deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# 🎓 FIXED STUDENT CONTROLLER
# ==========================================
@app.route('/api/students', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/students/<int:id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_students_master(id=None):
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🛡️ SaaS Safety: If company_id is 'null' in URL, use the user's ID from JWT
    raw_cid = request.args.get('company_id')
    final_cid = int(raw_cid) if (raw_cid and raw_cid.isdigit()) else user.company_id

    if request.method == 'GET':
        from sqlalchemy import func
        user = db.session.get(User, int(get_jwt_identity()))
        
        query = Student.query.filter_by(company_id=final_cid)

        # 🛡️ SaaS Security: Non-SuperAdmins are LOCKED to their own company
        if user.role.lower() != 'super_admin':
            final_cid = user.company_id
        else:
            raw_cid = request.args.get('company_id')
            final_cid = int(raw_cid) if (raw_cid and raw_cid.isdigit()) else user.company_id

        query = Student.query.filter_by(company_id=final_cid)

        # 🔒 CASE A: Branch Incharge
        print(f"🕵️ DEBUG: Searching for Company ID: {final_cid}")
        all_students_in_co = Student.query.filter_by(company_id=final_cid).all()
        print(f"🕵️ DEBUG: Total students in this company (any branch): {len(all_students_in_co)}")
        for s in all_students_in_co[:3]: # Print first 3 to check their branch strings
            print(f"   -> Student: {s.name} | Branch in DB: '{s.branch}'")

        if user.role.lower() == 'branch_incharge':
            branch_obj = db.session.get(Branch, user.branch_id)
            if branch_obj:
                search_name = branch_obj.name.strip().upper()
                print(f"🕵️ DEBUG: Incharge is searching for branch: '{search_name}'")
                query = query.filter(func.trim(func.upper(Student.branch)) == search_name)
            else:
                return jsonify([]), 200
        
        # 🔓 CASE B: Admin Filtering
        else:
            target_branch = request.args.get('branch', '').strip().upper()
            if target_branch and target_branch not in ["ALL", "ALL BRANCHES", ""]:
                query = query.filter(func.trim(func.upper(Student.branch)) == target_branch)

        students = query.order_by(Student.name.asc()).all()
        return jsonify([s.to_dict() for s in students]), 200

    branch_obj = db.session.get(Branch, user.branch_id)
    if branch_obj:
        # 🚀 THE BULLETPROOF FILTER
        assigned_branch_name = branch_obj.name.strip().upper()
        query = query.filter(func.upper(Student.branch) == assigned_branch_name)
        print(f"🔍 Security: User {user.username} limited to students in {assigned_branch_name}")
    else:
        print(f"⚠️ Branch ID {user.branch_id} not found in Branch table!")
        return jsonify([]), 200

    # ➕ 2. ADD STUDENT (POST)
    if request.method == 'POST':
        data = request.json
        raw_cid = data.get('company_id')
        
        # Determining company ownership
        final_company_id = int(raw_cid) if (user.role == 'super_admin' and raw_cid) else user.company_id
        
        if not final_company_id:
            return jsonify({"error": "No company_id specified"}), 400

        new_student = Student(
            name=data.get('student_name'),
            admission_no=data.get('admission_no'),
            company_id=final_company_id,
            branch=data.get('branch', 'MAIN').upper(),
            grade=data.get('grade'),
            division=data.get('division'),
            parent_mobile=data.get('parent_mobile'),
            bus_id=data.get('bus_id'),
            pickup_stop_id=data.get('pickup_stop_id'),
            drop_stop_id=data.get('drop_stop_id'),
            total_fee=float(data.get('total_fee', 0)),
            rfid_tag=data.get('rfid_tag'),
            payment_status=data.get('payment_status', 'Pending'),
            # 🚀 MULTI-SHIFT ROUTES CAPTURED HERE:
            morning_route_id=data.get('morning_route_id'),
            noon_route_id=data.get('noon_route_id'),
            evening_route_id=data.get('evening_route_id')
        )
        db.session.add(new_student)
        db.session.commit()
        return jsonify(new_student.to_dict()), 201

    # 📝 3. UPDATE STUDENT (PUT)
    if request.method == 'PUT':
        student = db.session.get(Student, id)
        if not student: return jsonify({'error': 'Not found'}), 404
        
        if user.role != 'super_admin' and student.company_id != user.company_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json
        student.name = data.get('student_name', student.name)
        student.admission_no = data.get('admission_no', student.admission_no)
        student.grade = data.get('grade', student.grade)
        student.division = data.get('division', student.division)
        student.parent_mobile = data.get('parent_mobile', student.parent_mobile)
        student.branch = data.get('branch', student.branch).upper()
        student.rfid_tag = data.get('rfid_tag', student.rfid_tag)
        student.bus_id = data.get('bus_id', student.bus_id)
        student.pickup_stop_id = data.get('pickup_stop_id', student.pickup_stop_id)
        student.drop_stop_id = data.get('drop_stop_id', student.drop_stop_id)
        student.total_fee = float(data.get('total_fee', student.total_fee))
        student.payment_status = data.get('payment_status', student.payment_status)
        
        # 🚀 UPDATE MULTI-SHIFT ROUTES:
        student.morning_route_id = data.get('morning_route_id', student.morning_route_id)
        student.noon_route_id = data.get('noon_route_id', student.noon_route_id)
        student.evening_route_id = data.get('evening_route_id', student.evening_route_id)

        db.session.commit()
        return jsonify(student.to_dict()), 200

    # 🗑️ 4. DELETE STUDENT (DELETE)
    if request.method == 'DELETE':
        student = db.session.get(Student, id)
        if not student: return jsonify({'error': 'Not found'}), 404
        
        if user.role != 'super_admin' and student.company_id != user.company_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        db.session.delete(student)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'}), 200

# ==========================================
# 💰 PRICING SLABS / FEE ZONES
# ==========================================
@app.route('/api/pricing_slabs', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_pricing_slabs():
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🛡️ SaaS ID Logic
    raw_cid = request.args.get('company_id')
    final_cid = int(raw_cid) if (raw_cid and raw_cid != 'null') else user.company_id

    # Using FeeZone model (ensure this matches your class name)
    slabs = FeeZone.query.filter_by(company_id=final_cid).all()
    return jsonify([s.to_dict() for s in slabs]), 200

# ==========================================
# 🚌 MASTER BUS CONTROLLER
# ==========================================
@app.route('/api/admin/buses', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required()
def handle_admin_buses():
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    is_super = user.role.lower() == 'super_admin'
    
    raw_cid = request.args.get('company_id')
    final_cid = get_safe_id(raw_cid) if is_super else user.company_id

    # 📂 1. FETCH BUSES (GET)
    if request.method == 'GET':
        query = Bus.query
        
        # 🛡️ God View Logic
        if not is_super or final_cid:
            query = query.filter_by(company_id=final_cid)
        
        target_branch = request.args.get('branch', '').strip().lower()

        # 🚀 Smart Filter (Role-Based)
        if user.role.lower() == 'branch_incharge':
            # Branch incharges are strictly locked to their ID or Name
            search_val = (user.branch_id or "").strip().lower()
            query = query.filter(func.lower(func.trim(Bus.branch)) == search_val)
            
        elif target_branch and target_branch not in ["all", "all branches", "null", ""]:
            # Admins/SuperAdmins filtering by selected branch
            query = query.filter(func.lower(func.trim(Bus.branch)) == target_branch)

        buses = query.all()
        
        # 🛠️ Enrich data with Route and Attender names
        results = []
        for b in buses:
            bus_data = b.to_dict()
            bus_data.update({
                "morning_route_name": b.morning_route.route_name if b.morning_route else "Not Assigned",
                "noon_route_name": b.noon_route.route_name if b.noon_route else "Not Assigned",
                "evening_route_name": b.evening_route.route_name if b.evening_route else "Not Assigned",
                "attender_name": b.attender.username if b.attender else "Not Assigned"
            })
            results.append(bus_data)
            
        return jsonify(results), 200

    # ➕ 2. ADD BUS (POST)
    if request.method == 'POST':
        data = request.json
        try:
            new_bus = Bus(
                bus_no=data.get('bus_number'), 
                company_id=final_cid,
                branch=str(data.get('branch', user.branch_id)).upper().strip(),
                morning_route_id=data.get('morning_route_id'),
                noon_route_id=data.get('noon_route_id'),
                evening_route_id=data.get('evening_route_id'),
                attender_id=data.get('attender_id'),
                gps_device_id=data.get('gps_device_id'),
                sim_no=data.get('sim_no'),
                rfid_reader_id=data.get('rfid_reader_id'),
                seater_capacity=data.get('seater_capacity', 30),
                status='stopped'
            )
            db.session.add(new_bus)
            db.session.commit()
            return jsonify(new_bus.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# ==========================================
# 🔧 SINGLE BUS OPERATIONS (Update/Delete)
# ==========================================
@app.route('/api/admin/buses/<int:bus_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_bus_item(bus_id):
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200
    
    bus = db.session.get(Bus, bus_id)
    if not bus:
        return jsonify({"error": "Bus not found"}), 404

    if request.method == 'DELETE':
        db.session.delete(bus)
        db.session.commit()
        return jsonify({"message": "Bus deleted successfully"}), 200

    if request.method == 'PUT':
        data = request.json
        # 🚌 Update Core Info
        bus.bus_no = data.get('bus_number', bus.bus_no)
        bus.chassis_no = data.get('chassis_no', bus.chassis_no)
        bus.seater_capacity = data.get('seater_capacity', bus.seater_capacity)
        
        # 🛣️ Update 3-Shift Routes
        bus.morning_route_id = data.get('morning_route_id')
        bus.noon_route_id = data.get('noon_route_id')
        bus.evening_route_id = data.get('evening_route_id')
        
        # 👩‍🏫 Update Staff & Hardware
        bus.attender_id = data.get('attender_id')
        bus.rfid_reader_id = data.get('rfid_reader_id', bus.rfid_reader_id)
        bus.sim_no = data.get('sim_no', bus.sim_no)
        bus.gps_device_id = data.get('gps_device_id', bus.gps_device_id)
        
        db.session.commit()
        print(f"✅ Bus {bus.bus_no} updated with Routes: AM:{bus.morning_route_id}, Noon:{bus.noon_route_id}, PM:{bus.evening_route_id}")
        return jsonify(bus.to_dict()), 200

# ==========================================
# ⚠️ BULK DELETE (Updated with School Guard)
# ==========================================
@app.route('/api/admin/bulk_delete/buses', methods=['DELETE'])
@jwt_required()
def bulk_delete_buses():
    user = db.session.get(User, int(get_jwt_identity()))
    target_branch = request.args.get('branch', '').upper()
    
    # Determine the school ID safely
    raw_cid = request.args.get('company_id')
    final_cid = get_safe_id(raw_cid) if user.role == 'super_admin' else user.company_id

    if not target_branch or not final_cid:
        return jsonify({"error": "Branch and Company ID required"}), 400

    try:
        # ✅ THE FIX: Only delete buses for this specific branch AND this specific school
        deleted_count = Bus.query.filter_by(branch=target_branch, company_id=final_cid).delete()
        db.session.commit()
        return jsonify({"message": f"Successfully deleted {deleted_count} buses from {target_branch}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500          
        
# ==========================================
# 📂 SMART BULK UPLOAD (Expanded for SaaS)
# ==========================================
@app.route('/api/admin/upload/bulk', methods=['POST'])
@jwt_required()
def smart_bulk_upload():
    user = db.session.get(User, int(get_jwt_identity()))
    file = request.files.get('file')
    raw_cat = (request.form.get('category') or '').lower().strip()
    form_branch = request.form.get('branch', '').strip().upper() 
    
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        # Read file safely
        df = pd.read_excel(file, dtype=str) if file.filename.endswith('.xlsx') else pd.read_csv(file, dtype=str)
        df.columns = df.columns.str.strip() # Remove spaces from headers
        count = 0

        # 📍 1. BUS STOPS (Fixed Model Name: Stop)
        if "stop" in raw_cat:
            for _, row in df.iterrows():
                stop_name = str(row.get('Stop Name') or '').strip()
                if not stop_name: continue
                
                z_name = str(row.get('Zone', 'General')).strip()
                km_val = float(row.get('Distance (KM)', 0.0))
                lat_val = float(row.get('Latitude', 0.0))
                lng_val = float(row.get('Longitude', 0.0))
                
                # 🚀 FIXED: Changed 'BusStop' to 'Stop' to match your model
                stop = Stop.query.filter_by(stop_name=stop_name, branch=form_branch, company_id=user.company_id).first()
                
                if stop:
                    stop.km = km_val
                    stop.latitude = lat_val
                    stop.longitude = lng_val
                    stop.zone = z_name
                else:
                    db.session.add(Stop(
                        stop_name=stop_name, 
                        zone=z_name, 
                        branch=form_branch, 
                        company_id=user.company_id, 
                        km=km_val,
                        latitude=lat_val, 
                        longitude=lng_val
                    ))
                count += 1

        # 🎓 2. STUDENTS (Handles Multi-Shift Routes)
        elif "student" in raw_cat:
            for _, row in df.iterrows():
                name = str(row.get('Student Name') or '').strip()
                adm_no = str(row.get('Admission No') or '').strip()
                if not adm_no or not name: continue

                # 🛡️ Force the student to belong to the logged-in user's company and branch
                student = Student.query.filter_by(admission_no=adm_no, company_id=user.company_id).first()
                
                # Lookups
                am_r = Route.query.filter_by(route_name=str(row.get('AM Route','')).strip(), shift='Morning', company_id=user.company_id).first()
                noon_r = Route.query.filter_by(route_name=str(row.get('Noon Route','')).strip(), shift='Noon', company_id=user.company_id).first()
                pm_r = Route.query.filter_by(route_name=str(row.get('PM Route','')).strip(), shift='Evening', company_id=user.company_id).first()

                if student:
                    student.name = name
                    student.branch = form_branch # 🚀 Force update branch
                    student.company_id = user.company_id
                    student.morning_route_id = am_r.id if am_r else student.morning_route_id
                else:
                    db.session.add(Student(
                        name=name, 
                        admission_no=adm_no, 
                        branch=form_branch, # This is 'TESTONE' from Flutter
                        company_id=user.company_id,
                        grade=row.get('Grade', 'N/A'), 
                        division=row.get('Div', 'A'),
                        morning_route_id=am_r.id if am_r else None,
                        noon_route_id=noon_r.id if noon_r else None,
                        evening_route_id=pm_r.id if pm_r else None
                    ))
                count += 1

        # 👩‍🏫 3. LADY ATTENDERS
        elif "attender" in raw_cat:
            for _, row in df.iterrows():
                name = str(row.get('Attender Name') or '').strip()
                phone = str(row.get('Phone Number') or '').strip()
                if not name or not phone: continue

                attender = User.query.filter_by(contact_number=phone, company_id=user.company_id).first()
                if not attender:
                    db.session.add(User(
                        username=name, contact_number=phone, role='attender',
                        company_id=user.company_id, branch_id=form_branch,
                        password_hash=generate_password_hash("1234"),
                        license_info=str(row.get('Aadhar / ID Number', ''))
                    ))
                    count += 1

        # 🛣️ 4. ROUTES
        elif "route" in raw_cat:
            for _, row in df.iterrows():
                r_name = str(row.get('Route Name') or '').strip()
                # Default to Morning if shift is missing
                r_shift = str(row.get('Shift') or 'Morning').strip().capitalize() 
                if not r_name: continue

                exists = Route.query.filter_by(route_name=r_name, shift=r_shift, company_id=user.company_id).first()
                if not exists:
                    db.session.add(Route(route_name=r_name, shift=r_shift, company_id=user.company_id))
                    count += 1

# 🚌 5. BUSES (The Missing Link!)
        elif "bus" in raw_cat:
            for _, row in df.iterrows():
                b_no = str(row.get('Bus Number') or '').strip()
                if not b_no: continue

                # Look up Route IDs by their names from the Excel
                am_r = Route.query.filter_by(route_name=str(row.get('Morning Route', '')).strip(), shift='Morning', company_id=user.company_id).first()
                noon_r = Route.query.filter_by(route_name=str(row.get('Noon Route', '')).strip(), shift='Noon', company_id=user.company_id).first()
                pm_r = Route.query.filter_by(route_name=str(row.get('Evening Route', '')).strip(), shift='Evening', company_id=user.company_id).first()
                
                # Look up Attender by Name
                attender = User.query.filter_by(username=str(row.get('Lady Attender', '')).strip(), role='attender', company_id=user.company_id).first()

                bus = Bus.query.filter_by(bus_no=b_no, company_id=user.company_id).first()
                
                if bus:
                    # Update existing bus info
                    bus.branch = form_branch
                    bus.morning_route_id = am_r.id if am_r else bus.morning_route_id
                    bus.noon_route_id = noon_r.id if noon_r else bus.noon_route_id
                    bus.evening_route_id = pm_r.id if pm_r else bus.evening_route_id
                    bus.attender_id = attender.id if attender else bus.attender_id
                    bus.seater_capacity = int(row.get('Seater Capacity', 30))
                    bus.gps_device_id = str(row.get('GPS Device ID', ''))
                else:
                    # Create new bus
                    db.session.add(Bus(
                        bus_no=b_no,
                        company_id=user.company_id,
                        branch=form_branch,
                        morning_route_id=am_r.id if am_r else None,
                        noon_route_id=noon_r.id if noon_r else None,
                        evening_route_id=pm_r.id if pm_r else None,
                        attender_id=attender.id if attender else None,
                        seater_capacity=int(row.get('Seater Capacity', 30)),
                        gps_device_id=str(row.get('GPS Device ID', '')),
                        status='stopped'
                    ))
                count += 1

        db.session.commit()
        return jsonify({"message": f"Uploaded {count} {raw_cat} records successfully"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ BULK UPLOAD ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
# ==========================================
#  🛰️ UNIFIED LIVE TRACKING SYSTEM
# ==========================================

@app.route('/api/hardware/gps', methods=['POST'])
def update_hardware_gps():
    data = request.json
    if not data:
        return jsonify({"error": "No data received"}), 400

    # 1. Get the Device ID (Hardware ID from Excel/Simulator)
    device_id = str(data.get('device_id', '')).strip().replace('.0', '')
    
    # 2. Find the bus specifically by GPS Device ID
    bus = Bus.query.filter_by(gps_device_id=device_id).first()
    
    if bus:
        try:
            # 3. Update coordinates and status
            bus.last_lat = float(data.get('lat', 0))
            bus.last_lng = float(data.get('lng', 0))
            bus.speed = float(data.get('speed', 0))
            
            # Status Logic: If it's moving, it's 'moving', otherwise 'stopped'
            bus.status = 'moving' if bus.speed > 0 else 'stopped'
            
            db.session.commit()
            
            # This print helps you see the simulation working in your terminal
            print(f"🛰️ GPS SYNC: {bus.bus_no} | ID: {device_id} | Lat: {bus.last_lat}")
            return jsonify({"status": "success", "bus": bus.bus_no}), 200

        except Exception as e:
            db.session.rollback()
            print(f"❌ DB ERROR: {str(e)}")
            return jsonify({"error": "Internal database error"}), 500
            
    # 4. If ID doesn't match anything in your Excel/DB
    print(f"⚠️ GPS ALERT: Unknown Device ID [{device_id}] sent data.")
    return jsonify({"error": f"Device {device_id} not registered"}), 404

# ==========================================
# 📍 SECURE STOPS MANAGEMENT (SaaS)
# ==========================================
@app.route('/api/stops', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/stops/<int:id>', methods=['PUT', 'DELETE', 'OPTIONS']) # 👈 Added PUT here
@jwt_required()
def handle_stops_master(id=None):
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'CORS OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🛡️ 1. Determine the School ID
    raw_cid = request.args.get('company_id')
    target_cid = get_safe_id(raw_cid)
    final_cid = target_cid if (user.role == 'super_admin' and target_cid) else user.company_id

    # 📂 FETCH STOPS (GET) - Fixed for Parent View
    if request.method == 'GET':
        from sqlalchemy import func
        query = Stop.query.filter_by(company_id=final_cid)
        
        # 🚀 1. Get the branch name from the URL (?branch=testone)
        target_branch = request.args.get('branch', '').strip().upper()

        # 🛡️ 2. SMART SECURITY LOGIC
        if user.role.lower() == 'branch_incharge':
            # 🔒 Branch Incharges stay locked to their specific assigned branch name
            search_val = (user.branch_id or "").strip()
            search_branch = search_val.upper()
            if search_val.isdigit():
                branch_obj = db.session.get(Branch, int(search_val))
                if branch_obj: search_branch = branch_obj.name.upper()
            
            query = query.filter(func.upper(func.trim(Stop.branch)) == search_branch)
            print(f"🔒 Staff Security: Locked to {search_branch}")

        elif target_branch and target_branch not in ["ALL", "ALL BRANCHES", ""]:
            # 🔓 Admins / Super Admins only filter if they picked a specific branch
            query = query.filter(func.upper(func.trim(Stop.branch)) == target_branch)
            print(f"🔓 Admin Filter: Showing {target_branch}")

        stops = query.order_by(Stop.stop_name.asc()).all()
        return jsonify([s.to_dict() for s in stops]), 200

    # ➕ ADD STOP (POST)
    if request.method == 'POST':
        data = request.json
        try:
            new_stop = Stop(
                stop_name=data.get('stop_name'),
                latitude=float(data.get('latitude', 0.0)),
                longitude=float(data.get('longitude', 0.0)),
                branch=str(data.get('branch', 'MAIN')).upper(),
                zone=data.get('zone'), 
                km=float(data.get('km', 0.0)),
                company_id=final_cid,
                # 🔗 Link the ID so auto-fee-calculation works!
                fee_zone_id=data.get('fee_zone_id') 
            )
            db.session.add(new_stop)
            db.session.commit()
            return jsonify(new_stop.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # 📝 UPDATE STOP (PUT)
    if request.method == 'PUT':
        stop = Stop.query.get(id)
        if not stop: return jsonify({'error': 'Not found'}), 404
        if user.role != 'super_admin' and stop.company_id != user.company_id:
            return jsonify({'error': 'Unauthorized'}), 403

        data = request.json
        stop.stop_name = data.get('stop_name', stop.stop_name)
        stop.km = float(data.get('km', stop.km))
        stop.zone = data.get('zone', stop.zone)
        stop.fee_zone_id = data.get('fee_zone_id', stop.fee_zone_id)
        
        db.session.commit()
        return jsonify(stop.to_dict()), 200

    # 🗑️ DELETE STOP (DELETE)
    if request.method == 'DELETE':
        stop = Stop.query.get(id)
        if not stop: return jsonify({'error': 'Stop not found'}), 404
        
        # Security: Only owner or Super Admin
        if user.role != 'super_admin' and stop.company_id != user.company_id:
            return jsonify({'error': 'Unauthorized'}), 403

        db.session.delete(stop)
        db.session.commit()
        return jsonify({'message': 'Stop deleted'}), 200

@app.route('/api/calculate_fee', methods=['POST', 'OPTIONS'])
def calculate_fee():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200
    try:
        data = request.json
        stop_id = data.get('stop_id')
        branch = data.get('branch', 'PSBN').strip()
        
        # 1. Fetch the stop using the correct model 'Stop'
        stop = db.session.get(Stop, stop_id)
        if not stop:
            print(f"⚠️ Stop ID {stop_id} not found.")
            return jsonify({'price': 0}), 200
            
        # 2. Smart Conversion for distance (handles "1.5 KM" or 1.5)
        raw_km = getattr(stop, 'km', 0)
        try:
            if isinstance(raw_km, str):
                dist = float(raw_km.upper().replace('KM', '').strip())
            else:
                dist = float(raw_km or 0)
        except:
            dist = 0.0

        # 3. Find the FeeZone for THIS specific school (company_id)
        zone = FeeZone.query.filter(
            FeeZone.company_id == stop.company_id, # 🛡️ SaaS isolation
            FeeZone.branch.ilike(branch), 
            FeeZone.min_km <= dist,
            FeeZone.max_km >= dist
        ).first()
        
        final_price = 0
        if zone and zone.price is not None:
            final_price = int(zone.price)
            
        print(f"💰 Fee Calculated: {dist}KM at {branch} = ₹{final_price}")
        return jsonify({'price': final_price}), 200

    except Exception as e:
        print(f"❌ FEE ERROR: {e}")
        return jsonify({'price': 0, 'error': str(e)}), 500

# ==========================================
# 🛰️ UNIFIED LIVE MAP FEED (Final Fix)
# ==========================================
@app.route('/api/hardware/gps/all', methods=['GET'])
def get_all_bus_locations():
    try:
        # 1. Fetch only buses that have a GPS device ID
        buses = Bus.query.filter(Bus.gps_device_id != None).all()
        
        results = []
        for bus in buses:
            # 🚀 FIXED: Changed bus_number to bus_no to match your DB model
            results.append({
                "bus_number": getattr(bus, 'bus_no', 'Unknown'), 
                "lat": getattr(bus, 'last_lat', 13.1187) or 13.1187, 
                "lng": getattr(bus, 'last_lng', 77.5752) or 77.5752,
                "status": getattr(bus, 'status', 'stopped') or "stopped",
                "speed": getattr(bus, 'speed', 0) or 0,
                "device_id": bus.gps_device_id
            })
            
        return jsonify(results), 200
    except Exception as e:
        # 🐛 This will print the EXACT error in your Python terminal
        print(f"❌ GPS API CRASH: {str(e)}") 
        return jsonify({"error": str(e)}), 500

# 📊 SMART DASHBOARD STATS (Fixed to prevent Crash)
@app.route('/api/admin/stats', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required() # 🚀 ADD THIS GUARD HERE
def get_stats():
    # Handle the "Preflight" check for browsers
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200

    # Now it is safe to use get_jwt_identity() because of the guard above
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    # Get the branch from the URL
    branch_name = request.args.get('branch', 'All Branches')
    
    # 🛡️ SECURITY: If not Super Admin, they can ONLY see their own school's stats
    if user.role != 'super_admin':
        # Force the branch to be their school name instead of "All Branches"
        branch_name = user.company.name if user.company else 'Main'

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🕵️ SUPER ADMIN (Mansoor) Logic
    if user.role == 'super_admin' and not user.company_id:
        return jsonify({
            "total_clients": Company.query.count(),
            "total_buses": Bus.query.count(),
            "is_super_developer": True
        }), 200

    # 🏢 SCHOOL ADMIN / BRANCH INCHARGE Logic
    query = Bus.query.filter_by(company_id=user.company_id)
    if user.role == 'admin': # Branch Incharge
        query = query.filter_by(company_id=user.company_id)
    
    return jsonify({
        "moving": query.filter_by(status='moving').count(),
        "stopped": query.filter_by(status='stopped').count(),
        "idle": query.filter_by(status='idle').count(),
        "total": query.count(),
        "students": Student.query.filter_by(company_id=user.company_id).count()
    }), 200
    
# 🗺️ 2. FIX THE MAP (Previously 500-ing)
@app.route('/api/admin/fleet_locations', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_fleet_locations():
    if request.method == 'OPTIONS': return _cors_response()
    
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        is_super = user.role.lower() == 'super_admin'
        
        # 🏢 Get target company from URL if managing a specific school
        raw_cid = request.args.get('company_id')
        final_cid = get_safe_id(raw_cid) if is_super else user.company_id
        
        markers = []
        branch_name = request.args.get('branch', '').strip().upper()
        is_global_view = not branch_name or branch_name in ["ALL BRANCHES", "GLOBAL", "NULL", ""]

        # 🏫 1. Query Schools (Branches)
        school_query = Branch.query
        # 🛡️ God View Logic: Only filter by company if we aren't Super Admin OR if a specific school is picked
        if not is_super or final_cid:
            school_query = school_query.filter_by(company_id=final_cid)
        
        if not is_global_view:
            school_query = school_query.filter(func.upper(Branch.name) == branch_name)
        
        for br in school_query.all():
            if br.latitude:
                markers.append({
                    "id": f"school_{br.id}", 
                    "type": "school", 
                    "name": br.name,
                    "lat": float(br.latitude), 
                    "lng": float(br.longitude)
                })

        # 🏢 2. Query Buses
        bus_query = Bus.query
        # 🛡️ God View Logic: Show all buses for Super Admin unless a specific school is picked
        if not is_super or final_cid:
            bus_query = bus_query.filter_by(company_id=final_cid)
        
        if not is_global_view:
            bus_query = bus_query.filter(func.upper(Bus.branch) == branch_name)

        buses = bus_query.all()
        for i, bus in enumerate(buses):
            lat = float(getattr(bus, 'last_lat', 13.1187) or 13.1187)
            lng = float(getattr(bus, 'last_lng', 77.5752) or 77.5752)
            
            markers.append({
                "id": f"bus_{bus.id}", 
                "type": "bus", 
                "name": bus.bus_no,
                "lat": lat + (0.0004 * i),
                "lng": lng + (0.0004 * i),
                "status": "Active"
            })

        return jsonify(markers), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 👩‍🏫 LADY ATTENDER MANAGEMENT (SaaS)
# ==========================================
@app.route('/api/admin/attenders', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required()
def handle_admin_attenders():
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    is_super = user.role.lower() == 'super_admin'
    
    # 🏢 Determine the School ID (SaaS Isolation)
    raw_cid = request.args.get('company_id')
    final_cid = get_safe_id(raw_cid) if is_super else user.company_id

    # 📂 1. FETCH ATTENDERS (GET)
    if request.method == 'GET':
        from sqlalchemy import func
        query = User.query.filter_by(company_id=final_cid, role='attender')
        
        # Get branch name from Flutter (e.g., 'TESTTWO')
        target_branch = request.args.get('branch', '').strip().upper()

        # 🛡️ SMART FILTERING
        if user.role.lower() == 'branch_incharge':
            # 🔒 Branch Incharges only see their own branch
            search_val = (user.branch_id or "").strip().upper()
            query = query.filter(func.upper(User.branch_id) == search_val)
        
        elif target_branch and target_branch not in ["ALL", "ALL BRANCHES", ""]:
            # 🔓 Admins filter by selected branch
            query = query.filter(func.upper(User.branch_id) == target_branch)
            print(f"🕵️‍♂️ Admin Filtering Attenders for: {target_branch}")

        attenders = query.all()
        return jsonify([u.to_dict() for u in attenders]), 200

    # ➕ 2. ADD ATTENDER (POST)
    if request.method == 'POST':
        data = request.json
        phone_as_username = data.get('phone') 
        real_name = data.get('username') # This is "Shilpa" from Flutter
        branch_from_flutter = data.get('branch', '').strip().upper()
        
        # 🛡️ 1. Determine assigned_branch
        if user.role.lower() == 'branch_incharge':
            assigned_branch = (user.branch_id or "").strip().upper()
        else:
            assigned_branch = "MAIN" if branch_from_flutter in ["ALL", "ALL BRANCHES", ""] else branch_from_flutter

        try:
            # 🛡️ 2. Unique Check
            existing_user = User.query.filter_by(username=phone_as_username).first()
            if existing_user:
                return jsonify({"error": f"Phone number {phone_as_username} is already registered."}), 400

            new_attender = User(
                username=phone_as_username, 
                name=real_name,             # 👈 SAVE THE REAL NAME HERE
                password_hash=generate_password_hash(data.get('password', '1234')),
                role='attender',
                company_id=final_cid,
                branch_id=assigned_branch, 
                contact_number=data.get('phone'),
                license_info=data.get('license_info')
            )
            db.session.add(new_attender)
            db.session.commit()
            return jsonify(new_attender.to_dict()), 201
                
        except Exception as e:
            db.session.rollback()
            error_msg = str(e)
            if "users.license_info" in error_msg:
                clean_error = "This Aadhar/ID is already registered to another staff member."
            else:
                clean_error = "Database Error: " + error_msg
            return jsonify({"error": clean_error}), 400

# 📝 Update Attender (Fixes the 'phone' attribute error)
@app.route('/api/admin/attenders/<int:id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_single_attender(id):
    if request.method == 'OPTIONS': return _cors_response()
    
    user = db.session.get(User, id)
    if not user: return jsonify({"error": "Staff member not found"}), 404

    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "Staff deleted successfully"}), 200

    # 📝 3. UPDATE ATTENDER (PUT)
    if request.method == 'PUT':
        attender = db.session.get(User, id)
        if not attender: return jsonify({'error': 'Not found'}), 404
        
        data = request.json
        # 🚀 THE FIX: Update the name field during edits
        # Inside your PUT logic for attenders:
        attender.name = data.get('username', attender.name) # Now 'name' is a valid attribute!
        attender.contact_number = data.get('phone', attender.contact_number)
        attender.license_info = data.get('license_info', attender.license_info)
        attender.branch_id = data.get('branch', attender.branch_id).upper()

        db.session.commit()
        return jsonify(attender.to_dict()), 200

# ==========================================
# 📥 UNIFIED DOWNLOAD (Excel Exporter)
# ==========================================
@app.route('/api/admin/download/<string:data_type>', methods=['GET'])
def unified_download_excel(data_type):
    try:
        # 🛡️ 1. AUTHENTICATION
        token = request.args.get('token') or request.args.get('access_token')
        if not token:
            return jsonify({"error": "No token provided"}), 401
        
        from flask_jwt_extended import decode_token
        decoded = decode_token(token)
        user = db.session.get(User, int(decoded['sub']))

        # 🏢 2. CLEANING & SETUP
        # This turns 'buses_full' or 'buses_template' into just 'buses'
        clean_type = data_type.lower().replace('_full', '').replace('_template', '').strip()
        is_template = 'template' in data_type.lower()
        target_branch = request.args.get('branch', 'ALL').strip().upper()
        
        data = []
        columns = []

        print(f"📥 DOWNLOAD REQUEST: Type={clean_type}, Template={is_template}, Branch={target_branch}")

        # 🎓 A. STUDENTS
        if clean_type == 'students':
            columns = ['Student Name', 'Admission No', 'Grade', 'Div', 'AM Route', 'Noon Route', 'PM Route', 'Assigned Bus']
            if not is_template:
                query = Student.query.filter_by(company_id=user.company_id)
                if target_branch != "ALL" and target_branch != "ALL BRANCHES":
                    query = query.filter(db.func.upper(Student.branch) == target_branch)
                recs = query.all()
                data = [s.to_dict() for s in recs] # Simplification for example

        # 🚌 B. BUSES (The section causing your error)
        elif clean_type == 'buses':
            columns = [
                'Bus Number', 'Chassis Number', 'Seater Capacity', 
                'Morning Route', 'Noon Route', 'Evening Route', 
                'Lady Attender', 'GPS Device ID', 'SIM No', 'RFID Reader ID', 'Branch'
            ]
            
            if not is_template:
                query = Bus.query.filter_by(company_id=user.company_id)
                if target_branch != "ALL" and target_branch != "ALL BRANCHES":
                    query = query.filter(db.func.upper(Bus.branch) == target_branch)
                recs = query.all()

                for r in recs:
                    morning_obj = db.session.get(Route, r.morning_route_id) if r.morning_route_id else None
                    noon_obj = db.session.get(Route, r.noon_route_id) if r.noon_route_id else None
                    evening_obj = db.session.get(Route, r.evening_route_id) if r.evening_route_id else None
                    staff_obj = db.session.get(User, r.attender_id) if r.attender_id else None

                    data.append({
                        'Bus Number': r.bus_no, 'Chassis Number': r.chassis_no, 
                        'Seater Capacity': r.seater_capacity,
                        'Morning Route': morning_obj.route_name if morning_obj else "Not Assigned",
                        'Noon Route': noon_obj.route_name if noon_obj else "Not Assigned",
                        'Evening Route': evening_obj.route_name if evening_obj else "Not Assigned",
                        'Lady Attender': staff_obj.username if staff_obj else "Not Assigned",
                        'GPS Device ID': r.gps_device_id, 'SIM No': r.sim_no, 
                        'RFID Reader ID': r.rfid_reader_id, 'Branch': r.branch
                    })

        # 📍 C. STOPS
        elif clean_type == 'stops':
            columns = ['Stop Name', 'Zone', 'Distance (KM)', 'Latitude', 'Longitude']
            if not is_template:
                recs = Stop.query.filter_by(company_id=user.company_id).all()
                data = [{'Stop Name': s.stop_name, 'Zone': s.zone, 'Distance (KM)': s.km} for s in recs]

        # 🛑 SAFETY CHECK: If clean_type matched nothing
        else:
            return jsonify({"error": f"Invalid data type: {clean_type}"}), 400

        # 🛡️ 3. FINAL FILE GENERATION
        if is_template and not data:
            data = [{col: "" for col in columns}]

        if not data and not is_template:
            return jsonify({"error": "No data found to export"}), 404

        # Generate the Excel file
        df = pd.DataFrame(data, columns=columns)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        output.seek(0)
        return send_file(
            output, 
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True, 
            download_name=f"{target_branch}_{clean_type}.xlsx"
        )

    except Exception as e:
        db.session.rollback()
        print(f"❌ MASTER DOWNLOAD ERROR: {str(e)}")
        return jsonify({"error": str(e)}), 500

# ==========================================
#  🚌 GENERAL SIMULATOR ROUTE (Fixes 404)
# ==========================================
@app.route('/api/bus/live_location', methods=['GET'])
def get_general_live_location():
    # This provides a default location for the "Simulator" sidebar tab
    return jsonify({
        "bus_number": "KA-01-TEST",
        "latitude": 13.1000 + random.uniform(-0.001, 0.001), 
        "longitude": 77.5900 + random.uniform(-0.001, 0.001),
        "speed": 45.0,
        "status": "Moving"
    }), 200

# ==========================================
#  👨‍👩‍👧‍👦 PARENT DASHBOARD API
# ==========================================
# 👨‍👩‍👧 GET PARENT CHILDREN (Fixed: Sends GPS ID for Tracking)
@app.route('/api/parent/student_info', methods=['GET'])
def get_parent_student_info():
    user_id_raw = request.args.get('user_id')
    if not user_id_raw or user_id_raw == 'null':
        return jsonify({"message": "User ID missing"}), 400
        
    user = db.session.get(User, int(user_id_raw))
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Fetch all students linked to this parent's mobile (username)
    students = Student.query.filter_by(parent_mobile=user.username).all()
    
    results = []
    for s in students:
        # 🕵️‍♂️ FIND THE ATTENDER FOR THIS CHILD'S BUS
        bus = Bus.query.get(s.bus_id) if s.bus_id else None
        attender = User.query.get(bus.attender_id) if (bus and bus.attender_id) else None

        results.append({
            "id": s.id,
            "student_name": getattr(s, 'student_name', getattr(s, 'name', 'Unknown')),
            "admission_no": s.admission_no,
            "grade": s.grade,
            "total_fee": s.total_fee,
            "payment_status": s.payment_status,
            "last_status": s.last_status or "AT HOME",
            "parent_name": user.username,
            "branch": s.branch,
            "bus_gps_id": s.bus_id, 
            "pickup_point": f"Stop ID: {s.pickup_stop_id}" if s.pickup_stop_id else "Not Assigned",
            "bus_number": bus.bus_no if bus else "Not Assigned",
            # ✨ ADDED FOR THE CALL BUTTON ✨
            "attender_name": attender.name if attender else "Not Assigned",
            "attender_phone": attender.contact_number if attender else None
        })
    return jsonify(results), 200

@app.route('/api/attendance', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_attendance():
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200
    
    try:
        from sqlalchemy import func, or_
        user = db.session.get(User, int(get_jwt_identity()))
        
        # 🛡️ THE SMART QUERY:
        # Show logs that match the company_id OR logs that are NULL (old data)
        query = AttendanceLog.query.filter(
            or_(
                AttendanceLog.company_id == user.company_id,
                AttendanceLog.company_id == None
            )
        )

        branch_param = request.args.get('branch', '').strip().upper()
        if branch_param and branch_param not in ["ALL", "ALL BRANCHES", ""]:
            query = query.filter(func.upper(AttendanceLog.branch) == branch_param)

        logs = query.order_by(AttendanceLog.timestamp.desc()).limit(100).all()
        return jsonify([log.to_dict() for log in logs]), 200

    except Exception as e:
        print(f"❌ Attendance API Error: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
#  🆔 RFID ATTENDANCE SYSTEM
# ==========================================
@app.route('/api/hardware/rfid', methods=['POST'])
def receive_rfid_scan():
    data = request.json
    tag = data.get('rfid_tag')
    
    # Find the student to get their branch
    student = Student.query.filter_by(rfid_tag=tag).first()
    if not student:
        return jsonify({"error": "Unknown Card"}), 404

    new_status = "Boarded" if student.last_status != "Boarded" else "Dropped"
    student.last_status = new_status 
    
    # ✅ FIX: Tag the log with the student's branch (e.g., PSBN)
    log = AttendanceLog(
        student_id=student.id,
        status=new_status,
        branch=student.branch, # 🚀 This is what the Flutter filter looks for
        location="School/Bus Stop"
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"message": "Success", "student": student.name, "status": new_status}), 200

# ==========================================
# 🎫 RFID / I-CARD TAP HANDLER
# ==========================================
@app.route('/api/attendance/tap', methods=['POST'])
def handle_rfid_tap():
    data = request.json
    # 1. Get IDs from the hardware request
    student_id = data.get('student_id')
    bus_no = data.get('bus_number')
    
    if not student_id:
        return jsonify({"error": "Missing Student ID"}), 400

    # 🕵️‍♂️ 2. Find the student in the database
    student = db.session.get(Student, int(student_id))
    if not student:
        return jsonify({"error": "Student not found in database"}), 404

    try:
        # 🚀 3. THE MAGIC: "Inherit" data from the student record
        # This ensures the log is NEVER 'null' for branch or company
        new_log = AttendanceLog(
            student_id=student.id,
            student_name=student.name,
            status="Boarded", 
            bus_number=bus_no,
            branch=student.branch,       # 📍 From Student record
            company_id=student.company_id, # 🏢 From Student record
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_log)
        db.session.commit()
        
        print(f"✅ Attendance Logged: {student.name} boarded Bus {bus_no} ({student.branch})")
        return jsonify({"message": f"Welcome, {student.name}"}), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Tap Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500

# ==========================================
#  🛰️ HARDWARE GPS TRACKING (Fixes 404)
# ==========================================
@app.route('/api/hardware/gps/<device_id>', methods=['GET'])
def get_device_live_location(device_id):
    try:
        # Simulate GPS coordinates for the requested Device ID
        return jsonify({
            "device_id": device_id,
            "latitude": 13.1000 + random.uniform(-0.001, 0.001), 
            "longitude": 77.5900 + random.uniform(-0.001, 0.001),
            "speed": 45.0,
            "status": "Moving",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
#  📢 CIRCULAR / NOTICE BOARD APIs
# ==========================================
@app.route('/api/admin/notice', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
def upload_notice():
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'CORS OK'}), 200

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    verify_jwt_in_request()
    
    user = db.session.get(User, int(get_jwt_identity()))
    
    try:
        # 1. Get Text Data
        title = request.form.get('title')
        description = request.form.get('description')
        target_branch = request.form.get('branch', 'All Branches') # From Flutter Dropdown
        
        # 2. Logic: If Admin selects "All Branches", we store as "GLOBAL"
        # If it's a Branch Incharge, it will just be their branch name (e.g., TESTONE)
        final_branch = "GLOBAL" if target_branch == "All Branches" else target_branch.upper()

        file_filename = None
        # 3. Handle File Upload (Image/PDF)
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                file_filename = unique_filename

        # 4. Save to DB with Company ID
        new_notice = Notice(
            title=title, 
            description=description, 
            file_path=file_filename,
            branch=final_branch,
            company_id=user.company_id # 🛡️ Anchors notice to this school only
        )
        db.session.add(new_notice)
        db.session.commit()

        return jsonify({"message": "Notice Sent Successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/notices', methods=['GET', 'OPTIONS'])
@jwt_required() # 🛡️ Always protect data
def get_notices():
    if request.method == 'OPTIONS': return jsonify({'ok': True}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🔍 Step 1: Base query (Stay within this school)
    query = Notice.query.filter_by(company_id=user.company_id)
    
    # 🔍 Step 2: Branch logic
    if user.role in ['admin', 'super_admin']:
        # Admins can see everything in their school
        pass 
    else:
        # Incharges/Parents only see their branch + Global ones
        # First, find the branch name for this user
        BranchModel = globals().get('Branch')
        b_name = "UNKNOWN"
        if BranchModel:
            b_obj = db.session.get(BranchModel, user.branch_id)
            b_name = b_obj.name.upper() if b_obj else "GLOBAL"

        query = query.filter((Notice.branch == b_name) | (Notice.branch == "GLOBAL"))

    notices = query.order_by(Notice.date_posted.desc()).all()
    
    output = []
    for n in notices:
        file_url = f"{request.host_url}static/notices/{n.file_path}" if n.file_path else None
        output.append({
            "id": n.id,
            "title": n.title,
            "description": n.description,
            "branch": n.branch, # Shows if it's GLOBAL or specific
            "date": n.date_posted.strftime("%Y-%m-%d"),
            "file_url": file_url
        })
    return jsonify(output), 200

# ==========================================
#  💰 FEES & PAYMENTS APIs
# ==========================================

# 1. Admin Assigns a Fee to a Student
@app.route('/api/admin/fees/assign', methods=['POST', 'OPTIONS'])
@jwt_required() # Require token
def secure_assign_fee():
    if request.method == 'OPTIONS':
        return _cors_response()
    
    data = request.json
    try:
        # Check if student exists
        student = db.session.get(Student, data['student_id'])
        if not student:
            return jsonify({"error": "Student not found"}), 404

        new_fee = FeeRecord(
            student_id=data['student_id'],
            company_id=student.company_id, # 🛡️ Link it to the school!
            title=data['title'],
            amount=float(data['amount']),
            due_date=data.get('due_date', '2026-04-10'),
            status="Pending"
        )
        db.session.add(new_fee)
        db.session.commit()
        return jsonify({"message": "Fee Assigned Successfully!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# 👨‍👩‍👧 PARENT API: Child & Bus Discovery
# ==========================================
@app.route('/api/parent/login', methods=['POST'])
def parent_login():
    data = request.json
    mobile = data.get('mobile', '').strip()
    
    # Find the child linked to this mobile number
    student = Student.query.filter_by(parent_mobile=mobile).first()
    
    if not student:
        return jsonify({"error": "No student found with this mobile number"}), 404
        
    # Get the assigned bus details
    bus = Bus.query.get(student.bus_id) if student.bus_id else None
    
    return jsonify({
        "student_id": student.id,
        "student_name": student.name,
        "bus_number": bus.bus_number if bus else "Not Assigned",
        "bus_id": bus.id if bus else None,
        "fee_total": student.total_fee,
        "payment_status": student.payment_status
    }), 200

# 2. Parent Views Their Fees
@app.route('/api/parent/fees', methods=['GET'])
def get_parent_fees():
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    
    if not user:
        return jsonify([])

    # 1. Find the student linked to this parent's mobile (username)
    # This matches the TEST SAARA record you added
    students = Student.query.filter_by(parent_mobile=user.username).all()
    
    output = []
    for s in students:
        # 2. Check the Student Table for the Base Transport Fee
        # If the Branch In-charge set a fee but status isn't 'Paid'
        if s.payment_status != "Paid" and (s.total_fee or 0) > 0:
            output.append({
                "id": s.id, 
                "student_name": s.name, # ✅ Fixed field name
                "title": "Annual Transport Fee",
                "amount": float(s.total_fee),
                "due_date": "2026-03-31",
                "status": s.payment_status or "Pending",
                "payment_date": "-"
            })
            
    # 3. Also check the FeeRecord table for any specific invoices
    fee_records = FeeRecord.query.filter(FeeRecord.student_id.in_([s.id for s in students])).all()
    for f in fee_records:
        output.append({
            "id": f.id,
            "student_name": f.student.name, # ✅ Fixed: changed student_name to name
            "title": f.title,
            "amount": float(f.amount),
            "due_date": f.due_date,
            "status": f.status,
            "payment_date": f.payment_date.strftime('%Y-%m-%d') if f.payment_date else "-"
        })
        
    return jsonify(output), 200

# 3. Parent Pays the Fee (Simulated)
@app.route('/api/parent/pay', methods=['POST'])
def pay_fee():
    data = request.json
    fee_id = data.get('fee_id')
    
    # 1. First, check if it's a specific record in the FeeRecord table
    fee = FeeRecord.query.get(fee_id)
    if fee:
        fee.status = "Paid"
        fee.payment_date = datetime.now()
        db.session.commit()
        return jsonify({"message": "Payment Successful!", "status": "Paid"}), 200

    # 2. If not in FeeRecord, check if it's the Base Transport Fee in the Student table
    # Since we passed s.id as the fee_id in the previous step
    student = Student.query.get(fee_id)
    if student:
        student.payment_status = "Paid" # ✅ This enables the "TRACK LIVE BUS" button!
        db.session.commit()
        return jsonify({"message": "Annual Fee Paid!", "status": "Paid"}), 200

    return jsonify({"error": "Invoice not found"}), 404

@app.route('/api/students/<int:id>/pay', methods=['POST'])
def process_payment(id):
    student = Student.query.get(id)
    data = request.json
    
    # ✅ Update the actual database field
    student.total_fee = float(data.get('amount', 27500)) 
    student.paid_fee = student.total_fee # Mark as fully paid
    student.last_status = "Fee Paid"
    
    db.session.commit()
    return jsonify({"message": "Payment recorded", "fee": student.total_fee}), 200

# ==========================================
#  🤖 SMART TRANSPORT ASSIGNMENT (Auto-Fee)
# ==========================================
@app.route('/api/admin/assign_transport', methods=['POST'])
@jwt_required()
def assign_transport():
    current_user_id = get_jwt_identity()
    admin_user = db.session.get(User, int(current_user_id))
    
    data = request.json
    student_id = data.get('student_id')
    stop_id = data.get('stop_id') 

    # 🚀 FIX 1: Use 'Stop' (the name of your class), not 'BusStop'
    student = db.session.get(Student, student_id)
    stop = db.session.get(Stop, stop_id)

    if not student or not stop:
        return jsonify({"error": "Student or Stop not found"}), 404

    # 🕵️ ROLE-BASED SECURITY CHECK
    # Allow Super Admin, School Admin, and Branch Incharge
    allowed_roles = ['super_admin', 'admin', 'branch_incharge']
    if admin_user.role.lower() not in allowed_roles:
        return jsonify({"error": "Unauthorized"}), 403

    # 🔒 Branch Lockdown: Incharge can only edit their own branch
    if admin_user.role.lower() == 'branch_incharge':
        if str(student.branch).upper() != str(admin_user.branch_id).upper():
            return jsonify({"error": "Unauthorized! Student is in a different branch."}), 403

    # 1. ASSIGN STOP
    student.pickup_stop_id = stop_id
    
    # 2. AUTO-LINK BUS (If the stop belongs to a bus)
    # We look for a bus that has this branch and matches the shift
    # For now, we link the stop directly if your model supports it
    
    # 3. FIX 2: Use 'FeeZone' (the name of your class), not 'Zone'
    zone = db.session.get(FeeZone, stop.fee_zone_id) if stop.fee_zone_id else None
    
    if not zone:
        db.session.commit()
        return jsonify({"message": "Stop assigned, but no Fee Zone price found."}), 200

    # 4. AUTO-CREATE FEE
    student.total_fee = zone.price
    student.payment_status = "Pending" 

    existing_fee = FeeRecord.query.filter_by(student_id=student.id, title="Transport Fee (Auto)").first()
    
    if not existing_fee:
        new_fee = FeeRecord(
            student_id=student.id,
            title="Transport Fee (Auto)",
            amount=zone.price,
            due_date="2026-06-30",
            status="Pending"
        )
        db.session.add(new_fee)
        message = f"Success: Transport assigned & Fee of ₹{zone.price} generated."
    else:
        existing_fee.amount = zone.price
        message = f"Success: Transport updated for {student.name}."

    db.session.commit()
    return jsonify({"message": message}), 200

# ==========================================
#  🚌 SELF-SERVICE TRANSPORT (Updated)
# ==========================================

# 1. Get Stops with Prices (Smart KM Check) 🧠
@app.route('/api/public/stops', methods=['GET'])
def get_public_stops():
    # FIX: Use 'Stop' and 'FeeZone'
    stops = Stop.query.all()
    zones = FeeZone.query.all() 
    output = []
    
    for s in stops:
        price = 0
        # Check by KM match if no explicit link
        for z in zones:
            if z.min_km <= s.km <= z.max_km:
                price = z.price
                break
        
        output.append({
            "id": s.id,
            "name": s.stop_name,
            "price": price,
            "branch": s.branch
        })
    return jsonify(output), 200


@app.route('/api/parent/select_transport', methods=['POST'])
def parent_select_transport():
    try:
        data = request.json
        student_id = data.get('student_id')
        stop_id = data.get('stop_id')

        student = db.session.get(Student, student_id)
        stop = db.session.get(Stop, stop_id) # Using 'Stop' to match your class name

        if not student or not stop: 
            return jsonify({"error": "Student or Stop not found"}), 404

        # 1. 🧠 SMART PRICE CALCULATION
        # Look for a FeeZone that matches the KM of this stop
        price = 0.0
        zones = FeeZone.query.filter_by(company_id=student.company_id).all()
        for z in zones:
            if z.min_km <= stop.km <= z.max_km:
                price = z.price
                break
        
        if price == 0:
            price = 20.0 # Emergency fallback for your demo

        # 2. Assign Stop to Student
        student.pickup_stop_id = stop_id
        student.total_fee = price
        student.payment_status = "Pending"

        # 3. Create/Update the FeeRecord
        existing_fee = FeeRecord.query.filter_by(student_id=student.id, title="Annual Transport Fee").first()
        
        if existing_fee:
            if existing_fee.status == "Paid":
                return jsonify({"error": "Fee already paid! Please contact school to change stops."}), 400
            existing_fee.amount = price 
        else:
            new_fee = FeeRecord(
                student_id=student.id,
                title="Annual Transport Fee",
                amount=price,
                due_date="2026-06-01",
                status="Pending"
            )
            db.session.add(new_fee)

        db.session.commit()
        return jsonify({
            "message": f"Transport Assigned! Please pay ₹{price} to enable tracking.",
            "fee": price
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# ==========================================
# 🏢 MASTER BRANCH CONTROLLER (SaaS Version)
# ==========================================
@app.route('/api/branches', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/branches/<int:id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def handle_branches_master(id=None):
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 📂 1. FETCH BRANCHES (GET)
    if request.method == 'GET':
        # Use our helper to safely handle 'null' or missing IDs
        target_company = get_safe_id(request.args.get('company_id'))

        if user.role == 'super_admin':
            if target_company:
                # 🏫 Mansoor managing a specific school
                query = Branch.query.filter_by(company_id=target_company)
            else:
                # 🌍 Mansoor in Global Mode (shows every branch)
                query = Branch.query
        else:
            # 🔒 Regular Admin/Staff: Locked to their own school
            query = Branch.query.filter_by(company_id=user.company_id)
            
        # Sort A-Z so the dropdown in Flutter looks professional
        branches = query.order_by(Branch.name.asc()).all()
        return jsonify([b.to_dict() for b in branches]), 200

    # 📝 2. CREATE BRANCH (POST)
    if request.method == 'POST':
        data = request.json
        name = data.get('name') or data.get('branch_name')
        
        # Determine company ownership safely
        raw_cid = data.get('company_id')
        target_company_id = get_safe_id(raw_cid) if user.role == 'super_admin' else user.company_id

        if not target_company_id or not name:
            return jsonify({'error': 'Missing branch name or company_id'}), 400

        new_branch = Branch(
            name=name,
            latitude=data.get('latitude', 0.0),
            longitude=data.get('longitude', 0.0),
            company_id=target_company_id
        )
        db.session.add(new_branch)
        db.session.commit()
        return jsonify({'message': 'Branch created successfully', 'id': new_branch.id}), 201

    # 🗑️ 3. DELETE BRANCH (DELETE)
    if request.method == 'DELETE':
        if not id:
            return jsonify({'error': 'No branch ID provided'}), 400
            
        branch = Branch.query.get(id)
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
            
        # Security: Prevent deleting branches from other schools
        if user.role != 'super_admin' and branch.company_id != user.company_id:
            return jsonify({'error': 'Unauthorized'}), 403
            
        db.session.delete(branch)
        db.session.commit()
        return jsonify({'message': 'Branch deleted successfully'}), 200

# ==========================================
# 🗺️ SECURE ZONE & FEES MANAGEMENT (SaaS)
# ==========================================
@app.route('/api/admin/zones', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required()
def manage_zones():
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'CORS OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    
    # 🛡️ 1. Determine the School ID (The SaaS Key)
    raw_cid = request.args.get('company_id')
    target_cid = get_safe_id(raw_cid)
    
    # Final School ID logic
    final_cid = target_cid if (user.role == 'super_admin' and target_cid) else user.company_id

    # 📂 2. FETCH ZONES (GET)
    if request.method == 'GET':
        from sqlalchemy import func
        query = FeeZone.query.filter_by(company_id=final_cid)

        branch_filter = request.args.get('branch', '').strip().upper()
        
        # 🚀 THE FIX: Use func.upper for case-insensitive matching
        if branch_filter and branch_filter not in ["ALL", "ALL BRANCHES", "GLOBAL (ALL BRANCHES)", ""]:
            query = query.filter(func.upper(FeeZone.branch) == branch_filter)

        zones = query.order_by(FeeZone.zone_name.asc()).all()
        return jsonify([z.to_dict() for z in zones]), 200

    # ➕ 3. ADD ZONE (POST)
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('zone_name') or data.get('name')
            if not name:
                return jsonify({'error': 'Zone name is required'}), 400

            # Use our safe helper for numbers
            def safe_float(val):
                try:
                    return float(val) if val and str(val).strip() != "" else 0.0
                except:
                    return 0.0

            new_zone = FeeZone(
                zone_name=name,
                min_km=safe_float(data.get('min_km')),
                max_km=safe_float(data.get('max_km')),
                price=safe_float(data.get('price')),
                branch=str(data.get('branch', 'MAIN')).upper(),
                term=data.get('term', 'Annual'),
                mode=data.get('mode', 'Two-Way'),
                company_id=final_cid # ✅ Correctly linked to school
            )
            
            db.session.add(new_zone)
            db.session.commit()
            return jsonify(new_zone.to_dict()), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

@app.route('/api/admin/zones/<int:id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_single_zone(id):
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'CORS OK'}), 200
        
    user = db.session.get(User, int(get_jwt_identity()))
    # 🛡️ Security: Only find the zone if it belongs to THIS company
    zone = FeeZone.query.filter_by(id=id, company_id=user.company_id).first()
    
    if not zone:
        return jsonify({'error': 'Zone not found or access denied'}), 404
        
    if request.method == 'DELETE':
        db.session.delete(zone)
        db.session.commit()
        return jsonify({'message': 'Zone deleted'}), 200
    
    if request.method == 'PUT':
        data = request.json
        zone.zone_name = data.get('name', zone.zone_name)
        zone.price = float(data.get('price', zone.price))
        zone.min_km = float(data.get('min_km', zone.min_km))
        zone.max_km = float(data.get('max_km', zone.max_km))
        zone.branch = data.get('branch', zone.branch).upper()
        db.session.commit()
        return jsonify({'message': 'Zone updated successfully'}), 200

# ==========================================
# 🚀 BULK DATA ALLOTMENT LOGIC
# ==========================================
@app.route('/api/admin/bulk-allot', methods=['POST'])
@jwt_required()
def bulk_allot_students():
    try:
        data = request.json
        bus_id = data.get('bus_id')
        stop_names = data.get('stops')
        branch_name = data.get('branch')
        
        # 🏢 THE SaaS FIX: Use the company_id from the JSON if Super Admin, 
        # otherwise use the user's assigned company.
        user_id = get_jwt_identity()
        user = db.session.get(User, int(user_id))
        
        target_company_id = data.get('company_id') if user.role == 'super_admin' else user.company_id

        # 1. Validation
        bus = Bus.query.filter_by(id=bus_id, company_id=target_company_id).first()
        if not bus:
            return jsonify({"error": "Bus not found for this school"}), 404

        # 2. Filter students
        query = Student.query.filter_by(company_id=target_company_id)
        if branch_name and branch_name != "All Branches":
            query = query.filter_by(branch=branch_name.upper())
            
        # 🚀 MASS UPDATE (Ensure your Student model has 'stop_name' column)
        students_to_update = query.filter(Student.stop_name.in_(stop_names)).all()

        count = 0
        for student in students_to_update:
            student.bus_id = bus_id
            count += 1
            
        db.session.commit()
        return jsonify({"message": f"Successfully assigned {count} students", "count": count}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/fleet')
@jwt_required() # 🔑 Added protection
def get_fleet():
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    # Get params from URL
    role = request.args.get('role')
    # If they are a branch_incharge, force them to ONLY see their own branch from the DB
    branch = user.branch if user.role == 'branch_incharge' else request.args.get('branch')

    # Top level isolation: Always filter by company_id
    query = Bus.query.filter_by(company_id=user.company_id)

    if user.role in ['super_admin', 'transport_manager']:
        if branch and branch != "All":
            query = query.filter_by(branch=branch.upper())
        buses = query.all()
    else:
        # Branch incharge can ONLY see their assigned branch
        buses = query.filter_by(branch=user.branch.upper()).all()
        
    return jsonify([b.to_dict() for b in buses])

@app.route('/api/admin/reports/data', methods=['GET'])
@jwt_required()
def get_daily_reports():
    try:
        from sqlalchemy import func # 👈 Ensure this is imported!
        branch_from_url = request.args.get('branch', '').strip().upper()
        user = db.session.get(User, int(get_jwt_identity()))

        query = Bus.query.filter_by(company_id=user.company_id)
        
        # 🚀 THE FIX: Use func.upper for a bulletproof match
        if branch_from_url and branch_from_url not in ["ALL", "ALL BRANCHES", ""]:
            query = query.filter(func.upper(Bus.branch) == branch_from_url)

        buses = query.all()
        report = []
        for bus in buses:
            # Using your safe helper 🛡️
            dist = get_safe_attr(bus, ['total_km', 'km', 'distance', 'mileage'])
            avg = get_safe_attr(bus, ['avg_speed', 'average_speed'])
            mx = get_safe_attr(bus, ['max_speed', 'top_speed'])

            report.append({
                "bus_number": bus.bus_no,
                "total_distance": f"{dist} km",
                "avg_speed": f"{avg} km/h",
                "max_speed": f"{mx} km/h",
                "status": "Active"
            })
        return jsonify(report), 200

    except Exception as e:
        print(f"❌ Daily Report Error: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# 🛰️ GPS FLEET STATS EXCEL EXPORT
# ==========================================
@app.route('/api/admin/reports/export', methods=['GET']) # 🚀 Matches your Flutter URL
@jwt_required(locations=["headers", "query_string"]) 
def export_gps_report():
    try:
        from sqlalchemy import func
        user = db.session.get(User, int(get_jwt_identity()))
        
        # Determine branch filter
        if user.role.lower() == 'branch_incharge':
            target_branch = (user.branch_id or "").strip().upper()
        else:
            target_branch = request.args.get('branch', '').strip().upper()

        # Query the Bus table for fleet stats
        query = Bus.query.filter_by(company_id=user.company_id)
        if target_branch and target_branch not in ["ALL BRANCHES", "ALL", ""]:
            query = query.filter(func.upper(Bus.branch) == target_branch)

        buses = query.all()
        
        # Create the Excel file
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Fleet Travel Report"
        ws.append(["Bus Number", "Branch", "Distance", "Avg Speed", "Max Speed"])

        for bus in buses:
            dist = get_safe_attr(bus, ['total_km', 'km', 'distance'])
            avg = get_safe_attr(bus, ['avg_speed', 'average_speed'])
            mx = get_safe_attr(bus, ['max_speed', 'top_speed'])
            ws.append([
                bus.bus_no, 
                bus.branch or "Main", 
                f"{dist} km", 
                f"{avg} km/h", 
                f"{mx} km/h"
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return send_file(
            output, 
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True, 
            download_name=f"Fleet_Report_{target_branch or 'Global'}.xlsx"
        )

    except Exception as e:
        print(f"❌ GPS Export Error: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
# 📊 1. STUDENT ATTENDANCE EXPORT
# ==========================================
@app.route('/api/attendance/export', methods=['GET'])
@jwt_required(locations=["headers", "query_string"])
def export_attendance_excel():
    try:
        from sqlalchemy import func
        user = db.session.get(User, int(get_jwt_identity()))
        
        # Security: Force branch if Incharge
        if user.role.lower() == 'branch_incharge':
            branch = (user.branch_id or "").strip().upper()
        else:
            branch = request.args.get('branch', '').strip().upper()

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Query AttendanceLog (Not Bus!)
        query = AttendanceLog.query.filter_by(company_id=user.company_id)
        if branch and branch not in ["ALL BRANCHES", "ALL", ""]:
            query = query.filter(func.upper(AttendanceLog.branch) == branch)
        if start_date and end_date:
            query = query.filter(AttendanceLog.timestamp.between(f"{start_date} 00:00:00", f"{end_date} 23:59:59"))

        logs = query.order_by(AttendanceLog.timestamp.desc()).all()
        data = []
        for log in logs:
            # 🚀 THE SMART FALLBACK:
            # Try the log column first, then the student's record, then 'Main'
            actual_branch = log.branch or (log.student.branch if log.student else "Main")
            actual_name = log.student_name or (log.student.name if log.student else "Unknown Student")

            data.append({
                "Student Name": actual_name,
                "Status": log.status,
                "Branch": actual_branch.upper(), # Make it look clean in Excel
                "Bus": log.bus_number,
                "Time": log.timestamp[:16] if isinstance(log.timestamp, str) else log.timestamp.strftime('%Y-%m-%d %H:%M')
            })

        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance')
        output.seek(0)
        return send_file(output, as_attachment=True, download_name="Attendance_Report.xlsx")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/companies', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required(optional=True)
def handle_companies():
    # 🚀 1. Handle CORS Pre-flight
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OK'}), 200

    # 🚀 2. Enforce Security
    from flask_jwt_extended import verify_jwt_in_request
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Missing or invalid token"}), 401

    user = db.session.get(User, get_jwt_identity())
    if not user or user.role.lower() not in ['super_admin', 'developer', 'admin']:
        return jsonify({"error": f"Unauthorized"}), 403

    # 📂 3. FETCH CLIENTS (GET)
    if request.method == 'GET':
        if user.role.lower() in ['super_admin', 'developer']:
            companies = Company.query.all()
        else:
            companies = Company.query.filter_by(id=user.company_id).all()
        return jsonify([c.to_dict() for c in companies]), 200

    # 📝 4. REGISTER NEW CLIENT (POST)
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data or not data.get('name'):
                return jsonify({"error": "Company name is required"}), 400

            new_co = Company(
                name=data.get('name'),
                logo_url=data.get('logo_url', ''),
                address=data.get('address', ''),
                phone_number=data.get('phone', ''),
                bank_name=data.get('bank_name', ''),
                account_no=data.get('account_no', ''),
                ifsc_code=data.get('ifsc_code', ''),
                upi_id=data.get('upi_id', '')  # ✨ Now saving UPI
            )
            db.session.add(new_co)
            db.session.commit()
            return jsonify({"message": "Company Registered Successfully", "id": new_co.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Registration failed: {str(e)}"}), 500

    return jsonify({"error": "Method not allowed"}), 405


@app.route('/api/admin/companies/<int:id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_single_company(id):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, get_jwt_identity())
    if not user or user.role.lower() not in ['super_admin', 'developer']:
        return jsonify({"error": "Unauthorized"}), 403

    company = Company.query.get_or_404(id)

    # ✏️ UPDATE CLIENT (PUT)
    if request.method == 'PUT':
     data = request.get_json()
    
    # Python looks for what Flutter sends in _saveChanges
    company.name = data.get('name', company.name)
    company.address = data.get('address', company.address)
    company.phone_number = data.get('phone', company.phone_number)
    company.logo_url = data.get('logo_url', company.logo_url)
    
    # Match these to your Flutter's "bank_name", "account_no", etc.
    company.bank_name = data.get('bank_name', company.bank_name)
    company.account_no = data.get('account_no', company.account_no)
    company.ifsc_code = data.get('ifsc_code', company.ifsc_code)
    company.upi_id = data.get('upi_id', company.upi_id)

    print(f"📥 UPDATING DB: Bank={company.bank_name}, UPI={company.upi_id}")

    db.session.commit()
    return jsonify({"message": "Success"}), 200
    return jsonify({"message": "Updated successfully"}), 200

    # 🗑️ REMOVE CLIENT (DELETE)
    if request.method == 'DELETE':
        db.session.delete(company)
        db.session.commit()
        return jsonify({"message": "Company deleted"}), 200

from datetime import datetime

# 🚀 SIMULATION A: Tap by Student ID (Good for testing specific students)
@app.route('/api/simulate/tap/id/<int:student_id>/<string:bus_no>', methods=['GET'])
def simulate_tap_by_id(student_id, bus_no):
    try:
        student = db.session.get(Student, student_id)
        if not student:
            return jsonify({"error": "Student not found"}), 404
        
        return process_tap(student, bus_no)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🚀 SIMULATION B: Tap by RFID Tag (Mimics the actual hardware)
@app.route('/api/simulate/tap/tag/<string:tag>/<string:bus_no>', methods=['GET'])
def simulate_tap_by_tag(tag, bus_no):
    try:
        student = Student.query.filter_by(rfid_tag=tag).first()
        if not student:
            return jsonify({"error": f"Tag {tag} not assigned"}), 404
        
        return process_tap(student, bus_no)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🧠 INTERNAL HELPER: This avoids repeating the same logic twice
def process_tap(student, bus_no):
    # 1. Update Student Status
    new_status = "Boarded" if student.last_status != "Boarded" else "Dropped"
    student.last_status = new_status
    
    # 2. Assign/Unassign Bus
    student.current_bus = bus_no if new_status == "Boarded" else None
    
    # 3. Log the event
    log = AttendanceLog(
        student_id=student.id,
        bus_number=bus_no,
        status=new_status,
        timestamp=datetime.now()
    )
    
    db.session.add(log)
    db.session.commit()
    
    # 🚀 FUTURE: Trigger Push Notification to Parent here!
    
    return jsonify({
        "message": "Success", 
        "student": student.name, 
        "status": new_status,
        "parent_mobile": student.parent_mobile
    }), 201

@app.route('/api/admin/bus_history/<int:bus_id>', methods=['GET'])
@jwt_required()
def get_bus_history(bus_id):
    # Fetch last 50 points for that bus
    history = BusHistory.query.filter_by(bus_id=bus_id)\
              .order_by(BusHistory.timestamp.desc())\
              .limit(50).all()
    
    points = [{"lat": p.lat, "lng": p.lng} for p in reversed(history)]
    return jsonify(points), 200

# ==========================================
# 🛣️ UPDATED ROUTE HANDLER (Fixes TypeError)
# ==========================================
@app.route('/api/admin/routes', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required()
def handle_routes_master():
    if request.method == 'OPTIONS': return jsonify({'message': 'OK'}), 200

    user = db.session.get(User, int(get_jwt_identity()))
    is_super = user.role.lower() == 'super_admin'
    
    # 🏢 THE MASTER FIX: Determine which company's routes to show
    raw_cid = request.args.get('company_id')
    final_cid = get_safe_id(raw_cid) if is_super else user.company_id

    from sqlalchemy import func

    if request.method == 'GET':
        target_branch_name = request.args.get('branch', '').strip().upper()
        
        # 🛡️ Use final_cid here so Super Admins can see the client's routes
        query = Route.query.filter_by(company_id=final_cid)

        if user.role.lower() == 'branch_incharge':
            query = query.filter_by(branch_id=user.branch_id)
        
        elif target_branch_name and target_branch_name not in ["ALL", "ALL BRANCHES", ""]:
            # Ensure we look for the branch within the correct company
            branch_obj = Branch.query.filter_by(company_id=final_cid).filter(func.upper(Branch.name) == target_branch_name).first()
            if branch_obj:
                query = query.filter(Route.branch_id == branch_obj.id)
            else:
                return jsonify([]), 200

        routes = query.all()
        return jsonify([r.to_dict() for r in routes]), 200

    if request.method == 'POST':
        data = request.json
        branch_name = data.get('branch', '').strip().upper()
        target_branch_id = None

        if user.role.lower() == 'branch_incharge':
            target_branch_id = user.branch_id
        elif branch_name and branch_name not in ["ALL", "ALL BRANCHES", ""]:
            b_obj = Branch.query.filter_by(company_id=final_cid).filter(func.upper(Branch.name) == branch_name).first()
            if b_obj: target_branch_id = b_obj.id

        try:
            new_route = Route(
                route_name=data.get('route_name'),
                shift=data.get('shift'), 
                company_id=final_cid, # 👈 Fix: Save to the correct client
                branch_id=target_branch_id,
                stop_ids=data.get('stop_ids')
            )
            db.session.add(new_route)
            db.session.commit()
            return jsonify(new_route.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# ==========================================
# 🚌 UPDATED BUS TO_DICT (Harmonized Keys)
# ==========================================
# Inside your Bus class...
def to_dict(self):
    return {
        "id": self.id,
        "bus_number": self.bus_no,
        "chassis_no": self.chassis_no or "N/A",
        "seater_capacity": self.seater_capacity or 0,
        "gps_device_id": self.gps_device_id or "N/A",
        "sim_no": self.sim_no or "N/A",
        "rfid_reader_id": self.rfid_reader_id or "N/A", # 👈 Changed from "rfid" to match Flutter
        "branch": self.branch,
        "morning_route_name": self.morning_route.route_name if self.morning_route else "Not Assigned",
        "noon_route_name": self.noon_route.route_name if self.noon_route else "Not Assigned",
        "evening_route_name": self.evening_route.route_name if self.evening_route else "Not Assigned",
        "morning_route_id": self.morning_route_id,
        "noon_route_id": self.noon_route_id,
        "evening_route_id": self.evening_route_id,
        "attender_id": self.attender_id,
        "attender_name": self.attender.username if self.attender else "Not Assigned"
    }

@app.route('/api/admin/routes/<int:id>', methods=['DELETE', 'PUT', 'OPTIONS'])
@jwt_required()
def handle_route_item(id):
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'OK'}), 200

    route = db.session.get(Route, id)
    if not route:
        return jsonify({"error": "Route not found"}), 404

    # 🛡️ SaaS Security: Ensure user only deletes their own company's routes
    user = db.session.get(User, int(get_jwt_identity()))
    if user.role != 'super_admin' and route.company_id != user.company_id:
        return jsonify({"error": "Unauthorized"}), 403

    if request.method == 'DELETE':
        db.session.delete(route)
        db.session.commit()
        return jsonify({"message": "Route deleted successfully"}), 200

    if request.method == 'PUT':
        data = request.json
        route.route_name = data.get('route_name', route.route_name)
        route.shift = data.get('shift', route.shift)
        db.session.commit()
        return jsonify(route.to_dict()), 200

@app.route('/api/debug/promote_admin')
def promote_admin():
    user = User.query.filter_by(username='admin').first()
    if user:
        user.role = 'super_admin'
        db.session.commit()
        return "Admin promoted to super_admin!"
    return "User not found"

def _cors_response():
    response = jsonify({'status': 'ok'})
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    return response

@app.route('/api/admin/debug/clear_test_fleet', methods=['GET'])
def clear_test_fleet():
    # ⚠️ This wipes TEST1 specifically so you can re-upload perfectly
    Bus.query.filter_by(branch='TEST1').delete()
    db.session.commit()
    return "TEST1 Fleet Cleared. Please re-upload your cleaned Excel now."

@app.route('/api/admin/debug/show_all_buses', methods=['GET'])
def debug_show_all_buses():
    # 🕵️ This bypasses all filters to see what is actually in the DB
    buses = Bus.query.all()
    results = []
    for b in buses:
        results.append({
            "id": b.id,
            "bus_no": b.bus_no,
            "branch": f"'{b.branch}'", # Single quotes show hidden spaces
            "company_id": b.company_id,
            "gps_id": b.gps_device_id
        })
    return jsonify(results)

@app.route('/api/admin/route_coordinates', methods=['GET'])
@jwt_required()
def get_route_coordinates():
    try:
        user = db.session.get(User, int(get_jwt_identity()))
        branch_param = request.args.get('branch', '').strip().upper()
        
        # 🚀 THE FIX: We must sort by KM as a NUMBER (Float), not Text.
        # This ensures the line goes: 1.5km -> 2.3km -> 2.4km -> 4.0km
        stops = Stop.query.filter_by(
            company_id=user.company_id, 
            branch=branch_param
        ).order_by(cast(Stop.km, Float).asc()).all()

        coordinates = []
        for s in stops:
            if s.latitude and s.longitude:
                coordinates.append({
                    "lat": float(s.latitude),
                    "lng": float(s.longitude)
                })

        return jsonify(coordinates), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 🏫 FIX: Fetching Students for Fee Assignment
@app.route('/api/admin/students', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_admin_students():
    if request.method == 'OPTIONS': 
        return _cors_response()

    try:
        user_id = get_jwt_identity()
        user = db.session.get(User, user_id)
        
        if not user:
            return jsonify({"error": "User not found"}), 401

        # 🚀 1. Get the branch name from the URL (?branch=testone)
        branch_filter = request.args.get('branch')
        
        query = Student.query
        
        # 🛡️ 2. Apply Security Filters
        if user.role == 'branch_incharge':
            # Branch Incharges can ONLY see their own school's students
            # and we filter by the branch name passed from Flutter
            query = query.filter(
                Student.company_id == user.company_id,
                Student.branch.ilike(branch_filter) if branch_filter else Student.branch != None
            )
        elif user.role == 'admin':
            # School Admins see the whole school
            query = query.filter_by(company_id=user.company_id)
            if branch_filter and branch_filter != "All Branches":
                query = query.filter(Student.branch.ilike(branch_filter))
        
        # Super Admins see everything
        elif user.role in ['super_admin', 'developer']:
            if branch_filter and branch_filter != "All Branches":
                query = query.filter(Student.branch.ilike(branch_filter))

        students = query.all()
        return jsonify([s.to_dict() for s in students]), 200

    except Exception as e:
        # This will now print the REAL error if it happens again
        print(f"❌ SERVER ERROR: {str(e)}")
        return jsonify({"error": "Internal Server Error"}), 500

# 🏢 FIX: Branding Route (Fixes the Net::ERR_FAILED)
@app.route('/api/admin/company_branding', methods=['GET', 'OPTIONS'])
def get_branding():
    # ✨ CRITICAL: Handle the browser's "OPTIONS" handshake
    if request.method == 'OPTIONS':
        return _cors_response()

    # Get company_id from URL or default to 1
    company_id = request.args.get('company_id', 1)
    company = db.session.get(Company, company_id)
    
    if not company:
        return jsonify({"company_name": "FleetTrack Pro", "upi_id": "", "bank_details": {}}), 200
        
    return jsonify(company.to_dict()), 200

@app.route('/api/version', methods=['GET'])
def get_version():
    return jsonify({
        "status": "online",
        "version": "1.0.0",
        "message": "FleetTrackPro Backend is Live"
    }), 200

@app.route('/api/debug/check_stops')
def debug_stops():
    stops = BusStop.query.all()
    return jsonify([{"name": s.stop_name, "branch_in_db": f"'{s.branch}'"} for s in stops])

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "backend": "Python/Flask",
        "database": "SQLite (Local)",
        "cloud": "Firebase Connected" if firebase_key else "Firebase Missing",
        "cors": "enabled"
    }), 200

# ==========================================
# 🚀 LIVE BUS SIMULATION (Add this at the bottom)
# ==========================================
def auto_move_bus():
    # We use app_context so the thread can talk to the database
    with app.app_context():
     try:
        db.create_all()
        # 🕵️ Make Mansoor a GLOBAL SUPER ADMIN (No company_id)
        if not User.query.filter_by(username='admin_mansoor').first():
            new_admin = User(
                username='admin_mansoor',
                password_hash=generate_password_hash('admin123'),
                role='super_admin',
                company_id=None  # 🚀 THIS RESTORES THE "ADD CLIENT" BUTTON
            )
            db.session.add(new_admin)
            db.session.commit()
            print("🚀 SEED SUCCESS: Global Super Admin Created")
     except Exception as e:
        print(f"❌ STARTUP ERROR: {e}")

# Create this helper at the top of app.py
def get_safe_id(val):
    if val is None or str(val).lower() in ['null', 'none', '']:
        return None
    try:
        return int(val)
    except:
        return None

# ==========================================
# 🚀 STARTUP, TABLE CREATION & ADMIN SEEDING
# ==========================================
with app.app_context():
    try:
        db.create_all()
        
        # 🕵️ Check if admin exists
        admin = User.query.filter_by(username='admin_mansoor').first()
        
        if admin:
            # If he exists but has a company, fix him so the buttons return
            admin.company_id = None 
            admin.role = 'super_admin'
        else:
            # If he doesn't exist, create him as a Global Developer
            admin = User(
                username='admin_mansoor',
                password_hash=generate_password_hash('admin123'),
                role='super_admin',
                company_id=None # 🚀 THIS BRINGS THE BUTTON BACK
            )
            db.session.add(admin)
            
        db.session.commit()
        print("✅ GLOBAL ADMIN READY: 'Add Client' button restored.")
    except Exception as e:
        print(f"❌ STARTUP ERROR: {e}")

if __name__ == "__main__":
    # Render provides the "PORT" environment variable. 
    # If it's not there (like on your laptop), we default to 5000.
    port = int(os.environ.get("PORT", 5000))
    
    # Use debug=True only for local testing
    app.run(host='0.0.0.0', port=port, debug=True)