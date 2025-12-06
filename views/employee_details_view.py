import flet as ft
from db import get_employee_by_id, db, update_employee, create_user

def employee_details_view(page: ft.Page, go_to, create_app_bar, show_snackbar, employee_id=None, readonly=False):
    """Create and return the employee edit/view content"""

    # Define colors
    BLACK = "#0F0F0F"

    if readonly:
         return _view_employee_detail(page, go_to, create_app_bar, show_snackbar, employee_id)

    # Get employee data if ID provided
    employee_data = None
    if employee_id:
        employee_data = get_employee_by_id(employee_id)
        if not employee_data:
            # If employee not found, show error and redirect
            def show_error_and_redirect():
                show_snackbar("Employee not found", ft.Colors.RED)
                go_to("/employees")

            page.add(ft.Container())  # Placeholder
            page.update()
            show_error_and_redirect()
            return

    # Get departments for dropdown
    departments_data = db.get_all_departments()
    department_options = [ft.dropdown.Option(key=str(dept.get('id', dept['name'])),
                                        text=dept['name'].title()) for dept in departments_data]

    # Form fields
    full_name_field = ft.TextField(
        label="Full Name",
        value=employee_data.get('full_name', '') if employee_data else '',
        width=300,
        border_radius=12,
        border_color=BLACK,
        bgcolor=ft.Colors.WHITE
    )

    username_field = ft.TextField(
        label="Username",
        value=employee_data.get('username', '') if employee_data else '',
        width=300,
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
        border_color=BLACK,
        disabled=bool(employee_data)
    )

    password_field = ft.TextField(
        label="Password" if not employee_data else "New Password (leave empty to keep current)",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=12,
        border_color=BLACK,
        bgcolor=ft.Colors.WHITE
    )

    role_field = ft.Dropdown(
        label="Role",
        options=[
            ft.dropdown.Option("admin", "Administrator"),
            ft.dropdown.Option("secretary", "secretary"),
            ft.dropdown.Option("team_leader", "team_leader"),
            ft.dropdown.Option("technician", "technician")
        ],
        value=employee_data.get('role', '') if employee_data else '',
        width=300,
        bgcolor=ft.Colors.WHITE,
        border_color=BLACK,
        border_radius=12
    )

    department_field = ft.Dropdown(
        label="Department",
        options=department_options,
        value=str(employee_data.get('department_id', '')) if employee_data else '',
        width=300,
        border_color=BLACK,
        bgcolor=ft.Colors.WHITE,
        border_radius=12
    )

    active_field = ft.Checkbox(
        label="Active Employee",
        value=employee_data.get('active', True) if employee_data else True
    )

    # Phone field
    phone_field = ft.TextField(
        label="Phone Number (Optional)",
        value=employee_data.get('phone', '') if employee_data else '',
        width=300,
        border_color=BLACK,
        border_radius=12,
        bgcolor=ft.Colors.WHITE
    )

    # Email field
    email_field = ft.TextField(
        label="Email (Optional)",
        border_color=BLACK,
        value=employee_data.get('email', '') if employee_data else '',
        width=300,
        border_radius=12,
        bgcolor=ft.Colors.WHITE
    )

    # Loading state
    is_loading = False

    def validate_form():
        """Validate form fields"""
        errors = []

        if not full_name_field.value or not full_name_field.value.strip():
            errors.append("Full name is required")

        if not username_field.value or not username_field.value.strip():
            errors.append("Username is required")

        if not employee_data and (not password_field.value or not password_field.value.strip()):
            errors.append("Password is required for new employees")

        if not role_field.value:
            errors.append("Role is required")

        if not department_field.value:
            errors.append("Department is required")

        # Validate username format (alphanumeric and underscore only)
        username = username_field.value.strip() if username_field.value else ""
        if username and not username.replace('_', '').isalnum():
            errors.append("Username can only contain letters, numbers, and underscores")

        # Validate email format if provided
        email = email_field.value.strip() if email_field.value else ""
        if email and '@' not in email:
            errors.append("Invalid email format")

        return errors

    def save_employee(e):
        """Save employee data"""
        nonlocal is_loading

        if is_loading:
            return

        # Validate form
        validation_errors = validate_form()
        if validation_errors:
            error_message = "\n".join(validation_errors)
            show_snackbar(f"Validation errors:\n{error_message}", ft.Colors.RED)
            return

        is_loading = True
        save_button.disabled = True
        save_button.text = "Saving..."
        page.update()

        try:
            # Prepare employee data
            employee_update_data = {
                'full_name': full_name_field.value.strip(),
                'username': username_field.value.strip(),
                'role': role_field.value,
                'department_id': int(department_field.value),
                'active': active_field.value
            }

            # Add optional fields if provided
            if phone_field.value and phone_field.value.strip():
                employee_update_data['phone'] = phone_field.value.strip()

            if email_field.value and email_field.value.strip():
                employee_update_data['email'] = email_field.value.strip()

            # Add password if provided
            if password_field.value and password_field.value.strip():
                employee_update_data['password'] = password_field.value

            # Save employee
            if employee_data:  # Update existing employee
                success = update_employee(employee_data['id'], employee_update_data)
                if success:
                    show_snackbar("Employee updated successfully!", ft.Colors.GREEN)
                    # Refresh employees data logic should be handled by caller or refresh on load
                    go_to("/employees")
                else:
                    show_snackbar("Failed to update employee", ft.Colors.RED)
            else:  # Create new employee
                success = create_user(
                    username=employee_update_data['username'],
                    full_name=employee_update_data['full_name'],
                    password=employee_update_data['password'],
                    role=employee_update_data['role'],
                    department_id=employee_update_data['department_id'],
                    active=employee_update_data['active']
                )

                if success:
                    show_snackbar("Employee created successfully!", ft.Colors.GREEN)
                    # Refresh employees data
                    go_to("/employees")
                else:
                    show_snackbar("Failed to create employee. Username may already exist.", ft.Colors.RED)

        except Exception as ex:
            print(f"Error saving employee: {ex}")
            show_snackbar("An error occurred while saving employee", ft.Colors.RED)

        finally:
            is_loading = False
            save_button.disabled = False
            save_button.text = "Save Employee"
            page.update()

    def cancel_edit(e):
        """Cancel editing and go back"""
        go_to("/employees")

    # Action buttons
    save_button = ft.ElevatedButton(
        "Save Employee",
        icon=ft.Icons.SAVE,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.BLUE,
            color=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=24, vertical=12)
        ),
        on_click=save_employee
    )

    cancel_button = ft.ElevatedButton(
        "Cancel",
        icon=ft.Icons.CANCEL,
        style=ft.ButtonStyle(
            bgcolor=ft.Colors.GREY_300,
            color=ft.Colors.GREY_800,
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=ft.padding.symmetric(horizontal=24, vertical=12)
        ),
        on_click=cancel_edit
    )

    # Employee info display (for edit mode)
    info_section = None
    if employee_data:
        info_section = ft.Container(
            content=ft.Column([
                ft.Text("Employee Information", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text(f"Created: {employee_data.get('created_at', 'Unknown')[:10] if employee_data.get('created_at') else 'Unknown'}",
                                size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"Last Updated: {employee_data.get('updated_at', 'Unknown')[:10] if employee_data.get('updated_at') else 'Unknown'}",
                                size=12, color=ft.Colors.GREY_600),
                    ], spacing=4),
                    ft.Column([
                        ft.Text(f"Last Login: {employee_data.get('last_login', 'Never')[:10] if employee_data.get('last_login') else 'Never'}",
                                size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"Status: {'Active' if employee_data.get('active') else 'Inactive'}",
                                size=12,
                                color=ft.Colors.GREEN if employee_data.get('active') else ft.Colors.RED,
                                weight=ft.FontWeight.BOLD),
                    ], spacing=4)
                ])
            ], spacing=8),
            bgcolor=ft.Colors.BLUE_GREY_50,
            border_radius=12,
            padding=16,
            margin=ft.margin.only(bottom=20)
        )

    # Form content
    form_content = ft.Column([
        # Info section for existing employees
        info_section if info_section else ft.Container(),

        # Form title
        ft.Text(
            f"{'Edit Employee' if employee_data else 'Add New Employee'}",
            size=24,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_GREY_800
        ),

        ft.Divider(),

        # Form fields in two columns
        ft.Column([
            ft.Column([
                full_name_field,
                username_field,
                password_field,
                role_field
            ], spacing=16),

            ft.Column([
                department_field,
                phone_field,
                email_field,
                ft.Container(
                    content=active_field,
                    margin=ft.margin.only(top=12)
                )
            ], spacing=16)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

        ft.Divider(),

        # Action buttons
        ft.Row([
            cancel_button,
            save_button
        ], alignment=ft.MainAxisAlignment.END, spacing=12)

    ], spacing=10, scroll=ft.ScrollMode.AUTO)

    # Return the complete view
    return ft.View(
        route=f"/edit_employee{'/' + employee_id if employee_id else ''}",
        appbar=create_app_bar(
            f"{'Edit Employee' if employee_data else 'Add Employee'}",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Back to Employees",
                    on_click=lambda e: go_to("/employees")
                )
            ]
        ),
        controls=[
            ft.Container(
                content=form_content,
                expand=True,
                margin=ft.margin.only(left=15, right=15, top=10, bottom=10),
                padding=20
            )
        ]
    )


