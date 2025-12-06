import flet as ft
from datetime import datetime
from db import create_vehicle, db

def add_vehicle_view(page: ft.Page, create_app_bar, current_user, show_snackbar):
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
