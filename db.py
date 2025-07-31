"""
SmartConnect Manager - Firebase Database Layer
Using Firebase Firestore as the backend database
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime, date
import hashlib
import uuid
from typing import List, Dict, Optional, Any
import json

# Initialize Firebase
try:
    if not firebase_admin._apps:
        # Look for Service.json file in the current directory or specified path
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "Service.json")
        
        if os.path.exists(service_account_path):
            # Use the Service.json file
            cred = credentials.Certificate(service_account_path)
            print(f"Using Firebase credentials from: {service_account_path}")
        else:
            # Fallback to environment variables if Service.json doesn't exist
            firebase_config = {
                "type": "service_account",
                "project_id": os.getenv("FIREBASE_PROJECT_ID", "your-project-id"),
                "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
            }
            
            # Check if we have the required environment variables
            if not firebase_config["project_id"] or firebase_config["project_id"] == "your-project-id":
                raise Exception("No Service.json file found and FIREBASE_PROJECT_ID not set in environment variables")
            
            cred = credentials.Certificate(firebase_config)
            print("Using Firebase credentials from environment variables")
        
        firebase_admin.initialize_app(cred)
        print("Firebase initialized successfully")
    
    # Initialize Firestore client
    db_client = firestore.client()
    print("Firestore client initialized successfully")
    
except Exception as e:
    print(f"Firebase initialization error: {e}")
    print("Please ensure:")
    print("1. Service.json file exists in the project root directory, OR")
    print("2. Set FIREBASE_SERVICE_ACCOUNT_PATH environment variable to the correct path, OR") 
    print("3. Set all required Firebase environment variables")
    db_client = None

class DatabaseManager:
    def __init__(self):
        self.db = db_client
        
        # Collection names
        self.USERS_COLLECTION = 'users'
        self.VEHICLES_COLLECTION = 'vehicles'
        self.TOOLS_COLLECTION = 'tools'
        self.MISSIONS_COLLECTION = 'missions'
        self.DEPARTMENTS_COLLECTION = 'departments'
        self.ACTIVITY_LOGS_COLLECTION = 'activity_logs'
        self.TOOL_ASSIGNMENTS_COLLECTION = 'tool_assignments'
        self.VEHICLE_ASSIGNMENTS_COLLECTION = 'vehicle_assignments'
        self.MISSION_REPORTS_COLLECTION = 'mission_reports'
        self.NOTIFICATIONS_COLLECTION = 'notifications'
    
    # ========== UTILITY FUNCTIONS ==========
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def generate_id(self) -> str:
        """Generate unique ID"""
        return str(uuid.uuid4())
    
    def to_dict(self, doc_snapshot):
        """Convert Firestore document to dictionary"""
        if doc_snapshot.exists:
            data = doc_snapshot.to_dict()
            data['id'] = doc_snapshot.id
            return data
        return None
    
    # ========== AUTHENTICATION ==========
    
    def login(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user login"""
        try:
            if not self.db:
                return None
                
            hashed_password = self.hash_password(password)
            
            # Query users collection
            users_ref = self.db.collection(self.USERS_COLLECTION)
            query = users_ref.where('username', '==', username).where('password', '==', hashed_password).where('active', '==', True).limit(1)
            
            results = query.stream()
            for doc in results:
                user_data = self.to_dict(doc)
                if user_data:
                    # Update last login
                    self.db.collection(self.USERS_COLLECTION).document(doc.id).update({
                        'last_login': datetime.now().isoformat()
                    })
                    return user_data
            
            return None
        except Exception as e:
            print(f"Login error: {e}")
            return None
    
    def create_user(self, username: str, full_name: str, password: str, role: str, department_id: int, active: bool = True) -> bool:
        """Create new user"""
        try:
            if not self.db:
                return False
                
            user_data = {
                'username': username,
                'full_name': full_name,
                'password': self.hash_password(password),
                'role': role,
                'department_id': department_id,
                'active': active,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'last_login': None
            }
            
            # Check if username already exists
            existing_user = self.db.collection(self.USERS_COLLECTION).where('username', '==', username).limit(1).stream()
            if any(existing_user):
                return False
            
            # Add user to Firestore
            doc_ref = self.db.collection(self.USERS_COLLECTION).add(user_data)
            return bool(doc_ref)
        except Exception as e:
            print(f"Create user error: {e}")
            return False
    
    # ========== EMPLOYEE MANAGEMENT ==========
    
    def get_all_employees(self) -> List[Dict]:
        """Get all employees with department info"""
        try:
            if not self.db:
                return []
                
            employees = []
            users_ref = self.db.collection(self.USERS_COLLECTION)
            
            # Get all users
            for doc in users_ref.stream():
                user_data = self.to_dict(doc)
                if user_data:
                    # Get department info
                    department_name = 'Unknown'
                    if user_data.get('department_id'):
                        dept_doc = self.db.collection(self.DEPARTMENTS_COLLECTION).document(str(user_data['department_id'])).get()
                        if dept_doc.exists:
                            dept_data = dept_doc.to_dict()
                            department_name = dept_data.get('name', 'Unknown')
                    
                    employees.append({
                        'id': user_data['id'],
                        'name': user_data['full_name'],
                        'username': user_data['username'],
                        'role': user_data['role'],
                        'department': department_name,
                        'status': 'ACTIVE' if user_data['active'] else 'INACTIVE',
                        'last_login': user_data.get('last_login'),
                        'created_at': user_data.get('created_at')
                    })
            
            return employees
        except Exception as e:
            print(f"Get employees error: {e}")
            return []
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        try:
            if not self.db:
                return None
                
            doc = self.db.collection(self.USERS_COLLECTION).document(employee_id).get()
            return self.to_dict(doc)
        except Exception as e:
            print(f"Get employee error: {e}")
            return None
    
    def update_employee(self, employee_id: str, update_data: Dict) -> bool:
        """Update employee information"""
        try:
            if not self.db:
                return False
                
            if 'password' in update_data:
                update_data['password'] = self.hash_password(update_data['password'])
            
            update_data['updated_at'] = datetime.now().isoformat()
            
            self.db.collection(self.USERS_COLLECTION).document(employee_id).update(update_data)
            return True
        except Exception as e:
            print(f"Update employee error: {e}")
            return False
    
    # ========== VEHICLE MANAGEMENT ==========
    
    def get_all_vehicles(self) -> List[Dict]:
        """Get all vehicles"""
        try:
            if not self.db:
                return []
                
            vehicles = []
            vehicles_ref = self.db.collection(self.VEHICLES_COLLECTION)
            
            for doc in vehicles_ref.stream():
                vehicle_data = self.to_dict(doc)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            return vehicles
        except Exception as e:
            print(f"Get vehicles error: {e}")
            return []
    
    def get_available_vehicles(self) -> List[Dict]:
        """Get available vehicles"""
        try:
            if not self.db:
                return []
                
            vehicles = []
            vehicles_ref = self.db.collection(self.VEHICLES_COLLECTION).where('status', '==', 'AVAILABLE')
            
            for doc in vehicles_ref.stream():
                vehicle_data = self.to_dict(doc)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            return vehicles
        except Exception as e:
            print(f"Get available vehicles error: {e}")
            return []
    
    def create_vehicle(self, vehicle_data: Dict) -> bool:
        """Create new vehicle"""
        try:
            if not self.db:
                return False
                
            # Set timestamps
            vehicle_data['created_at'] = datetime.now().isoformat()
            vehicle_data['last_updated'] = datetime.now().isoformat()
            
            # Check if plate number already exists
            if vehicle_data.get('plate_number'):
                existing_vehicle = self.db.collection(self.VEHICLES_COLLECTION).where('plate_number', '==', vehicle_data['plate_number']).limit(1).stream()
                if any(existing_vehicle):
                    print(f"Vehicle with plate number {vehicle_data['plate_number']} already exists")
                    return False
            
            doc_ref = self.db.collection(self.VEHICLES_COLLECTION).add(vehicle_data)
            return bool(doc_ref)
        except Exception as e:
            print(f"Create vehicle error: {e}")
            return False
    
    def update_vehicle_status(self, vehicle_id: str, status: str, location: str = None) -> bool:
        """Update vehicle status and location"""
        try:
            if not self.db:
                return False
                
            update_data = {
                'status': status,
                'last_updated': datetime.now().isoformat()
            }
            
            if location:
                update_data['location'] = location
            
            self.db.collection(self.VEHICLES_COLLECTION).document(vehicle_id).update(update_data)
            return True
        except Exception as e:
            print(f"Update vehicle status error: {e}")
            return False
    
    # ========== EQUIPMENT/TOOLS MANAGEMENT ==========
    
    def get_all_tools(self) -> List[Dict]:
        """Get all tools/equipment"""
        try:
            if not self.db:
                return []
                
            tools = []
            tools_ref = self.db.collection(self.TOOLS_COLLECTION)
            
            for doc in tools_ref.stream():
                tool_data = self.to_dict(doc)
                if tool_data:
                    tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Get tools error: {e}")
            return []
    
    def get_available_tools(self) -> List[Dict]:
        """Get available tools"""
        try:
            if not self.db:
                return []
                
            tools = []
            tools_ref = self.db.collection(self.TOOLS_COLLECTION).where('available_quantity', '>', 0)
            
            for doc in tools_ref.stream():
                tool_data = self.to_dict(doc)
                if tool_data:
                    tools.append(tool_data)
            
            return tools
        except Exception as e:
            print(f"Get available tools error: {e}")
            return []
    
    def create_tool(self, tool_data: Dict) -> bool:
        """Create new tool"""
        try:
            if not self.db:
                return False
                
            # Set timestamps
            tool_data['created_at'] = datetime.now().isoformat()
            tool_data['last_updated'] = datetime.now().isoformat()
            
            # Ensure available_quantity matches total_quantity if not provided
            if 'available_quantity' not in tool_data:
                tool_data['available_quantity'] = tool_data.get('total_quantity', 0)
            
            # Check if serial number already exists
            if tool_data.get('serial_number'):
                existing_tool = self.db.collection(self.TOOLS_COLLECTION).where('serial_number', '==', tool_data['serial_number']).limit(1).stream()
                if any(existing_tool):
                    print(f"Tool with serial number {tool_data['serial_number']} already exists")
                    return False
            
            doc_ref = self.db.collection(self.TOOLS_COLLECTION).add(tool_data)
            return bool(doc_ref)
        except Exception as e:
            print(f"Create tool error: {e}")
            return False
    
    def update_tool_quantity(self, tool_id: str, used_quantity: int, operation: str = 'assign') -> bool:
        """Update tool quantity (assign/return)"""
        try:
            if not self.db:
                return False
                
            # Get current tool info
            tool_doc = self.db.collection(self.TOOLS_COLLECTION).document(tool_id).get()
            
            if not tool_doc.exists:
                return False
            
            tool_data = tool_doc.to_dict()
            current_available = tool_data.get('available_quantity', 0)
            
            if operation == 'assign':
                new_available = current_available - used_quantity
                if new_available < 0:
                    return False  # Not enough tools available
            else:  # return
                new_available = min(current_available + used_quantity, tool_data.get('total_quantity', 0))
            
            self.db.collection(self.TOOLS_COLLECTION).document(tool_id).update({
                'available_quantity': new_available,
                'last_updated': datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            print(f"Update tool quantity error: {e}")
            return False
    
    # ========== MISSION/PROJECT MANAGEMENT ==========
    
    def create_mission(self, mission_data: Dict) -> bool:
        """Create new mission"""
        try:
            if not self.db:
                return False
                
            mission_data['created_at'] = datetime.now().isoformat()
            mission_data['updated_at'] = datetime.now().isoformat()
            
            doc_ref, doc_id = self.db.collection(self.MISSIONS_COLLECTION).add(mission_data)
            
            if doc_ref:
                # Create activity log
                self.log_activity('mission_created', {
                    'mission_id': doc_id,
                    'title': mission_data['title'],
                    'assigned_to': mission_data.get('assigned_person_id')
                })
                
                return True
            return False
        except Exception as e:
            print(f"Create mission error: {e}")
            return False
    
    def get_all_missions(self) -> List[Dict]:
        """Get all missions with related data"""
        try:
            if not self.db:
                return []
                
            missions = []
            missions_ref = self.db.collection(self.MISSIONS_COLLECTION)
            
            for doc in missions_ref.stream():
                mission_data = self.to_dict(doc)
                if mission_data:
                    # Get assigned user info
                    if mission_data.get('assigned_person_id'):
                        user_doc = self.db.collection(self.USERS_COLLECTION).document(mission_data['assigned_person_id']).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
                    
                    # Get team leader info
                    if mission_data.get('team_leader_id'):
                        leader_doc = self.db.collection(self.USERS_COLLECTION).document(mission_data['team_leader_id']).get()
                        if leader_doc.exists:
                            leader_data = leader_doc.to_dict()
                            mission_data['team_leader'] = {'full_name': leader_data.get('full_name')}
                    
                    # Get vehicle info
                    if mission_data.get('vehicle_id'):
                        vehicle_doc = self.db.collection(self.VEHICLES_COLLECTION).document(mission_data['vehicle_id']).get()
                        if vehicle_doc.exists:
                            vehicle_data = vehicle_doc.to_dict()
                            mission_data['vehicle'] = {
                                'model': vehicle_data.get('model'),
                                'plate_number': vehicle_data.get('plate_number')
                            }
                    
                    missions.append(mission_data)
            
            return missions
        except Exception as e:
            print(f"Get missions error: {e}")
            return []
    
    def get_missions_by_user(self, user_id: str) -> List[Dict]:
        """Get missions assigned to specific user"""
        try:
            if not self.db:
                return []
                
            missions = []
            missions_ref = self.db.collection(self.MISSIONS_COLLECTION).where('assigned_person_id', '==', user_id)
            
            for doc in missions_ref.stream():
                mission_data = self.to_dict(doc)
                if mission_data:
                    # Get additional info like in get_all_missions
                    missions.append(mission_data)
            
            return missions
        except Exception as e:
            print(f"Get user missions error: {e}")
            return []
    
    def update_mission_status(self, mission_id: str, status: str, notes: str = None) -> bool:
        """Update mission status"""
        try:
            if not self.db:
                return False
                
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if notes:
                update_data['notes'] = notes
            
            if status == 'COMPLETED':
                update_data['completed_at'] = datetime.now().isoformat()
            
            self.db.collection(self.MISSIONS_COLLECTION).document(mission_id).update(update_data)
            
            # Log activity
            self.log_activity('mission_status_updated', {
                'mission_id': mission_id,
                'new_status': status,
                'notes': notes
            })
            
            return True
        except Exception as e:
            print(f"Update mission status error: {e}")
            return False
    
    # ========== ACTIVITY LOGGING ==========
    
    def log_activity(self, activity_type: str, activity_data: Dict, user_id: str = None) -> bool:
        """Log system activity"""
        try:
            if not self.db:
                return False
                
            log_data = {
                'activity_type': activity_type,
                'activity_data': activity_data,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            }
            
            doc_ref = self.db.collection(self.ACTIVITY_LOGS_COLLECTION).add(log_data)
            return bool(doc_ref)
        except Exception as e:
            print(f"Log activity error: {e}")
            return False
    
    def get_recent_activities(self, limit: int = 10) -> List[Dict]:
        """Get recent activities"""
        try:
            if not self.db:
                return []
                
            activities = []
            activities_ref = self.db.collection(self.ACTIVITY_LOGS_COLLECTION).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(limit)
            
            for doc in activities_ref.stream():
                activity_data = self.to_dict(doc)
                if activity_data:
                    # Get user info if available
                    if activity_data.get('user_id'):
                        user_doc = self.db.collection(self.USERS_COLLECTION).document(activity_data['user_id']).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            activity_data['user'] = {'full_name': user_data.get('full_name')}
                    
                    activities.append(activity_data)
            
            return activities
        except Exception as e:
            print(f"Get activities error: {e}")
            return []
    
    # ========== REPORTS AND ANALYTICS ==========
    
    def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics"""
        try:
            if not self.db:
                return self._get_empty_stats()
            
            # Get employee stats
            employees = list(self.db.collection(self.USERS_COLLECTION).stream())
            total_employees = len(employees)
            active_employees = len([emp for emp in employees if emp.to_dict().get('active', False)])
            
            # Get mission stats
            missions = list(self.db.collection(self.MISSIONS_COLLECTION).stream())
            total_missions = len(missions)
            active_missions = len([m for m in missions if m.to_dict().get('status') in ['PENDING', 'IN_PROGRESS']])
            completed_missions = len([m for m in missions if m.to_dict().get('status') == 'COMPLETED'])
            
            # Get vehicle stats
            vehicles = list(self.db.collection(self.VEHICLES_COLLECTION).stream())
            total_vehicles = len(vehicles)
            available_vehicles = len([v for v in vehicles if v.to_dict().get('status') == 'AVAILABLE'])
            in_use_vehicles = len([v for v in vehicles if v.to_dict().get('status') == 'IN_USE'])
            
            # Get tool stats
            tools = list(self.db.collection(self.TOOLS_COLLECTION).stream())
            total_tools = sum([t.to_dict().get('total_quantity', 0) for t in tools])
            available_tools = sum([t.to_dict().get('available_quantity', 0) for t in tools])
            in_use_tools = total_tools - available_tools
            
            return {
                "employees": {
                    "total": total_employees,
                    "active": active_employees,
                    "on_leave": total_employees - active_employees
                },
                "projects": {
                    "total": total_missions,
                    "active": active_missions,
                    "completed": completed_missions
                },
                "vehicles": {
                    "total": total_vehicles,
                    "available": available_vehicles,
                    "in_use": in_use_vehicles
                },
                "equipment": {
                    "total": total_tools,
                    "operational": available_tools,
                    "maintenance": in_use_tools
                }
            }
        except Exception as e:
            print(f"Get dashboard stats error: {e}")
            return self._get_empty_stats()
    
    def _get_empty_stats(self):
        """Return empty stats structure"""
        return {
            "employees": {"total": 0, "active": 0, "on_leave": 0},
            "projects": {"total": 0, "active": 0, "completed": 0},
            "vehicles": {"total": 0, "available": 0, "in_use": 0},
            "equipment": {"total": 0, "operational": 0, "maintenance": 0}
        }
    
    # ========== DEPARTMENTS ==========
    
    def get_all_departments(self) -> List[Dict]:
        """Get all departments"""
        try:
            if not self.db:
                return []
                
            departments = []
            departments_ref = self.db.collection(self.DEPARTMENTS_COLLECTION)
            
            for doc in departments_ref.stream():
                dept_data = self.to_dict(doc)
                if dept_data:
                    departments.append(dept_data)
            
            return departments
        except Exception as e:
            print(f"Get departments error: {e}")
            return []
    
    def initialize_default_data(self):
        """Initialize default departments and sample data"""
        try:
            if not self.db:
                return False
                
            # Check if departments exist
            departments = list(self.db.collection(self.DEPARTMENTS_COLLECTION).limit(1).stream())
            
            if not departments:
                # Create default departments
                default_departments = [
                    {'id': '1', 'name': 'logistics', 'description': 'Logistics and supply chain management'},
                    {'id': '2', 'name': 'administration', 'description': 'Administrative operations'},
                    {'id': '3', 'name': 'field_operations', 'description': 'Field and terrain operations'},
                    {'id': '4', 'name': 'management', 'description': 'Management and oversight'}
                ]
                
                for dept in default_departments:
                    self.db.collection(self.DEPARTMENTS_COLLECTION).document(dept['id']).set({
                        'name': dept['name'],
                        'description': dept['description'],
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    })
                
                print("Default departments created successfully")
            
            return True
        except Exception as e:
            print(f"Initialize default data error: {e}")
            return False

# Initialize database manager
db = DatabaseManager()

# Initialize default data on startup
db.initialize_default_data()

# Convenience functions for backward compatibility
def login(username: str, password: str) -> Optional[Dict]:
    return db.login(username, password)

def create_user(username: str, full_name: str, password: str, role: str, department_id: int, active: bool = True) -> bool:
    return db.create_user(username, full_name, password, role, department_id, active)

def get_dashboard_stats() -> Dict:
    return db.get_dashboard_stats()

def get_all_employees() -> List[Dict]:
    return db.get_all_employees()

def get_all_vehicles() -> List[Dict]:
    return db.get_all_vehicles()

def get_all_tools() -> List[Dict]:
    return db.get_all_tools()

def create_mission(mission_data: Dict) -> bool:
    return db.create_mission(mission_data)

def get_recent_activities(limit: int = 10) -> List[Dict]:
    return db.get_recent_activities(limit)

def get_all_missions() -> List[Dict]:
    return db.get_all_missions()

def update_mission_status(mission_id: str, status: str, notes: str = None) -> bool:
    return db.update_mission_status(mission_id, status, notes)

def create_vehicle(vehicle_data: Dict) -> bool:
    db.create_vehicle(vehicle_data) 
    
def create_tool(tool_data: Dict) -> bool:
    db.create_tool(tool_data) 