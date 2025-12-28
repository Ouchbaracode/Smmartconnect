import flet as ft
from db import get_all_vehicles, db, delete_vehicle

def vehicles_view(page: ft.Page, create_app_bar, go_to, show_snackbar):
    """Car management page using real database data"""

    # Define colors
    GOLD = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#0F0F0F"

    vehicles_data = []

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

        def delete_car_action(e):
            def confirm_delete(e):
                try:
                    success = delete_vehicle(car["id"])
                    if success:
                        show_snackbar("Vehicle deleted successfully", ft.Colors.GREEN)
                        refresh_cars_and_update()
                        confirm_dialog.open = False
                        close_dialog(e)
                    else:
                        show_snackbar("Failed to delete vehicle (must be AVAILABLE)", ft.Colors.RED)
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
                title=ft.Text("Confirm Delete"),
                content=ft.Text(f"Are you sure you want to delete {car.get('model', 'this vehicle')}?"),
                actions=[
                    ft.TextButton("Cancel", on_click=cancel_delete),
                    ft.TextButton("Delete", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ],
            )
            page.open(confirm_dialog)
            confirm_dialog.open = True
            page.update()

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
                ft.Row([
                    ft.ElevatedButton(
                        "Delete",
                        icon=ft.Icons.DELETE,
                        on_click=delete_car_action,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_50, color=ft.Colors.RED)
                    ),
                    ft.ElevatedButton(
                        "Maintenance",
                        icon=ft.Icons.BUILD,
                        on_click=schedule_maintenance,
                        style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE)
                    )
                ])
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        page.open(dialog)
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
        show_snackbar("Vehicles refreshed", ft.Colors.GREEN)

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
            "Vehicle",
            show_nav=False,
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh Vehicles",
                    on_click=lambda e: refresh_cars_and_update()
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD_BOX,
                    tooltip="Add Vehicle",
                    on_click=lambda e: go_to("/add-vehicle")
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
