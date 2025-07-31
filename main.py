import flet as ft
from datetime import datetime 
import time 
# Updated imports to use the new database
from db import (
    login as db_login, 
    create_user, 
    get_dashboard_stats,
    get_all_employees,
    get_all_vehicles, 
    get_all_tools,
    create_mission,
    get_recent_activities,
    get_all_missions,
    update_mission_status,
    create_tool,
    create_vehicle,
    db,  # Import the database manager instance
)

def dashboard_router(page: ft.Page):
    """Main dashboard router function with all functionality inside"""
    
    # Initialize page settings
    page.title = "SmartConnect Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400   
    page.window.height = 780 
    page.padding = 5 
    page.bgcolor = "#f5f5f5"
    page.scroll = ft.ScrollMode.AUTO
    
    # Colors
    GOLD = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#0F0F0F"
    
    # Global variables for data caching
    dashboard_data = {}
    employees_data = []
    vehicles_data = []
    tools_data = []
    global current_user
    current_user = None  # Store logged-in user info

    def refresh_dashboard_data():
        """Refresh dashboard statistics from database"""
        nonlocal dashboard_data
        try:
            dashboard_data = get_dashboard_stats()
        except Exception as e:
            print(f"Error refreshing dashboard data: {e}")
            # Fallback to empty data
            dashboard_data = {
                "employees": {"total": 0, "active": 0, "on_leave": 0},
                "projects": {"total": 0, "active": 0, "completed": 0},
                "vehicles": {"total": 0, "available": 0, "in_use": 0},
                "equipment": {"total": 0, "operational": 0, "maintenance": 0}
            }
    
    def refresh_employees_data():
        """Refresh employees data from database"""
        nonlocal employees_data
        try:
            employees_data = get_all_employees()
        except Exception as e:
            print(f"Error refreshing employees data: {e}")
            employees_data = []
    
    def refresh_vehicles_data():
        """Refresh vehicles data from database"""
        nonlocal vehicles_data
        try:
            vehicles_data = get_all_vehicles()
            # Transform database format to match UI expectations
            for vehicle in vehicles_data:
                vehicle['plate'] = vehicle.get('plate_number', 'Unknown')
                vehicle['last_updated'] = vehicle.get('last_updated', 'Unknown')
        except Exception as e:
            print(f"Error refreshing vehicles data: {e}")
            vehicles_data = []
    
    def refresh_tools_data():
        """Refresh tools data from database"""
        nonlocal tools_data
        try:
            tools_data = get_all_tools()
            # Transform database format to match UI expectations
            for tool in tools_data:
                tool['quantity'] = tool.get('total_quantity', 0)
                tool['available'] = tool.get('available_quantity', 0)
                tool['in_use'] = tool['quantity'] - tool['available']
                tool['icon'] = ft.Icons.BUILD  # Default icon
        except Exception as e:
            print(f"Error refreshing tools data: {e}")
            tools_data = []

    def go_to(route):
        """Navigate to a route"""
        page.go(route)
    
    def create_app_bar(title, show_nav=True, actions=None):
        """Create app bar with consistent styling"""
        leading = None
        if not show_nav:
            leading = ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda _: go_to("/dashboard")
            )
        
        return ft.AppBar(
            leading=leading,
            leading_width=40,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=WHITE,
            actions=actions or []
        )
    
    def show_snackbar(message, color=ft.Colors.RED):
        snackbar = ft.SnackBar(
            content=ft.Text(message, color=WHITE),
            bgcolor=color,
            duration=3000
        )
        page.overlay.append(snackbar)
        snackbar.open = True 
        page.update() 
            
    def create_bottom_nav(selected_index=0):
        """Create bottom navigation bar"""
        def on_nav_change(e):
            index = e.control.selected_index
            routes = ["/dashboard", "/employees", "/tools", "/settings"]
            if index < len(routes):
                go_to(routes[index])
        
        return ft.NavigationBar(
            selected_index=selected_index,
            destinations=[
                ft.NavigationBarDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
                ft.NavigationBarDestination(icon=ft.Icons.SUPERVISOR_ACCOUNT_ROUNDED, label="Employés"),
                ft.NavigationBarDestination(icon=ft.Icons.BUILD, label="Tools"),
                ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Settings")
            ],
            on_change=on_nav_change
        )
    
    def create_header():
        """Create dashboard header"""
        user_name = current_user.get('full_name', 'Unknown User') if current_user else 'Guest'
        user_role = current_user.get('role', 'User').title() if current_user else 'Guest'
        current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("SmartConnect Manager", size=23, weight=ft.FontWeight.BOLD, color=GOLD),
                    ft.Text(f"Connecté en tant que: {user_role}", size=14, color="#64748b"),
                    ft.Text(f"Utilisateur: {user_name}", size=12, color="#94a3b8"),
                    ft.Text(f"Dernière mise à jour: {current_time}", size=12, color="#94a3b8")
                ], spacing=5),
            ]),
            padding=20,
            bgcolor=WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color="#e2e8f0")
        )
    
    def create_stat_card(title, total, active, inactive, color):
        """Create individual stat card"""
        return ft.Container( 
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ANALYTICS, color=color, size=20),
                    ft.Text(title, size=14, weight=ft.FontWeight.BOLD, color="#1e293b")
                ], alignment=ft.MainAxisAlignment.START),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Text(f"Total: {total}", size=12, color="#64748b"),
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"Actifs: {active}", size=9, color=WHITE),
                        padding=5,
                        bgcolor="#10b981",
                        border_radius=5
                    ),
                    ft.Container(
                        content=ft.Text(f"Inactifs: {inactive}", size=9, color=WHITE),
                        padding=5,
                        bgcolor="#ef4444",
                        border_radius=5
                    )
                ], spacing=5)
            ], spacing=5),
            padding=20,
            bgcolor=WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color="#e2e8f0"),
            width=160,
            height=130
        )
    
    def create_stats_section():
        """Create stats cards section using real data"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    create_stat_card("Employés", dashboard_data["employees"]["total"], 
                                   dashboard_data["employees"]["active"], dashboard_data["employees"]["on_leave"], "#3b82f6"),
                    create_stat_card("Projets", dashboard_data["projects"]["total"], 
                                   dashboard_data["projects"]["active"], dashboard_data["projects"]["completed"], "#10b981")
                ]),
                ft.Column([
                    create_stat_card("Véhicules", dashboard_data["vehicles"]["total"], 
                                   dashboard_data["vehicles"]["available"], dashboard_data["vehicles"]["in_use"], "#f59e0b"),
                    create_stat_card("Équipements", dashboard_data["equipment"]["total"], 
                                   dashboard_data["equipment"]["operational"], dashboard_data["equipment"]["maintenance"], "#8b5cf6")
                ])
            ]),
            margin=ft.margin.only(top=20, left=13)
        )
    
    def create_quick_actions(handle_action):
        """Create quick actions section"""
        actions = [
            {"title": "Ajouter Employé", "icon": ft.Icons.PERSON_ADD, "color": "#3b82f6"},
            {"title": "Nouveau Projet", "icon": ft.Icons.ADD_TASK, "color": "#10b981"},
            {"title": "View All Car", "icon": ft.Icons.DIRECTIONS_CAR, "color": "#f59e0b"},
            {"title": "Add New Car", "icon": ft.Icons.CAR_CRASH_ROUNDED, "color": "#8b5cf6"}
        ]
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Actions Rapides :", size=18, weight=ft.FontWeight.BOLD, color="#1e293b", text_align="CENTER"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Column([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(action["icon"], color=action["color"]),
                            ft.Text(action["title"], color="#1e293b")
                        ], spacing=10),
                        on_click=lambda e, title=action["title"]: handle_action(title),
                        style=ft.ButtonStyle(
                            bgcolor="#f8fafc",
                            color="#1e293b",
                            elevation=2
                        ),
                        width=350
                    ) for action in actions
                ], spacing=10)
            ], spacing=15),
            padding=20,
            bgcolor=WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color="#e2e8f0"),
            width=350
        )
    
    def create_recent_activities():
        """Create recent activities section using real data"""
        try:
            activities_data = get_recent_activities(4)  # Get 4 recent activities
            
            if not activities_data:
                # Fallback activities if database is empty
                activities_data = [
                    {"activity_type": "login", "timestamp": datetime.now().isoformat(), "activity_data": {"message": "No recent activities"}},
                ]
        except Exception as e:
            print(f"Error getting activities: {e}")
            activities_data = [
                {"activity_type": "error", "timestamp": datetime.now().isoformat(), "activity_data": {"message": "Error loading activities"}},
            ]
        
        def get_activity_display(activity):
            """Convert database activity to display format"""
            activity_type = activity.get('activity_type', 'Unknown')
            activity_data = activity.get('activity_data', {})
            timestamp = activity.get('timestamp', '')
            
            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.now() - dt.replace(tzinfo=None)
                
                if time_diff.days > 0:
                    time_str = f"Il y a {time_diff.days} jour(s)"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"Il y a {hours}h"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    time_str = f"Il y a {minutes} min"
                else:
                    time_str = "Maintenant"
            except:
                time_str = "Récemment"
            
            # Format activity message based on type
            if activity_type == 'mission_created':
                message = f"Mission créée: {activity_data.get('title', 'Unknown')}"
                activity_type_display = "success"
            elif activity_type == 'mission_status_updated':
                message = f"Mission mise à jour: {activity_data.get('new_status', 'Unknown')}"
                activity_type_display = "info"
            elif activity_type == 'user_login':
                message = f"Connexion utilisateur: {activity_data.get('username', 'Unknown')}"
                activity_type_display = "info"
            else:
                message = activity_data.get('message', f'Activité: {activity_type}')
                activity_type_display = "info"
            
            return {
                "action": message,
                "time": time_str,
                "type": activity_type_display
            }
        
        activities = [get_activity_display(activity) for activity in activities_data]
        
        def get_activity_color(activity_type):
            colors = {
                "info": "#3b82f6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444"
            }
            return colors.get(activity_type, "#64748b")
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Activités Récentes :", size=18, weight=ft.FontWeight.BOLD, color="#1e293b"),
                ft.Divider(height=1, color="#e2e8f0"),
                ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Container(
                                width=4,
                                height=40,
                                bgcolor=get_activity_color(activity["type"]),
                                border_radius=2
                            ),
                            ft.Column([
                                ft.Text(activity["action"], size=14, color="#1e293b"),
                                ft.Text(activity["time"], size=12, color="#64748b")
                            ], spacing=2, expand=True)
                        ], spacing=10),
                        padding=10,
                        bgcolor="#f8fafc",
                        border_radius=8,
                        margin=ft.margin.only(bottom=5)
                    ) for activity in activities
                ], spacing=5, scroll=ft.ScrollMode.AUTO, height=300)
            ], spacing=15),
            padding=20,
            bgcolor=WHITE,
            border_radius=10,
            shadow=ft.BoxShadow(blur_radius=5, color="#e2e8f0"),
            expand=True
        )
    
    def handle_quick_action(title):
        """Handle quick action clicks"""
        if title == "Nouveau Projet":
            go_to("/add-mission")
        elif title == "Ajouter Employé":
            go_to("/adduser")
        elif title == "View All Car":
            go_to("/cars")
        else:
            go_to("/add-vehicle")
            # Show snackbar for other actions
            
    # ========== VIEW FUNCTIONS ==========
    
    def dashboard_view():
        """Dashboard view"""
        # Refresh data when dashboard loads
        refresh_dashboard_data()
        
        content = ft.Column([
            create_header(),
            create_stats_section(),
            create_quick_actions(handle_quick_action),
            create_recent_activities(),
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        return ft.View(
            route="/dashboard",
            appbar=create_app_bar(
                "Dashboard",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, 
                        tooltip="Refresh Data", 
                        on_click=lambda e: refresh_all_data()
                    ),
                    ft.IconButton(
                        icon=ft.Icons.LOGOUT, 
                        tooltip="Logout", 
                        on_click=lambda e: logout_user()
                    )
                ]
            ),
            navigation_bar=create_bottom_nav(0),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    margin=ft.margin.only(left=15)
                )
            ]
        )
    
    def employees_view():
        """Create and return the complete employee management content using real data"""  
        # Refresh employees data
        refresh_employees_data()
        
        # Create employee card
        def create_employee_card(employee_data):
            # Status color mapping
            status_colors = {
                "ACTIVE": ft.Colors.GREEN,
                "ON LEAVE": ft.Colors.ORANGE,
                "INACTIVE": ft.Colors.RED
            }
            
            # Department icon mapping
            department_icons = {
                "logistic": ft.Icons.LOCAL_SHIPPING,
                "administration": ft.Icons.ADMIN_PANEL_SETTINGS,
                "terrain": ft.Icons.ENGINEERING,
                "admin": ft.Icons.SUPERVISOR_ACCOUNT,
                "default": ft.Icons.WORK
            }
            
            def view_employee(e):
                print(f"Viewing employee: {employee_data['name']}")
                # Here you could navigate to a detailed employee view
            
            def edit_employee(e):
                print(f"Editing employee: {employee_data['name']}")
                # Here you could navigate to an employee edit form
            
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        # Header row with name and status
                        ft.Row([
                            ft.Text(
                                employee_data["name"],
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                expand=True
                            ),
                            ft.Container(
                                content=ft.Text(
                                    employee_data["status"],
                                    size=12,
                                    color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.BOLD
                                ),
                                bgcolor=status_colors.get(employee_data["status"], ft.Colors.GREY),
                                border_radius=12,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4)
                            )
                        ]),
                        
                        # Department and role row
                        ft.Row([
                            ft.Icon(
                                department_icons.get(employee_data["department"].lower(), department_icons["default"]),
                                size=20,
                                color=ft.Colors.BLUE_GREY_600
                            ),
                            ft.Column([
                                ft.Text(
                                    employee_data["role"].replace('_', ' ').title(),
                                    size=14,
                                    weight=ft.FontWeight.W_500
                                ),
                                ft.Text(
                                    employee_data["department"].title(),
                                    size=12,
                                    color=ft.Colors.GREY_600
                                )
                            ], spacing=0, expand=True)
                        ]),
                        
                        # Last login info
                        ft.Row([
                            ft.Icon(ft.Icons.LOGIN, size=16, color=ft.Colors.GREY_500),
                            ft.Text(
                                f"Dernière connexion: {employee_data.get('last_login', 'Jamais') or 'Jamais'}",
                                size=10,
                                color=ft.Colors.GREY_500
                            )
                        ]),
                        
                        # Action buttons
                        ft.Row([
                            ft.ElevatedButton(
                                "View",
                                icon=ft.Icons.VISIBILITY,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_50,
                                    color=ft.Colors.BLUE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=view_employee
                            ),
                            ft.ElevatedButton(
                                "Edit",
                                icon=ft.Icons.EDIT,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREY_50,
                                    color=ft.Colors.GREY_700,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=edit_employee
                            )
                        ], alignment=ft.MainAxisAlignment.END)
                    ], spacing=8),
                    padding=16
                ),
                elevation=2,
                margin=ft.margin.only(bottom=8)
            )
        
        # Filter employees function
        def filter_employees(employees, search_term="", department="", status=""):
            filtered = employees.copy()
            
            if search_term:
                filtered = [emp for emp in filtered if search_term.lower() in emp["name"].lower() or 
                        search_term.lower() in emp["role"].lower()]
            
            if department and department != "All Departments":
                filtered = [emp for emp in filtered if emp["department"].lower() == department.lower()]
            
            if status and status != "All Status":
                filtered = [emp for emp in filtered if emp["status"] == status]
            
            return filtered
        
        # Initialize filtered data
        filtered_employees = employees_data.copy()
        
        # Get unique departments from database
        departments = list(set([emp["department"].title() for emp in employees_data]))
        departments.sort()
        
        # Create UI components
        search_field = ft.TextField(
            hint_text="Search employees...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            bgcolor=ft.Colors.WHITE
        )
        
        department_options = [ft.dropdown.Option("All Departments")] + [ft.dropdown.Option(dept) for dept in departments]
        department_filter = ft.Dropdown(
            options=department_options,
            value="All Departments",
            width=185,
            bgcolor=ft.Colors.WHITE,
            border_radius=12
        )
        
        status_filter = ft.Dropdown(
            options=[
                ft.dropdown.Option("All Status"),
                ft.dropdown.Option("ACTIVE"),
                ft.dropdown.Option("INACTIVE")
            ],
            value="All Status",
            width=135,
            bgcolor=ft.Colors.WHITE,
            border_radius=12
        )
        
        employee_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)
        employee_count = ft.Container(
            content=ft.Text(
                f"Total: {len(filtered_employees)} employees",
                size=14,
                color=ft.Colors.GREY_600
            ),
            margin=ft.margin.only(top=8, bottom=8)
        )
        
        # Update employee list function
        def update_employee_list(page=None):
            nonlocal filtered_employees
            filtered_employees = filter_employees(
                employees_data,
                search_field.value or "",
                department_filter.value,
                status_filter.value
            )
            
            employee_list.controls.clear()
            
            if not filtered_employees:
                employee_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=64, color=ft.Colors.GREY_400),
                            ft.Text("No employees found", size=16, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        height=200
                    )
                )
            else:
                for employee in filtered_employees:
                    employee_list.controls.append(create_employee_card(employee))
            
            employee_count.content.value = f"Total: {len(filtered_employees)} employees"
            
            # Update the page if provided
            if page:
                page.update()
            
        # Add event handlers
        def on_search_change(e):
            update_employee_list(page)
        
        def on_department_change(e):
            update_employee_list(page)
        
        def on_status_change(e):
            update_employee_list(page)
        
        search_field.on_change = on_search_change
        department_filter.on_change = on_department_change
        status_filter.on_change = on_status_change
        
        # Initial load
        update_employee_list()
        
        # Return the complete content
        content = ft.Column([
            # Search
            search_field,
            
            # Filters and Add button
            ft.Row([
                department_filter,
                status_filter
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Employee count
            employee_count,
            
            # Employee list
            ft.Container(
                content=employee_list,
                expand=True
            )
        ], spacing=12)

        return ft.View(
            route="/employees",
            appbar=create_app_bar(
                "Employés",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, 
                        tooltip="Refresh", 
                    ),
                    ft.IconButton(
                        icon=ft.Icons.PERSON_ADD, 
                        tooltip="Add Employee", 
                        icon_color="#3b82f6",
                        on_click=lambda e: go_to("/adduser")
                    )
                ]
            ),
            navigation_bar=create_bottom_nav(1),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    margin=ft.margin.only(left=15)
                )
            ]
        )
        
        def refresh_employees_and_update():
            """Refresh employees data and update the view"""
            refresh_employees_data()
            update_employee_list(page)
            show_snackbar("Données actualisées", ft.Colors.GREEN)
    
    def tools_view():
        """Create and return the complete tools management content using real data"""
        
        # Refresh tools data
        refresh_tools_data()
        
        # Get status color
        def get_status_color(available, total):
            if available == 0:
                return ft.Colors.RED  # All in use
            elif available == total:
                return ft.Colors.GREEN  # All available
            else:
                return ft.Colors.ORANGE  # Partially available
        
        def get_status_text(available, total):
            if available == 0:
                return "All In Use"
            elif available == total:
                return "Available"
            else:
                return "Partially Available"
        
        # Create tool card
        def create_tool_card(tool):
            def show_tool_details(e):
                show_tool_dialog(tool)
            
            def quick_assign(e):
                print(f"Quick assign tool: {tool['name']}")
                # Here you would implement tool assignment logic
            
            status = get_status_text(tool['available'], tool['quantity'])
            status_color = get_status_color(tool['available'], tool['quantity'])
            
            # Status badge
            status_badge = ft.Container(
                content=ft.Text(
                    status,
                    size=10,
                    color=ft.Colors.WHITE,
                    weight=ft.FontWeight.BOLD
                ),
                bgcolor=status_color,
                border_radius=8,
                padding=ft.padding.symmetric(horizontal=6, vertical=2)
            )
            
            # Availability info
            availability_text = f"{tool['available']}/{tool['quantity']} Available"
            availability_color = ft.Colors.GREEN if tool['available'] > 0 else ft.Colors.RED
            
            return ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        # Header row
                        ft.Row([
                            ft.Container(
                                content=ft.Icon(tool.get("icon", ft.Icons.BUILD), size=32, color=ft.Colors.WHITE),
                                width=50,
                                height=50,
                                bgcolor=ft.Colors.BLUE,
                                border_radius=12,
                                alignment=ft.alignment.center
                            ),
                            ft.Column([
                                ft.Text(
                                    tool["name"],
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    expand=True
                                ),
                                ft.Text(
                                    tool.get("model", "N/A"),
                                    size=12,
                                    color=ft.Colors.GREY_600
                                ),
                                ft.Text(
                                    availability_text,
                                    size=12,
                                    color=availability_color,
                                    weight=ft.FontWeight.W_500
                                )
                            ], spacing=2, expand=True),
                            ft.Column([
                                status_badge
                            ], horizontal_alignment=ft.CrossAxisAlignment.END)
                        ]),
                        
                        # Info row
                        ft.Row([
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.GREY_600),
                                    ft.Text(tool.get("location", "Unknown"), size=12, color=ft.Colors.GREY_600)
                                ]),
                                expand=True
                            ),
                            ft.Container(
                                content=ft.Text(
                                    tool.get("condition", "Good"),
                                    size=12,
                                    color=ft.Colors.BLUE,
                                    weight=ft.FontWeight.W_500
                                )
                            )
                        ]),
                        
                        # Action buttons
                        ft.Row([
                            ft.ElevatedButton(
                                "Details",
                                icon=ft.Icons.INFO,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.BLUE_50,
                                    color=ft.Colors.BLUE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=show_tool_details
                            ),
                            ft.ElevatedButton(
                                "Assign" if tool['available'] > 0 else "Reserve",
                                icon=ft.Icons.ASSIGNMENT if tool['available'] > 0 else ft.Icons.SCHEDULE,
                                style=ft.ButtonStyle(
                                    bgcolor=ft.Colors.GREEN_50 if tool['available'] > 0 else ft.Colors.ORANGE_50,
                                    color=ft.Colors.GREEN if tool['available'] > 0 else ft.Colors.ORANGE,
                                    shape=ft.RoundedRectangleBorder(radius=8)
                                ),
                                on_click=quick_assign,
                                disabled=tool['available'] == 0
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                    ], spacing=12),
                    padding=16,
                    on_click=show_tool_details
                ),
                elevation=2,
                margin=ft.margin.only(bottom=12)
            )
        
        # Tool detail dialog
        def show_tool_dialog(tool):
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            def assign_tool(e):
                print(f"Assigning tool: {tool['name']}")
                close_dialog(e)
            
            def schedule_maintenance(e):
                print(f"Scheduling maintenance for: {tool['name']}")
                close_dialog(e)
            
            dialog = ft.AlertDialog(
                title=ft.Text(tool["name"], weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(tool.get("icon", ft.Icons.BUILD), size=48, color=ft.Colors.BLUE),
                            ft.Column([
                                ft.Text(f"Model: {tool.get('model', 'N/A')}", size=14),
                                ft.Text(f"Serial: {tool.get('serial_number', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"Condition: {tool.get('condition', 'Good')}", size=12, color=ft.Colors.BLUE)
                            ], spacing=4, expand=True)
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Total Quantity:", weight=ft.FontWeight.BOLD),
                            ft.Text(str(tool['quantity']))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Available:", weight=ft.FontWeight.BOLD),
                            ft.Text(str(tool['available']), color=ft.Colors.GREEN if tool['available'] > 0 else ft.Colors.RED)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("In Use:", weight=ft.FontWeight.BOLD),
                            ft.Text(str(tool['in_use']), color=ft.Colors.ORANGE if tool['in_use'] > 0 else ft.Colors.GREY)
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Location:", weight=ft.FontWeight.BOLD),
                            ft.Text(tool.get('location', 'Unknown'))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Divider(),
                        ft.Text("Calibration Info:", weight=ft.FontWeight.BOLD),
                        ft.Text(f"Last: {tool.get('last_calibration', 'N/A')}", size=12),
                        ft.Text(f"Next: {tool.get('next_calibration', 'N/A')}", size=12),
                    ], spacing=8),
                    width=300,
                    height=400
                ),
                actions=[
                    ft.TextButton("Close", on_click=close_dialog),
                    ft.ElevatedButton(
                        "Assign Tool",
                        icon=ft.Icons.ASSIGNMENT,
                        on_click=assign_tool,
                        disabled=tool['available'] == 0
                    ),
                    ft.ElevatedButton(
                        "Maintenance",
                        icon=ft.Icons.BUILD,
                        on_click=schedule_maintenance,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # Initialize filtered data
        filtered_tools = tools_data.copy()
        
        # Create UI components
        search_field = ft.TextField(
            hint_text="Search tools...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=12,
            bgcolor=ft.Colors.WHITE,
            expand=True
        )
        
        status_filter = ft.Dropdown(
            options=[
                ft.dropdown.Option("All Status"),
                ft.dropdown.Option("Available"),
                ft.dropdown.Option("All In Use"),
                ft.dropdown.Option("Partially Available")
            ],
            value="All Status",
            width=150,
            bgcolor=ft.Colors.WHITE,
            border_radius=12
        )
        
        tools_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)
        
        # Statistics cards
        def create_stats_cards():
            if not tools_data:
                return ft.Container()
                
            total_tools = sum(tool['quantity'] for tool in tools_data)
            available_tools = sum(tool['available'] for tool in tools_data)
            in_use_tools = sum(tool['in_use'] for tool in tools_data)
            needs_maintenance = len([tool for tool in tools_data if tool.get('condition') == 'Needs Maintenance'])
            
            return ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(str(total_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                        ft.Text("Total Tools", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=12,
                    border_radius=8,
                    expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(str(available_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                        ft.Text("Available", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.GREEN_50,
                    padding=12,
                    border_radius=8,
                    expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(str(in_use_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                        ft.Text("In Use", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.ORANGE_50,
                    padding=12,
                    border_radius=8,
                    expand=True
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text(str(needs_maintenance), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text("Maintenance", size=12, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.RED_50,
                    padding=12,
                    border_radius=8,
                    expand=True
                )
            ], spacing=8)
        
        # Filter tools
        def filter_tools():
            nonlocal filtered_tools
            search_term = search_field.value.lower() if search_field.value else ""
            status_filter_value = status_filter.value
            
            filtered_tools = tools_data.copy()
            
            if search_term:
                filtered_tools = [tool for tool in filtered_tools if 
                                search_term in tool['name'].lower() or 
                                search_term in tool.get('model', '').lower() or
                                search_term in tool.get('location', '').lower()]
            
            if status_filter_value and status_filter_value != "All Status":
                if status_filter_value == "Available":
                    filtered_tools = [tool for tool in filtered_tools if tool['available'] == tool['quantity']]
                elif status_filter_value == "All In Use":
                    filtered_tools = [tool for tool in filtered_tools if tool['available'] == 0]
                elif status_filter_value == "Partially Available":
                    filtered_tools = [tool for tool in filtered_tools if 0 < tool['available'] < tool['quantity']]
            
            update_tools_list()
        
        # Update tools list
        def update_tools_list():
            tools_list.controls.clear()
            
            if not filtered_tools:
                tools_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Icon(ft.Icons.SEARCH_OFF, size=64, color=ft.Colors.GREY_400),
                            ft.Text("No tools found", size=16, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        alignment=ft.alignment.center,
                        height=200
                    )
                )
            else:
                for tool in filtered_tools:
                    tools_list.controls.append(create_tool_card(tool))
            
            page.update()
        
        # Event handlers
        def on_search_change(e):
            filter_tools()
        
        def on_status_filter_change(e):
            filter_tools()
        
        def add_new_tool():
            go_to("/add-tool")
            # Here you would implement tool creation
        
        def refresh_tools_and_update():
            """Refresh tools data and update the view"""
            refresh_tools_data()
            filter_tools()
            show_snackbar("Outils actualisés", ft.Colors.GREEN)
        
        # Set event handlers
        search_field.on_change = on_search_change
        status_filter.on_change = on_status_filter_change
        
        # Initial load
        update_tools_list()
        
        # Return the complete content
        content = ft.Stack([
            ft.Column([
                # Statistics
                create_stats_cards(),
                
                # Search and filters
                ft.Row([
                    search_field,
                    status_filter
                ], spacing=8),
                
                # Tools list
                ft.Container(
                    content=tools_list,
                    expand=True,
                    margin=ft.margin.only(top=16)
                )
            ], spacing=12),
        ])
 
        return ft.View(
            route="/tools",
            appbar=create_app_bar(
                "My Tools",
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, 
                        tooltip="Refresh Tools",
                        on_click=lambda e: refresh_tools_and_update()
                    ),
                    ft.IconButton(
                        icon=ft.Icons.ADD, 
                        tooltip="Add Tool",
                        on_click=lambda e: add_new_tool()
                    )
                ]
            ),
            navigation_bar=create_bottom_nav(2),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    margin=ft.margin.only(left=15)
                )
            ]
        )
    
    def settings_view():
        """Create and return the complete settings page content"""
        
        # App information
        app_info = {
            "name": "SmartConnect Manager",
            "version": "V1.0.0",
            "developer": "Mohamed Ouchbara"
        }
        
        # Settings sections
        def create_section_header(title):
            return ft.Container(
                content=ft.Text(
                    title,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_700
                ),
                margin=ft.margin.only(top=20, bottom=10)
            )
        
        def create_setting_item(icon, title, subtitle=None, trailing_widget=None, on_click=None):
            content = [
                ft.Row([
                    ft.Icon(icon, size=24, color=ft.Colors.BLUE_600),
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.W_500),
                        ft.Text(subtitle, size=12, color=ft.Colors.GREY_600) if subtitle else ft.Container()
                    ], spacing=2, expand=True),
                    trailing_widget if trailing_widget else ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=ft.Colors.GREY_400)
                ])
            ]
            
            return ft.Card(
                content=ft.Container(
                    content=ft.Column(content, spacing=0),
                    padding=16,
                    on_click=on_click if on_click else lambda e: print(f"Clicked: {title}")
                ),
                elevation=1,
                margin=ft.margin.only(bottom=8)
            )
        
        # Theme settings
        dark_mode_switch = ft.Switch(
            value=False,
            active_color=ft.Colors.BLUE,
            on_change=lambda e: toggle_theme(e.control.value)
        )
        
        # Notification settings
        notifications_switch = ft.Switch(
            value=True,
            active_color=ft.Colors.BLUE,
            on_change=lambda e: toggle_notifications(e.control.value)
        )
        
        # Language dropdown
        language_dropdown = ft.Dropdown(
            options=[
                ft.dropdown.Option("English"),
                ft.dropdown.Option("French"),
                ft.dropdown.Option("Arabic"),
                ft.dropdown.Option("Spanish")
            ],
            value="English",
            width=120,
            bgcolor=ft.Colors.WHITE,
            border_radius=8,
            on_change=lambda e: change_language(e.control.value)
        )
        
        # Event handlers
        def toggle_theme(is_dark):
            theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
            page.theme_mode = theme_mode
            page.update()
            print(f"Dark mode: {'On' if is_dark else 'Off'}")
        
        def toggle_notifications(is_enabled):
            print(f"Notifications: {'Enabled' if is_enabled else 'Disabled'}")
        
        def change_language(language):
            print(f"Language changed to: {language}")
        
        def show_about():
            dialog = ft.AlertDialog(
                title=ft.Text("About SmartConnect Manager"),
                content=ft.Column([
                    ft.Text(f"Version: {app_info['version']}", size=14),
                    ft.Text(f"Developer: {app_info['developer']}", size=14),
                    ft.Text("A comprehensive management system for telecom and field operations.", size=12),
                ], tight=True),
                actions=[ft.TextButton("Close", on_click=lambda e: close_dialog())],
            )
            
            def close_dialog():
                dialog.open = False
                page.update()
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        def show_privacy():
            print("Privacy policy would open here")
        
        def show_terms():
            print("Terms of service would open here")
        
        def contact_support():
            print("Contact support would open here")
        
        def export_data():
            show_snackbar("Export feature coming soon", ft.Colors.BLUE)
        
        def import_data():
            show_snackbar("Import feature coming soon", ft.Colors.BLUE)
        
        def backup_data():
            show_snackbar("Backup started", ft.Colors.GREEN)
        
        def reset_app():
            dialog = ft.AlertDialog(
                title=ft.Text("Reset Application", color=ft.Colors.RED),
                content=ft.Text("This will delete all your data. Are you sure?"),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                    ft.ElevatedButton(
                        "Reset", 
                        bgcolor=ft.Colors.RED,
                        color=ft.Colors.WHITE,
                        on_click=lambda e: confirm_reset()
                    ),
                ],
            )
            
            def close_dialog():
                dialog.open = False
                page.update()
            
            def confirm_reset():
                close_dialog()
                show_snackbar("Reset cancelled - Feature disabled for safety", ft.Colors.ORANGE)
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # Create settings content
        content = ft.Column([
            # Scrollable content
            ft.Container(
                content=ft.Column([
                    # App Information Section
                    create_section_header("App Information"),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Icon(ft.Icons.APP_REGISTRATION, size=48, color=ft.Colors.BLUE),
                                    ft.Column([
                                        ft.Text(
                                            app_info["name"],
                                            size=20,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700
                                        ),
                                        ft.Text(
                                            f"Version {app_info['version']}",
                                            size=14,
                                            color=ft.Colors.GREY_600
                                        ),
                                        ft.Text(
                                            f"Developer: {app_info['developer']}",
                                            size=12,
                                            color=ft.Colors.GREY_500
                                        ),
                                        ft.Text(
                                            f"User: {current_user.get('full_name', 'Guest') if current_user else 'Guest'}",
                                            size=12,
                                            color=ft.Colors.GREY_500
                                        )
                                    ], spacing=2, expand=True)
                                ])
                            ]),
                            padding=16,
                            bgcolor=ft.Colors.BLUE_50,
                            border_radius=8
                        ),
                        elevation=2,
                        margin=ft.margin.only(bottom=8)
                    ),
                    
                    # Appearance Section
                    create_section_header("Appearance"),
                    create_setting_item(
                        ft.Icons.DARK_MODE,
                        "Dark Mode",
                        "Switch between light and dark theme",
                        dark_mode_switch
                    ),
                    create_setting_item(
                        ft.Icons.LANGUAGE,
                        "Language",
                        "Choose your preferred language",
                        language_dropdown
                    ),
                    
                    # Notifications Section
                    create_section_header("Notifications"),
                    create_setting_item(
                        ft.Icons.NOTIFICATIONS,
                        "Push Notifications",
                        "Receive notifications about updates",
                        notifications_switch
                    ),
                    create_setting_item(
                        ft.Icons.EMAIL,
                        "Email Notifications",
                        "Get notified via email"
                    ),
                    
                    # Data Management Section
                    create_section_header("Data Management"),
                    create_setting_item(
                        ft.Icons.BACKUP,
                        "Backup Data",
                        "Create a backup of your data",
                        on_click=lambda e: backup_data()
                    ),
                    create_setting_item(
                        ft.Icons.CLOUD_UPLOAD,
                        "Export Data",
                        "Export your data to file",
                        on_click=lambda e: export_data()
                    ),
                    create_setting_item(
                        ft.Icons.CLOUD_DOWNLOAD,
                        "Import Data",
                        "Import data from file",
                        on_click=lambda e: import_data()
                    ),
                    
                    # Support Section
                    create_section_header("Support & Information"),
                    create_setting_item(
                        ft.Icons.HELP,
                        "Help & Support",
                        "Get help and contact support",
                        on_click=lambda e: contact_support()
                    ),
                    create_setting_item(
                        ft.Icons.INFO,
                        "About",
                        "Learn more about the app",
                        on_click=lambda e: show_about()
                    ),
                    create_setting_item(
                        ft.Icons.PRIVACY_TIP,
                        "Privacy Policy",
                        "Read our privacy policy",
                        on_click=lambda e: show_privacy()
                    ),
                    create_setting_item(
                        ft.Icons.DESCRIPTION,
                        "Terms of Service",
                        "Read terms and conditions",
                        on_click=lambda e: show_terms()
                    ),
                    
                    # Danger Zone Section
                    create_section_header("Danger Zone"),
                    ft.Card(
                        content=ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.WARNING, size=24, color=ft.Colors.RED),
                                ft.Column([
                                    ft.Text("Reset App", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.RED),
                                    ft.Text("This will delete all your data", size=12, color=ft.Colors.RED_300)
                                ], spacing=2, expand=True),
                                ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=ft.Colors.RED_300)
                            ]),
                            padding=16,
                            on_click=lambda e: reset_app()
                        ),
                        elevation=1,
                        margin=ft.margin.only(bottom=8),
                        color=ft.Colors.RED_50
                    ),
                    
                    # Footer
                    ft.Container(
                        content=ft.Column([
                            ft.Text(
                                f"© 2024 {app_info['developer']}",
                                size=12,
                                color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER
                            ),
                            ft.Text(
                                "All rights reserved",
                                size=10,
                                color=ft.Colors.GREY_400,
                                text_align=ft.TextAlign.CENTER
                            )
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        margin=ft.margin.only(top=20, bottom=20)
                    )
                ], scroll=ft.ScrollMode.AUTO),
                expand=True
            )
        ], spacing=0)
        
        return ft.View(
            route="/settings",
            appbar=create_app_bar("Paramètres"),
            navigation_bar=create_bottom_nav(3),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    margin=ft.margin.only(left=15)
                )
            ]
        )
    
    def add_mission_view():
        """Enhanced mission creation with real database integration"""
        # Define colors
        GOLD = "#FFD700"
        WHITE = "#FFFFFF"
        BLACK = "#0F0F0F"
        
        # Form field references
        title_field = ft.Ref[ft.TextField]()
        location_field = ft.Ref[ft.TextField]()
        due_date_field = ft.Ref[ft.TextField]()
        due_time_field = ft.Ref[ft.TextField]()
        status_dropdown = ft.Ref[ft.Dropdown]()
        description_field = ft.Ref[ft.TextField]()
        
        # New assignment fields
        assigned_person_dropdown = ft.Ref[ft.Dropdown]()
        team_leader_dropdown = ft.Ref[ft.Dropdown]()
        technician_field = ft.Ref[ft.TextField]()
        tools_field = ft.Ref[ft.TextField]()
        vehicle_dropdown = ft.Ref[ft.Dropdown]()
        
        # Success/Error message
        message_container = ft.Ref[ft.Container]()
        
        # Load data from database
        def load_form_data():
            """Load employees, vehicles, etc. from database"""
            try:
                # Get employees for assignment
                employees = get_all_employees()
                persons = [{"key": emp["id"], "name": emp["name"]} for emp in employees if emp["status"] == "ACTIVE"]
                
                # Get team leaders (filter by role)
                team_leaders = [{"key": emp["id"], "name": emp["name"]} for emp in employees 
                              if emp["role"] in ["team_leader", "admin"] and emp["status"] == "ACTIVE"]
                
                # Get available vehicles
                vehicles = get_all_vehicles()
                vehicle_list = [{"key": vehicle["id"], "name": f"{vehicle.get('model', 'Unknown')} - {vehicle.get('plate_number', 'No Plate')}"} 
                               for vehicle in vehicles if vehicle.get("status") == "AVAILABLE"]
                
                return persons, team_leaders, vehicle_list
            except Exception as e:
                print(f"Error loading form data: {e}")
                return [], [], []
        
        # Load the data
        PERSONS, TEAM_LEADERS, VEHICLES = load_form_data()
        
        # Form validation
        def validate_form():
            errors = []
            
            if not title_field.current.value or not title_field.current.value.strip():
                errors.append("Mission title is required")
                
            if not location_field.current.value or not location_field.current.value.strip():
                errors.append("Location is required")
                
            if not due_date_field.current.value or not due_date_field.current.value.strip():
                errors.append("Due date is required")
                
            if not due_time_field.current.value or not due_time_field.current.value.strip():
                errors.append("Due time is required")
                
            if not status_dropdown.current.value:
                errors.append("Status is required")
                
            if not assigned_person_dropdown.current.value:
                errors.append("Assigned person is required")
                
            if not team_leader_dropdown.current.value:
                errors.append("Team leader is required")
            
            return errors
        
        # Show message to user
        def show_message(text, is_error=False):
            message_container.current.content = ft.Text(
                text,
                color="#D32F2F" if is_error else "#4CAF50",
                size=14,
                weight=ft.FontWeight.W_500,
                text_align=ft.TextAlign.CENTER
            )
            message_container.current.bgcolor = "#FFEBEE" if is_error else "#E8F5E8"
            message_container.current.visible = True
            message_container.current.update()
        
        # Clear form
        def clear_form():
            title_field.current.value = ""
            location_field.current.value = ""
            due_date_field.current.value = ""
            due_time_field.current.value = ""
            status_dropdown.current.value = None
            description_field.current.value = ""
            assigned_person_dropdown.current.value = None
            team_leader_dropdown.current.value = None
            technician_field.current.value = ""
            tools_field.current.value = ""
            vehicle_dropdown.current.value = None
            
            # Update all fields
            for field in [title_field.current, location_field.current, due_date_field.current, 
                        due_time_field.current, status_dropdown.current, description_field.current,
                        assigned_person_dropdown.current, team_leader_dropdown.current, 
                        technician_field.current, tools_field.current, vehicle_dropdown.current]:
                field.update()
        
        # Submit handler
        def on_submit(e):
            # Validate form
            errors = validate_form()
            
            if errors:
                show_message(f"Please fix the following errors: {', '.join(errors)}", True)
                return
            
            # Parse technicians (comma-separated)
            technicians_list = []
            if technician_field.current.value and technician_field.current.value.strip():
                technicians_list = [tech.strip() for tech in technician_field.current.value.split(",")]
            
            # Parse tools (comma-separated)
            tools_list = []
            if tools_field.current.value and tools_field.current.value.strip():
                tools_list = [tool.strip() for tool in tools_field.current.value.split(",")]
            
            # Prepare mission data for database
            mission_data = {
                "title": title_field.current.value.strip(),
                "location": location_field.current.value.strip(),
                "due_date": due_date_field.current.value.strip(),
                "due_time": due_time_field.current.value.strip(),
                "status": status_dropdown.current.value,
                "description": description_field.current.value.strip() if description_field.current.value else "",
                "assigned_person_id": assigned_person_dropdown.current.value,
                "team_leader_id": team_leader_dropdown.current.value,
                "technicians": technicians_list,
                "required_tools": tools_list,
                "vehicle_id": vehicle_dropdown.current.value,
                "created_by": current_user.get("id") if current_user else None,
            }
            
            # Call database function
            try:
                success = create_mission(mission_data)
                
                if success:
                    show_message("Mission created successfully!", False)
                    clear_form()
                    
                    # Update vehicle status if assigned
                    if vehicle_dropdown.current.value:
                        try:
                            db.update_vehicle_status(vehicle_dropdown.current.value, "IN_USE", mission_data["location"])
                        except Exception as ve:
                            print(f"Error updating vehicle status: {ve}")
                    
                    # Log the activity
                    try:
                        db.log_activity('mission_created', {
                            'title': mission_data['title'],
                            'assigned_to': mission_data['assigned_person_id'],
                            'created_by': current_user.get('full_name') if current_user else 'Unknown'
                        }, current_user.get('id') if current_user else None)
                    except Exception as le:
                        print(f"Error logging activity: {le}")
                    
                else:
                    show_message("Failed to create mission. Please try again.", True)
                    
            except Exception as ex:
                show_message(f"Error: {str(ex)}", True)
        
        # Cancel/Clear handler
        def on_clear(e):
            clear_form()
            message_container.current.visible = False
            message_container.current.update()
        
        # Date picker handler (placeholder)
        def on_date_click(e):
            today = datetime.now().strftime("%Y-%m-%d")
            due_date_field.current.value = today
            due_date_field.current.update()
        
        # Time picker handler (placeholder)
        def on_time_click(e):
            current_time = datetime.now().strftime("%H:%M")
            due_time_field.current.value = current_time
            due_time_field.current.update()
        
        # Create form fields
        title_field.current = ft.TextField(
            label="Mission Title *",
            hint_text="Enter mission title",
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        location_field.current = ft.TextField(
            label="Location *",
            hint_text="Enter mission location",
            prefix_icon=ft.Icons.LOCATION_ON,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        due_date_field.current = ft.TextField(
            label="Due Date *",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_date_click,
            read_only=False,
        )
        
        due_time_field.current = ft.TextField(
            label="Due Time *",
            hint_text="HH:MM",
            prefix_icon=ft.Icons.ACCESS_TIME,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_time_click,
            read_only=False,
        )
        
        status_dropdown.current = ft.Dropdown(
            label="Status *",
            options=[
                ft.dropdown.Option("PENDING", "Pending"),
                ft.dropdown.Option("IN_PROGRESS", "In Progress"),
                ft.dropdown.Option("COMPLETED", "Completed"),
            ],
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        # Assignment fields with real data
        assigned_person_dropdown.current = ft.Dropdown(
            label="Assigned Person *",
            options=[ft.dropdown.Option(p["key"], p["name"]) for p in PERSONS],
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        team_leader_dropdown.current = ft.Dropdown(
            label="Team Leader *",
            options=[ft.dropdown.Option(tl["key"], tl["name"]) for tl in TEAM_LEADERS],
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        technician_field.current = ft.TextField(
            label="Additional Technicians",
            hint_text="Enter technician names separated by commas",
            prefix_icon=ft.Icons.ENGINEERING,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        tools_field.current = ft.TextField(
            label="Required Tools",
            hint_text="Enter required tools separated by commas",
            prefix_icon=ft.Icons.BUILD,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        vehicle_dropdown.current = ft.Dropdown(
            label="Vehicle",
            options=[ft.dropdown.Option(v["key"], v["name"]) for v in VEHICLES],
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        description_field.current = ft.TextField(
            label="Description",
            hint_text="Enter mission description (optional)",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=8,
            bgcolor=WHITE,
            border_color="#E0E0E0",
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        # Message container
        message_container.current = ft.Container(
            content=ft.Text(""),
            padding=12,
            border_radius=8,
            visible=False,
            margin=ft.margin.symmetric(horizontal=16),
        )
        
        # Action buttons
        submit_button = ft.ElevatedButton(
            text="Create Mission",
            bgcolor=GOLD,
            color=BLACK,
            style=ft.ButtonStyle(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_submit,
            expand=True,
        )
        
        clear_button = ft.OutlinedButton(
            text="Clear Form",
            style=ft.ButtonStyle(
                color={"": BLACK},
                side={"": ft.BorderSide(width=1,color="#E0E0E0")},
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_clear,
            expand=True,
        )
        
        # Main content
        content = ft.Column([
            # Message container
            message_container.current,
            
            # Form
            ft.Container(
                content=ft.Column([
                    # Mission Details Section
                    ft.Text(
                        "Mission Details",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    title_field.current,
                    location_field.current,
                    
                    ft.Row([
                        ft.Container(due_date_field.current, expand=True),
                        ft.Container(due_time_field.current, expand=True),
                    ], spacing=12),
                    
                    status_dropdown.current,
                    
                    # Team Assignment Section
                    ft.Container(height=10),  # Spacer
                    ft.Text(
                        "Team Assignment",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    assigned_person_dropdown.current,
                    team_leader_dropdown.current,
                    technician_field.current,
                    
                    # Resources Section
                    ft.Container(height=10),  # Spacer
                    ft.Text(
                        "Resources",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    tools_field.current,
                    vehicle_dropdown.current,
                    
                    # Additional Info Section
                    ft.Container(height=10),  # Spacer
                    ft.Text(
                        "Additional Information",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    description_field.current,
                    
                    ft.Container(height=20),  # Spacer
                    
                    # Action buttons
                    ft.Row([
                        clear_button,
                        submit_button,
                    ], spacing=12),
                    
                ], spacing=16),
                bgcolor=WHITE,
                padding=20,
                margin=16,
                border_radius=12,
                border=ft.border.all(1, "#E0E0E0"),
            ),
            
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)
            

        return ft.View(
            route="/add-mission",
            appbar=create_app_bar("Create Mission", show_nav=False),
            controls=[content],
            bgcolor="#F8F9FA"
        )
    
    def add_user_view():
        """Enhanced user creation with database integration"""
        # Light mode colors
        GOLD = "#FFD700"
        WHITE = "#FFFFFF"
        BLACK = "#000000"
        LIGHT_GRAY = "#FFFFFF"
        DARK_GRAY = "#333333"
        BORDER_COLOR = "#e0e0e0"
        
        role_list = ['admin', 'secretaire', 'team_leader', 'technicien']
        is_loading = False
        
        # Get departments from database
        try:
            departments_data = db.get_all_departments()
            departements = {dept['id']: dept['name'] for dept in departments_data}
        except Exception as e:
            print(f"Error loading departments: {e}")
            # Fallback departments
            departements = {
                1: "logistic",
                2: "administration", 
                3: "terrain",
                4: "admin"
            }
        
        def get_departement_id_from_dict(dropdown_value, departement_dict):
            if dropdown_value:
                try:
                    key = int(dropdown_value.split()[0])
                    return key if key in departement_dict else None
                except:
                    return None
            return None
    
        def show_snackbar(message, color=ft.Colors.RED):
            snackbar = ft.SnackBar(
                content=ft.Text(message, color=WHITE),
                bgcolor=color,
                duration=3000
            )
            page.overlay.append(snackbar)
            snackbar.open = True 
            page.update() 
        
        def toggle_password_visibility(e):
            password_field.password = not password_field.password
            password_toggle.icon = ft.Icons.VISIBILITY_OFF if password_field.password else ft.Icons.VISIBILITY
            page.update()
            
        def add_user(e):
            # Validate inputs
            if not username_field.value or not username_field.value.strip():
                show_snackbar("Username is required")
                return
                
            if not Full_name.value or not Full_name.value.strip():
                show_snackbar("Full name is required")
                return
                
            if not password_field.value or len(password_field.value) < 6:
                show_snackbar("Password must be at least 6 characters long")
                return
                
            if not Rol_Drop.value:
                show_snackbar("Role is required")
                return
                
            if not departement_field.value:
                show_snackbar("Department is required")
                return
            
            username = username_field.value.strip()
            Fullname = Full_name.value.strip()
            password = password_field.value.strip()
            departement_id = get_departement_id_from_dict(departement_field.value, departements)       
            Role = Rol_Drop.value
            active = True

            try:
                success = create_user(username, Fullname, password, Role, departement_id, active)
                if success:
                    show_snackbar("User created successfully!", color=ft.Colors.GREEN)
                    # Clear form
                    username_field.value = ""
                    Full_name.value = ""
                    password_field.value = ""
                    Rol_Drop.value = None
                    departement_field.value = None
                    page.update()
                    
                    # Log the activity
                    try:
                        db.log_activity('user_created', {
                            'username': username,
                            'full_name': Fullname,
                            'role': Role,
                            'created_by': current_user.get('full_name') if current_user else 'System'
                        }, current_user.get('id') if current_user else None)
                    except Exception as le:
                        print(f"Error logging activity: {le}")
                        
                else:
                    show_snackbar("Failed to create user. Username might already exist.", color=ft.Colors.RED)
            except Exception as ex:
                show_snackbar(f"Error creating user: {str(ex)}", color=ft.Colors.RED)
                
        # Logo and title section
        logo_section = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.PERSON_ADD_ALT_SHARP, 
                        size=60,
                        color=GOLD
                    ),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Text(
                    "CREATE USER",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=DARK_GRAY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Add new team members to the system",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=40)
        )
        
        # Username field
        username_field = ft.TextField(
            label="Username",
            hint_text="Enter unique username",
            prefix_icon=ft.Icons.PERSON,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color=ft.Colors.GREY_600),
            text_style=ft.TextStyle(color=BLACK),
            cursor_color=GOLD,
            bgcolor=WHITE,
            border_radius=12,
            height=60,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
        
        # Full name field
        Full_name = ft.TextField(
            label="Full Name",
            hint_text="Enter employee's full name",
            prefix_icon=ft.Icons.BADGE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color=ft.Colors.GREY_600),
            text_style=ft.TextStyle(color=BLACK),
            cursor_color=GOLD,
            bgcolor=WHITE,
            border_radius=12,
            height=60,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
        
        # Role dropdown
        Rol_Drop = ft.Dropdown(
            label="Role",
            options=[ft.dropdown.Option(role.replace('_', ' ').title(), role) for role in role_list],
            width=700,
            border_radius=12,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            label_style=ft.TextStyle(color=ft.Colors.GREY_600),
            text_style=ft.TextStyle(color=BLACK),
            color=BLACK,
        )
        
        # Password toggle button
        password_toggle = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            icon_color=ft.Colors.GREY_600,
            on_click=toggle_password_visibility,
            tooltip="Toggle password visibility"
        )
        
        # Password field
        password_field = ft.TextField( 
            label="Password",
            hint_text="Enter secure password (min 6 characters)",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            suffix=password_toggle,
            password=True,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color=ft.Colors.GREY_600),
            text_style=ft.TextStyle(color=BLACK),
            cursor_color=GOLD,
            bgcolor=WHITE,
            border_radius=12,
            height=60,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
        
        # Department dropdown
        departement_field = ft.Dropdown(
            label="Department",
            options=[ft.dropdown.Option(f"{key} {value.title()}", f"{key} {value}") for key, value in departements.items()],
            width=700, 
            border_radius=12,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            label_style=ft.TextStyle(color=ft.Colors.GREY_600),
            text_style=ft.TextStyle(color=BLACK),
            color=BLACK,
        )
        
        # Create user button
        Create_user_btn = ft.ElevatedButton(
            content=ft.Text("Create User", color=BLACK, weight=ft.FontWeight.BOLD, size=16),
            bgcolor=GOLD,
            color=BLACK,
            height=55,
            width=300,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=3,
                shadow_color=GOLD,
                animation_duration=200
            ),
            on_click=add_user
        )
        
        # Main form container
        form_container = ft.Container(
            content=ft.Column([
                logo_section,
                ft.Container(
                    content=ft.Column([
                        username_field,
                        ft.Container(height=10),
                        Full_name,
                        ft.Container(height=10),
                        password_field, 
                        ft.Container(height=10),
                        departement_field,
                        ft.Container(height=10),
                        Rol_Drop,
                        ft.Container(height=20),
                        Create_user_btn,
                        ft.Container(height=15),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=30)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,scroll=ft.ScrollMode.AUTO),
            bgcolor=LIGHT_GRAY,
            border_radius=0,
            padding=20,
            expand=True
        )
        
        # Put all design in content variable
        content = ft.Container(
            content=form_container,
            expand=True,
        )
                
        return ft.View(
            route="/adduser",
            appbar=create_app_bar("Create User", show_nav=False),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                )
            ]
        )
    
    def login_view():
        """Enhanced login with proper database authentication"""
        PRIMARY_BLUE = "#FFD700"
        WHITE = "#FFFFFF"
        BLACK = "#212121"
        GRAY_300 = "#e0e0e0"
        GRAY_600 = "#757575"
        
        is_loading = False
        
        def show_snackbar(message, color=ft.Colors.RED):
            snackbar = ft.SnackBar(
                content=ft.Text(message, color=WHITE),
                bgcolor=color,
                duration=3000
            )
            page.overlay.append(snackbar)
            snackbar.open = True 
            page.update() 
        
        def on_login_click(e):
            nonlocal is_loading
            global current_user
        
            # Validate inputs
            if not username_field.value:
                show_snackbar("Please enter your username")
                return
                    
            if not password_field.value:
                show_snackbar("Please enter your password")
                return
            
            if len(password_field.value) < 6:
                show_snackbar("Password must be at least 6 characters long")
                return
            
            # Show loading state
            is_loading = True
            login_button.content = ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2, color=WHITE),
                ft.Text("Signing in...", color=WHITE, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.CENTER, tight=True)
            login_button.disabled = True
            page.update()
            
            # Simulate login process delay
            time.sleep(1)
            
            try:
                username = username_field.value.strip()
                password = password_field.value.strip()
                
                # Authenticate with database
                authenticated_user = db_login(username, password)

                if authenticated_user:
                    # Store current user globally
                    current_user = authenticated_user
                    
                    # Log the login activity
                    try:
                        db.log_activity('user_login', {
                            'username': username,
                            'login_time': datetime.now().isoformat()
                        }, authenticated_user.get('id'))
                    except Exception as le:
                        print(f"Error logging login activity: {le}")
                    
                    # Reset button state
                    is_loading = False
                    login_button.content = ft.Text("Sign In", color=WHITE, weight=ft.FontWeight.BOLD, size=16)
                    login_button.disabled = False
                    
                    # Show success message
                    show_snackbar(f"Welcome back, {authenticated_user.get('full_name', username)}!", color=ft.Colors.GREEN)
                    
                    # Navigate to dashboard
                    page.go("/dashboard")
                else:
                    # Show error message
                    is_loading = False
                    login_button.content = ft.Text("Sign In", color=WHITE, weight=ft.FontWeight.BOLD, size=16)
                    login_button.disabled = False
                    show_snackbar("Invalid username or password", color=ft.Colors.RED)
                    page.update()
                    
            except Exception as ex:
                # Handle any database errors
                is_loading = False
                login_button.content = ft.Text("Sign In", color=WHITE, weight=ft.FontWeight.BOLD, size=16)
                login_button.disabled = False
                show_snackbar(f"Login error: {str(ex)}", color=ft.Colors.RED)
                page.update()
        
        def on_forgot_password(e):
            show_snackbar("Password reset feature coming soon", ft.Colors.BLUE)
        
        def toggle_password_visibility(e):
            password_field.password = not password_field.password
            password_toggle.icon = ft.Icons.VISIBILITY_OFF if password_field.password else ft.Icons.VISIBILITY
            page.update()
        
        # Logo and title section
        logo_section = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CONNECT_WITHOUT_CONTACT, 
                        size=60,
                        color=PRIMARY_BLUE
                    ),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Text(
                    "SmartConnect Manager",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=BLACK,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Welcome back! Please sign in to continue",
                    size=14,
                    color=GRAY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=40)
        )
        
        # Username field
        username_field = ft.TextField(
            label="Username",
            hint_text="Enter your username",
            prefix_icon=ft.Icons.PERSON,
            border_color=GRAY_300,
            focused_border_color=PRIMARY_BLUE,
            label_style=ft.TextStyle(color=GRAY_600),
            text_style=ft.TextStyle(color=BLACK),
            cursor_color=PRIMARY_BLUE,
            bgcolor=WHITE,
            border_radius=12,
            height=60,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
        
        # Password toggle button
        password_toggle = ft.IconButton(
            icon=ft.Icons.VISIBILITY_OFF,
            icon_color=GRAY_600,
            on_click=toggle_password_visibility,
            tooltip="Toggle password visibility"
        )
        
        # Password field
        password_field = ft.TextField( 
            label="Password",
            hint_text="Enter your password",
            prefix_icon=ft.Icons.LOCK_OUTLINED,
            suffix=password_toggle,
            password=True,
            border_color=GRAY_300,
            focused_border_color=PRIMARY_BLUE,
            label_style=ft.TextStyle(color=GRAY_600),
            text_style=ft.TextStyle(color=BLACK),
            cursor_color=PRIMARY_BLUE,
            bgcolor=WHITE,
            border_radius=12,
            height=60,
            content_padding=ft.padding.symmetric(horizontal=20, vertical=15)
        )
        
        # Remember me checkbox
        remember_me = ft.Checkbox(
            label="Remember me",
            value=False,
            check_color=WHITE,
            active_color=PRIMARY_BLUE,
            label_style=ft.TextStyle(color=GRAY_600)
        )
        
        # Forgot password link
        forgot_password_link = ft.TextButton(
            "Forgot Password?",
            style=ft.ButtonStyle(
                color=PRIMARY_BLUE,
                overlay_color=ft.Colors.TRANSPARENT
            ),
            on_click=on_forgot_password
        )
        
        # Login button
        login_button = ft.ElevatedButton(
            content=ft.Text("Sign In", color=WHITE, weight=ft.FontWeight.BOLD, size=16),
            bgcolor=PRIMARY_BLUE,
            color=WHITE,
            height=55,
            width=300,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=12),
                elevation=3,
                shadow_color=PRIMARY_BLUE,
                animation_duration=200
            ),
            on_click=on_login_click 
        )
        
        # Social login section
        social_divider = ft.Row([
            ft.Container(
                content=ft.Divider(color=GRAY_300, height=1),
                expand=True
            ),
            ft.Text("or", color=GRAY_600, size=12),
            ft.Container(
                content=ft.Divider(color=GRAY_300, height=1),
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Sign up section - only show for admin users
        signup_section = ft.Row([
            ft.Text("Need to add users? ", color=GRAY_600, size=14),
            ft.TextButton(
                "Admin Panel",
                style=ft.ButtonStyle(
                    color=PRIMARY_BLUE,
                    overlay_color=ft.Colors.TRANSPARENT
                ),
                on_click=lambda e: show_snackbar("Login as admin first", ft.Colors.BLUE)
            )
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Main form container
        form_container = ft.Container(
            content=ft.Column([
                logo_section,
                ft.Container(
                    content=ft.Column([
                        username_field,
                        ft.Container(height=20),
                        password_field,
                        ft.Container(height=15),
                        ft.Row([
                            remember_me,
                            forgot_password_link
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Container(height=30),
                        login_button,
                        ft.Container(height=25),
                        social_divider,
                        ft.Container(height=20),
                        signup_section
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.symmetric(horizontal=30)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,scroll=ft.ScrollMode.AUTO),
            bgcolor=WHITE,
            border_radius=0,
            padding=20,
            expand=True
        )
        
        # Put all design in content variable
        content = ft.Container(
            content=form_container,
            expand=True,
            bgcolor=WHITE
        )
        
        return ft.View(
            route="/login",
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    alignment=ft.alignment.center
                )
            ]
        )
    
    def view_all_car():
        """Car management page using real database data"""
        # Refresh vehicles data
        refresh_vehicles_data()
        
        def get_status_color(status):
            """Return color based on car status"""
            if status == "AVAILABLE":
                return ft.Colors.GREEN
            elif status == "IN_USE":
                return GOLD
            elif status == "MAINTENANCE":
                return ft.Colors.RED
            else:
                return ft.Colors.GREY

        def create_car_card(car):
            """Create a car card component using real data"""
            return ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text(
                            size=14,
                            color=ft.Colors.GREY_600,
                            weight=ft.FontWeight.W_500
                        ),
                        ft.Container(
                            content=ft.Text(
                                car.get("status", "Unknown"),
                                size=12,
                                color=WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=get_status_color(car.get("status", "Unknown")),
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=12
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Text(
                        car.get("model", "Unknown Model"),
                        size=18,
                        color=BLACK,
                        weight=ft.FontWeight.BOLD
                    ),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.CONFIRMATION_NUMBER, size=16, color=ft.Colors.GREY_600),
                        ft.Text(
                            car.get("plate", car.get("plate_number", "No Plate")),
                            size=14,
                            color=ft.Colors.GREY_700
                        )
                    ], spacing=5),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.GREY_600),
                        ft.Text(
                            car.get("location", "Unknown Location"),
                            size=14,
                            color=ft.Colors.GREY_700
                        )
                    ], spacing=5),
                    
                    ft.Row([
                        ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=ft.Colors.GREY_600),
                        ft.Text(
                            f"Updated: {car.get('last_updated', 'Unknown')}",
                            size=12,
                            color=ft.Colors.GREY_600
                        )
                    ], spacing=5)
                ], spacing=8),
                padding=16,
                margin=ft.margin.only(bottom=8),
                bgcolor=WHITE,
                border_radius=12,
                border=ft.border.all(1, ft.Colors.GREY_300),
                ink=True,
                on_click=lambda e, car_id=car.get("id", "Unknown"): show_car_details(car)
            )
        
        def show_car_details(car):
            """Show detailed car information"""
            def close_dialog(e):
                dialog.open = False
                page.update()
            
            def assign_vehicle(e):
                if car.get("status") == "AVAILABLE":
                    try:
                        success = db.update_vehicle_status(car["id"], "IN_USE", "Assigned via app")
                        if success:
                            show_snackbar("Vehicle assigned successfully", ft.Colors.GREEN)
                            refresh_vehicles_data()
                            close_dialog(e)
                        else:
                            show_snackbar("Failed to assign vehicle", ft.Colors.RED)
                    except Exception as ex:
                        show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
                else:
                    show_snackbar("Vehicle not available", ft.Colors.ORANGE)
            
            def schedule_maintenance(e):
                try:
                    success = db.update_vehicle_status(car["id"], "MAINTENANCE", "Scheduled maintenance")
                    if success:
                        show_snackbar("Maintenance scheduled", ft.Colors.BLUE)
                        refresh_vehicles_data()
                        close_dialog(e)
                    else:
                        show_snackbar("Failed to schedule maintenance", ft.Colors.RED)
                except Exception as ex:
                    show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
            
            dialog = ft.AlertDialog(
                title=ft.Text(f"{car.get('model', 'Unknown')} Details", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Icon(ft.Icons.DIRECTIONS_CAR, size=48, color=ft.Colors.BLUE),
                            ft.Column([
                                ft.Text(f"Model: {car.get('model', 'Unknown')}", size=14),
                                ft.Text(f"Plate: {car.get('plate', car.get('plate_number', 'Unknown'))}", size=12, color=ft.Colors.GREY_600),
                                ft.Text(f"Status: {car.get('status', 'Unknown')}", size=12, color=get_status_color(car.get('status', 'Unknown')))
                            ], spacing=4, expand=True)
                        ]),
                        ft.Divider(),
                        ft.Row([
                            ft.Text("Location:", weight=ft.FontWeight.BOLD),
                            ft.Text(car.get("location", "Unknown"))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Last Updated:", weight=ft.FontWeight.BOLD),
                            ft.Text(car.get("last_updated", "Unknown"))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Year:", weight=ft.FontWeight.BOLD),
                            ft.Text(str(car.get("year", "Unknown")))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Row([
                            ft.Text("Fuel Type:", weight=ft.FontWeight.BOLD),
                            ft.Text(car.get("fuel_type", "Unknown"))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ], spacing=8),
                    width=300,
                    height=300
                ),
                actions=[
                    ft.TextButton("Close", on_click=close_dialog),
                    ft.ElevatedButton(
                        "Assign" if car.get("status") == "AVAILABLE" else "Reserved",
                        icon=ft.Icons.ASSIGNMENT,
                        on_click=assign_vehicle,
                        disabled=car.get("status") != "AVAILABLE"
                    ),
                    ft.ElevatedButton(
                        "Maintenance",
                        icon=ft.Icons.BUILD,
                        on_click=schedule_maintenance,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE)
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
            
            page.dialog = dialog
            dialog.open = True
            page.update()
        
        # State variables for filtering and searching
        current_filter = "All"
        search_query = ""
        
        def filter_cars(cars, filter_status, search_text):
            """Filter cars based on status and search query"""
            filtered_cars = cars.copy()
            
            # Filter by status
            if filter_status != "All":
                status_map = {
                    "Available": "AVAILABLE",
                    "In Use": "IN_USE", 
                    "Maintenance": "MAINTENANCE"
                }
                filtered_cars = [car for car in filtered_cars if car.get("status") == status_map.get(filter_status, filter_status)]
            
            # Filter by search query
            if search_text:
                search_lower = search_text.lower()
                filtered_cars = [
                    car for car in filtered_cars 
                    if (search_lower in car.get("model", "").lower() or 
                        search_lower in car.get("plate", car.get("plate_number", "")).lower() or 
                        search_lower in car.get("location", "").lower() or
                        search_lower in str(car.get("id", "")).lower())
                ]
            
            return filtered_cars
        
        def create_filter_button(text, is_active=False, on_click=None):
            """Create a filter button with active/inactive states"""
            return ft.Container(
                content=ft.Text(
                    text, 
                    color=BLACK if is_active else ft.Colors.GREY_600,
                    weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL
                ),
                bgcolor=GOLD if is_active else WHITE,
                padding=ft.padding.symmetric(horizontal=16, vertical=8),
                border_radius=20,
                ink=True,
                on_click=on_click
            )
        
        # Form field references
        search_field = ft.Ref[ft.TextField]()
        car_list_ref = ft.Ref[ft.Column]()
        filter_buttons_ref = ft.Ref[ft.Row]()
        
        def update_car_list():
            """Update the car list based on current filter and search"""
            filtered_cars = filter_cars(vehicles_data, current_filter, search_query)
            car_list_ref.current.controls = [create_car_card(car) for car in filtered_cars]
            car_list_ref.current.update()
        
        def on_filter_click(filter_name):
            """Handle filter button clicks"""
            nonlocal current_filter
            current_filter = filter_name
            
            # Update filter buttons appearance
            filter_buttons_ref.current.controls = [
                create_filter_button("All", current_filter == "All", lambda e: on_filter_click("All")),
                create_filter_button("Available", current_filter == "Available", lambda e: on_filter_click("Available")),
                create_filter_button("In Use", current_filter == "In Use", lambda e: on_filter_click("In Use")),
                create_filter_button("Maintenance", current_filter == "Maintenance", lambda e: on_filter_click("Maintenance"))
            ]
            filter_buttons_ref.current.update()
            
            update_car_list()
        
        def on_search_change(e):
            """Handle search input changes"""
            nonlocal search_query
            search_query = e.control.value
            update_car_list()
        
        def refresh_cars_and_update():
            """Refresh vehicle data and update the view"""
            refresh_vehicles_data()
            update_car_list()
            show_snackbar("Véhicules actualisés", ft.Colors.GREEN)
        
        # Initialize form fields
        search_field.current = ft.TextField(
            hint_text="Search by car model, plate, location, or ID...",
            prefix_icon=ft.Icons.SEARCH,
            border_radius=25,
            filled=True,
            bgcolor=WHITE,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=GOLD,
            on_change=on_search_change
        )
        
        # Filter buttons
        filter_buttons_ref.current = ft.Row([
            create_filter_button("All", True, lambda e: on_filter_click("All")),
            create_filter_button("Available", False, lambda e: on_filter_click("Available")),
            create_filter_button("In Use", False, lambda e: on_filter_click("In Use")),
            create_filter_button("Maintenance", False, lambda e: on_filter_click("Maintenance"))
        ], spacing=8, scroll=ft.ScrollMode.AUTO)
        
        # Car list (initially showing all cars)
        car_list_ref.current = ft.Column([
            create_car_card(car) for car in vehicles_data
        ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)
        
        # Statistics section for vehicles
        def create_vehicle_stats():
            if not vehicles_data:
                return ft.Container()
                
            available_count = len([v for v in vehicles_data if v.get("status") == "AVAILABLE"])
            in_use_count = len([v for v in vehicles_data if v.get("status") == "IN_USE"])
            maintenance_count = len([v for v in vehicles_data if v.get("status") == "MAINTENANCE"])
            total_count = len(vehicles_data)
            
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(total_count), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                            ft.Text("Total", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(available_count), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                            ft.Text("Available", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(in_use_count), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                            ft.Text("In Use", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.ORANGE_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(maintenance_count), size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                            ft.Text("Maintenance", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.RED_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    )
                ], spacing=8),
                margin=ft.margin.only(bottom=16)
            )
        
        # Main content
        content = ft.Column([
            ft.Container(
                content=ft.Column([
                    create_vehicle_stats(),
                    search_field.current,
                    filter_buttons_ref.current,
                    car_list_ref.current
                ], spacing=16),
                padding=16,
                expand=True
            )
        ], spacing=0, expand=True)
        
        return ft.View(
            route="/cars",
            appbar=create_app_bar(
                "Vehicle Fleet",
                show_nav=False,
                actions=[
                    ft.IconButton(
                        icon=ft.Icons.REFRESH, 
                        tooltip="Refresh Vehicles",
                        on_click=lambda e: refresh_cars_and_update()
                    )
                ]
            ),
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                )
            ]
        )
    def add_tool():
        
        """Enhanced tool creation with database integration"""
        # Light mode colors
        GOLD = "#FFD700"
        WHITE = "#FFFFFF"
        BLACK = "#000000"
        LIGHT_GRAY = "#FFFFFF"
        DARK_GRAY = "#333333"
        BORDER_COLOR = "#e0e0e0"
        
        # Tool condition options
        condition_options = ['Good', 'Fair', 'Needs Maintenance', 'Poor']
        
        # Tool categories
        category_options = ['Electrical', 'Mechanical', 'Safety', 'Measurement', 'Communication', 'Other']
        
        # Form field references
        name_field = ft.Ref[ft.TextField]()
        model_field = ft.Ref[ft.TextField]()
        serial_field = ft.Ref[ft.TextField]()
        category_dropdown = ft.Ref[ft.Dropdown]()
        condition_dropdown = ft.Ref[ft.Dropdown]()
        location_field = ft.Ref[ft.TextField]()
        quantity_field = ft.Ref[ft.TextField]()
        available_quantity_field = ft.Ref[ft.TextField]()
        purchase_date_field = ft.Ref[ft.TextField]()
        last_calibration_field = ft.Ref[ft.TextField]()
        next_calibration_field = ft.Ref[ft.TextField]()
        notes_field = ft.Ref[ft.TextField]()
        
        # Success/Error message
        message_container = ft.Ref[ft.Container]()
            
        def default_show_snackbar(message, color=ft.Colors.RED):
            if show_snackbar:
                show_snackbar(message, color)
            else:
                snackbar = ft.SnackBar(
                    content=ft.Text(message, color=WHITE),
                    bgcolor=color,
                    duration=3000
                )
                page.overlay.append(snackbar)
                snackbar.open = True 
                page.update()
        
        # Form validation
        def validate_form():
            errors = []
            
            if not name_field.current.value or not name_field.current.value.strip():
                errors.append("Tool name is required")
                
            if not model_field.current.value or not model_field.current.value.strip():
                errors.append("Model is required")
                
            if not serial_field.current.value or not serial_field.current.value.strip():
                errors.append("Serial number is required")
                
            if not category_dropdown.current.value:
                errors.append("Category is required")
                
            if not condition_dropdown.current.value:
                errors.append("Condition is required")
                
            if not location_field.current.value or not location_field.current.value.strip():
                errors.append("Location is required")
                
            if not quantity_field.current.value:
                errors.append("Total quantity is required")
            else:
                try:
                    quantity = int(quantity_field.current.value)
                    if quantity <= 0:
                        errors.append("Quantity must be greater than 0")
                except ValueError:
                    errors.append("Quantity must be a valid number")
            
            if not available_quantity_field.current.value:
                errors.append("Available quantity is required")
            else:
                try:
                    available = int(available_quantity_field.current.value)
                    if available < 0:
                        errors.append("Available quantity cannot be negative")
                    
                    if quantity_field.current.value:
                        try:
                            total = int(quantity_field.current.value)
                            if available > total:
                                errors.append("Available quantity cannot exceed total quantity")
                        except ValueError:
                            pass
                except ValueError:
                    errors.append("Available quantity must be a valid number")
            
            return errors
        
        # Show message to user
        def show_message(text, is_error=False):
            message_container.current.content = ft.Text(
                text,
                color="#D32F2F" if is_error else "#4CAF50",
                size=14,
                weight=ft.FontWeight.W_500,
                text_align=ft.TextAlign.CENTER
            )
            message_container.current.bgcolor = "#FFEBEE" if is_error else "#E8F5E8"
            message_container.current.visible = True
            message_container.current.update()
        
        # Clear form
        def clear_form():
            fields = [
                name_field.current, model_field.current, serial_field.current,
                location_field.current, quantity_field.current, available_quantity_field.current,
                purchase_date_field.current, last_calibration_field.current, 
                next_calibration_field.current, notes_field.current
            ]
            
            for field in fields:
                field.value = ""
                field.update()
            
            category_dropdown.current.value = None
            condition_dropdown.current.value = None
            category_dropdown.current.update()
            condition_dropdown.current.update()
        
        # Submit handler
        def on_submit(e):
            # Validate form
            errors = validate_form()
            
            if errors:
                show_message(f"Please fix the following errors: {', '.join(errors)}", True)
                return
            
            # Prepare tool data for database
            tool_data = {
                "name": name_field.current.value.strip(),
                "model": model_field.current.value.strip(),
                "serial_number": serial_field.current.value.strip(),
                "category": category_dropdown.current.value,
                "condition": condition_dropdown.current.value,
                "location": location_field.current.value.strip(),
                "total_quantity": int(quantity_field.current.value),
                "available_quantity": int(available_quantity_field.current.value),
                "purchase_date": purchase_date_field.current.value.strip() if purchase_date_field.current.value else None,
                "last_calibration": last_calibration_field.current.value.strip() if last_calibration_field.current.value else None,
                "next_calibration": next_calibration_field.current.value.strip() if next_calibration_field.current.value else None,
                "notes": notes_field.current.value.strip() if notes_field.current.value else None,
                "created_by": current_user.get("id") if current_user else None,
            }
            
            # Call database function
            try:
                success = create_tool(tool_data)
                
                if success:
                    show_message("Tool created successfully!", False)
                    clear_form()
                    
                    # Log the activity
                    try:
                        db.log_activity('tool_created', {
                            'name': tool_data['name'],
                            'model': tool_data['model'],
                            'quantity': tool_data['total_quantity'],
                            'created_by': current_user.get('full_name') if current_user else 'Unknown'
                        }, current_user.get('id') if current_user else None)
                    except Exception as le:
                        print(f"Error logging activity: {le}")
                    
                else:
                    show_message("Failed to create tool. Please try again.", True)
                    
            except Exception as ex:
                show_message(f"Error: {str(ex)}", True)
        
        # Cancel/Clear handler
        def on_clear(e):
            clear_form()
            message_container.current.visible = False
            message_container.current.update()
        
        # Date picker handlers
        def on_purchase_date_click(e):
            today = datetime.now().strftime("%Y-%m-%d")
            purchase_date_field.current.value = today
            purchase_date_field.current.update()
        
        def on_last_calibration_click(e):
            today = datetime.now().strftime("%Y-%m-%d")
            last_calibration_field.current.value = today
            last_calibration_field.current.update()
        
        def on_next_calibration_click(e):
            future_date = datetime.now().replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")
            next_calibration_field.current.value = future_date
            next_calibration_field.current.update()
        
        # Auto-fill available quantity when total changes
        def on_quantity_change(e):
            if quantity_field.current.value and not available_quantity_field.current.value:
                available_quantity_field.current.value = quantity_field.current.value
                available_quantity_field.current.update()
        
        # Create form fields
        name_field.current = ft.TextField(
            label="Tool Name *",
            hint_text="Enter tool name",
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        model_field.current = ft.TextField(
            label="Model *",
            hint_text="Enter model number/name",
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        serial_field.current = ft.TextField(
            label="Serial Number *",
            hint_text="Enter serial number",
            prefix_icon=ft.Icons.NUMBERS,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        category_dropdown.current = ft.Dropdown(
            label="Category *",
            options=[ft.dropdown.Option(cat) for cat in category_options],
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        condition_dropdown.current = ft.Dropdown(
            label="Condition *",
            options=[ft.dropdown.Option(cond) for cond in condition_options],
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        location_field.current = ft.TextField(
            label="Location *",
            hint_text="Where is this tool stored?",
            prefix_icon=ft.Icons.LOCATION_ON,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        quantity_field.current = ft.TextField(
            label="Total Quantity *",
            hint_text="Total number of units",
            prefix_icon=ft.Icons.INVENTORY,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=on_quantity_change
        )
        
        available_quantity_field.current = ft.TextField(
            label= "Available Quantity *",
            hint_text="Available units",
            prefix_icon=ft.Icons.EVENT_AVAILABLE_SHARP,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        purchase_date_field.current = ft.TextField(
            label="Purchase Date",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_purchase_date_click,
            read_only=False,
        )
        
        last_calibration_field.current = ft.TextField(
            label="Last Calibration",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.TUNE,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_last_calibration_click,
            read_only=False,
        )
        
        next_calibration_field.current = ft.TextField(
            label="Next Calibration",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.SCHEDULE,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_next_calibration_click,
            read_only=False,
        )
        
        notes_field.current = ft.TextField(
            label="Notes",
            hint_text="Additional notes about this tool",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        # Message container
        message_container.current = ft.Container(
            content=ft.Text(""),
            padding=12,
            border_radius=8,
            visible=False,
            margin=ft.margin.symmetric(horizontal=16),
        )
        
        # Action buttons
        submit_button = ft.ElevatedButton(
            text="Add Tool",
            bgcolor=GOLD,
            color=BLACK,
            style=ft.ButtonStyle(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_submit,
            expand=True,
        )
        
        clear_button = ft.OutlinedButton(
            text="Clear Form",
            style=ft.ButtonStyle(
                color={"": BLACK},
                side={"": ft.BorderSide(width=1, color=BORDER_COLOR)},
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_clear,
            expand=True,
        )
        
        # Logo and title section
        logo_section = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.BUILD, 
                        size=60,
                        color=GOLD
                    ),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Text(
                    "ADD NEW TOOL",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=DARK_GRAY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Add new tools to the inventory system",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=30)
        )
        
        # Main content
        content = ft.Column([
            # Message container
            message_container.current,
            
            # Form
            ft.Container(
                content=ft.Column([
                    logo_section,
                    
                    # Basic Information Section
                    ft.Text(
                        "Basic Information",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    name_field.current,
                    model_field.current,
                    serial_field.current,
                    
                    ft.Row([
                        ft.Container(category_dropdown.current, expand=True),
                        ft.Container(condition_dropdown.current, expand=True),
                    ], spacing=12),
                    
                    # Location and Quantity Section
                    ft.Container(height=10),
                    ft.Text(
                        "Location & Quantity",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    location_field.current,
                    ft.Row([
                        ft.Container(quantity_field.current, expand=True),
                        ft.Container(available_quantity_field.current, expand=True),
                    ], spacing=12),
                    
                    # Dates Section
                    ft.Container(height=10),
                    ft.Text(
                        "Dates & Calibration",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    purchase_date_field.current,
                    ft.Row([
                        ft.Container(last_calibration_field.current, expand=True),
                        ft.Container(next_calibration_field.current, expand=True),
                    ], spacing=12),
                    
                    # Additional Information Section
                    ft.Container(height=10),
                    ft.Text(
                        "Additional Information",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    notes_field.current,
                    
                    ft.Container(height=20),
                    
                    # Action buttons
                    ft.Row([
                        clear_button,
                        submit_button,
                    ], spacing=12),
                    
                ], spacing=16),
                bgcolor=WHITE,
                padding=20,
                margin=16,
                border_radius=12,
                border=ft.border.all(1, BORDER_COLOR),
            ),
            
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)

        return ft.View(
            route="/add-tool",
            appbar=create_app_bar("Add New Tool", show_nav=False),
            controls=[content]
        )
    
    
    def add_vehicle():
        """Enhanced vehicle creation with database integration"""
        # Light mode colors
        GOLD = "#FFD700"
        WHITE = "#FFFFFF"
        BLACK = "#000000"
        LIGHT_GRAY = "#FFFFFF"
        DARK_GRAY = "#333333"
        BORDER_COLOR = "#e0e0e0"
        
        # Vehicle options
        fuel_type_options = ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'LPG', 'CNG']
        vehicle_type_options = ['Car', 'Truck', 'Van', 'Motorcycle', 'Bus', 'Other']
        status_options = ['AVAILABLE', 'IN_USE', 'MAINTENANCE', 'OUT_OF_SERVICE']
        
        # Form field references
        model_field = ft.Ref[ft.TextField]()
        brand_field = ft.Ref[ft.TextField]()
        year_field = ft.Ref[ft.TextField]()
        plate_number_field = ft.Ref[ft.TextField]()
        vin_field = ft.Ref[ft.TextField]()
        vehicle_type_dropdown = ft.Ref[ft.Dropdown]()
        fuel_type_dropdown = ft.Ref[ft.Dropdown]()
        status_dropdown = ft.Ref[ft.Dropdown]()
        location_field = ft.Ref[ft.TextField]()
        mileage_field = ft.Ref[ft.TextField]()
        insurance_expiry_field = ft.Ref[ft.TextField]()
        registration_expiry_field = ft.Ref[ft.TextField]()
        last_service_field = ft.Ref[ft.TextField]()
        next_service_field = ft.Ref[ft.TextField]()
        notes_field = ft.Ref[ft.TextField]()
        
        # Success/Error message
        message_container = ft.Ref[ft.Container]()
        
        # Form validation
        def validate_form():
            errors = []
            
            if not model_field.current.value or not model_field.current.value.strip():
                errors.append("Vehicle model is required")
                
            if not brand_field.current.value or not brand_field.current.value.strip():
                errors.append("Brand is required")
                
            if not year_field.current.value:
                errors.append("Year is required")
            else:
                try:
                    year = int(year_field.current.value)
                    if year < 1900 or year > datetime.now().year + 1:
                        errors.append("Please enter a valid year")
                except ValueError:
                    errors.append("Year must be a valid number")
                
            if not plate_number_field.current.value or not plate_number_field.current.value.strip():
                errors.append("Plate number is required")
                
            if not vehicle_type_dropdown.current.value:
                errors.append("Vehicle type is required")
                
            if not fuel_type_dropdown.current.value:
                errors.append("Fuel type is required")
                
            if not status_dropdown.current.value:
                errors.append("Status is required")
                
            if not location_field.current.value or not location_field.current.value.strip():
                errors.append("Location is required")
            
            if mileage_field.current.value:
                try:
                    mileage = float(mileage_field.current.value)
                    if mileage < 0:
                        errors.append("Mileage cannot be negative")
                except ValueError:
                    errors.append("Mileage must be a valid number")
            
            return errors
        
        # Show message to user
        def show_message(text, is_error=False):
            message_container.current.content = ft.Text(
                text,
                color="#D32F2F" if is_error else "#4CAF50",
                size=14,
                weight=ft.FontWeight.W_500,
                text_align=ft.TextAlign.CENTER
            )
            message_container.current.bgcolor = "#FFEBEE" if is_error else "#E8F5E8"
            message_container.current.visible = True
            message_container.current.update()
        
        # Clear form
        def clear_form():
            fields = [
                model_field.current, brand_field.current, year_field.current,
                plate_number_field.current, vin_field.current, location_field.current,
                mileage_field.current, insurance_expiry_field.current, 
                registration_expiry_field.current, last_service_field.current,
                next_service_field.current, notes_field.current
            ]
            
            for field in fields:
                field.value = ""
                field.update()
            
            dropdowns = [vehicle_type_dropdown.current, fuel_type_dropdown.current, status_dropdown.current]
            for dropdown in dropdowns:
                dropdown.value = None
                dropdown.update()
        
        # Submit handler
        def on_submit(e):
            # Validate form
            errors = validate_form()
            
            if errors:
                show_message(f"Please fix the following errors: {', '.join(errors)}", True)
                return
            
            # Prepare vehicle data for database
            vehicle_data = {
                "model": model_field.current.value.strip(),
                "brand": brand_field.current.value.strip(),
                "year": int(year_field.current.value),
                "plate_number": plate_number_field.current.value.strip(),
                "vin": vin_field.current.value.strip() if vin_field.current.value else None,
                "vehicle_type": vehicle_type_dropdown.current.value,
                "fuel_type": fuel_type_dropdown.current.value,
                "status": status_dropdown.current.value,
                "location": location_field.current.value.strip(),
                "mileage": float(mileage_field.current.value) if mileage_field.current.value else None,
                "insurance_expiry": insurance_expiry_field.current.value.strip() if insurance_expiry_field.current.value else None,
                "registration_expiry": registration_expiry_field.current.value.strip() if registration_expiry_field.current.value else None,
                "last_service": last_service_field.current.value.strip() if last_service_field.current.value else None,
                "next_service": next_service_field.current.value.strip() if next_service_field.current.value else None,
                "notes": notes_field.current.value.strip() if notes_field.current.value else None,
                "created_by": current_user.get("id") if current_user else None,
            }
            
            # Call database function
            try:
                success = create_vehicle(vehicle_data)
                
                if success:
                    show_message("Vehicle created successfully!", False)
                    clear_form()
                    
                    # Log the activity
                    try:
                        db.log_activity('vehicle_created', {
                            'model': vehicle_data['model'],
                            'brand': vehicle_data['brand'],
                            'plate_number': vehicle_data['plate_number'],
                            'created_by': current_user.get('full_name') if current_user else 'Unknown'
                        }, current_user.get('id') if current_user else None)
                    except Exception as le:
                        print(f"Error logging activity: {le}")
                    
                else:
                    show_message("Failed to create vehicle. Plate number might already exist.", True)
                    
            except Exception as ex:
                show_message(f"Error: {str(ex)}", True)
        
        # Cancel/Clear handler
        def on_clear(e):
            clear_form()
            message_container.current.visible = False
            message_container.current.update()
        
        # Date picker handlers
        def on_insurance_expiry_click(e):
            future_date = datetime.now().replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")
            insurance_expiry_field.current.value = future_date
            insurance_expiry_field.current.update()
        
        def on_registration_expiry_click(e):
            future_date = datetime.now().replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")
            registration_expiry_field.current.value = future_date
            registration_expiry_field.current.update()
        
        def on_last_service_click(e):
            today = datetime.now().strftime("%Y-%m-%d")
            last_service_field.current.value = today
            last_service_field.current.update()
        
        def on_next_service_click(e):
            future_date = datetime.now().replace(month=datetime.now().month + 6 if datetime.now().month <= 6 else datetime.now().month - 6, year=datetime.now().year + (1 if datetime.now().month > 6 else 0)).strftime("%Y-%m-%d")
            next_service_field.current.value = future_date
            next_service_field.current.update()
        
        # Create form fields
        model_field.current = ft.TextField(
            label="Vehicle Model *",
            hint_text="Enter vehicle model",
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        brand_field.current = ft.TextField(
            label="Brand *",
            hint_text="Enter vehicle brand",
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        year_field.current = ft.TextField(
            label="Year *",
            hint_text="Enter manufacturing year",
            prefix_icon=ft.Icons.CALENDAR_TODAY,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        plate_number_field.current = ft.TextField(
            label="Plate Number *",
            hint_text="Enter license plate number",
            prefix_icon=ft.Icons.CONFIRMATION_NUMBER,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        vin_field.current = ft.TextField(
            label="VIN Number",
            hint_text="Enter vehicle identification number",
            prefix_icon=ft.Icons.NUMBERS,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        vehicle_type_dropdown.current = ft.Dropdown(
            label="Vehicle Type *",
            options=[ft.dropdown.Option(vtype) for vtype in vehicle_type_options],
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        fuel_type_dropdown.current = ft.Dropdown(
            label="Fuel Type *",
            options=[ft.dropdown.Option(fuel) for fuel in fuel_type_options],
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        status_dropdown.current = ft.Dropdown(
            label="Status *",
            options=[ft.dropdown.Option(status) for status in status_options],
            value="AVAILABLE",  # Default value
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        location_field.current = ft.TextField(
            label="Current Location *",
            hint_text="Where is this vehicle parked?",
            prefix_icon=ft.Icons.LOCATION_ON,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        mileage_field.current = ft.TextField(
            label="Current Mileage",
            hint_text="Enter current mileage",
            prefix_icon=ft.Icons.SPEED,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        
        insurance_expiry_field.current = ft.TextField(
            label="Insurance Expiry",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.SHIELD,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_insurance_expiry_click,
            read_only=False,
        )
        
        registration_expiry_field.current = ft.TextField(
            label="Registration Expiry",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.DESCRIPTION,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_registration_expiry_click,
            read_only=False,
        )
        
        last_service_field.current = ft.TextField(
            label="Last Service Date",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.BUILD,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_last_service_click,
            read_only=False,
        )
        
        next_service_field.current = ft.TextField(
            label="Next Service Due",
            hint_text="YYYY-MM-DD",
            prefix_icon=ft.Icons.SCHEDULE,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
            on_click=on_next_service_click,
            read_only=False,
        )
        
        notes_field.current = ft.TextField(
            label="Notes",
            hint_text="Additional notes about this vehicle",
            multiline=True,
            min_lines=3,
            max_lines=5,
            border_radius=8,
            bgcolor=WHITE,
            border_color=BORDER_COLOR,
            focused_border_color=GOLD,
            label_style=ft.TextStyle(color="#666666"),
            text_style=ft.TextStyle(color=BLACK),
        )
        
        # Message container
        message_container.current = ft.Container(
            content=ft.Text(""),
            padding=12,
            border_radius=8,
            visible=False,
            margin=ft.margin.symmetric(horizontal=16),
        )
        
        # Action buttons
        submit_button = ft.ElevatedButton(
            text="Add Vehicle",
            bgcolor=GOLD,
            color=BLACK,
            style=ft.ButtonStyle(
                elevation=2,
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_submit,
            expand=True,
        )
        
        clear_button = ft.OutlinedButton(
            text="Clear Form",
            style=ft.ButtonStyle(
                color={"": BLACK},
                side={"": ft.BorderSide(width=1, color=BORDER_COLOR)},
                shape=ft.RoundedRectangleBorder(radius=8),
            ),
            on_click=on_clear,
            expand=True,
        )
        
        # Logo and title section
        logo_section = ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.DIRECTIONS_CAR, 
                        size=60,
                        color=GOLD
                    ),
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Text(
                    "ADD NEW VEHICLE",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=DARK_GRAY,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Add new vehicles to the fleet management system",
                    size=14,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=30)
        )
        
        # Main content
        content = ft.Column([
            # Message container
            message_container.current,
            
            # Form
            ft.Container(
                content=ft.Column([
                    logo_section,
                    
                    # Vehicle Information Section
                    ft.Text(
                        "Vehicle Information",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    model_field.current,
                    brand_field.current,
                    
                    ft.Row([
                        ft.Container(year_field.current, expand=True),
                        ft.Container(vehicle_type_dropdown.current, expand=True),
                    ], spacing=12),
                    
                    # Identification Section
                    ft.Container(height=10),
                    ft.Text(
                        "Identification",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    plate_number_field.current,
                    vin_field.current,
                    
                    # Specifications Section
                    ft.Container(height=10),
                    ft.Text(
                        "Specifications & Status",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    ft.Row([
                        ft.Container(fuel_type_dropdown.current, expand=True),
                        ft.Container(status_dropdown.current, expand=True),
                    ], spacing=12),
                    
                    ft.Row([
                        ft.Container(location_field.current, expand=True),
                        ft.Container(mileage_field.current, expand=True),
                    ], spacing=12),
                    
                    # Documentation Section
                    ft.Container(height=10),
                    ft.Text(
                        "Documentation & Service",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    ft.Row([
                        ft.Container(insurance_expiry_field.current, expand=True),
                        ft.Container(registration_expiry_field.current, expand=True),
                    ], spacing=12),
                    
                    ft.Row([
                        ft.Container(last_service_field.current, expand=True),
                        ft.Container(next_service_field.current, expand=True),
                    ], spacing=12),
                    
                    # Additional Information Section
                    ft.Container(height=10),
                    ft.Text(
                        "Additional Information",
                        size=16,
                        weight=ft.FontWeight.W_600,
                        color=BLACK,
                    ),
                    
                    notes_field.current,
                    
                    ft.Container(height=20),
                    
                    # Action buttons
                    ft.Row([
                        clear_button,
                        submit_button,
                    ], spacing=12),
                    
                ], spacing=16),
                bgcolor=WHITE,
                padding=20,
                margin=16,
                border_radius=12,
                border=ft.border.all(1, BORDER_COLOR),
            ),
            
        ], spacing=0, expand=True, scroll=ft.ScrollMode.AUTO)

        return ft.View(
            route="/add-vehicle",
            appbar=create_app_bar("Add New Vehicle", show_nav=False),
            controls=[content]
        )
    
    
    def not_found_view():
        """404 view"""
        content = ft.Column([
            ft.Icon(ft.Icons.ERROR, size=100, color=ft.Colors.RED),
            ft.Text("404 - Page Not Found", size=24, weight=ft.FontWeight.BOLD),
            ft.Text("The page you're looking for doesn't exist."),
            ft.Container(height=20),
            ft.ElevatedButton(
                "Go to Dashboard",
                on_click=lambda _: go_to("/dashboard")
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.View(
            route="/404",
            controls=[
                ft.Container(
                    content=content,
                    expand=True,
                    alignment=ft.alignment.center
                )
            ]
        )
    
    # ========== UTILITY FUNCTIONS ==========
    
    def refresh_all_data():
        """Refresh all data from database"""
        refresh_dashboard_data()
        refresh_employees_data()
        refresh_vehicles_data()
        refresh_tools_data()
        show_snackbar("All data refreshed", ft.Colors.GREEN)
        page.update()
    
    def logout_user():
        """Handle user logout"""
        global current_user
        
        # Log the logout activity
        if current_user:
            try:
                db.log_activity('user_logout', {
                    'username': current_user.get('username'),
                    'logout_time': datetime.now().isoformat()
                }, current_user.get('id')) 
            except Exception as le:
                print(f"Error logging logout activity: {le}")
        
        # Clear current user
        current_user = None
        
        # Show logout message
        show_snackbar("Logged out successfully", ft.Colors.BLUE)
        
        # Navigate to login
        go_to("/login")
    
    # ========== ROUTE HANDLING ==========
    
    def route_change(e):
        """Handle route changes"""        
        # Clear the page
        page.views.clear()
        
        # Check if user is logged in for protected routes
        protected_routes = ["/dashboard", "/employees", "/tools", "/settings", "/add-mission", "/adduser", "/cars"]
        
        if page.route in protected_routes and not current_user:
            # Redirect to login if not authenticated
            page.views.append(login_view())
            page.update()
            return
        
        # Define routes
        routes = {
            "/": dashboard_view if current_user else login_view,
            "/dashboard": dashboard_view,
            "/employees": employees_view,
            "/tools": tools_view,
            "/settings": settings_view,
            "/add-mission": add_mission_view,
            "/adduser": add_user_view,
            "/login": login_view,
            "/cars": view_all_car,
            "/add-tool":add_tool,
            "/add-vehicle": add_vehicle
        }
        
        # Get the route handler
        route_handler = routes.get(page.route, not_found_view)
        
        # Get the view
        view = route_handler()
        
        # Add view to page
        page.views.append(view)
        page.update()
    
    # Set up route change handler
    page.on_route_change = route_change
    
    # Navigate to login initially 
    page.go("/login")


def main(page: ft.Page):
    """Main function to initialize the app"""
    dashboard_router(page)


if __name__ == "__main__":
    ft.app(target=main)