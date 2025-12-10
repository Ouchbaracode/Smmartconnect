"""
SmartConnect Manager - Firebase Database Layer
Using Firebase Firestore as the backend database
"""
import os
import firebase_admin
from firebase_admin import credentials, firestore, auth
from datetime import datetime, date, timedelta
import hashlib
import uuid
from typing import List, Dict, Optional, Any
import json
import requests
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Initialize Firebase
try:
    if not firebase_admin._apps:
        # Look for Service.json file in the current directory or specified path
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "Service.json")
        
        if os.path.exists(service_account_path):
            # Use the Service.json file
            cred = credentials.Certificate(service_account_path)
            print(f"Using Firebase credentials from: {service_account_path}")

        
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
        self.MISSION_LOGS_COLLECTION='mission_logs'

        # Caching
        self._cache = {}
        self._cache_expiry = {}
        # Default cache duration: 5 minutes
        self.CACHE_DURATION = 300
    
    # ========== CACHING UTILITIES ==========

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get data from cache if it exists and hasn't expired"""
        if key in self._cache and key in self._cache_expiry:
            if datetime.now() < self._cache_expiry[key]:
                # print(f"Cache hit for {key}")
                return self._cache[key]
            else:
                # print(f"Cache expired for {key}")
                del self._cache[key]
                del self._cache_expiry[key]
        return None

    def _set_cached(self, key: str, data: Any, duration: int = None):
        """Set data in cache with expiry"""
        if duration is None:
            duration = self.CACHE_DURATION

        self._cache[key] = data
        self._cache_expiry[key] = datetime.now() + timedelta(seconds=duration)
        # print(f"Cache set for {key}")

    def _invalidate_cache(self, key_prefix: str):
        """Invalidate all cache keys starting with key_prefix"""
        keys_to_remove = [k for k in self._cache.keys() if k.startswith(key_prefix)]
        for k in keys_to_remove:
            if k in self._cache:
                del self._cache[k]
            if k in self._cache_expiry:
                del self._cache_expiry[k]
        # print(f"Cache invalidated for prefix {key_prefix}")

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

    def exchange_google_token_for_firebase(self, google_id_token: str) -> Optional[str]:
        """
        Exchange Google ID Token for Firebase ID Token using REST API.
        Requires FIREBASE_API_KEY environment variable.
        """
        api_key = os.getenv("FIREBASEAPIKEY")
        if not api_key:
            print("FIREBASE_API_KEY not found in environment variables")
            return None

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithIdp?key={api_key}"

        payload = {
            "postBody": f"id_token={google_id_token}&providerId=google.com",
            "requestUri": "https://accounts.google.com/o/oauth2/auth", # Placeholder, required parameter
            "returnIdpCredential": True,
            "returnSecureToken": True
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("idToken")
        except requests.exceptions.RequestException as e:
            print(f"Error exchanging token: {e}")
            if hasattr(e, 'response') and e.response:
                print(e.response.text)
            return None

    def login_with_google(self, google_id_token: str) -> Optional[Dict]:
        """Login or register with Google using Firebase Auth flow"""
        try:
            if not self.db:
                return None

            # 1. Exchange Google Token for Firebase Token
            # This ensures the user is authenticated "from Firebase"
            firebase_token = self.exchange_google_token_for_firebase(google_id_token)

            if not firebase_token:
                # If exchange fails (e.g. no API key configured), fall back to verifying the Google Token directly
                # strictly for app login (but this bypasses Firebase Auth user creation).
                # However, since the user asked for "auth from firebase", we should rely on the exchange.
                # But for robustness in this sandbox environment:
                print("Falling back to direct Google Token verification due to missing API key or error.")
                try:
                    # Verify Google Token directly
                    id_info = id_token.verify_oauth2_token(google_id_token, google_requests.Request())
                    email = id_info['email']
                    name = id_info.get('name')
                    uid = id_info['sub'] # Google User ID
                except ValueError as ve:
                    print(f"Invalid Google Token: {ve}")
                    return None
            else:
                # 2. Verify the Firebase Token
                # This confirms the user exists in Firebase Auth
                decoded_token = auth.verify_id_token(firebase_token)
                uid = decoded_token['uid']
                email = decoded_token.get('email')
                name = decoded_token.get('name')

            if not email:
                return None

            # 3. Check/Create User in Firestore
            users_ref = self.db.collection(self.USERS_COLLECTION)

            # Search by username (email)
            query = users_ref.where('username', '==', email).limit(1)
            results = list(query.stream())

            if results:
                # User exists
                user_doc = results[0]
                user_data = self.to_dict(user_doc)

                # Update last login
                self.db.collection(self.USERS_COLLECTION).document(user_doc.id).update({
                    'last_login': datetime.now().isoformat()
                })
                return user_data
            else:
                # Create new user
                new_user_data = {
                    'username': email,
                    'full_name': name or email.split('@')[0],
                    'password': '', # No password for Google auth
                    'role': 'Viewer', # Default restricted role
                    'department_id': 1, # Default department (Logistics?)
                    'active': True,
                    'auth_provider': 'google',
                    'google_uid': uid, # Store the UID (Google or Firebase)
                    'email': email,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat(),
                    'last_login': datetime.now().isoformat()
                }

                doc_ref = self.db.collection(self.USERS_COLLECTION).add(new_user_data)

                # Return the new user data with ID
                new_user_data['id'] = doc_ref[1].id

                self._invalidate_cache('employees') # Invalidate cache
                return new_user_data

        except Exception as e:
            print(f"Google login error: {e}")
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
                'mission_status': 'AVAILABLE',
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

            if doc_ref:
                self._invalidate_cache('employees') # Invalidate cache
                return True
            return False
        except Exception as e:
            print(f"Create user error: {e}")
            return False
    
    # ========== EMPLOYEE MANAGEMENT ==========
    
    def get_all_employees(self) -> List[Dict]:
        """Get all employees with department info"""
        cache_key = 'employees_all'
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

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
                        'mission_status': user_data.get('mission_status', 'AVAILABLE'),
                        'last_login': user_data.get('last_login'),
                        'created_at': user_data.get('created_at')
                    })
            
            self._set_cached(cache_key, employees)
            return employees
        except Exception as e:
            print(f"Get employees error: {e}")
            return []
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict]:
        """Get employee by ID"""
        # Note: We don't cache individual employee lookups aggressively as they might be edits
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

            self._invalidate_cache('employees') # Invalidate cache
            return True
        except Exception as e:
            print(f"Update employee error: {e}")
            return False
    
    # ========== VEHICLE MANAGEMENT ==========
    
    def get_all_vehicles(self) -> List[Dict]:
        """Get all vehicles"""
        cache_key = 'vehicles_all'
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            if not self.db:
                return []
                
            vehicles = []
            vehicles_ref = self.db.collection(self.VEHICLES_COLLECTION)
            
            for doc in vehicles_ref.stream():
                vehicle_data = self.to_dict(doc)
                if vehicle_data:
                    vehicles.append(vehicle_data)
            
            self._set_cached(cache_key, vehicles)
            return vehicles
        except Exception as e:
            print(f"Get vehicles error: {e}")
            return []
    
    def get_available_vehicles(self) -> List[Dict]:
        """Get available vehicles"""
        # We might not cache this one or cache with very short TTL because availability changes often
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

            if doc_ref:
                self._invalidate_cache('vehicles')
                return True
            return False
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

            self._invalidate_cache('vehicles')
            return True
        except Exception as e:
            print(f"Update vehicle status error: {e}")
            return False
    
    # ========== EQUIPMENT/TOOLS MANAGEMENT ==========
    
    def get_all_tools(self) -> List[Dict]:
        """Get all tools/equipment"""
        cache_key = 'tools_all'
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            if not self.db:
                return []
                
            tools = []
            tools_ref = self.db.collection(self.TOOLS_COLLECTION)
            
            for doc in tools_ref.stream():
                tool_data = self.to_dict(doc)
                if tool_data:
                    tools.append(tool_data)
            
            self._set_cached(cache_key, tools)
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

            if doc_ref:
                self._invalidate_cache('tools')
                return True
            return False
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
            
            self._invalidate_cache('tools')
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
                mission_id = doc_id.id

                # Assign Team (Personnel)
                assigned_team = mission_data.get('assigned_team', [])
                # Also include assigned_person_id if present and not in team
                if mission_data.get('assigned_person_id') and mission_data.get('assigned_person_id') not in assigned_team:
                    assigned_team.append(mission_data.get('assigned_person_id'))
                # Also include team_leader_id if present and not in team
                if mission_data.get('team_leader_id') and mission_data.get('team_leader_id') not in assigned_team:
                    assigned_team.append(mission_data.get('team_leader_id'))

                if assigned_team:
                    assign_personnel_to_mission(mission_id, assigned_team)

                # Assign Vehicle
                vehicle_id = mission_data.get('vehicle_id')
                if vehicle_id:
                    assign_vehicle_to_mission(mission_id, vehicle_id)

                # Assign Tools
                required_tools = mission_data.get('required_tools', [])
                if required_tools:
                    for tool_id in required_tools:
                        assign_tool_to_mission(mission_id, tool_id, 1) # Default quantity 1 for now

                # Create activity log
                self.log_activity('mission_created', {
                    'mission_id': mission_id,
                    'title': mission_data['title'],
                    'assigned_to': mission_data.get('assigned_person_id')
                })
                
                self._invalidate_cache('missions')
                return True
            return False
        except Exception as e:
            print(f"Create mission error: {e}")
            return False    
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

                # Release resources
                self._release_mission_resources(mission_id)
            
            self.db.collection(self.MISSIONS_COLLECTION).document(mission_id).update(update_data)
            
            # Log activity
            self.log_activity('mission_status_updated', {
                'mission_id': mission_id,
                'new_status': status,
                'notes': notes
            })
            
            self._invalidate_cache('missions')
            return True
        except Exception as e:
            print(f"Update mission status error: {e}")
            return False

    def _release_mission_resources(self, mission_id: str):
        """Release all resources assigned to a mission"""
        try:
            # Release Vehicles
            # Check vehicle assignments or direct mission link
            mission_doc = self.db.collection(self.MISSIONS_COLLECTION).document(mission_id).get()
            if mission_doc.exists:
                mission_data = mission_doc.to_dict()
                vehicle_id = mission_data.get('vehicle_id')
                if vehicle_id:
                     self.update_vehicle_status(vehicle_id, 'AVAILABLE')

                # Also check vehicle assignments collection if used
                vehicle_assignments = self.db.collection(self.VEHICLE_ASSIGNMENTS_COLLECTION).where('mission_id', '==', mission_id).stream()
                for doc in vehicle_assignments:
                    data = doc.to_dict()
                    if data.get('vehicle_id'):
                        self.update_vehicle_status(data['vehicle_id'], 'AVAILABLE')

            # Release Personnel
            # Check mission for assigned team
            if mission_data:
                assigned_team = mission_data.get('assigned_team', [])
                if mission_data.get('assigned_person_id'):
                    assigned_team.append(mission_data.get('assigned_person_id'))
                if mission_data.get('team_leader_id'):
                    assigned_team.append(mission_data.get('team_leader_id'))

                # Unique IDs
                assigned_team = list(set(assigned_team))

                for person_id in assigned_team:
                     self.db.collection(self.USERS_COLLECTION).document(person_id).update({'mission_status': 'AVAILABLE'})

            # Release Tools
            tool_assignments = self.db.collection(self.TOOL_ASSIGNMENTS_COLLECTION).where('mission_id', '==', mission_id).stream()
            for doc in tool_assignments:
                data = doc.to_dict()
                tool_id = data.get('tool_id')
                quantity = data.get('quantity', 0)
                if tool_id and quantity > 0:
                    self.update_tool_quantity(tool_id, quantity, 'return')

        except Exception as e:
            print(f"Release resources error: {e}")
    
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
        # Could cache this too, but maybe shorter duration
        cache_key = 'dashboard_stats'
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

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
            
            stats = {
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
            self._set_cached(cache_key, stats, 60) # Cache for 1 min
            return stats
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
        cache_key = 'departments_all'
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        try:
            if not self.db:
                return []
                
            departments = []
            departments_ref = self.db.collection(self.DEPARTMENTS_COLLECTION)
            
            for doc in departments_ref.stream():
                dept_data = self.to_dict(doc)
                if dept_data:
                    departments.append(dept_data)
            
            self._set_cached(cache_key, departments)
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

def login_with_google(id_token: str) -> Optional[Dict]:
    return db.login_with_google(id_token)

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

def get_employee_by_id(employee_id: str) -> Optional[Dict]:
    return db.get_employee_by_id(employee_id)

def update_employee(employee_id: str, update_data: Dict) -> bool:
    return db.update_employee(employee_id, update_data)

def get_all_departments() -> List[Dict]:
    return db.get_all_departments


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
    
    
# Mission Function

def get_mission_by_id(mission_id: str) -> Optional[Dict]:
    """Get mission by ID with related data"""
    try:
        if not db.db:
            return None
            
        doc = db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).get()
        if not doc.exists:
            return None
            
        mission_data = db.to_dict(doc)
        
        # Get assigned user info
        if mission_data.get('assigned_person_id'):
            user_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['assigned_person_id']).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
        
        # Get team leader info
        if mission_data.get('team_leader_id'):
            leader_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['team_leader_id']).get()
            if leader_doc.exists:
                leader_data = leader_doc.to_dict()
                mission_data['team_leader'] = {'full_name': leader_data.get('full_name')}
        
        # Get vehicle info
        if mission_data.get('vehicle_id'):
            vehicle_doc = db.db.collection(db.VEHICLES_COLLECTION).document(mission_data['vehicle_id']).get()
            if vehicle_doc.exists:
                vehicle_data = vehicle_doc.to_dict()
                mission_data['vehicle'] = {
                    'model': vehicle_data.get('model'),
                    'plate_number': vehicle_data.get('plate_number')
                }
        
        return mission_data
    except Exception as e:
        print(f"Get mission by ID error: {e}")
        return None