def _view_employee_detail(page, go_to, create_app_bar, show_snackbar, employee_id: str):
    """View employee details (read-only)"""
    employee_data = db.get_employee_by_id(employee_id)

    if not employee_data:
        show_snackbar("Employee not found", ft.Colors.RED)
        go_to("/employees")
        return

    # Get department name
    department_name = "Unknown"
    if employee_data.get('department_id'):
        departments = db.get_all_departments()
        for dept in departments:
            if str(dept.get('id')) == str(employee_data['department_id']):
                department_name = dept['name'].title()
                break

    # Create read-only view
    content = ft.Column([
        # Header
        ft.Container(
            content=ft.Row([
                ft.CircleAvatar(
                    content=ft.Text(
                        employee_data['full_name'][0].upper(),
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    bgcolor=ft.Colors.BLUE,
                    radius=30
                ),
                ft.Column([
                    ft.Text(
                        employee_data['full_name'],
                        size=20,
                        weight=ft.FontWeight.BOLD
                    ),
                    ft.Text(
                        f"@{employee_data['username']}",
                        size=14,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=0, expand=True),
                ft.Container(
                    content=ft.Text(
                        "ACTIVE" if employee_data['active'] else "INACTIVE",
                        size=12,
                        color=ft.Colors.WHITE,
                        weight=ft.FontWeight.BOLD
                    ),
                    bgcolor=ft.Colors.GREEN if employee_data['active'] else ft.Colors.RED,
                    border_radius=12,
                    padding=ft.padding.symmetric(horizontal=12, vertical=6)
                )
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=20,
            margin=ft.margin.only(bottom=20)
        ),

        # Details cards
        ft.Column([
            # Basic info
            ft.Container(
                content=ft.Column([
                    ft.Text("Basic Information", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.WORK, color=ft.Colors.BLUE),
                        title=ft.Text("Role"),
                        subtitle=ft.Text(employee_data['role'].replace('_', ' ').title())
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.BUSINESS, color=ft.Colors.BLUE),
                        title=ft.Text("Department"),
                        subtitle=ft.Text(department_name)
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.EMAIL, color=ft.Colors.BLUE),
                        title=ft.Text("Email"),
                        subtitle=ft.Text(employee_data.get('email', 'Not provided'))
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.PHONE, color=ft.Colors.BLUE),
                        title=ft.Text("Phone"),
                        subtitle=ft.Text(employee_data.get('phone', 'Not provided'))
                    )
                ], spacing=0),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=20,
                expand=True
            ),

            # Activity info
            ft.Container(
                content=ft.Column([
                    ft.Text("Activity Information", size=16, weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.CALENDAR_TODAY, color=ft.Colors.GREEN),
                        title=ft.Text("Created"),
                        subtitle=ft.Text(employee_data.get('created_at', 'Unknown')[:10] if employee_data.get('created_at') else 'Unknown')
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.UPDATE, color=ft.Colors.ORANGE),
                        title=ft.Text("Last Updated"),
                        subtitle=ft.Text(employee_data.get('updated_at', 'Unknown')[:10] if employee_data.get('updated_at') else 'Unknown')
                    ),
                    ft.ListTile(
                        leading=ft.Icon(ft.Icons.LOGIN, color=ft.Colors.PURPLE),
                        title=ft.Text("Last Login"),
                        subtitle=ft.Text(employee_data.get('last_login', 'Never')[:10] if employee_data.get('last_login') else 'Never')
                    )
                ], spacing=0),
                bgcolor=ft.Colors.WHITE,
                border_radius=12,
                padding=20,
                expand=True
            )
        ], spacing=20),

        # Action buttons
        ft.Row([
            ft.ElevatedButton(
                "Edit Employee",
                icon=ft.Icons.EDIT,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE,
                    shape=ft.RoundedRectangleBorder(radius=12)
                ),
                on_click=lambda e: go_to(f"/edit_employee/{employee_id}")
            ),
            ft.ElevatedButton(
                "Back to List",
                icon=ft.Icons.ARROW_BACK,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREY_300,
                    color=ft.Colors.GREY_800,
                    shape=ft.RoundedRectangleBorder(radius=12)
                ),
                on_click=lambda e: go_to("/employees")
            )
        ], alignment=ft.MainAxisAlignment.END, spacing=12)

    ], spacing=20, scroll=ft.ScrollMode.AUTO)

    return ft.View(
        route=f"/view_employee/{employee_id}",
        appbar=create_app_bar(
            f"Employee Details",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    tooltip="Edit Employee",
                    on_click=lambda e: go_to(f"/edit_employee/{employee_id}")
                ),
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Back to Employees",
                    on_click=lambda e: go_to("/employees")
                )
            ]
        ),
        controls=[
            ft.Container(
                content=content,
                expand=True,
                margin=ft.margin.only(left=15, right=15, top=10, bottom=10)
            )
        ]
    )
