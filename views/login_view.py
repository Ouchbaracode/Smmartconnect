import flet as ft
from db import login as db_login, login_with_google as db_login_google
import time
import os
from google_auth_oauthlib.flow import InstalledAppFlow

def login_view(page: ft.Page, on_login_success, show_snackbar):
    """Enhanced login with proper database authentication"""
    PRIMARY_BLUE = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#212121"
    GRAY_300 = "#e0e0e0"
    GRAY_600 = "#757575"
    GOOGLE_BLUE = "#4285F4"

    is_loading = False

    def on_login_click(e):
        nonlocal is_loading

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
                on_login_success(authenticated_user)
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

    def on_google_login_click(e):
        """Handle Google Login using InstalledAppFlow"""
        nonlocal is_loading

        is_loading = True
        google_login_button.content = ft.Row([
            ft.ProgressRing(width=20, height=20, stroke_width=2, color=GRAY_600),
            ft.Text("Opening Browser...", color=GRAY_600, weight=ft.FontWeight.BOLD)
        ], alignment=ft.MainAxisAlignment.CENTER, tight=True)
        google_login_button.disabled = True
        page.update()

        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

            if not client_id or not client_secret:
                # Fallback simulation if no env vars (for testing)
                time.sleep(1)
                print("Missing Google Credentials, using simulation")
                fake_id_token = "simulate_google_token_12345"
                authenticated_user = db_login_google(fake_id_token)
                if authenticated_user:
                    on_login_success(authenticated_user)
                else:
                    raise Exception("Simulation failed")
                return

            # Construct client config manually to avoid writing a file
            client_config = {
                "installed": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": ["http://localhost"]
                }
            }

            # Create flow
            flow = InstalledAppFlow.from_client_config(
                client_config,
                scopes=['openid', 'https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile']
            )

            # Run local server to get credentials
            creds = flow.run_local_server(port=0)

            # Get ID token
            if creds and creds.id_token:
                authenticated_user = db_login_google(creds.id_token)

                if authenticated_user:
                    on_login_success(authenticated_user)
                else:
                    raise Exception("Authentication failed after getting token")
            else:
                raise Exception("Failed to retrieve ID token")

        except Exception as ex:
            is_loading = False
            google_login_button.content = google_button_content
            google_login_button.disabled = False
            show_snackbar(f"Google Login Error: {str(ex)}", color=ft.Colors.RED)
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

    # Google Login Button
    google_button_content = ft.Row([
        ft.Image(src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg", width=24, height=24),
        ft.Text("Sign in with Google", color=GRAY_600, weight=ft.FontWeight.BOLD, size=16)
    ], alignment=ft.MainAxisAlignment.CENTER, tight=True)

    google_login_button = ft.OutlinedButton(
        content=google_button_content,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            side=ft.BorderSide(1, GRAY_300),
            padding=ft.padding.symmetric(vertical=15),
            overlay_color=GRAY_300,
        ),
        height=55,
        width=300,
        on_click=on_google_login_click
    )

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
                    google_login_button, # Added Google Button here
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