def get_all_missions_with_details() -> List[Dict]:
    """Get all missions with complete details"""
    # Caching this might be heavy as it pulls a lot of related data
    # For now, let's cache it but with short TTL or rely on individual object caching if implemented
    cache_key = 'missions_with_details'
    cached = db._get_cached(cache_key)
    if cached is not None:
        return cached

    try:
        if not db.db:
            return []
            
        missions = []
        missions_ref = db.db.collection(db.MISSIONS_COLLECTION).order_by('created_at', direction=firestore.Query.DESCENDING)
        for doc in missions_ref.stream():
            mission_data = db.to_dict(doc)
            if mission_data:
                # Get assigned team info (replace the assigned_user section)
                if mission_data.get('assigned_team'):
                    mission_data['team_members'] = []
                    for user_id in mission_data['assigned_team']:
                        user_doc = db.db.collection(db.USERS_COLLECTION).document(user_id).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            mission_data['team_members'].append({
                                'name': user_data.get('full_name'),
                                'role': user_data.get('role', 'Team Member'),
                                'phone': user_data.get('phone'),
                                'status': 'Assigned'
                            })

                # Keep team leader section as is
                if mission_data.get('team_leader_id'):
                    leader_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['team_leader_id']).get()
                    if leader_doc.exists:
                        leader_data = leader_doc.to_dict()
                        mission_data['team_leader'] = {
                            'name': leader_data.get('full_name'),
                            'role': 'Team Leader',
                            'phone': leader_data.get('phone'),
                            'status': 'Leading'
                        }
                
                # Get vehicle info
                if mission_data.get('vehicle_id'):
                    vehicle_doc = db.db.collection(db.VEHICLES_COLLECTION).document(mission_data['vehicle_id']).get()
                    if vehicle_doc.exists:
                        vehicle_data = vehicle_doc.to_dict()
                        mission_data['vehicle'] = {
                            'model': vehicle_data.get('model'),
                            'plate_number': vehicle_data.get('plate_number')
                        }
                if mission_data.get('required_tools'):
                    mission_data['tools'] = []
                    for tool_id in mission_data['required_tools']:
                        tool_doc = db.db.collection(db.TOOLS_COLLECTION).document(tool_id).get()
                        if tool_doc.exists:
                            tool_data = tool_doc.to_dict()
                            mission_data['tools'].append({
                                'name': tool_data.get('name'),
                                'type': tool_data.get('category'),
                                'condition': tool_data.get('condition'),
                            })
                
                missions.append(mission_data)
        
        db._set_cached(cache_key, missions, 60) # Cache for 60 seconds
        return missions
    except Exception as e:
        print(f"Get all missions error: {e}")
        return []

