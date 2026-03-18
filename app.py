from flask import Flask, jsonify, request, send_file
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
import threading


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

# ==========================================
# 🚀 RENDER-SPECIFIC DATABASE CONFIG
# ==========================================
basedir = os.path.abspath(os.path.dirname(__file__))
db_name = "v4_transport.db" 
db_path = os.path.join(basedir, db_name)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + db_path.lstrip('/')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'super-secret-key-12345'
app.config["JWT_SECRET_KEY"] = "school-transport-999-secure-key"

# ✅ REMOVED THE REDUNDANT 'db = SQLAlchemy(app)' HERE

# ==========================================
# 🚀 2. INITIALIZE PLUGINS (ONLY ONCE!)
# ==========================================
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

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
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    branch_id = db.Column(db.String(50))
    contact_number = db.Column(db.String(20)) 
    license_info = db.Column(db.String(50))

    def to_dict(self):
      return {
        "id": self.id,
        "username": self.username,
        "role": self.role.upper(),
        # 🛡️ Ensure it looks for the branch name if company name is generic
        "company_name": self.company.name if self.company else "Unknown School",
        "branch_id": self.branch_id, # 🚀 Add this to help Flutter
        "contact_number": self.contact_number,
        "company_id": self.company_id
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
    upi_id = db.Column(db.String(100)) # ✅ Add this: e.g., "school@upi"
    users = db.relationship('User', backref='company', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "company_name": self.name,
            "upi_id": self.upi_id, # ✅ Ensure this is sent to Flutter
            "company_logo": self.logo_url,
            "address": self.address,
            "phone": self.phone_number,
            "bank_details": {
                "bank": self.bank_name,
                "account": self.account_no,
                "ifsc": self.ifsc_code
            }
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
            "id": self.id, "name": self.name, "location": self.location,
            "latitude": self.latitude, "longitude": self.longitude
        }

class Bus(db.Model):
    __tablename__ = 'buses'
    id = db.Column(db.Integer, primary_key=True)
    bus_no = db.Column(db.String(50), nullable=False) 
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    chassis_no = db.Column(db.String(50))
    seater_capacity = db.Column(db.Integer)
    gps_device_id = db.Column(db.String(50))
    sim_no = db.Column(db.String(20)) # 👈 Ensure this matches your bulk upload
    rfid_reader_id = db.Column(db.String(50)) # 👈 Ensure this matches your bulk upload
    branch = db.Column(db.String(50))
    status = db.Column(db.String(20), default='stopped') 
    last_lat = db.Column(db.Float)
    last_lng = db.Column(db.Float)
    speed = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "id": self.id,
            "bus_number": self.bus_no,
            "chassis_no": self.chassis_no,
            "seater_capacity": self.seater_capacity,
            "gps_device_id": self.gps_device_id,
            "sim_no": self.sim_no,
            "rfid_reader_id": self.rfid_reader_id,
            "branch": self.branch,
            "status": self.status,
            "last_lat": self.last_lat,
            "last_lng": self.last_lng,
            "speed": self.speed
        }

