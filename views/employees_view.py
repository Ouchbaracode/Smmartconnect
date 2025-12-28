import flet as ft
from db import get_all_employees, delete_employee

def employees_view(page: ft.Page, go_to, create_app_bar, create_bottom_nav, show_snackbar):
    """Create and return the complete employee management content using real data"""

    employees_data = []

    def refresh_employees_data():
        """Refresh employees data from database"""
        nonlocal employees_data
        try:
            employees_data = get_all_employees()
        except Exception as e:
            print(f"Error refreshing employees data: {e}")
            employees_data = []

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
            go_to(f"/view_employee/{employee_data['id']}")
            # Here you could navigate to a detailed employee view

        def edit_employee(e):
            go_to(f"/edit_employee/{employee_data['id']}")
            # Here you could navigate to an employee edit form

        def delete_employee_action(e):
            def confirm_delete(e):
                try:
                    success = delete_employee(employee_data["id"])
                    if success:
                        show_snackbar("Employee deactivated successfully", ft.Colors.GREEN)
                        refresh_employees_and_update()
                        confirm_dialog.open = False
                        page.update()
                    else:
                        show_snackbar("Failed to deactivate employee", ft.Colors.RED)
                        confirm_dialog.open = False
                        page.update()
                except Exception as ex:
                    show_snackbar(f"Error: {str(ex)}", ft.Colors.RED)
                    confirm_dialog.open = False
                    page.update()

            def cancel_delete(e):
                confirm_dialog.open = False
                page.update()

            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Confirm Deactivation"),
                content=ft.Text(f"Are you sure you want to deactivate {employee_data['name']}?"),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_delete),
                    ft.TextButton("Deactivate", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
            )
            page.open(confirm_dialog)
            confirm_dialog.open = True
            page.update()

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
                        ),
                        # Mission Status
                        ft.Container(
                            content=ft.Text(
                                employee_data.get("mission_status", "AVAILABLE").replace('_', ' '),
                                size=10,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=ft.Colors.ORANGE if employee_data.get("mission_status") == "IN_MISSION" else ft.Colors.BLUE_GREY,
                            border_radius=12,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            visible=employee_data.get("mission_status") == "IN_MISSION"
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

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
                            f"Last login: {employee_data.get('last_login', 'Never') or 'Never'}",
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
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            tooltip="Deactivate Employee",
                            on_click=delete_employee_action
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

    def refresh_employees_and_update():
            """Refresh employees data and update the view"""
            refresh_employees_data()
            update_employee_list(page)
            show_snackbar("Updated data", ft.Colors.GREEN)

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
            "Employees",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh",
                    on_click=lambda e: refresh_employees_and_update()
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