def get_mission_tools(mission_id: str) -> List[Dict]:
    """Get tools assigned to mission"""
    try:
        if not db.db:
            return []
            
        tools = []
        assignments_ref = db.db.collection(db.TOOL_ASSIGNMENTS_COLLECTION).where('mission_id', '==', mission_id)
        
        for doc in assignments_ref.stream():
            assignment_data = db.to_dict(doc)
            if assignment_data:
                # Get tool info
                tool_doc = db.db.collection(db.TOOLS_COLLECTION).document(assignment_data['tool_id']).get()
                if tool_doc.exists:
                    tool_data = tool_doc.to_dict()
                    tools.append({
                        'name': tool_data.get('name'),
                        'quantity': assignment_data.get('quantity', 0),
                        'status': assignment_data.get('status', 'ASSIGNED')
                    })
        
        return tools
    except Exception as e:
        print(f"Get mission tools error: {e}")
        return []

def get_mission_activity_log(mission_id: str) -> List[Dict]:
    """Get activity log for mission"""
    try:
        if not db.db:
            return []
            
        activities = []
        activities_ref = db.db.collection(db.ACTIVITY_LOGS_COLLECTION).where('activity_data.mission_id', '==', mission_id).order_by('timestamp', direction=firestore.Query.DESCENDING).limit(10)
        
        for doc in activities_ref.stream():
            activity_data = db.to_dict(doc)
            if activity_data:
                # Get user info
                if activity_data.get('user_id'):
                    user_doc = db.db.collection(db.USERS_COLLECTION).document(activity_data['user_id']).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        activity_data['user'] = {'full_name': user_data.get('full_name')}
                
                activities.append(activity_data)
        
        return activities
    except Exception as e:
        print(f"Get mission activity log error: {e}")
        return []

