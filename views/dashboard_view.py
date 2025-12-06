import flet as ft
from datetime import datetime
from db import get_dashboard_stats, get_recent_activities

def dashboard_view(page: ft.Page, logout_user, go_to, current_user, refresh_all_data, create_bottom_nav):
    """Dashboard view with document management system design style"""

    # Define colors
    GOLD = "#FFD700"

    # Define UI elements that need to be updated
    employees_stat_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#2D9CDB")
    projects_stat_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#27AE60")
    vehicles_stat_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#FFB000")
    tools_stat_text = ft.Text("0", size=24, weight=ft.FontWeight.BOLD, color="#EB5757")
    recent_activities_container = ft.Container()

    def refresh_dashboard_data():
        """Refresh dashboard statistics from database"""
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

        # Update UI elements
        employees_stat_text.value = str(dashboard_data["employees"]["total"])
        projects_stat_text.value = str(dashboard_data["projects"]["total"])
        vehicles_stat_text.value = str(dashboard_data["vehicles"]["total"])
        tools_stat_text.value = str(dashboard_data["equipment"]["total"])

        # Update recent activities
        update_recent_activities()

        page.update()

    def logout_click(e):
        logout_user()

    def handle_quick_action(title):
        """Handle quick action clicks"""
        if title == "New Missions":
            go_to("/add-mission")
        elif title == "Add Employé":
            go_to("/adduser")
        elif title == "View All Car":
            go_to("/cars")
        elif title == "View All Mission":
            go_to("/missions")

    # Get current user info
    user_name = current_user.get('full_name', 'Unknown User') if current_user else 'Guest'

    def update_recent_activities():
        """Fetch and update recent activities widget content"""
        try:
            activities_data = get_recent_activities(10)

            if not activities_data:
                activities_data = [
                    {"activity_type": "login", "timestamp": datetime.now().isoformat(),
                    "activity_data": {"message": "No recent activities"}},
                ]
        except Exception as e:
            activities_data = [
                {"activity_type": "error", "timestamp": datetime.now().isoformat(),
                "activity_data": {"message": "Error loading activities"}},
            ]

        def get_activity_display(activity):
            activity_type = activity.get('activity_type', 'Unknown')
            activity_data = activity.get('activity_data', {})
            timestamp = activity.get('timestamp', '')

            # Parse timestamp
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_diff = datetime.now() - dt.replace(tzinfo=None)

                if time_diff.days > 0:
                    time_str = f"{time_diff.days}d ago"
                elif time_diff.seconds > 3600:
                    hours = time_diff.seconds // 3600
                    time_str = f"{hours}h ago"
                elif time_diff.seconds > 60:
                    minutes = time_diff.seconds // 60
                    time_str = f"{minutes}m ago"
                else:
                    time_str = "Now"
            except:
                time_str = "Recently"

            # Format activity message based on type
            if activity_type == 'mission_created':
                message = f"Mission: {activity_data.get('title', 'New task')}"
                activity_type_display = "success"
            elif activity_type == 'mission_status_updated':
                message = f"Updated: {activity_data.get('new_status', 'Status')}"
                activity_type_display = "info"
            elif activity_type == 'user_login':
                message = f"Login: {activity_data.get('username', 'User')}"
                activity_type_display = "info"
            else:
                message = activity_data.get('message', f'Activity: {activity_type}')
                activity_type_display = "info"

            return {
                "action": message[:35] + "..." if len(message) > 35 else message,
                "time": time_str,
                "type": activity_type_display
            }

        activities = [get_activity_display(activity) for activity in activities_data]

        def get_activity_color(activity_type):
            colors = {
                "info": "#2D9CDB",
                "success": "#27AE60",
                "warning": "#FFB000",
                "error": "#EB5757"
            }
            return colors.get(activity_type, "#666666")

        recent_activities_container.content = ft.Column([
            ft.Container(
                content=ft.Row([
                    ft.Container(
                        width=3,
                        height=35,
                        bgcolor=get_activity_color(activity["type"]),
                        border_radius=2
                    ),
                    ft.Column([
                        ft.Text(activity["action"], size=12, color="#1e293b"),
                        ft.Text(activity["time"], size=10, color="#64748b")
                    ], spacing=2, expand=True)
                ], spacing=8),
                padding=ft.padding.symmetric(vertical=6, horizontal=8),
                bgcolor="#f8fafc",
                border_radius=6,
                margin=ft.margin.only(bottom=4)
            ) for activity in activities
        ], spacing=0, scroll=ft.ScrollMode.AUTO, height=300)

    # Initial data load
    refresh_dashboard_data()

    # Statistics cards - two per row
    stat_cards = ft.Column([
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.PEOPLE, color="#2D9CDB", size=30),
                    employees_stat_text,
                    ft.Text("Employees", size=12, color="#666666")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white",
                padding=15,
                border_radius=10,
                width=110,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                    offset=ft.Offset(0, 2),
                )
            ),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.WORK, color="#27AE60", size=30),
                    projects_stat_text,
                    ft.Text("Projects", size=12, color="#666666")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white",
                padding=15,
                border_radius=10,
                width=110,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                    offset=ft.Offset(0, 2),
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
        ft.Container(height=15),
        ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.DIRECTIONS_CAR, color="#FFB000", size=30),
                    vehicles_stat_text,
                    ft.Text("Vehicles", size=12, color="#666666")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white",
                padding=15,
                border_radius=10,
                width=110,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                    offset=ft.Offset(0, 2),
                )
            ),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.Icons.BUILD, color="#EB5757", size=30),
                    tools_stat_text,
                    ft.Text("Tools", size=12, color="#666666")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="white",
                padding=15,
                border_radius=10,
                width=110,
                shadow=ft.BoxShadow(
                    spread_radius=1,
                    blur_radius=5,
                    color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                    offset=ft.Offset(0, 2),
                )
            )
        ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
    ])

    recent_activities_widget = ft.Container(
        content=ft.Column([
            ft.Text("Recent Activities", size=18, weight=ft.FontWeight.BOLD, color="#2D9CDB"),
            ft.Divider(height=1, color="#E0E0E0"),
            recent_activities_container
        ], spacing=10),
        bgcolor="white",
        padding=20,
        border_radius=15,
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=10,
            color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
            offset=ft.Offset(0, 3),
        ),
        margin=ft.margin.only(bottom=15)
    )

    def on_refresh_click(e):
        refresh_dashboard_data()
        refresh_all_data()

    dashboard_content = [
        # Header
        ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("SmartConnect Manager", size=20, weight=ft.FontWeight.BOLD, color="white"),
                    ft.Text(f"Welcome back, {user_name}", size=14, color="white")
                ], expand=True),
                    ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    icon_color="white",
                    tooltip="Refresh Data",
                    on_click=on_refresh_click,
                    bgcolor=ft.Colors.with_opacity(0.2, "white"),
                    style=ft.ButtonStyle(shape=ft.CircleBorder())
                ),
                ft.IconButton(
                    icon=ft.Icons.LOGOUT,
                    icon_color="white",
                    on_click=logout_click,
                    bgcolor=ft.Colors.with_opacity(0.2, "white"),
                    style=ft.ButtonStyle(shape=ft.CircleBorder())
                )
            ]),
            bgcolor=GOLD,
            padding=25,
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.with_opacity(0.3, GOLD),
                offset=ft.Offset(0, 5),
            )
        ),
        ft.Container(height=25),

        # Statistics Overview
        ft.Container(
            content=ft.Column([
                ft.Text("Overview", size=18, weight=ft.FontWeight.BOLD, color="#2D9CDB"),
                ft.Container(height=15),
                stat_cards
            ]),
            bgcolor="white",
            padding=20,
            border_radius=15,
            margin=ft.margin.only(bottom=20),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.1, ft.Colors.GREY),
                offset=ft.Offset(0, 3),
            )
        ),

        # Action buttons - two per row
        ft.Column([
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.PERSON_ADD, color="white"),
                        ft.Text("Add employee", color="white")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: handle_quick_action("Add Employé"),
                    bgcolor="#2D9CDB",
                    width=140,
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD_TASK, color="white"),
                        ft.Text("Add Project", color="white")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: handle_quick_action("New Missions"),
                    bgcolor="#27AE60",
                    width=140,
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.DIRECTIONS_CAR, color="white"),
                        ft.Text("All Vehicles", color="white")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: handle_quick_action("View All Car"),
                    bgcolor="#FFB000",
                    width=140,
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.VIEW_LIST, color="white"),
                        ft.Text("All Projects", color="white")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda e: handle_quick_action("View All Mission"),
                    bgcolor="#EB5757",
                    width=140,
                    height=45,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)
        ]),

        ft.Container(height=25),

        # Recent Activities section
        recent_activities_widget
    ]

    return ft.View(
        route="/dashboard",
        navigation_bar=create_bottom_nav(0),
        controls=[
            ft.Container(
                content=ft.Column(
                    dashboard_content,
                    scroll=ft.ScrollMode.AUTO,
                    expand=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=20,
                expand=True
            )
        ]
    )
