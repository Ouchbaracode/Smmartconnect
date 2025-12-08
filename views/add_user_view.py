import flet as ft
from db import create_user, db

def add_user_view(page: ft.Page, create_app_bar, current_user, show_snackbar):
    """Enhanced user creation with database integration"""
    # Light mode colors
    GOLD = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    LIGHT_GRAY = "#FFFFFF"
    DARK_GRAY = "#333333"
    BORDER_COLOR = "#e0e0e0"

    role_list = ['admin', 'secretary', 'team_leader', 'technician']
    is_loading = False

    # Get departments from database
    departments = {
        1: "logistic",
        2: "administration",
        3: "Field_Operations",
        4: "admin"
    }

    def get_department_id_from_dict(dropdown_value, department_dict):
        if dropdown_value:
            try:
                key = int(dropdown_value.split()[0])
                return key if key in department_dict else None
            except:
                return None
        return None

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

        if not department_field.value:
            show_snackbar("Department is required")
            return

        username = username_field.value.strip()
        Fullname = Full_name.value.strip()
        password = password_field.value.strip()
        department_id = get_department_id_from_dict(department_field.value, departments)
        Role = Rol_Drop.value
        active = True

        try:
            success = create_user(username, Fullname, password, Role, department_id, active)
            if success:
                show_snackbar("User created successfully!", color=ft.Colors.GREEN)
                # Clear form
                username_field.value = ""
                Full_name.value = ""
                password_field.value = ""
                Rol_Drop.value = None
                department_field.value = None
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
    department_field = ft.Dropdown(
        label="Department",
        options=[ft.dropdown.Option(f"{key} {value.title()}", f"{key} {value}") for key, value in departments.items()],
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
                    department_field,
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