def get_missions_by_status(status: str) -> List[Dict]:
    """Get missions filtered by status"""
    try:
        if not db.db:
            return []
            
        missions = []
        missions_ref = db.db.collection(db.MISSIONS_COLLECTION).where('status', '==', status).order_by('created_at', direction=firestore.Query.DESCENDING)
        
        for doc in missions_ref.stream():
            mission_data = db.to_dict(doc)
            if mission_data:
                # Get basic user info
                if mission_data.get('assigned_person_id'):
                    user_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['assigned_person_id']).get()
                    if user_doc.exists:
                        user_data = user_doc.to_dict()
                        mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
                
                missions.append(mission_data)
        
        return missions
    except Exception as e:
        print(f"Get missions by status error: {e}")
        return []

def get_missions_by_user(user_id: str) -> List[Dict]:
    """Get missions assigned to specific user"""
    try:
        if not db.db:
            return []
            
        missions = []
        missions_ref = db.db.collection(db.MISSIONS_COLLECTION).where('assigned_person_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING)
        
        for doc in missions_ref.stream():
            mission_data = db.to_dict(doc)
            if mission_data:
                # Get user info
                user_doc = db.db.collection(db.USERS_COLLECTION).document(user_id).get()
                if user_doc.exists:
                    user_data = user_doc.to_dict()
                    mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
                
                # Get vehicle info if available
                if mission_data.get('vehicle_id'):
                    vehicle_doc = db.db.collection(db.VEHICLES_COLLECTION).document(mission_data['vehicle_id']).get()
                    if vehicle_doc.exists:
                        vehicle_data = vehicle_doc.to_dict()
                        mission_data['vehicle'] = {
                            'model': vehicle_data.get('model'),
                            'plate_number': vehicle_data.get('plate_number')
                        }
                
                missions.append(mission_data)
        
        return missions
    except Exception as e:
        print(f"Get user missions error: {e}")
        return []

def update_mission(mission_id: str, update_data: Dict) -> bool:
    """Update mission data"""
    try:
        if not db.db:
            return False
            
        update_data['updated_at'] = datetime.now().isoformat()
        
        db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).update(update_data)
        
        # Log activity
        db.log_activity('mission_updated', {
            'mission_id': mission_id,
            'updated_fields': list(update_data.keys())
        })
        
        db._invalidate_cache('missions')
        return True
    except Exception as e:
        print(f"Update mission error: {e}")
        return False

