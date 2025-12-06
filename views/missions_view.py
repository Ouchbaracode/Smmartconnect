import flet as ft
from datetime import datetime
from db import get_all_missions_with_details, get_mission_stats, update_mission_status, add_mission_log

def missions_view(page: ft.Page, go_to, show_snackbar):
    """Mission management page using real database data"""

    # Define colors
    GOLD = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#0F0F0F"
    ORANGE = "#FFA500"
    GREEN = "#4CAF50"
    RED = "#F44336"
    GRAY = "#9E9E9E"
    BLUE = "#2196F3"

    def format_date_short(date_string: str) -> str:
        """Format date string for display (short version)"""
        try:
            if not date_string:
                return "Not set"

            # Parse ISO format date
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime("%b %d, %Y")
        except:
            return date_string

    def get_status_color(status):
        """Return color based on mission status"""
        if status == "PENDING":
            return ORANGE
        elif status == "IN_PROGRESS":
            return GOLD
        elif status == "COMPLETED":
            return GREEN
        elif status == "CANCELLED":
            return RED
        else:
            return GRAY


    def create_mission_card(mission):
        """Create a mission card component using real data"""
        def go_to_detail(e):
            show_mission_details(mission)

        def quick_status_update(new_status):
            def update_status(e):
                try:
                    success = update_mission_status(mission['id'], new_status)
                    if success:
                        show_snackbar(f"Mission status updated to {new_status}", GREEN)
                        refresh_missions_and_update()
                    else:
                        show_snackbar("Failed to update mission status", RED)
                except Exception as ex:
                    show_snackbar(f"Error: {str(ex)}", RED)
            return update_status

        # Quick action buttons based on current status
        quick_actions = []
        current_status = mission.get('status', 'PENDING')

        if current_status == 'PENDING':
            quick_actions.append(
                ft.IconButton(
                    ft.Icons.PLAY_ARROW,
                    tooltip="Start Mission",
                    icon_color=GOLD,
                    on_click=quick_status_update('IN_PROGRESS')
                )
            )
        elif current_status == 'IN_PROGRESS':
            quick_actions.append(
                ft.IconButton(
                    ft.Icons.CHECK_CIRCLE,
                    tooltip="Complete Mission",
                    icon_color=GREEN,
                    on_click=quick_status_update('COMPLETED')
                )
            )

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(
                        f"#{mission.get('id', 'Unknown')[:8]}",
                        size=14,
                        color=ft.Colors.GREY_600,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(
                        content=ft.Text(
                            mission.get("status", "Unknown"),
                            size=12,
                            color=WHITE,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=get_status_color(mission.get("status", "Unknown")),
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        border_radius=12
                    )
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Text(
                    mission.get("title", "Untitled Mission"),
                    size=18,
                    color=BLACK,
                    weight=ft.FontWeight.BOLD
                ),

                ft.Row([
                    ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.GREY_600),
                    ft.Text(
                        mission.get("location", "No location"),
                        size=14,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=5),


                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=16, color=ft.Colors.GREY_600),
                    ft.Text(
                        f"Due: {format_date_short(mission.get('due_date', ''))}",
                        size=12,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5),

                ft.Row([
                    ft.Container(
                    ),
                    ft.Row([
                        *quick_actions,
                        ft.IconButton(
                            ft.Icons.VISIBILITY,
                            tooltip="View Details",
                            icon_color=BLACK,
                            on_click=go_to_detail
                        )
                    ], spacing=0)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            ], spacing=8),
            padding=16,
            margin=ft.margin.only(bottom=8),
            bgcolor=WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.Colors.GREY_300),
            ink=True,
            on_click=go_to_detail
        )

    def show_mission_details(mission):
        """Show detailed mission information with personnel, tools, and vehicles"""
        def close_dialog(e):
            dialog.open = False
            page.update()

        def update_status_action(new_status):
            def update_status(e):
                try:
                    success = update_mission_status(mission["id"], new_status)
                    if success:
                        # Add log entry
                        add_mission_log(mission["id"], f"Status changed to {new_status}", "System")
                        show_snackbar(f"Mission status updated to {new_status}", GREEN)
                        refresh_missions_and_update()
                        close_dialog(e)
                    else:
                        show_snackbar("Failed to update mission status", RED)
                except Exception as ex:
                    show_snackbar(f"Error: {str(ex)}", RED)
            return update_status

        def add_note_action(e):
            def save_note(e):
                note_text = note_field.value.strip()
                if note_text:
                    try:
                        success = add_mission_log(mission["id"], "Note added", "Current User", note_text)
                        if success:
                            show_snackbar("Note added successfully", GREEN)
                            note_field.value = ""
                            note_field.update()
                        else:
                            show_snackbar("Failed to add note", RED)
                    except Exception as ex:
                        show_snackbar(f"Error: {str(ex)}", RED)
                else:
                    show_snackbar("Please enter a note", RED)

            note_field = ft.TextField(
                hint_text="Enter your note...",
                multiline=True,
                max_lines=3,
                bgcolor=WHITE
            )

            note_dialog = ft.AlertDialog(
                title=ft.Text("Add Note", weight=ft.FontWeight.BOLD),
                content=ft.Container(
                    content=note_field,
                    width=300,
                    height=100
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: (setattr(note_dialog, 'open', False), page.update())),
                    ft.ElevatedButton(
                        "Save Note",
                        bgcolor=GOLD,
                        color=BLACK,
                        on_click=save_note
                    )
                ]
            )

            page.open(note_dialog)
            note_dialog.open = True
            page.update()

        # Helper functions to create resource items
        def create_personnel_item(person):
            """Create a personnel item display"""
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.PERSON, color=WHITE, size=16),
                        bgcolor=GOLD,
                        width=32,
                        height=32,
                        border_radius=16,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            person.get('name', person.get('full_name', 'Unknown')),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=BLACK
                        ),
                        ft.Text(
                            person.get('role', person.get('position', 'Staff')),
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(
                            person.get('status', 'Available'),
                            color=WHITE,
                            size=8,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=GREEN if person.get('status', 'Available') == 'Available' else ORANGE,
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=8
                    )
                ], spacing=8),
                bgcolor=ft.Colors.GREY_50,
                padding=8,
                border_radius=6,
                margin=ft.margin.only(bottom=4)
            )

        def create_tool_item(tool):
            """Create a tool item display"""
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.BUILD, color=WHITE, size=16),
                        bgcolor=BLUE,
                        width=32,
                        height=32,
                        border_radius=6,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            tool.get('name', tool.get('tool_name', 'Unknown Tool')),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=BLACK
                        ),
                        ft.Text(
                            tool.get('type', tool.get('category', 'Equipment')),
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(
                            tool.get('condition', tool.get('status', 'Good')),
                            color=WHITE,
                            size=8,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=GREEN if tool.get('condition', tool.get('status', 'Good')) in ['Good', 'Available'] else
                                (ORANGE if tool.get('condition', tool.get('status', 'Good')) == 'Fair' else RED),
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=8
                    )
                ], spacing=8),
                bgcolor=ft.Colors.GREY_50,
                padding=8,
                border_radius=6,
                margin=ft.margin.only(bottom=4)
            )

        def create_vehicle_item(vehicle):
            """Create a vehicle item display"""
            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.DIRECTIONS_CAR, color=WHITE, size=16),
                        bgcolor=ORANGE,
                        width=32,
                        height=32,
                        border_radius=6,
                        alignment=ft.alignment.center
                    ),
                    ft.Column([
                        ft.Text(
                            vehicle.get('name', vehicle.get('model', 'Unknown Vehicle')),
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=BLACK
                        ),
                        ft.Text(
                            f"Plate: {vehicle.get('license_plate', vehicle.get('plate_number', vehicle.get('plate', 'N/A')))}",
                            size=10,
                            color=ft.Colors.GREY_600
                        )
                    ], spacing=2, expand=True),
                    ft.Container(
                        content=ft.Text(
                            vehicle.get('status', 'Available'),
                            color=WHITE,
                            size=8,
                            weight=ft.FontWeight.BOLD
                        ),
                        bgcolor=GREEN if vehicle.get('status', 'Available') == 'Available' else
                                (ORANGE if vehicle.get('status') == 'In Use' else RED),
                        padding=ft.padding.symmetric(horizontal=6, vertical=2),
                        border_radius=8
                    )
                ], spacing=8),
                bgcolor=ft.Colors.GREY_50,
                padding=8,
                border_radius=6,
                margin=ft.margin.only(bottom=4)
            )

        # Determine available actions based on status
        current_status = mission.get('status', 'PENDING')
        action_buttons = []

        if current_status == 'PENDING':
            action_buttons.append(
                ft.ElevatedButton(
                    "Start Mission",
                    icon=ft.Icons.PLAY_ARROW,
                    on_click=update_status_action('IN_PROGRESS'),
                    bgcolor=GOLD,
                    color=BLACK
                )
            )
        elif current_status == 'IN_PROGRESS':
            action_buttons.extend([
                ft.ElevatedButton(
                    "Complete",
                    icon=ft.Icons.CHECK_CIRCLE,
                    on_click=update_status_action('COMPLETED'),
                    bgcolor=GREEN,
                    color=WHITE
                ),
                ft.ElevatedButton(
                    "Pause",
                    icon=ft.Icons.PAUSE,
                    on_click=update_status_action('PENDING'),
                    bgcolor=ORANGE,
                    color=WHITE
                )
            ])

        action_buttons.append(
            ft.ElevatedButton(
                "Add Note",
                icon=ft.Icons.NOTE_ADD,
                on_click=add_note_action,
                style=ft.ButtonStyle(bgcolor=BLUE, color=WHITE)
            )
        )

        # Create scrollable content with tabs for better organization
        def create_basic_info_tab():
            return ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT, size=48, color=GOLD),
                    ft.Column([
                        ft.Text(f"ID: #{mission.get('id', 'Unknown')[:8]}", size=14),
                        ft.Text(f"Status: {mission.get('status', 'Unknown')}", size=12, color=get_status_color(mission.get('status', 'Unknown'))),
                    ], spacing=4, expand=True)
                ]),
                ft.Divider(),
                ft.Column([
                    ft.Text("Description:", weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(mission.get("description", "No description"), size=11, color=ft.Colors.GREY_700),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Text("Location:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Text(mission.get("location", "No location"), size=11)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Due Date:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Text(format_date_short(mission.get("due_date", "")), size=11)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Duration:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Text(f"{mission.get('estimated_duration', 0)} hours" if mission.get('estimated_duration') else "Not specified", size=11)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Created:", weight=ft.FontWeight.BOLD, size=12),
                        ft.Text(format_date_short(mission.get("created_at", "")), size=11)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=6)
            ], spacing=8)

        def create_resources_tab():
            # Extract personnel data - combine assigned user and team leader
            personnel = []
            if mission.get('team_members'):
                personnel.extend(mission['team_members'])

            # Add team leader
            if mission.get('team_leader'):
                personnel.append(mission['team_leader'])

            # Extract vehicle data - convert single vehicle to array
            vehicles = []
            if mission.get('vehicle'):
                vehicles.append({
                    'name': mission['vehicle'].get('model', 'Unknown Vehicle'),
                    'license_plate': mission['vehicle'].get('plate_number', 'N/A'),
                    'status': 'Assigned'
                })

            # Tools - your database doesn't seem to have tools yet
            tools = mission.get('tools', [])  # This will be empty for now

            return ft.Column([
                # Personnel Section
                ft.Text("👥 Personnel", weight=ft.FontWeight.BOLD, size=14, color=GOLD),
                ft.Container(
                    content=ft.Column([
                        create_personnel_item(person) for person in personnel
                    ] if personnel else [
                        ft.Container(
                            content=ft.Text("No personnel assigned", color=ft.Colors.GREY_500, size=12),
                            alignment=ft.alignment.center,
                            height=40
                        )
                    ], spacing=4),
                    height=max(min(len(personnel) * 50, 300), 50) if personnel else 50,
                    expand=True
                ),

                ft.Container(height=8),

                # Tools Section
                ft.Text("🔧 Tools & Equipment", weight=ft.FontWeight.BOLD, size=14, color=BLUE),
                ft.Container(
                    content=ft.Column([
                        create_tool_item(tool) for tool in tools
                    ] if tools else [
                        ft.Container(
                            content=ft.Text("No tools assigned", color=ft.Colors.GREY_500, size=12),
                            alignment=ft.alignment.center,
                            height=40
                        )
                    ], spacing=4),
                    height=max(min(len(tools) * 50, 300), 50) if tools else 50,
                    expand=True
                ),

                ft.Container(height=8),

                # Vehicles Section
                ft.Text("🚗 Vehicles", weight=ft.FontWeight.BOLD, size=14, color=ORANGE),
                ft.Container(
                    content=ft.Column([
                        create_vehicle_item(vehicle) for vehicle in vehicles
                    ] if vehicles else [
                        ft.Container(
                            content=ft.Text("No vehicles assigned", color=ft.Colors.GREY_500, size=12),
                            alignment=ft.alignment.center,
                            height=40
                        )
                    ], spacing=4),
                    height=120,
                    expand=True
                )
            ], spacing=8, scroll=ft.ScrollMode.AUTO)

        # Create tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Details",
                    icon=ft.Icons.INFO,
                    content=ft.Container(
                        content=create_basic_info_tab(),
                        padding=ft.padding.all(8)
                    )
                ),
                ft.Tab(
                    text="Resources",
                    icon=ft.Icons.INVENTORY,
                    content=ft.Container(
                        content=create_resources_tab(),
                        padding=ft.padding.all(8)
                    )
                )
            ]
        )

        dialog = ft.AlertDialog(
            title=ft.Text(f"{mission.get('title', 'Unknown')}", weight=ft.FontWeight.BOLD, size=16),
            content=ft.Container(
                content=tabs,
                width=450,
                height=400
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
                *action_buttons
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        page.open(dialog)
        dialog.open = True
        page.update()

    # State variables for filtering and searching
    current_filter = "All"
    search_query = ""
    missions_data = []

    def refresh_missions_data():
        """Refresh missions data from database"""
        nonlocal missions_data
        try:
            missions_data = get_all_missions_with_details()
            return True
        except Exception as e:
            print(f"Error loading missions: {e}")
            show_snackbar(f"Error loading missions: {str(e)}", RED)
            return False

    def filter_missions(missions, filter_status, search_text):
        """Filter missions based on status and search query"""
        filtered_missions = missions.copy()

        # Filter by status
        if filter_status != "All":
            status_map = {
                "Pending": "PENDING",
                "In Progress": "IN_PROGRESS",
                "Completed": "COMPLETED",
                "Cancelled": "CANCELLED"
            }
            filtered_missions = [mission for mission in filtered_missions if mission.get("status") == status_map.get(filter_status, filter_status)]

        # Filter by search query
        if search_text:
            search_lower = search_text.lower()
            filtered_missions = [
                mission for mission in filtered_missions
                if (search_lower in mission.get("title", "").lower() or
                    search_lower in mission.get("location", "").lower() or
                    search_lower in mission.get("description", "").lower() or
                    search_lower in str(mission.get("id", "")).lower() or
                    search_lower in mission.get('assigned_user', {}).get('full_name', '').lower())
            ]

        return filtered_missions

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
    mission_list_ref = ft.Ref[ft.Column]()
    filter_buttons_ref = ft.Ref[ft.Row]()

    def update_mission_list():
        """Update the mission list based on current filter and search"""
        filtered_missions = filter_missions(missions_data, current_filter, search_query)

        if not filtered_missions:
            mission_list_ref.current.controls = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.ASSIGNMENT, color=GRAY, size=64),
                        ft.Text("No missions found", color=GRAY, size=16),
                        ft.Text("Try adjusting your filters or search query",
                            color=GRAY, size=12, text_align=ft.TextAlign.CENTER)
                    ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    height=200
                )
            ]
        else:
            mission_list_ref.current.controls = [create_mission_card(mission) for mission in filtered_missions]

        mission_list_ref.current.update()

    def on_filter_click(filter_name):
        """Handle filter button clicks"""
        nonlocal current_filter
        current_filter = filter_name

        # Update filter buttons appearance
        filter_buttons_ref.current.controls = [
            create_filter_button("All", current_filter == "All", lambda e: on_filter_click("All")),
            create_filter_button("Pending", current_filter == "Pending", lambda e: on_filter_click("Pending")),
            create_filter_button("In Progress", current_filter == "In Progress", lambda e: on_filter_click("In Progress")),
            create_filter_button("Completed", current_filter == "Completed", lambda e: on_filter_click("Completed")),
            create_filter_button("Cancelled", current_filter == "Cancelled", lambda e: on_filter_click("Cancelled"))
        ]
        filter_buttons_ref.current.update()

        update_mission_list()

    def on_search_change(e):
        """Handle search input changes"""
        nonlocal search_query
        search_query = e.control.value
        update_mission_list()

    def refresh_missions_and_update():
        """Refresh mission data and update the view"""
        if refresh_missions_data():
            update_mission_list()
            show_snackbar("Missions refreshed", GREEN)
        else:
            show_snackbar("Failed to refresh missions", RED)

    # Load initial data
    refresh_missions_data()

    # Initialize form fields
    search_field.current = ft.TextField(
        hint_text="Search by title, location, description, ID, or assigned user...",
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
        create_filter_button("Pending", False, lambda e: on_filter_click("Pending")),
        create_filter_button("In Progress", False, lambda e: on_filter_click("In Progress")),
        create_filter_button("Completed", False, lambda e: on_filter_click("Completed")),
        create_filter_button("Cancelled", False, lambda e: on_filter_click("Cancelled"))
    ], spacing=8, scroll=ft.ScrollMode.AUTO)

    # Mission list (initially showing all missions)
    mission_list_ref.current = ft.Column([
        create_mission_card(mission) for mission in missions_data
    ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

    # Statistics section for missions
    def create_mission_stats():
        if not missions_data:
            return ft.Container()

        try:
            stats = get_mission_stats()
            total_count = stats.get('total', 0)
            pending_count = stats.get('pending', 0)
            in_progress_count = stats.get('in_progress', 0)
            completed_count = stats.get('completed', 0)
            cancelled_count = stats.get('cancelled', 0)

            return ft.Container(
                content=ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(total_count), size=20, weight=ft.FontWeight.BOLD, color=BLACK),
                            ft.Text("Total", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.BLUE_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(pending_count), size=20, weight=ft.FontWeight.BOLD, color=ORANGE),
                            ft.Text("Pending", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.ORANGE_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(in_progress_count), size=20, weight=ft.FontWeight.BOLD, color=GOLD),
                            ft.Text("Active", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.AMBER_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text(str(completed_count), size=20, weight=ft.FontWeight.BOLD, color=GREEN),
                            ft.Text("Completed", size=12, color=ft.Colors.GREY_600)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        bgcolor=ft.Colors.GREEN_50,
                        padding=12,
                        border_radius=8,
                        expand=True
                    )
                ], spacing=8),
                margin=ft.margin.only(bottom=16)
            )
        except Exception as e:
            return ft.Container(
                content=ft.Text(f"Error loading stats: {str(e)}", color=RED),
                padding=12
            )

    # Main content
    content = ft.Column([
        ft.Container(
            content=ft.Column([
                create_mission_stats(),
                search_field.current,
                filter_buttons_ref.current,
                mission_list_ref.current
            ], spacing=16),
            padding=16,
            expand=True
        )
    ], spacing=0, expand=True)

    return ft.View(
        route="/missions",
        appbar=ft.AppBar(
            title=ft.Text("Mission Management", color=BLACK, size=20, weight=ft.FontWeight.BOLD),
            center_title=True,
            bgcolor=WHITE,
            leading=ft.IconButton(
                ft.Icons.ARROW_BACK,
                on_click=lambda e: page.go("/dashboard"),
                icon_color=BLACK
            ),
            actions=[
                ft.IconButton(
                    ft.Icons.ADD,
                    tooltip="Add Mission",
                    on_click=lambda e: page.go("/add-mission"),
                    icon_color=BLACK
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh Missions",
                    on_click=lambda e: refresh_missions_and_update(),
                    icon_color=BLACK
                )
            ],
            elevation=0
        ),
        controls=[
            ft.Container(
                content=content,
                expand=True,
            )
        ]
    )
