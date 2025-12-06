import flet  as ft
from datetime import datetime
import time  
# Updated imports to use the new database
from db import db

# Import views
from views.dashboard_view import dashboard_view
from views.employees_view import employees_view
from views.tools_view import tools_view
from views.settings_view import settings_view
from views.add_mission_view import add_mission_view
from views.add_user_view import add_user_view
from views.login_view import login_view
from views.vehicles_view import vehicles_view
from views.add_tool_view import add_tool_view
from views.add_vehicle_view import add_vehicle_view
from views.missions_view import missions_view
from views.employee_details_view import employee_details_view

navigation_history = []

def dashboard_router(page: ft.Page):
    """Main dashboard router function with all functionality inside"""
    
    # Session state
    current_user = None

    # Initialize page settings
    page.title = "SmartConnect Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.width = 400   
    page.window.height = 780 
    page.padding = 5 
    page.bgcolor = "#f5f5f5"
    page.scroll = ft.ScrollMode.AUTO

    # Colors
    WHITE = "#FFFFFF"

    def go_to(route):
        """Navigate to a route"""
        page.go(route)
    
    def show_exit_dialog():
        """Show exit confirmation dialog"""
        def close_dialog(e):
            dialog.open = False
            page.update()

        def exit_app(e):
            page.window_close()

        dialog = ft.AlertDialog(
            title=ft.Text("Exit App"),
            content=ft.Text("Do you want to exit the application?"),
            actions=[
                ft.TextButton("Cancel", on_click=close_dialog),
                ft.TextButton("Exit", on_click=exit_app),
            ],
        )

        page.open(dialog)
        dialog.open = True
        page.update()

    def view_pop(e):
        """Handle Android back button press"""
        global navigation_history

        print(f"Back button pressed. Current route: {page.route}")  # Debug log
        print(f"Navigation history: {navigation_history}")  # Debug log

        # Remove current route from history if it's there
        if navigation_history and navigation_history[-1] == page.route:
            navigation_history.pop()

        # Check if there's a previous route to go back to
        if len(navigation_history) > 0:
            # Get the previous route
            previous_route = navigation_history[-1]
            # Remove it from history to avoid duplicating when route_change is called
            navigation_history.pop()

            # FIXED: Properly manage view stack before navigation
            if len(page.views) > 1:
                page.views.pop()  # Remove current view

            # Navigate to previous route
            print(f"Navigating back to: {previous_route}")  # Debug log
            page.go(previous_route)
        else:
            # No history available - handle based on current route
            if page.route == "/login":
                # On login page, show exit dialog or close app
                show_exit_dialog()
            elif current_user:
                # If logged in, go to dashboard
                page.go("/dashboard")
            else:
                # Not logged in, go to login
                page.go("/login")

    def create_app_bar(title, show_nav=True, actions=None):
        """Create app bar with consistent styling"""
        leading = None
        if not show_nav:
            leading = ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda e: view_pop(None)
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
        """Display a snackbar message"""
        # Create snackbar if it doesn't exist or replace it
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=WHITE),
            bgcolor=color,
            duration=3000
        )
        page.snack_bar.open = True
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
    
    def refresh_all_data():
        """Refresh all data from database"""
        # This function might need to be passed down or handled differently
        # as the individual views manage their own data refreshing now.
        # But we can keep it as a signal if needed.
        show_snackbar("Data refreshed", ft.Colors.GREEN)
        page.update()
    
    def logout_user():
        """Handle user logout"""
        nonlocal current_user
        
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
        
    def on_login_success(authenticated_user):
        """Handle successful login"""
        nonlocal current_user
        current_user = authenticated_user
        show_snackbar(f"Welcome back, {authenticated_user.get('full_name', 'User')}!", ft.Colors.GREEN)
        go_to("/dashboard")
        
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

    # ========== ROUTE HANDLING ==========
    
    def route_change(e):
        """Handle route changes"""
        global navigation_history
        # Add current route to navigation history (avoid duplicates)
        if not navigation_history or navigation_history[-1] != page.route:
            navigation_history.append(page.route)
            # Keep history reasonable size (optional)
            if len(navigation_history) > 20:
                navigation_history.pop(0)
        
        # Clear the page
        page.views.clear()
        
        # Check if user is logged in for protected routes
        protected_routes = ["/dashboard", "/employees", "/tools", "/settings", "/add-mission", "/adduser", "/cars"]
        
        # Add dynamic protected routes
        if (page.route.startswith("/edit_employee") or 
            page.route.startswith("/view_employee") or
            page.route in protected_routes) and not current_user:
            # Redirect to login if not authenticated
            page.views.append(login_view(page, on_login_success, show_snackbar))
            page.update()
            return
        
        # Handle dynamic routes first
        if page.route.startswith("/edit_employee"):
            # Extract employee ID from route
            route_parts = page.route.split("/")
            if len(route_parts) >= 3:
                employee_id = route_parts[2]
                view = employee_details_view(page, go_to, create_app_bar, show_snackbar, employee_id=employee_id)
            else:
                # No employee ID provided - create new employee
                view = employee_details_view(page, go_to, create_app_bar, show_snackbar)
            page.views.append(view)
            page.update()
            return
        
        if page.route.startswith("/view_employee"):
            # Extract employee ID from route
            route_parts = page.route.split("/")
            if len(route_parts) >= 3:
                employee_id = route_parts[2]
                view = employee_details_view(page, go_to, create_app_bar, show_snackbar, employee_id=employee_id, readonly=True)
                page.views.append(view)
                page.update()
                return
            else:
                # No employee ID provided - redirect to employees list
                page.route = "/employees"
                page.views.append(employees_view(page, go_to, create_app_bar, create_bottom_nav, show_snackbar))
                page.update()
                return
        
        # Define static routes
        routes = {
            "/": lambda: dashboard_view(page, logout_user, go_to, current_user, refresh_all_data, create_bottom_nav) if current_user else login_view(page, on_login_success, show_snackbar),
            "/dashboard": lambda: dashboard_view(page, logout_user, go_to, current_user, refresh_all_data, create_bottom_nav),
            "/employees": lambda: employees_view(page, go_to, create_app_bar, create_bottom_nav, show_snackbar),
            "/tools": lambda: tools_view(page, go_to, create_app_bar, create_bottom_nav, show_snackbar),
            "/settings": lambda: settings_view(page, create_app_bar, create_bottom_nav, current_user, show_snackbar),
            "/add-mission": lambda: add_mission_view(page, create_app_bar, current_user),
            "/adduser": lambda: add_user_view(page, create_app_bar, current_user, show_snackbar),
            "/login": lambda: login_view(page, on_login_success, show_snackbar),
            "/cars": lambda: vehicles_view(page, create_app_bar, go_to, show_snackbar),
            "/add-tool": lambda: add_tool_view(page, create_app_bar, current_user, show_snackbar),
            "/add-vehicle": lambda: add_vehicle_view(page, create_app_bar, current_user, show_snackbar),
            "/missions": lambda: missions_view(page, go_to, show_snackbar),
        }
        
        # Get the route handler
        route_handler = routes.get(page.route, not_found_view)
        
        # Get the view
        view = route_handler()
        
        # Add view to page
        page.views.append(view)
        page.update()

    # IMPORTANT: Register the handlers BEFORE calling page.go()
    page.on_route_change = route_change
    page.on_view_pop = view_pop

    # Navigate to login initially
    page.go("/login")


def main(page: ft.Page):
    """Main function to initialize the app"""
    dashboard_router(page)


if __name__ == "__main__":
    ft.app(target=main)