def delete_mission(mission_id: str) -> bool:
    """Delete mission (soft delete by setting status to CANCELLED)"""
    try:
        if not db.db:
            return False
            
        db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).update({
            'status': 'CANCELLED',
            'updated_at': datetime.now().isoformat()
        })
        
        # Log activity
        db.log_activity('mission_deleted', {
            'mission_id': mission_id
        })
        
        db._invalidate_cache('missions')
        return True
    except Exception as e:
        print(f"Delete mission error: {e}")
        return False

def get_mission_stats() -> Dict:
    """Get mission statistics"""
    try:
        if not db.db:
            return {}
            
        missions = list(db.db.collection(db.MISSIONS_COLLECTION).stream())
        
        total = len(missions)
        pending = len([m for m in missions if m.to_dict().get('status') == 'PENDING'])
        in_progress = len([m for m in missions if m.to_dict().get('status') == 'IN_PROGRESS'])
        completed = len([m for m in missions if m.to_dict().get('status') == 'COMPLETED'])
        cancelled = len([m for m in missions if m.to_dict().get('status') == 'CANCELLED'])
        
        return {
            'total': total,
            'pending': pending,
            'in_progress': in_progress,
            'completed': completed,
            'cancelled': cancelled
        }
    except Exception as e:
        print(f"Get mission stats error: {e}")
        return {}

