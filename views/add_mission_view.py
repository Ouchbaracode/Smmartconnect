import flet as ft
from datetime import datetime
from db import get_all_employees, get_all_vehicles, db, create_mission

def add_mission_view(page: ft.Page, create_app_bar, current_user):
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
    team_display_container = ft.Ref[ft.Column]()
    team_leader_dropdown = ft.Ref[ft.Dropdown]()
    vehicle_dropdown = ft.Ref[ft.Dropdown]()

    # Tools multi-select references
    tools_dropdown = ft.Ref[ft.Dropdown]()
    tools_display_container = ft.Ref[ft.Column]()  # Changed to Column for better control

    # Success/Error message
    message_container = ft.Ref[ft.Container]()

    # Selected tools tracking
    selected_tools_list = []
    # Selected team tracking
    selected_team_list = []

    # Load data from database
    def load_form_data():
        """Load employees, vehicles, tools, etc. from database"""
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

            # Get all tools from database
            tools = db.get_all_tools()
            tools_list = [{"key": tool["id"], "name": tool["name"]} for tool in tools if tool.get("status", "AVAILABLE") == "AVAILABLE"]

            return persons, team_leaders, vehicle_list, tools_list
        except Exception as e:
            print(f"Error loading form data: {e}")
            return [], [], [], []

    # Load the data
    PERSONS, TEAM_LEADERS, VEHICLES, TOOLS = load_form_data()

    # Tool selection handlers
    def on_tool_select(e):
        """Add tool to selected list"""
        if e.control.value:
            tool_id = e.control.value
            tool_name = next((t["name"] for t in TOOLS if t["key"] == tool_id), "Unknown Tool")

            # Check if tool is already selected
            if tool_id not in [t["id"] for t in selected_tools_list]:
                selected_tools_list.append({"id": tool_id, "name": tool_name})
                update_tools_display()

            # Reset dropdown
            e.control.value = None
            e.control.update()

    def on_person_select(e):
        """Add person to selected team list"""
        if e.control.value:
            person_id = e.control.value
            person_name = next((p["name"] for p in PERSONS if p["key"] == person_id), "Unknown Person")

            # Check if person is already selected
            if person_id not in [p["id"] for p in selected_team_list]:
                selected_team_list.append({"id": person_id, "name": person_name})
                update_team_display()

            # Reset dropdown
            e.control.value = None
            e.control.update()
    def on_person_remove(person_id):
        """Remove person from selected team list"""
        nonlocal selected_team_list
        selected_team_list = [p for p in selected_team_list if p["id"] != person_id]
        update_team_display()

    def update_team_display():
        """Update the visual display of selected team members"""
        try:
            # Create chips for selected team members
            chips = []
            for person in selected_team_list:
                chip = ft.Container(
                    content=ft.Row([
                        ft.Text(person["name"], size=12, color=BLACK),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color="#666666",
                            on_click=lambda e, pid=person["id"]: on_person_remove(pid),
                            tooltip="Remove person"
                        )
                    ], spacing=4, tight=True),
                    bgcolor="#E8F5E8",
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    margin=ft.margin.only(right=4, bottom=4)
                )
                chips.append(chip)

            # Update the container content
            if chips:
                team_display_container.current.controls = [
                    ft.Text("Selected Team Members:", size=12, color="#666666"),
                    ft.Row(chips, wrap=True, spacing=0)
                ]
            else:
                team_display_container.current.controls = []

            # Only update if the container is already on the page
            if team_display_container.current.page:
                team_display_container.current.update()

        except Exception as e:
            print(f"Error updating team display: {e}")

    def on_tool_remove(tool_id):
        """Remove tool from selected list"""
        nonlocal selected_tools_list
        selected_tools_list = [t for t in selected_tools_list if t["id"] != tool_id]
        update_tools_display()

    def update_tools_display():
        """Update the visual display of selected tools"""
        try:
            # Create chips for selected tools
            chips = []
            for tool in selected_tools_list:
                chip = ft.Container(
                    content=ft.Row([
                        ft.Text(tool["name"], size=12, color=BLACK),
                        ft.IconButton(
                            icon=ft.Icons.CLOSE,
                            icon_size=16,
                            icon_color="#666666",
                            on_click=lambda e, tid=tool["id"]: on_tool_remove(tid),
                            tooltip="Remove tool"
                        )
                    ], spacing=4, tight=True),
                    bgcolor="#E3F2FD",
                    border_radius=16,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    margin=ft.margin.only(right=4, bottom=4)
                )
                chips.append(chip)

            # Update the container content
            if chips:
                tools_display_container.current.controls = [
                    ft.Text("Selected Tools:", size=12, color="#666666"),
                    ft.Row(chips, wrap=True, spacing=0)
                ]
            else:
                tools_display_container.current.controls = []

            # Only update if the container is already on the page
            if tools_display_container.current.page:
                tools_display_container.current.update()

        except Exception as e:
            print(f"Error updating tools display: {e}")

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

        if not selected_team_list:
            errors.append("At least one team member is required")

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
        nonlocal selected_tools_list, selected_team_list

        title_field.current.value = ""
        location_field.current.value = ""
        due_date_field.current.value = ""
        due_time_field.current.value = ""
        status_dropdown.current.value = None
        description_field.current.value = ""
        assigned_person_dropdown.current.value = None
        team_leader_dropdown.current.value = None
        vehicle_dropdown.current.value = None
        tools_dropdown.current.value = None

        # Clear selected items
        selected_tools_list = []
        selected_team_list = []
        update_tools_display()
        update_team_display()

        # Update all fields
        for field in [title_field.current, location_field.current, due_date_field.current,
                    due_time_field.current, status_dropdown.current, description_field.current,
                    assigned_person_dropdown.current, team_leader_dropdown.current,
                    vehicle_dropdown.current, tools_dropdown.current]:
            if field:
                field.update()

    # Submit handler
    def on_submit(e):
        # Validate form
        errors = validate_form()

        if errors:
            show_message(f"Please fix the following errors: {', '.join(errors)}", True)
            return

        # Get selected team member IDs
        selected_team_ids = [person["id"] for person in selected_team_list]
        selected_tool_ids = [tool["id"] for tool in selected_tools_list]

        # Prepare mission data for database
        mission_data = {
            "title": title_field.current.value.strip(),
            "location": location_field.current.value.strip(),
            "due_date": due_date_field.current.value.strip(),
            "due_time": due_time_field.current.value.strip(),
            "status": status_dropdown.current.value,
            "description": description_field.current.value.strip() if description_field.current.value else "",
            "assigned_team": selected_team_ids,  # Changed from assigned_person_id
            "team_leader_id": team_leader_dropdown.current.value,
            "required_tools": selected_tool_ids,
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
                        'assigned_to': mission_data.get('assigned_person_id'),
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
        label="Select Team Members",
        hint_text="Choose team members for this mission",
        options=[ft.dropdown.Option(p["key"], p["name"]) for p in PERSONS],
        border_radius=8,
        bgcolor=WHITE,
        border_color="#E0E0E0",
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        on_change=on_person_select,
    )

    team_display_container.current = ft.Column([], spacing=4)
    team_section = ft.Container(
        content=ft.Column([
            assigned_person_dropdown.current,
            ft.Container(height=8),
            team_display_container.current,
        ], spacing=4),
        padding=0,
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


    # Tools multi-select dropdown
    tools_dropdown.current = ft.Dropdown(
        label="Select Tools",
        hint_text="Choose tools for this mission",
        options=[ft.dropdown.Option(t["key"], t["name"]) for t in TOOLS],
        border_radius=8,
        bgcolor=WHITE,
        border_color="#E0E0E0",
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        on_change=on_tool_select,
    )

    # Tools display container (Column for better control)
    tools_display_container.current = ft.Column([], spacing=4)

    # Tools container wrapper
    tools_section = ft.Container(
        content=ft.Column([
            tools_dropdown.current,
            ft.Container(height=8),
            tools_display_container.current,
        ], spacing=4),
        padding=0,
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

                team_section,  # Multi-select team section
                team_leader_dropdown.current,
                # Resources Section
                ft.Container(height=10),  # Spacer
                ft.Text(
                    "Resources",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=BLACK,
                ),

                tools_section,  # Multi-select tools section
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