class BusStop(db.Model):
    __tablename__ = 'stops'
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    stop_name = db.Column(db.String(100), nullable=False)
    zone = db.Column(db.String(100), default="General") 
    km = db.Column(db.Float, nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    branch = db.Column(db.String(50))
    # 🔗 ADD THIS: Link to FeeZone for auto-calculation
    fee_zone_id = db.Column(db.Integer, db.ForeignKey('fee_zones.id'), nullable=True)

    def to_dict(self):
        return {
            'id': self.id, 'stop_name': self.stop_name, 'zone': self.zone,
            'km': self.km, 'latitude': self.latitude, 'longitude': self.longitude, 'branch': self.branch
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

    def to_dict(self):
        return {
            "id": self.id,
            "student_name": self.name,
            "admission_no": self.admission_no,
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

    # 🔗 This link allows us to get the name without a separate column
    student = db.relationship('Student', backref='logs')

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.name if self.student else "Unknown", # ✅ Gets name from relationship
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

# ==========================================
# 🔐 AUTH & USER MGMT
# ==========================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data.get('username')).first()
    if user and check_password_hash(user.password_hash, data.get('password')):
        # 🔍 Fetch the actual Branch name
        branch_name = "testone" # Default
        if user.branch_id:
            branch_obj = db.session.get(Branch, user.branch_id)
            if branch_obj:
                branch_name = branch_obj.name
        
        company = db.session.get(Company, user.company_id)
        
        return jsonify({
            "access_token": create_access_token(identity=str(user.id)),
            "role": user.role,
            "branch": branch_name,  # ✅ Now sends "testone" instead of "1"
            "company_name": company.name if company else "testschool"
        }), 200

    # 🚀 ADD THIS LINE HERE to prevent the 500 crash
    return jsonify({"error": "Invalid username or password"}), 401

@app.route('/api/admin/users', methods=['GET', 'POST', 'PUT', 'OPTIONS'])
@jwt_required()
def handle_admin_users():
    if request.method == 'OPTIONS':
        return _cors_response()

    # 🚨 TEMPORARY BYPASS: We skip ALL security checks
    print("🔓 SECURITY BYPASS ACTIVE") 

    if request.method == 'POST':
        try:
            data = request.json
            # Create the user without checking who is asking
            new_user = User(
                username=data.get('username'),
                password_hash=generate_password_hash(data.get('password', '1234')),
                role='super_admin',
                company_id=1, 
                branch_id=data.get('branch_id')
            )
            db.session.add(new_user)
            db.session.commit()
            return jsonify({"message": "User created successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    return jsonify({"message": "Bypass active, use POST to create admin"}), 200

# Helper to get only drivers
@app.route('/api/admin/drivers', methods=['GET'])
@jwt_required() # 🛡️ Add security
def get_drivers():
    user = db.session.get(User, get_jwt_identity())
    
    # 🚀 Filter by company_id so schools don't see each other's drivers
    if user.role == 'super_admin':
        drivers = User.query.filter_by(role='driver').all()
    else:
        drivers = User.query.filter_by(role='driver', company_id=user.company_id).all()
    
    return jsonify([{
        'id': d.id, 
        'username': d.username, 
        'contact_number': d.contact_number, 
        'license_info': d.license_info,
        'branch_id': d.branch_id 
    } for d in drivers]), 200

@app.route('/api/admin/students', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True) # 🚀 Allow preflight handshake
def admin_get_students():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Missing or invalid token"}), 401

    user = db.session.get(User, int(get_jwt_identity()))
    branch_param = request.args.get('branch')

    # 🔒 Multi-tenant security
    query = Student.query.filter_by(company_id=user.company_id)

    # 🛡️ Admin vs Incharge Logic
    user_role = str(user.role).lower().strip()
    if user_role in ['super_admin', 'admin']:
        if branch_param and branch_param not in ["All Branches", "Global", "TEST SCHOOL"]:
            query = query.filter_by(branch=branch_param.upper())
    else:
        # Branch Incharge Logic
        BranchModel = globals().get('Branch')
        if BranchModel:
            b_obj = db.session.get(BranchModel, user.branch_id)
            if b_obj:
                query = query.filter_by(branch=b_obj.name.upper())

    students = query.all()
    return jsonify([s.to_dict() for s in students]), 200

@app.route('/api/admin/students/<int:id>', methods=['PUT', 'DELETE', 'POST', 'OPTIONS'])
def update_delete_student(id):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'OK'}), 200

    student = Student.query.get(id)
    if not student: 
        return jsonify({'error': 'Student not found'}), 404

    if request.method == 'DELETE':
        db.session.delete(student)
        db.session.commit()
        return jsonify({'message': 'Student deleted'}), 200

    # ✏️ UPDATE LOGIC (Matches your Flutter "Edit Student" screen)
    data = request.json
    try:
        # Standard Info
        if 'student_name' in data: student.name = data['student_name']
        if 'grade' in data: student.grade = data['grade']
        if 'parent_mobile' in data: student.parent_mobile = data['parent_mobile']
        
        # ✅ KEY OPERATIONAL FIELDS (Fixes the "null" and "not assigned" issues)
        if 'rfid_tag' in data: student.rfid_tag = data['rfid_tag']
        if 'bus_id' in data: student.bus_id = data['bus_id']
        
        # ✅ FINANCIAL FIELDS (Saves the ₹27500 value permanently)
        if 'calculated_fee' in data: 
            student.total_fee = float(data['calculated_fee'])
        
        # Stop Assignment
        if 'pickup_stop_id' in data: student.pickup_stop_id = data['pickup_stop_id']
        if 'drop_stop_id' in data: student.drop_stop_id = data['drop_stop_id']

        db.session.commit()
        print(f"✅ UPDATED STUDENT: {student.name} | Bus: {student.bus_id} | Fee: {student.total_fee}")
        return jsonify({'message': 'Student updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"❌ UPDATE ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ==========================================
# 🎓 STUDENTS ROUTE (Unified & Branch-Aware)
# ==========================================
@app.route('/api/students', methods=['GET', 'POST', 'OPTIONS'])
def handle_students():
    # 🚀 1. Handle Handshake
    if request.method == 'OPTIONS': 
        return _cors_response()

    # 🚀 2. Manual Token Verification (More stable than the decorator)
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    try:
        verify_jwt_in_request()
    except Exception as e:
        return jsonify({"error": "Token invalid or missing"}), 401

    # 🚀 3. Identity Check
    user_id = get_jwt_identity()
    user = db.session.get(User, int(user_id))
    
    if not user:
        return jsonify({"error": "User not found"}), 401

    if request.method == 'GET':
        query = Student.query.filter_by(company_id=user.company_id)
        branch = request.args.get('branch')
        if branch: query = query.filter_by(branch=branch.upper())
        return jsonify([s.to_dict() for s in query.all()]), 200

    if request.method == 'POST':
        try:
            data = request.json
            new_student = Student(
                name=data.get('student_name'),
                admission_no=data.get('admission_no'),
                company_id=user.company_id,
                branch=data.get('branch', 'PSBN').upper(),
                grade=data.get('grade'),
                parent_mobile=data.get('parent_mobile'),
                bus_id=data.get('bus_id'),
                pickup_stop_id=data.get('pickup_stop_id'),
                drop_stop_id=data.get('drop_stop_id'),
                total_fee=float(data.get('total_fee', 0)),
                rfid_tag=data.get('rfid_tag'),
                payment_status=data.get('payment_status', 'Pending')
            )
            db.session.add(new_student)
            db.session.commit()
            return jsonify(new_student.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# 🔍 UNIFIED SINGLE STUDENT HANDLER (Handles GET, PUT, DELETE)
@app.route('/api/students/<int:id>', methods=['GET', 'PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_single_student(id):
    # 🚀 1. Always handle CORS handshake first
    if request.method == 'OPTIONS': 
        return _cors_response()
    
    # 🚀 2. Identify the logged-in Admin
    user = db.session.get(User, get_jwt_identity())
    
    # 🚀 3. Security Guard: Find student ONLY within the Admin's school
    # This single query handles both existence and security
    student = Student.query.filter_by(id=id, company_id=user.company_id).first()

    # Special case for Fleet View (Dummy ID 0)
    if id == 0:
        return jsonify({'id': 0, 'student_name': 'Fleet View', 'stop_lat': None, 'stop_lng': None}), 200

    if not student: 
        return jsonify({'error': 'Access Denied or Student not found'}), 404

    # 📂 1️⃣ GET: Fetch details
    if request.method == 'GET':
        return jsonify(student.to_dict()), 200

    # 📝 2️⃣ PUT: Secure Update
    if request.method == 'PUT':
        try:
            data = request.json
            student.name = data.get('student_name', student.name)
            student.admission_no = data.get('admission_no', student.admission_no)
            student.grade = data.get('grade', student.grade)
            student.parent_mobile = data.get('parent_mobile', student.parent_mobile)
            student.rfid_tag = data.get('rfid_tag', student.rfid_tag)
            student.branch = data.get('branch', student.branch).strip().upper()
            student.pickup_stop_id = data.get('pickup_stop_id', student.pickup_stop_id)
            student.bus_id = data.get('bus_id', student.bus_id)
            student.total_fee = float(data.get('total_fee', student.total_fee))
            student.payment_status = data.get('payment_status', student.payment_status)

            db.session.commit()
            return jsonify(student.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    # 🗑️ 3️⃣ DELETE: Remove Student
    if request.method == 'DELETE':
        db.session.delete(student)
        db.session.commit()
        return jsonify({'message': 'Deleted successfully'}), 200

@app.route('/api/admin/buses', methods=['GET', 'POST', 'OPTIONS'])
def handle_admin_buses():
    if request.method == 'OPTIONS': 
        return _cors_response()

    from flask_jwt_extended import verify_jwt_in_request
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Unauthorized"}), 401
        
    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    if not user:
        return jsonify({"error": "User not found"}), 404

    # 🔍 1. GET: Fetching the list for your screen
    if request.method == 'GET':
        try:
            # 🧼 Aggressively clean the branch name coming from Flutter
            target_branch = request.args.get('branch', '').strip()
            
            # 🏢 Filter by company first
            query = Bus.query.filter_by(company_id=user.company_id)
            
            if target_branch:
                # ✅ Use ilike with % to handle any hidden space issues
                query = query.filter(Bus.branch.ilike(f"%{target_branch}%"))
                
            buses = query.all()
            print(f"📡 FINAL CHECK: Found {len(buses)} buses for '{target_branch}'")
            return jsonify([b.to_dict() for b in buses]), 200
        except Exception as e:
            print(f"❌ GET ERROR: {str(e)}")
            return jsonify({"error": str(e)}), 500

    # ➕ 2. POST: Adding a single bus manually (Fixed logic)
    if request.method == 'POST':
        try:
            data = request.json
            new_bus = Bus(
                bus_no=data.get('bus_number'), 
                company_id=user.company_id, # 🚀 REQUIRED: Link to school
                chassis_no=data.get('chassis_no'),
                seater_capacity=data.get('seater_capacity', 30),
                gps_device_id=data.get('gps_device_id'),
                sim_no=data.get('sim_no'),             
                rfid_reader_id=data.get('rfid_reader_id'), 
                branch=data.get('branch', 'TEST1').upper().strip(),
                status='stopped'
            )
            db.session.add(new_bus)
            db.session.commit()
            print(f"✅ MANUAL ADD: Bus {new_bus.bus_no} saved successfully.")
            return jsonify(new_bus.to_dict()), 201
        except Exception as e:
            db.session.rollback()
            print(f"❌ POST ERROR: {str(e)}")
            return jsonify({"error": str(e)}), 500

@app.route('/api/admin/buses/<int:bus_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
@jwt_required()
def handle_single_bus(bus_id):
    if request.method == 'OPTIONS':
        return _cors_response()

    current_user_id = get_jwt_identity()
    user = db.session.get(User, int(current_user_id))
    bus = Bus.query.filter_by(id=bus_id, company_id=user.company_id).first()
    
    if not bus:
        return jsonify({"error": "Bus not found"}), 404

    if request.method == 'PUT':
        try:
            data = request.json
            # ✅ Indented correctly to save all data
            bus.bus_no = data.get('bus_number', bus.bus_no)
            bus.chassis_no = data.get('chassis_no', bus.chassis_no)
            bus.seater_capacity = data.get('seater_capacity', bus.seater_capacity)
            bus.gps_device_id = data.get('gps_device_id', bus.gps_device_id)
            bus.sim_no = data.get('sim_no', bus.sim_no)
            bus.rfid_reader_id = data.get('rfid_reader_id', bus.rfid_reader_id)
            bus.branch = data.get('branch', bus.branch).strip().upper()
            
            db.session.commit()
            return jsonify(bus.to_dict()), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    if request.method == 'DELETE':
        try:
            db.session.delete(bus)
            db.session.commit()
            return jsonify({"message": "Bus deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/api/admin/bulk_delete/buses', methods=['DELETE'])
@jwt_required()
def bulk_delete_buses():
    try:
        branch = request.args.get('branch', 'TEST1').upper()
        # ⚠️ This deletes ALL buses for the specified branch
        deleted_count = Bus.query.filter_by(branch=branch).delete()
        db.session.commit()
        return jsonify({"message": f"Successfully deleted {deleted_count} buses from {branch}"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500            
        
# 📂 SMART BULK UPLOAD (Fixed Field Names)
@app.route('/api/admin/upload/bulk', methods=['POST'])
@jwt_required()
def smart_bulk_upload():
    user = db.session.get(User, int(get_jwt_identity()))
    file = request.files.get('file')
    raw_cat = (request.form.get('category') or '').lower().strip()
    form_branch = request.form.get('branch', '').strip().upper() # ✅ FORCE UPPERCASE
    
    if not file:
        return jsonify({"error": "No file provided"}), 400

    try:
        # Load file safely
        df = pd.read_excel(file, dtype=str) if file.filename.endswith('.xlsx') else pd.read_csv(file, dtype=str)
        df.columns = df.columns.str.strip() 
        count = 0

        # 📍 1. BUS STOPS
        if "stop" in raw_cat:
            # ✅ Standardize form_branch right at the start
            form_branch = form_branch.strip().upper()
            print(f"📍 PROCESSING: Stop Upload for standardized Branch: {form_branch}")

            for _, row in df.iterrows():
                stop_name = str(row.get('Stop Name') or row.get('stop_name') or '').strip()
                if not stop_name or stop_name.lower() in ['nan', '']: continue

                z_name = str(row.get('Zone', 'General')).strip()
                
                # 🔍 Fetch Zone Object - Using ilike to be safe with casing
                zone_obj = FeeZone.query.filter(
                    FeeZone.zone_name.ilike(z_name), 
                    FeeZone.branch == form_branch
                ).first()

                # Handle distance and coordinates
                try:
                    km = float(row.get('Distance (KM)') or row.get('KM') or row.get('km') or 0.0)
                    lat = float(row.get('Latitude') or row.get('latitude') or 0.0)
                    lng = float(row.get('Longitude') or row.get('longitude') or 0.0)
                except (ValueError, TypeError):
                    km, lat, lng = 0.0, 0.0, 0.0

                # 🔍 Check if stop exists for this specific branch and company
                stop = BusStop.query.filter_by(
                    stop_name=stop_name, 
                    branch=form_branch, 
                    company_id=user.company_id
                ).first()
                
                if stop:
                    stop.zone = z_name
                    stop.fee_zone_id = zone_obj.id if zone_obj else None
                    stop.km = km  
                    stop.latitude, stop.longitude = lat, lng
                    print(f"🔄 Updated Stop: {stop_name}")
                else:
                    db.session.add(BusStop(
                        stop_name=stop_name, 
                        zone=z_name,
                        branch=form_branch, 
                        company_id=user.company_id,
                        fee_zone_id=zone_obj.id if zone_obj else None,
                        km=km, 
                        latitude=lat, 
                        longitude=lng
                    ))
                    print(f"✨ Created Stop: {stop_name}")
                
                count += 1

        # 🎓 2. STUDENTS
        elif "student" in raw_cat:
            print(f"🎓 DETECTED: Student Upload for {form_branch}")
            for _, row in df.iterrows():
                name = str(row.get('Student Name') or row.get('name') or '').strip()
                adm_no = str(row.get('Admission No') or row.get('admission_no') or '').strip()
                if not adm_no or not name or name.lower() == 'nan': continue

                # 🚀 GET GRADE AND DIV FROM EXCEL
                # We use .get() to look for 'Div' specifically as per your file
                grade = str(row.get('Grade') or '').strip()
                division = str(row.get('Div') or row.get('Division') or '').strip()

                # 🚀 GET ZONE AND STOP NAMES FROM EXCEL
                excel_zone = str(row.get('Zone') or '').strip()
                p_stop_name = str(row.get('Pickup Stop') or '').strip()
                d_stop_name = str(row.get('Drop Stop') or '').strip()
                bus_no = str(row.get('Assigned Bus') or '').strip()

                # 🔍 Lookup foreign keys
                p_stop_obj = BusStop.query.filter_by(
                    stop_name=p_stop_name, 
                    zone=excel_zone, 
                    branch=form_branch, 
                    company_id=user.company_id
                ).first()

                d_stop_obj = BusStop.query.filter_by(
                    stop_name=d_stop_name, 
                    branch=form_branch, 
                    company_id=user.company_id
                ).first() if d_stop_name != p_stop_name else p_stop_obj

                bus_obj = Bus.query.filter_by(
                    bus_no=bus_no, 
                    branch=form_branch, 
                    company_id=user.company_id
                ).first()

                student = Student.query.filter_by(admission_no=adm_no, company_id=user.company_id).first()
                
                if student:
                    student.name, student.branch = name, form_branch
                    student.grade = grade # ✅ UPDATED
                    student.division = division # ✅ NEW FIELD
                    student.parent_mobile = str(row.get('Parent Mobile', student.parent_mobile))
                    student.rfid_tag = str(row.get('RFID Tag', student.rfid_tag))
                    student.pickup_stop_id = p_stop_obj.id if p_stop_obj else student.pickup_stop_id
                    student.drop_stop_id = d_stop_obj.id if d_stop_obj else student.drop_stop_id
                    student.bus_id = bus_obj.id if bus_obj else student.bus_id
                    student.total_fee = float(row.get('Fee') or student.total_fee or 0.0)
                    student.payment_status = str(row.get('Payment Status', student.payment_status or 'Pending'))
                else:
                    db.session.add(Student(
                        name=name, admission_no=adm_no, branch=form_branch,
                        company_id=user.company_id, 
                        grade=grade, # ✅ UPDATED
                        division=division, # ✅ NEW FIELD
                        parent_mobile=str(row.get('Parent Mobile', '')),
                        rfid_tag=str(row.get('RFID Tag', '')),
                        pickup_stop_id=p_stop_obj.id if p_stop_obj else None,
                        drop_stop_id=d_stop_obj.id if d_stop_obj else None,
                        bus_id=bus_obj.id if bus_obj else None,
                        total_fee=float(row.get('Fee') or 0.0),
                        payment_status=str(row.get('Payment Status') or 'Pending')
                    ))
                count += 1

        # 🚌 3. BUS FLEET bulk upload
        elif "bus" in raw_cat:
            form_branch = form_branch.strip().upper() # ✅ Keep it standardized
            print(f"🚌 DETECTED: Bus Fleet Upload for {form_branch}")
            
            # 🏫 Fetch school coordinates once to use as a starting point for all buses
            branch_obj = Branch.query.filter_by(name=form_branch, company_id=user.company_id).first()
            default_lat = branch_obj.latitude if (branch_obj and branch_obj.latitude) else 13.1065
            default_lng = branch_obj.longitude if (branch_obj and branch_obj.longitude) else 77.5779

            for _, row in df.iterrows():
                bus_num = str(row.get('Bus Number') or row.get('bus_no') or '').strip()
                if not bus_num or bus_num.lower() == 'nan': continue

                # Find existing bus by Number + Company
                bus = Bus.query.filter_by(bus_no=bus_num, company_id=user.company_id).first()
                
                gps_id = str(row.get('GPS Device ID', '')).strip().replace('.0', '')
                rfid_reader = str(row.get('RFID Reader ID', '')).strip()
                sim_no = str(row.get('SIM No', '')).strip()

                if bus:
                    bus.chassis_no = str(row.get('Chassis Number') or bus.chassis_no)
                    bus.branch = form_branch
                    bus.gps_device_id = gps_id if gps_id else bus.gps_device_id
                    bus.rfid_reader_id = rfid_reader if rfid_reader else bus.rfid_reader_id
                    bus.sim_no = sim_no if sim_no else bus.sim_no
                    
                    # ✅ If bus exists but has no coordinates, give it the school location
                    if not bus.last_lat or bus.last_lat == 0:
                        bus.last_lat, bus.last_lng = default_lat, default_lng
                else:
                    db.session.add(Bus(
                        bus_no=bus_num, 
                        gps_device_id=gps_id,
                        rfid_reader_id=rfid_reader,
                        sim_no=sim_no,
                        branch=form_branch, 
                        company_id=user.company_id,
                        seater_capacity=int(row.get('Seater Capacity', 30)), 
                        status='stopped',
                        # ✅ New buses start at the school coordinates
                        last_lat=default_lat,
                        last_lng=default_lng
                    ))
                count += 1

        db.session.commit() # This actually saves the changes to the database
        
        print(f"✅ BULK SUCCESS: Processed {count} records for {form_branch}")
        
        return jsonify({
            "message": f"Successfully uploaded {count} {raw_cat} records",
            "branch": form_branch,
            "count": count
        }), 201 # 201 means "Created"

    except Exception as e:
        db.session.rollback() # If any error happens, undo everything to prevent partial data
        print(f"❌ BULK ERROR: {str(e)}")
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
# 📍 BUS STOP & FEE LOGIC (Final GPS Enabled)
# ==========================================
@app.route('/api/stops', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required() # 🛡️ Ensure only logged-in users can access this
def handle_stops_unified():
    if request.method == 'OPTIONS': 
        return _cors_response()

    # Get the current logged-in user's company info
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)

    if request.method == 'GET':
        try:
            branch = request.args.get('branch', '').strip().upper()
            
            # 🛡️ Filter by BOTH Branch name AND Company ID
            query = BusStop.query.filter_by(company_id=user.company_id)
            
            if branch and branch != "ALL":
                stops = query.filter(BusStop.branch == branch).all()
            else:
                stops = query.all()
            
            print(f"📍 FETCH: {len(stops)} stops for {user.company.name} - Branch: {branch}")
            return jsonify([s.to_dict() for s in stops]), 200
        except Exception as e:
            return jsonify([]), 200

    if request.method == 'POST':
        try:
            data = request.json
            new_stop = BusStop(
                stop_name=data.get('stop_name'),
                zone=data.get('zone', 'General'), 
                km=float(data.get('km', 0)),
                latitude=float(data.get('latitude', 0)),
                longitude=float(data.get('longitude', 0)),
                branch=data.get('branch', 'PSBN').strip().upper(),
                # ✅ Essential for SaaS: Link this stop to the current user's school
                company_id=user.company_id 
            )
            db.session.add(new_stop)
            db.session.commit()
            return jsonify({"message": "Stop saved successfully"}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

# ==========================================
# 🔄 UPDATE & 🗑️ DELETE STOP LOGIC
# ==========================================
@app.route('/api/stops/<int:stop_id>', methods=['PUT', 'DELETE', 'OPTIONS'])
def handle_single_stop(stop_id):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200
        
    stop = db.session.get(BusStop, stop_id)
    if not stop:
        return jsonify({"error": "Stop not found"}), 404

    # --- HANDLE UPDATE (PUT) ---
    if request.method == 'PUT':
        try:
            data = request.json
            stop.stop_name = data.get('stop_name', stop.stop_name)
            stop.zone = data.get('zone', stop.zone)
            stop.km = float(data.get('km', stop.km))
            stop.latitude = float(data.get('latitude', stop.latitude))
            stop.longitude = float(data.get('longitude', stop.longitude))
            stop.branch = data.get('branch', stop.branch)
            
            db.session.commit()
            return jsonify({"message": "Stop updated successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

    # --- HANDLE DELETE (DELETE) ---
    if request.method == 'DELETE':
        try:
            db.session.delete(stop)
            db.session.commit()
            return jsonify({"message": "Stop deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/api/calculate_fee', methods=['POST', 'OPTIONS'])
def calculate_fee():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200
    try:
        data = request.json
        stop_id = data.get('stop_id')
        branch = data.get('branch', 'PSBN').strip()
        
        # 1. Fetch the stop
        stop = db.session.get(BusStop, stop_id)
        if not stop:
            return jsonify({'price': 0}), 200
            
        # 2. Smart Conversion for distance
        raw_km = getattr(stop, 'km', 0)
        try:
            if isinstance(raw_km, str):
                dist = float(raw_km.upper().replace('KM', '').strip())
            else:
                dist = float(raw_km or 0)
        except:
            dist = 0.0

        # ✅ FIXED: Changed PricingSlab to FeeZone
        # Also ensure we match based on the zone_name if needed, 
        # but here we use the distance logic you established.
        zone = FeeZone.query.filter(
            FeeZone.branch.ilike(branch), 
            FeeZone.min_km <= dist,
            FeeZone.max_km >= dist
        ).first()
        
        # 3. Ensure price is not null for Flutter safety
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
        # We fetch all buses that have a GPS ID assigned
        buses = Bus.query.filter(Bus.gps_device_id != None).all()
        
        results = []
        for bus in buses:
            results.append({
                "bus_number": bus.bus_number,
                "lat": bus.last_lat or 13.1187, # Default to school if no GPS signal yet
                "lng": bus.last_lng or 77.5752,
                "status": bus.status or "stopped",
                "speed": getattr(bus, 'speed', 0),
                "device_id": bus.gps_device_id
            })
            
        return jsonify(results), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📊 SMART DASHBOARD STATS (Fixed to prevent Crash)
@app.route('/api/admin/stats', methods=['GET', 'OPTIONS'])
@jwt_required(optional=True)
def get_stats():
    if request.method == 'OPTIONS': return jsonify({'ok': True}), 200
    
    try:
        from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
        from sqlalchemy import func
        verify_jwt_in_request()
        user = db.session.get(User, int(get_jwt_identity()))
        cid = user.company_id
        
        # 1. Get the branch from the request
        branch_param = request.args.get('branch', '').strip().upper()

        # 2. Start with a base query for the whole company
        bus_query = Bus.query.filter_by(company_id=cid)
        
        # 3. Apply branch filter ONLY if a specific branch is selected
        if branch_param and branch_param not in ["ALL BRANCHES", "GLOBAL", user.company.name.upper()]:
            bus_query = bus_query.filter(Bus.branch == branch_param)

        # 🚀 THE FIX: Move these counts OUTSIDE the "if" block 
        # This ensures they run even for "All Branches"
        moving = bus_query.filter(func.lower(Bus.status) == 'moving').count()
        stopped = bus_query.filter(func.lower(Bus.status) == 'stopped').count()
        idle = bus_query.filter(func.lower(Bus.status) == 'idle').count()
        total = bus_query.count()

        return jsonify({
            "moving": moving,
            "stopped": stopped,
            "idle": idle,
            "total": total,
            "students": Student.query.filter_by(company_id=cid).count()
        }), 200

    except Exception as e:
        print(f"❌ STATS ERROR: {e}")
        return jsonify({"error": str(e)}), 500
    
# 🗺️ 2. FIX THE MAP (Previously 500-ing)
@app.route('/api/admin/fleet_locations', methods=['GET', 'OPTIONS'])
@jwt_required()
def get_fleet_locations():
    if request.method == 'OPTIONS': 
        return jsonify({'ok': True}), 200

    try:
        # 1. Get User and Identity
        user = db.session.get(User, int(get_jwt_identity()))
        markers = []

        # 2. Handle Branch Filtering
        branch_param = request.args.get('branch', '').strip().upper()
        
        # 🏢 Start with a base query for the school icons
        branches_query = Branch.query.filter_by(company_id=user.company_id)
        
        # 🚌 Start with a base query for the buses
        bus_query = Bus.query.filter_by(company_id=user.company_id)

        # 🛡️ Apply filters ONLY if a specific branch is selected
        if branch_param and branch_param not in ["ALL BRANCHES", "GLOBAL", user.company.name.upper()]:
            bus_query = bus_query.filter(Bus.branch == branch_param)
            branches_query = branches_query.filter(Branch.name == branch_param)

        # 3. Process Schools (Branches)
        branches = branches_query.all()
        for b in branches:
            if b.latitude and b.longitude:
                markers.append({
                    "id": f"branch_{b.id}",
                    "type": "school",
                    "name": b.name,
                    "lat": float(b.latitude),
                    "lng": float(b.longitude)
                })

        # 4. Process Buses
        buses = bus_query.all()  # ✅ Now respects the filter!
        for bus in buses:
            # 🛰️ Coordinate Logic
            lat = getattr(bus, 'last_latitude', None) or getattr(bus, 'last_lat', None) or getattr(bus, 'latitude', None)
            lng = getattr(bus, 'last_longitude', None) or getattr(bus, 'last_lng', None) or getattr(bus, 'longitude', None)
            
            # 🏷️ Name Logic (The fix for "Unknown Bus")
            bus_name = getattr(bus, 'bus_number', None) or \
                       getattr(bus, 'registration_no', None) or \
                       getattr(bus, 'reg_no', None) or \
                       getattr(bus, 'bus_no', None) or \
                       getattr(bus, 'registration_number', None) or "Unnamed"

            if lat and lng and float(lat) != 0.0:
                markers.append({
                    "id": f"bus_{bus.id}",
                    "type": "bus",
                    "name": bus_name,
                    "lat": float(lat),
                    "lng": float(lng),
                    "status": getattr(bus, 'status', 'Stopped')
                })
            else:
                print(f"⚠️ SKIPPING BUS {bus_name}: No coordinates found.")

        print(f"📡 API SUCCESS: Sending {len(markers)} markers for branch: {branch_param or 'ALL'}")
        return jsonify(markers), 200

    except Exception as e:
        print(f"❌ MAP API ERROR: {e}")
        return jsonify({"error": str(e)}), 500

# ==========================================
#  🚖 DRIVER MANAGEMENT
# ==========================================
@app.route('/api/admin/drivers', methods=['GET', 'POST'])
@jwt_required()
def handle_drivers():
    user = db.session.get(User, get_jwt_identity())
    
    # 📂 FETCH DRIVERS (GET)
    if request.method == 'GET':
        # 🚀 THE FIX: Only fetch drivers for THIS school
        drivers = User.query.filter_by(role='driver', company_id=user.company_id).all()
        return jsonify([{
            'id': d.id, 
            'name': d.username, 
            'phone': d.contact_number, 
            'license': d.license_info
        } for d in drivers]), 200

    # 📝 ADD DRIVER (POST)
    try:
        data = request.json
        if User.query.filter_by(username=data.get('name')).first():
             return jsonify({'error': 'Driver username already exists'}), 400

        new_driver = User(
            username=data.get('name'),
            role='driver',
            company_id=user.company_id, # 🚀 Tag with school
            password_hash=generate_password_hash('1234'),
            contact_number=data.get('phone'),
            license_info=data.get('license')
        )
        db.session.add(new_driver)
        db.session.commit()
        return jsonify({'message': 'Driver added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/download/<string:data_type>', methods=['GET'])
def unified_download_excel(data_type):
    # 🔓 1. ULTRA-FLEXIBLE TOKEN SEARCH
    token = request.args.get('token') or request.args.get('access_token')
    
    if not token:
        auth_header = request.headers.get('Authorization')
        if auth_header and "Bearer " in auth_header:
            token = auth_header.split(" ")[1]

    if not token:
        print("❌ DOWNLOAD ATTEMPT FAILED: No token found in URL or Header")
        return jsonify({"msg": "Missing Authorization Token"}), 401
    
    from flask_jwt_extended import decode_token
    try:
        decoded = decode_token(token)
        user = db.session.get(User, int(decoded['sub']))
    except Exception:
        return jsonify({"msg": "Invalid Token"}), 401

    # 🏢 2. DATA PROCESSING
    target_branch = request.args.get('branch', 'TEST1').strip().upper()
    is_template = 'template' in data_type 
    clean_type = data_type.replace('_template', '').replace('_full', '').strip().lower()
    data, columns = [], []

    try:
        # 🎓 A. STUDENTS
        if clean_type == 'students':
            records = Student.query.filter_by(branch=target_branch, company_id=user.company_id).all()
            # ✅ Added 'Zone' to the columns list
            columns = [
                'Student Name', 'Admission No', 'Grade', 'Div', 'Parent Mobile', 
                'RFID Tag', 'Zone', 'Pickup Stop', 'Drop Stop', 'Assigned Bus', 'Fee', 'Payment Status'
            ]
            
            if is_template:
                data = [{col: "" for col in columns}]
            else:
                for r in records:
                    # 🚀 Fetching the Zone name from the Pickup Stop object
                    p_stop_obj = db.session.get(BusStop, r.pickup_stop_id) if r.pickup_stop_id else None
                    d_stop_obj = db.session.get(BusStop, r.drop_stop_id) if r.drop_stop_id else None
                    bus_obj = db.session.get(Bus, r.bus_id) if r.bus_id else None

                    # Get Zone name from the pickup stop
                    zone_name = p_stop_obj.zone if p_stop_obj else "N/A"

                    data.append({
                        'Student Name': r.name, 
                        'Admission No': r.admission_no, 
                        'Grade': r.grade,
                        'Div': r.division, # ✅ ADD THIS LINE
                        'Parent Mobile': r.parent_mobile, 
                        'RFID Tag': r.rfid_tag,
                        'Zone': zone_name, # ✅ Now Exporting the Zone
                        'Pickup Stop': p_stop_obj.stop_name if p_stop_obj else "N/A", 
                        'Drop Stop': d_stop_obj.stop_name if d_stop_obj else "N/A", 
                        'Assigned Bus': bus_obj.bus_no if bus_obj else "N/A",
                        'Fee': r.total_fee, 
                        'Payment Status': r.payment_status or 'Pending'
                    })

        # 🚌 B. BUS FLEET
        elif clean_type == 'buses':
            records = Bus.query.filter_by(branch=target_branch, company_id=user.company_id).all()
            columns = ['Bus Number', 'Chassis No', 'Seater Capacity', 'GPS Device ID', 'SIM No', 'RFID Reader ID']
            if is_template:
                data = [{col: "" for col in columns}]
            else:
                data = [{
                    'Bus Number': r.bus_no, 'Chassis No': r.chassis_no, 'Seater Capacity': r.seater_capacity,
                    'GPS Device ID': r.gps_device_id, 'SIM No': r.sim_no, 'RFID Reader ID': r.rfid_reader_id
                } for r in records]

# 📍 C. BUS STOPS inside app.py
        elif clean_type == 'stops':
            # 🔍 Look for stops matching the branch and EITHER your company OR no company
            records = BusStop.query.filter(
                BusStop.branch.ilike(target_branch.strip()),
               (BusStop.company_id == user.company_id) | (BusStop.company_id == None)
            ).all()
            
            columns = ['Stop Name', 'Zone', 'Distance (KM)', 'Latitude', 'Longitude']
            
            if is_template:
                data = [{col: "" for col in columns}]
            else:
                print(f"📊 DOWNLOAD DEBUG: Found {len(records)} stops. Checking for repairs...")
                
                for r in records:
                    # 🛠️ AUTO-REPAIR: If company_id is missing, fix it now!
                    if r.company_id is None:
                        print(f"🔧 REPAIRING: Assigning '{r.stop_name}' to company {user.company_id}")
                        r.company_id = user.company_id
                    
                    data.append({
                        'Stop Name': r.stop_name, 
                        'Zone': r.zone, 
                        'Distance (KM)': r.km,
                        'Latitude': r.latitude or 0.0,
                        'Longitude': r.longitude or 0.0
                    })
                
                # Save the repairs to the database
                if records:
                    db.session.commit()

            # 🛡️ FIX FOR TYPEERROR: Ensure we always return something
            if not data:
                return jsonify({"error": "No stops found to download"}), 404

# 🚀 FINAL STEP: Create and send the actual file
        df = pd.DataFrame(data, columns=columns)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        
        output.seek(0)
        return send_file(
            output, 
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            as_attachment=True, 
            download_name=f"{target_branch}_{data_type}.xlsx"
        )

    except Exception as e:
        print(f"❌ EXCEL ERROR: {str(e)}")
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
    user_id = request.args.get('user_id')
    user = db.session.get(User, user_id)
    
    if not user or user_id == 'null': # Added safety check for 'null' string
        return jsonify({"message": "User not found"}), 404

    # ✅ Use username because your logs show the phone is there
    students = Student.query.filter_by(parent_mobile=user.username).all()
    
    results = []
    for s in students:
        # Use .student_name or .name depending on your Student model
        results.append({
            "id": s.id,
            "student_name": getattr(s, 'student_name', getattr(s, 'name', 'Unknown')),
            "title": "Annual Transport Fee",
            "admission_no": s.admission_no,
            "grade": s.grade,
            "branch": s.branch,
            "total_fee": s.total_fee,
            "payment_status": s.payment_status,
            "parent_name": user.username,
            "last_status": s.last_status or "AT HOME" # ✅ This pulls the real RFID tap status
        })
        
    return jsonify(results), 200

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    try:
        branch = request.args.get('branch')
        # ✅ 3. Fix Logic: Handle the 'branch' parameter safely
        if branch and branch != "All":
            # Ensure your database model 'AttendanceLog' has a 'branch' column
            logs = AttendanceLog.query.filter_by(branch=branch).order_by(AttendanceLog.timestamp.desc()).all()
        else:
            logs = AttendanceLog.query.order_by(AttendanceLog.timestamp.desc()).all()
            
        return jsonify([log.to_dict() for log in logs]), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Internal Server Error"}), 500 # 🚀 Prevents 500 crash

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

# ✅ Use BytesIO for Excel files (binary), not StringIO (text)
@app.route('/api/attendance/export', methods=['GET'])
def export_attendance_excel():
    try:
        branch = request.args.get('branch')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 1. Query the logs
        query = AttendanceLog.query
        if branch and branch not in ["All Branches", "All"]:
            query = query.filter_by(branch=branch)

        if start_date and end_date:
            query = query.filter(AttendanceLog.timestamp.between(f"{start_date} 00:00:00", f"{end_date} 23:59:59"))

        logs = query.order_by(AttendanceLog.timestamp.desc()).all()

        # 2. Process Data & Calculate Totals
        data = []
        boarded_count = 0
        dropped_count = 0

        for log in logs:
            status = str(log.status).capitalize()
            if status == "Boarded": boarded_count += 1
            if status == "Dropped": dropped_count += 1

            data.append({
                "Student Name": log.student.name if log.student else "Unknown",
                "Status": status,
                "Branch": log.branch,
                "Location": log.location,
                "Timestamp": log.timestamp
            })

        # 3. Create DataFrame with guaranteed headers
        headers = ["Student Name", "Status", "Branch", "Location", "Timestamp"]
        df = pd.DataFrame(data, columns=headers)

        # 4. Save to Memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Attendance')
            
            worksheet = writer.sheets['Attendance']
            
            # --- Add Summary Rows at the bottom ---
            start_row = len(df) + 2
            worksheet.cell(row=start_row + 1, column=1, value="SUMMARY")
            worksheet.cell(row=start_row + 2, column=1, value=f"Total Boarded: {boarded_count}")
            worksheet.cell(row=start_row + 3, column=1, value=f"Total Dropped: {dropped_count}")
            worksheet.cell(row=start_row + 4, column=1, value=f"Grand Total: {len(df)}")

            # --- Auto-adjust column width ---
            for idx, col in enumerate(df.columns):
                series = df[col].astype(str)
                # Check for empty series to prevent max() error
                val_len = series.map(len).max() if not series.empty else 0
                max_len = max(val_len, len(col)) + 2
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(idx + 1)].width = max_len

        # 🚀 CRITICAL: Move pointer to the start so the file isn't "empty"
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"Attendance_{branch}_{start_date}.xlsx"
        )

    except Exception as e:
        print(f"❌ Excel Export Error: {e}")
        return jsonify({"error": str(e)}), 500

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
@jwt_required(optional=True)
def secure_assign_fee():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200
    
    from flask_jwt_extended import verify_jwt_in_request
    verify_jwt_in_request()
    
    data = request.json
    try:
        new_fee = FeeRecord(
            student_id=data['student_id'],
            title=data['title'],
            amount=float(data['amount']),
            due_date=data.get('due_date', '2026-03-31'),
            status="Pending"
        )
        db.session.add(new_fee)
        db.session.commit()
        return jsonify({"message": "Fee Assigned Successfully!"}), 201
    except Exception as e:
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
def assign_transport():
    data = request.json
    student_id = data.get('student_id')
    stop_id = data.get('stop_id') # The ID of the pickup point

    student = Student.query.get(student_id)
    stop = BusStop.query.get(stop_id)

    if not student or not stop:
        return jsonify({"error": "Student or Stop not found"}), 404

    # 1. Assign the Stop to the Student
    student.pickup_stop_id = stop_id
    
    # 2. Find the Zone & Price
    zone = Zone.query.get(stop.zone_id)
    if not zone:
        # If no zone assigned, just save stop but warn user
        db.session.commit()
        return jsonify({"message": "Stop assigned, but Zone price not found (No Fee Created)"}), 200

    # 3. AUTO-CREATE FEE 💰
    # Check if a transport fee already exists to prevent duplicates
    existing_fee = FeeRecord.query.filter_by(student_id=student.id, title="Transport Fee (Auto)").first()
    
    if not existing_fee:
        new_fee = FeeRecord(
            student_id=student.id,
            title="Transport Fee (Auto)",
            amount=zone.price,  # 👈 Magic happens here!
            due_date="2026-06-30", # Default due date
            status="Pending"
        )
        db.session.add(new_fee)
        message = f"Stop Assigned & Fee of ₹{zone.price} Auto-Created!"
    else:
        # Optional: Update the existing fee if price changed
        existing_fee.amount = zone.price
        message = f"Stop Updated & Fee adjusted to ₹{zone.price}"

    db.session.commit()
    return jsonify({"message": message}), 200

# ==========================================
#  🚌 SELF-SERVICE TRANSPORT (Updated)
# ==========================================

# 1. Get Stops with Prices (Smart KM Check) 🧠
@app.route('/api/public/stops', methods=['GET'])
def get_public_stops():
    stops = BusStop.query.all()
    zones = Zone.query.all() # Get all zones to compare KM
    output = []
    
    for s in stops:
        price = 0
        
        # Strategy A: Check explicit link
        if s.zone_id:
            zone = Session.get(db.session, Zone, s.zone_id) # Updated for SQLAlchemy 2.0
            if zone: price = zone.price
            
        # Strategy B: If no link, check KM match (The Fix!)
        if price == 0:
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


@app.route('/api/parent/my_bus', methods=['GET'])
@jwt_required()
def get_parent_bus():
    user_id = int(get_jwt_identity())
    
    # 1. Find the student linked to this parent user
    student = Student.query.filter_by(parent_id=user_id).first()
    
    if not student or not student.bus_id:
        return jsonify({"error": "No bus assigned to your child yet"}), 404

    # 2. Get the bus location
    bus = Bus.query.get(student.bus_id)
    
    # 3. Return the standard marker format
    return jsonify({
        "id": bus.id,
        "name": bus.bus_no,
        "lat": bus.last_lat,
        "lng": bus.last_lng,
        "status": bus.status,
        "speed": bus.speed,
        "driver_name": "Driver Name", # You can link your Driver model here later
    }), 200

# 2. Parent Selects Stop -> Auto-Generate Fee 💰 (FIXED & SAFER)
@app.route('/api/parent/select_transport', methods=['POST'])
def parent_select_transport():
    try:
        data = request.json
        student_id = data.get('student_id')
        stop_id = data.get('stop_id')

        student = Student.query.get(student_id)
        if not student: 
            return jsonify({"error": "Student not found"}), 404

        stop = BusStop.query.get(stop_id)
        if not stop:
            return jsonify({"error": "Stop not found"}), 404

        # 1. Assign Stop to Student
        student.pickup_stop_id = stop_id
        
        # 2. Set Price (Manually setting ₹20 for your company demo)
        # In a real system, you would use: price = stop.km * 10 or similar logic
        price = 20.0 

        # 3. Create or Update Fee in the FeeRecord table
        # This matches what your 'ParentPaymentScreen' is looking for
        existing_fee = FeeRecord.query.filter_by(student_id=student.id, title="Annual Transport Fee").first()
        
        if existing_fee:
            if existing_fee.status == "Paid":
                return jsonify({"error": "Fee already paid! Cannot change stop now."}), 400
            existing_fee.amount = price 
            message = f"Stop Updated! Fee updated to ₹{price}."
        else:
            new_fee = FeeRecord(
                student_id=student.id,
                title="Annual Transport Fee",
                amount=price,
                due_date="2026-06-01",
                status="Pending"
            )
            db.session.add(new_fee)
            message = f"Transport Assigned! Fee of ₹{price} generated."

        # ✅ ALSO update the Student table so the Home Screen knows to show the tracking block
        student.total_fee = price
        student.payment_status = "Pending"

        db.session.commit()
        return jsonify({"message": message, "fee": price}), 200

    except Exception as e:
        print(f"🔥 CRASH ERROR: {str(e)}") 
        db.session.rollback()
        return jsonify({"error": f"Backend Error: {str(e)}"}), 500

# ==========================================
# 🏢 BRANCH MANAGEMENT (Multi-Tenant Fix)
# ==========================================
from flask_jwt_extended import jwt_required, get_jwt_identity

@app.route('/api/branches', methods=['GET', 'POST', 'OPTIONS'])
@app.route('/api/admin/branches', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required() # 🛡️ STEP 1: Lock the door so we know who is logged in
def handle_branches_flexible():
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200

    # Get the ID of the person logged in (e.g., testadmin or fleetadmin)
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    # ------------------------------------------
    # 📂 FETCH BRANCHES (GET)
    # ------------------------------------------
    if request.method == 'GET':
        # 🛡️ DATA ISOLATION: 
        # Only fetch branches where company_id matches the logged-in user's school
        branches = Branch.query.filter_by(company_id=user.company_id).all()
        return jsonify([b.to_dict() for b in branches]), 200
    
    # ------------------------------------------
    # 📝 CREATE BRANCH (POST)
    # ------------------------------------------
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
        
    # Check if branch exists WITHIN this specific school
    if Branch.query.filter_by(name=data['name'], company_id=user.company_id).first():
        return jsonify({'error': 'Branch already exists in your school'}), 400
        
    # ✅ Auto-assign the Branch to the user's company_id
    new_branch = Branch(
        name=data['name'],
        latitude=data.get('latitude'), 
        longitude=data.get('longitude'),
        company_id=user.company_id # 🚀 THIS STOPS THE LEAKAGE
    )
    
    db.session.add(new_branch)
    db.session.commit()
    return jsonify({'message': 'Branch added successfully'}), 201

# Delete route (Also needs protection)
@app.route('/api/branches/<int:id>', methods=['DELETE', 'OPTIONS'])
@app.route('/api/admin/branches/<int:id>', methods=['DELETE', 'OPTIONS'])
@jwt_required()
def delete_branch_flexible(id):
    if request.method == 'OPTIONS':
        return jsonify({'message': 'CORS OK'}), 200
        
    current_user_id = get_jwt_identity()
    user = db.session.get(User, current_user_id)
    
    # 🛡️ Ensure they can only delete their own branches
    branch = Branch.query.filter_by(id=id, company_id=user.company_id).first()
    
    if not branch: 
        return jsonify({'error': 'Branch not found or unauthorized'}), 404
        
    db.session.delete(branch)
    db.session.commit()
    return jsonify({'message': 'Branch deleted'}), 200

# ==========================================
# 🗺️ SECURE ZONE & FEES MANAGEMENT
# ==========================================
@app.route('/api/admin/zones', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required(optional=True)
def manage_zones():
    if request.method == 'OPTIONS': 
        return jsonify({'message': 'CORS OK'}), 200

    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Unauthorized access"}), 401

    user = db.session.get(User, int(get_jwt_identity()))
    branch_param = request.args.get('branch')
    
    # 🔒 Base Filter: Always separate by school
    query = FeeZone.query.filter_by(company_id=user.company_id)

    if request.method == 'GET':
        # 🛡️ Use a safe role check
        user_role = str(user.role).lower().strip()
        
        if user_role in ['super_admin', 'admin']:
            # Admin View: Filter only if a specific branch is selected
            if branch_param and branch_param not in ["All Branches", "Global", "TEST SCHOOL"]:
                query = query.filter_by(branch=branch_param.upper())
        else:
            # 🏢 Branch Incharge: Look up their branch name
            # We use globals() to find the Branch class safely
            BranchModel = globals().get('Branch')
            if BranchModel:
                b_obj = db.session.get(BranchModel, user.branch_id)
                if b_obj:
                    query = query.filter_by(branch=b_obj.name.upper())

        zones = query.all()
        return jsonify([z.to_dict() for z in zones]), 200

    if request.method == 'POST':
        try:
            data = request.json
            new_zone = FeeZone(
                zone_name=data.get('name'), # This 'name' comes from your Flutter controller
                min_km=float(data.get('min_km', 0)),
                max_km=float(data.get('max_km', 0)),
                price=float(data.get('price', 0)),
                branch=data.get('branch', '').upper(),
                term=data.get('term', 'Annual'),
                mode=data.get('mode', 'Two-Way'),
                company_id=user.company_id 
            )
            db.session.add(new_zone)
            db.session.commit()
            return jsonify({'message': 'Zone added successfully'}), 201
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
        stop_names = data.get('stops') # List of stop names
        branch_name = data.get('branch')
        
        user = db.session.get(User, int(get_jwt_identity()))
        
        # 1. Validation: Ensure the bus belongs to this company
        bus = Bus.query.filter_by(id=bus_id, company_id=user.company_id).first()
        if not bus:
            return jsonify({"error": "Bus not found"}), 404

        # 2. Find all students belonging to this company AND branch AND these stops
        query = Student.query.filter_by(company_id=user.company_id)
        
        # If it's a specific branch, restrict the search
        if branch_name and branch_name != "All Branches":
            query = query.filter_by(branch=branch_name.upper())
            
        # Filter by the list of stops selected
        students_to_update = query.filter(Student.stop_name.in_(stop_names)).all()

        # 3. Mass Update 🚀
        count = 0
        for student in students_to_update:
            student.bus_id = bus_id
            count += 1
            
        db.session.commit()
        
        return jsonify({
            "message": f"Successfully assigned {count} students to Bus {bus.bus_no}",
            "count": count
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Bulk Allot Error: {e}")
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

@app.route('/api/admin/reports/daily', methods=['GET'])
@jwt_required()
def get_daily_report():
    try:
        # 1. Get branch from URL
        branch_from_url = request.args.get('branch', '').strip()
        user = db.session.get(User, int(get_jwt_identity()))

        # 2. Filter by Company (Always!)
        query = Bus.query.filter_by(company_id=user.company_id)
        
        # 3. Apply Branch Filter 🛡️
        # If the URL has a branch, use it. 
        if branch_from_url and branch_from_url.lower() != "all branches":
            query = query.filter_by(branch=branch_from_url.upper())
        # 🛑 Removed 'user.branch' check to prevent the AttributeError crash

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

@app.route('/api/admin/reports/export', methods=['GET'])
@jwt_required(locations=["headers", "query_string"])
def export_gps_report():
    try:
        branch = request.args.get('branch', '').strip()
        start_date = request.args.get('start_date')
        user = db.session.get(User, int(get_jwt_identity()))

        query = Bus.query.filter_by(company_id=user.company_id)
        if branch and branch.lower() != "all branches" and branch != "":
            query = query.filter_by(branch=branch.upper())
            filename = f"{branch}_Report.xlsx" if branch else "Global_Fleet_Report.xlsx"
        else:
            filename = "Global_Report.xlsx"

        buses = query.all()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Bus Number", "Branch", "Distance", "Avg Speed", "Max Speed"])
        
        for bus in buses:
            dist = get_safe_attr(bus, ['total_km', 'km', 'distance', 'mileage'])
            avg = get_safe_attr(bus, ['avg_speed', 'average_speed'])
            mx = get_safe_attr(bus, ['max_speed', 'top_speed'])
            ws.append([bus.bus_no, bus.branch, f"{dist} km", f"{avg} km/h", f"{mx} km/h"])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         as_attachment=True, download_name=filename)
    except Exception as e:
        print(f"Export Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/admin/company_branding', methods=['GET'])
@jwt_required()
def get_company_branding():
    user_id = get_jwt_identity()
    user = db.session.get(User, user_id)
    
    # 🛡️ If user belongs to a company, fetch that company specifically
    if user.company_id:
        company = db.session.get(Company, user.company_id)
        if company:
            return jsonify({
                "company_name": company.name,
                "company_logo": company.logo_url or ""
            }), 200
            
    # Fallback for Super Admin
    return jsonify({
        "company_name": "Super Admin Control",
        "company_logo": ""
    }), 200

@app.route('/api/admin/companies', methods=['GET', 'POST', 'OPTIONS'])
@jwt_required(optional=True) # 🛡️ STEP 1: Allow OPTIONS to pass without a token
def handle_companies():
    # 🚀 2. HANDLE CORS PRE-FLIGHT Handshake
    if request.method == 'OPTIONS':
        return _cors_response()

    # 🚀 3. NOW ENFORCE SECURITY for real data
    from flask_jwt_extended import verify_jwt_in_request
    try:
        verify_jwt_in_request()
    except Exception:
        return jsonify({"error": "Missing or invalid token"}), 401

    user = db.session.get(User, get_jwt_identity())
    if not user or user.role.lower() not in ['super_admin', 'developer', 'admin']:
        return jsonify({"error": f"Unauthorized. Your role is {user.role}"}), 403

    # 📂 4. FETCH CLIENTS (GET)
    if request.method == 'GET':
        if user.role.lower() in ['super_admin', 'developer']:
            companies = Company.query.all()
        else:
            # 🚀 Client Admin only sees their own record
            companies = Company.query.filter_by(id=user.company_id).all()
        return jsonify([c.to_dict() for c in companies]), 200

    # 📝 5. REGISTER NEW CLIENT (POST)
    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data.get('name'):
                return jsonify({"error": "Company name is required"}), 400

            new_co = Company(
                name=data.get('name'),
                logo_url=data.get('logo_url', ''),
                address=data.get('address', ''),
                phone_number=data.get('phone', ''),
                bank_name=data.get('bank_name', ''),
                account_no=data.get('account_no', ''),
                ifsc_code=data.get('ifsc_code', '')
            )
            db.session.add(new_co)
            db.session.commit()
            return jsonify({"message": "Company Registered Successfully", "id": new_co.id}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Registration failed: {str(e)}"}), 500

    return jsonify({"error": "Method not allowed"}), 405

@app.route('/api/admin/companies/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def handle_single_company(id):
    user = db.session.get(User, get_jwt_identity())

    # 🛡️ Only Super Admins/Developers can Edit or Delete Clients
    if not user or user.role.lower() not in ['super_admin', 'developer']:
        return jsonify({"error": "Unauthorized"}), 403

    company = Company.query.get_or_404(id)

    # ✏️ Update Client Info
    if request.method == 'PUT':
        data = request.get_json()
        
        company.name = data.get('name', company.name)
        company.address = data.get('address', company.address)
        company.phone_number = data.get('phone', company.phone_number)
        company.logo_url = data.get('logo_url', company.logo_url)
        company.bank_name = data.get('bank_name', company.bank_name)
        company.account_no = data.get('account_no', company.account_no)
        company.ifsc_code = data.get('ifsc_code', company.ifsc_code)

        db.session.commit()
        return jsonify({"message": f"Updated {company.name} successfully"}), 200

    # 🗑️ Remove Client
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
    from datetime import datetime
    new_status = "Boarded" if student.last_status != "Boarded" else "Dropped"
    student.last_status = new_status
    
    log = AttendanceLog(
        student_id=student.id,
        # ❌ Remove student_name=student.name from here
        bus_number=bus_no,
        status=new_status,
        branch=student.branch,
        company_id=student.company_id,
        timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"message": "Success", "student": student.name, "status": new_status}), 201

@app.route('/api/admin/bus_history/<int:bus_id>', methods=['GET'])
@jwt_required()
def get_bus_history(bus_id):
    # Fetch last 50 points for that bus
    history = BusHistory.query.filter_by(bus_id=bus_id)\
              .order_by(BusHistory.timestamp.desc())\
              .limit(50).all()
    
    points = [{"lat": p.lat, "lng": p.lng} for p in reversed(history)]
    return jsonify(points), 200

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

@app.route('/api/debug/check_stops')
def debug_stops():
    stops = BusStop.query.all()
    return jsonify([{"name": s.stop_name, "branch_in_db": f"'{s.branch}'"} for s in stops])

# ==========================================
# 🚀 LIVE BUS SIMULATION (Add this at the bottom)
# ==========================================
def auto_move_bus():
    # We use app_context so the thread can talk to the database
    with app.app_context():
        print("🛰️ Simulation Started: Moving Bus KA05AP1124...")
        while True:
            try:
                # Find your specific bus
                bus = Bus.query.filter_by(bus_no='KA05AP1124').first()
                if bus:
                    # 📍 Move the bus randomly around the PSBN School area
                    bus.last_lat = 13.1187 + random.uniform(-0.005, 0.005)
                    bus.last_lng = 77.5752 + random.uniform(-0.005, 0.005)
                    bus.status = 'moving'
                    bus.speed = random.uniform(20.0, 45.0)
                    
                    db.session.commit()
                    # Optional: print to terminal so you know it's working
                    # print(f"📡 SIMULATOR: {bus.bus_no} moved to {bus.last_lat}, {bus.last_lng}")
            except Exception as e:
                print(f"❌ Simulation Error: {e}")
                db.session.rollback()
            
            time.sleep(5) # ⏱️ Wait 5 seconds before next move

# ✅ START THE SIMULATOR
simulation_thread = threading.Thread(target=auto_move_bus, daemon=True)
simulation_thread.start()

# ==========================================
# 🚀 STARTUP, TABLE CREATION & SEEDING
# ==========================================
if __name__ == "__main__":
    with app.app_context():
        try:
            # 1. Create all tables
            db.create_all()
            
            # 2. Check tables for logs
            import sqlalchemy as sa
            inspector = sa.inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"✅ DATABASE INITIALIZED. Tables found: {tables}")

            # 3. Seed Default Super Admin if missing
            if not User.query.filter_by(username='admin').first():
                admin_co = Company.query.filter_by(name="Main Office").first()
                if not admin_co:
                    admin_co = Company(name="Main Office")
                    db.session.add(admin_co)
                    db.session.commit()
                
                admin_user = User(
                    username='admin', 
                    password_hash=generate_password_hash('admin123'),
                    role='super_admin',
                    company_id=admin_co.id
                )
                db.session.add(admin_user)
                db.session.commit()
                print("🚀 SEED SUCCESS: Created admin / admin123")
                
        except Exception as e:
            print(f"❌ STARTUP ERROR: {e}")

    # 4. Run App (Render uses PORT 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)