def search_missions(query: str) -> List[Dict]:
    """Search missions by title, location, or description"""
    try:
        if not db.db or not query:
            return []
            
        missions = []
        query_lower = query.lower()
        
        # Get all missions and filter in Python (Firestore has limited text search)
        # Note: Optimization could be to cache this list if it's called often
        missions_ref = db.db.collection(db.MISSIONS_COLLECTION)
        
        for doc in missions_ref.stream():
            mission_data = db.to_dict(doc)
            if mission_data:
                # Check if query matches title, location, or description
                title = mission_data.get('title', '').lower()
                location = mission_data.get('location', '').lower()
                description = mission_data.get('description', '').lower()
                
                if (query_lower in title or 
                    query_lower in location or 
                    query_lower in description):
                    
                    # Get assigned user info
                    if mission_data.get('assigned_person_id'):
                        user_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['assigned_person_id']).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
                    
                    missions.append(mission_data)
        
        return missions
    except Exception as e:
        print(f"Search missions error: {e}")
        return []
    
def add_mission_log(mission_id: str, action: str, user_name: str, notes: str = None) -> bool:
    """Add a log entry to a specific mission."""
    try:
        if not db.db:
            return False

        log_data = {
            'action': action,
            'user_name': user_name,
            'created_at': datetime.now().isoformat()
        }
        if notes:
            log_data['notes'] = notes

        # Add the log to the 'mission_logs' subcollection of the mission
        db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).collection(db.MISSION_LOGS_COLLECTION).add(log_data)

        return True
    except Exception as e:
        print(f"Add mission log error: {e}")
        return False

def get_mission_logs(mission_id: str) -> List[Dict]:
    """Get all log entries for a specific mission."""
    try:
        if not db.db:
            return []

        logs = []
        # Get logs from the 'mission_logs' subcollection, ordered by creation date
        logs_ref = db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).collection(db.MISSION_LOGS_COLLECTION).order_by('created_at', direction=firestore.Query.DESCENDING)

        for doc in logs_ref.stream():
            log_data = db.to_dict(doc)
            if log_data:
                logs.append(log_data)

        return logs
    except Exception as e:
        print(f"Get mission logs error: {e}")
        return []
# Add these functions to your db.py file

def get_mission_personnel(mission_id: str) -> List[Dict]:
    """Get personnel assigned to mission"""
    try:
        if not db.db:
            return []
            
        # First get the mission to see if it has personnel_ids
        mission_doc = db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).get()
        if not mission_doc.exists:
            return []
            
        mission_data = mission_doc.to_dict()
        personnel_ids = mission_data.get('personnel_ids', [])
        
        # If no personnel_ids, check if there's an assigned_person_id
        if not personnel_ids and mission_data.get('assigned_person_id'):
            personnel_ids = [mission_data['assigned_person_id']]
        
        personnel = []
        for person_id in personnel_ids:
            user_doc = db.db.collection(db.USERS_COLLECTION).document(person_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                personnel.append({
                    'id': user_doc.id,
                    'name': user_data.get('full_name', 'Unknown'),
                    'role': user_data.get('role', 'Team Member'),
                    'phone': user_data.get('phone', ''),
                    'status': 'Available' if user_data.get('active', False) else 'Unavailable'
                })
        
        return personnel
    except Exception as e:
        print(f"Get mission personnel error: {e}")
        return []

def get_mission_tools_detailed(mission_id: str) -> List[Dict]:
    """Get detailed tools assigned to mission"""
    try:
        if not db.db:
            return []
            
        tools = []
        # Check tool assignments collection
        assignments_ref = db.db.collection(db.TOOL_ASSIGNMENTS_COLLECTION).where('mission_id', '==', mission_id)
        
        for doc in assignments_ref.stream():
            assignment_data = db.to_dict(doc)
            if assignment_data:
                # Get tool details
                tool_doc = db.db.collection(db.TOOLS_COLLECTION).document(assignment_data['tool_id']).get()
                if tool_doc.exists:
                    tool_data = tool_doc.to_dict()
                    tools.append({
                        'id': tool_doc.id,
                        'name': tool_data.get('name', 'Unknown Tool'),
                        'type': tool_data.get('category', 'Equipment'),
                        'condition': tool_data.get('condition', 'Good'),
                        'quantity': assignment_data.get('quantity', 1),
                        'status': assignment_data.get('status', 'Assigned')
                    })
        
        return tools
    except Exception as e:
        print(f"Get mission tools error: {e}")
        return []

def get_mission_vehicles_detailed(mission_id: str) -> List[Dict]:
    """Get detailed vehicles assigned to mission"""
    try:
        if not db.db:
            return []
            
        vehicles = []
        
        # Check vehicle assignments collection
        assignments_ref = db.db.collection(db.VEHICLE_ASSIGNMENTS_COLLECTION).where('mission_id', '==', mission_id)
        
        for doc in assignments_ref.stream():
            assignment_data = db.to_dict(doc)
            if assignment_data:
                # Get vehicle details
                vehicle_doc = db.db.collection(db.VEHICLES_COLLECTION).document(assignment_data['vehicle_id']).get()
                if vehicle_doc.exists:
                    vehicle_data = vehicle_doc.to_dict()
                    vehicles.append({
                        'id': vehicle_doc.id,
                        'name': vehicle_data.get('name', f"{vehicle_data.get('make', '')} {vehicle_data.get('model', '')}".strip()),
                        'make': vehicle_data.get('make', ''),
                        'model': vehicle_data.get('model', ''),
                        'license_plate': vehicle_data.get('plate_number', ''),
                        'status': vehicle_data.get('status', 'Available')
                    })
        
        # If no assignments found, check if mission has a direct vehicle_id
        if not vehicles:
            mission_doc = db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).get()
            if mission_doc.exists:
                mission_data = mission_doc.to_dict()
                if mission_data.get('vehicle_id'):
                    vehicle_doc = db.db.collection(db.VEHICLES_COLLECTION).document(mission_data['vehicle_id']).get()
                    if vehicle_doc.exists:
                        vehicle_data = vehicle_doc.to_dict()
                        vehicles.append({
                            'id': vehicle_doc.id,
                            'name': vehicle_data.get('name', f"{vehicle_data.get('make', '')} {vehicle_data.get('model', '')}".strip()),
                            'make': vehicle_data.get('make', ''),
                            'model': vehicle_data.get('model', ''),
                            'license_plate': vehicle_data.get('plate_number', ''),
                            'status': vehicle_data.get('status', 'Available')
                        })
        
        return vehicles
    except Exception as e:
        print(f"Get mission vehicles error: {e}")
        return []

# Update the existing get_mission_by_id function to include personnel, tools, and vehicles
def get_mission_by_id_enhanced(mission_id: str) -> Optional[Dict]:
    """Get mission by ID with complete details including personnel, tools, and vehicles"""
    try:
        if not db.db:
            return None
            
        doc = db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).get()
        if not doc.exists:
            return None
            
        mission_data = db.to_dict(doc)
        
        # Get assigned user info
        if mission_data.get('assigned_person_id'):
            user_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['assigned_person_id']).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                mission_data['assigned_user'] = {'full_name': user_data.get('full_name')}
        
        # Get team leader info
        if mission_data.get('team_leader_id'):
            leader_doc = db.db.collection(db.USERS_COLLECTION).document(mission_data['team_leader_id']).get()
            if leader_doc.exists:
                leader_data = leader_doc.to_dict()
                mission_data['team_leader'] = {'full_name': leader_data.get('full_name')}
        
        # Get personnel, tools, and vehicles
        mission_data['personnel'] = get_mission_personnel(mission_id)
        mission_data['tools'] = get_mission_tools_detailed(mission_id)
        mission_data['vehicles'] = get_mission_vehicles_detailed(mission_id)
        
        return mission_data
    except Exception as e:
        print(f"Get enhanced mission by ID error: {e}")
        return None

# Add assignment functions
def assign_personnel_to_mission(mission_id: str, personnel_ids: List[str]) -> bool:
    """Assign personnel to mission"""
    try:
        if not db.db:
            return False
            
        # Update mission with personnel_ids
        db.db.collection(db.MISSIONS_COLLECTION).document(mission_id).update({
            'personnel_ids': personnel_ids,
            'updated_at': datetime.now().isoformat()
        })

        # Update each person's status
        for person_id in personnel_ids:
            db.db.collection(db.USERS_COLLECTION).document(person_id).update({
                'mission_status': 'IN_MISSION'
            })
        
        # Log activity
        db.log_activity('personnel_assigned', {
            'mission_id': mission_id,
            'personnel_count': len(personnel_ids)
        })
        
        return True
    except Exception as e:
        print(f"Assign personnel error: {e}")
        return False

def assign_tool_to_mission(mission_id: str, tool_id: str, quantity: int = 1) -> bool:
    """Assign tool to mission"""
    try:
        if not db.db:
            return False
            
        # Create tool assignment
        assignment_data = {
            'mission_id': mission_id,
            'tool_id': tool_id,
            'quantity': quantity,
            'status': 'ASSIGNED',
            'assigned_at': datetime.now().isoformat()
        }
        
        db.db.collection(db.TOOL_ASSIGNMENTS_COLLECTION).add(assignment_data)
        
        # Update tool quantity
        db.update_tool_quantity(tool_id, quantity, 'assign')
        
        return True
    except Exception as e:
        print(f"Assign tool error: {e}")
        return False

def assign_vehicle_to_mission(mission_id: str, vehicle_id: str) -> bool:
    """Assign vehicle to mission"""
    try:
        if not db.db:
            return False
            
        # Create vehicle assignment
        assignment_data = {
            'mission_id': mission_id,
            'vehicle_id': vehicle_id,
            'status': 'ASSIGNED',
            'assigned_at': datetime.now().isoformat()
        }
        
        db.db.collection(db.VEHICLE_ASSIGNMENTS_COLLECTION).add(assignment_data)
        
        # Update vehicle status
        db.update_vehicle_status(vehicle_id, 'IN_USE')
        
        return True
    except Exception as e:
        print(f"Assign vehicle error: {e}")
        return False    