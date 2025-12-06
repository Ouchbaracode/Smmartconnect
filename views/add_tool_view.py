import flet as ft
from datetime import datetime
from db import create_tool, db

def add_tool_view(page: ft.Page, create_app_bar, current_user, show_snackbar):
    """Enhanced tool creation with database integration"""
    # Light mode colors
    GOLD = "#FFD700"
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    LIGHT_GRAY = "#FFFFFF"
    DARK_GRAY = "#333333"
    BORDER_COLOR = "#e0e0e0"

    # Tool condition options
    condition_options = ['Good', 'Fair', 'Needs Maintenance', 'Poor']

    # Tool categories
    category_options = ['Electrical', 'Mechanical', 'Safety', 'Measurement', 'Communication', 'Other']

    # Form field references
    name_field = ft.Ref[ft.TextField]()
    model_field = ft.Ref[ft.TextField]()
    serial_field = ft.Ref[ft.TextField]()
    category_dropdown = ft.Ref[ft.Dropdown]()
    condition_dropdown = ft.Ref[ft.Dropdown]()
    location_field = ft.Ref[ft.TextField]()
    quantity_field = ft.Ref[ft.TextField]()
    available_quantity_field = ft.Ref[ft.TextField]()
    purchase_date_field = ft.Ref[ft.TextField]()
    last_calibration_field = ft.Ref[ft.TextField]()
    next_calibration_field = ft.Ref[ft.TextField]()
    notes_field = ft.Ref[ft.TextField]()

    # Success/Error message
    message_container = ft.Ref[ft.Container]()

    def default_show_snackbar(message, color=ft.Colors.RED):
        if show_snackbar:
            show_snackbar(message, color)
        else:
            snackbar = ft.SnackBar(
                content=ft.Text(message, color=WHITE),
                bgcolor=color,
                duration=3000
            )
            page.overlay.append(snackbar)
            snackbar.open = True
            page.update()

    # Form validation
    def validate_form():
        errors = []

        if not name_field.current.value or not name_field.current.value.strip():
            errors.append("Tool name is required")

        if not model_field.current.value or not model_field.current.value.strip():
            errors.append("Model is required")

        if not serial_field.current.value or not serial_field.current.value.strip():
            errors.append("Serial number is required")

        if not category_dropdown.current.value:
            errors.append("Category is required")

        if not condition_dropdown.current.value:
            errors.append("Condition is required")

        if not location_field.current.value or not location_field.current.value.strip():
            errors.append("Location is required")

        if not quantity_field.current.value:
            errors.append("Total quantity is required")
        else:
            try:
                quantity = int(quantity_field.current.value)
                if quantity <= 0:
                    errors.append("Quantity must be greater than 0")
            except ValueError:
                errors.append("Quantity must be a valid number")

        if not available_quantity_field.current.value:
            errors.append("Available quantity is required")
        else:
            try:
                available = int(available_quantity_field.current.value)
                if available < 0:
                    errors.append("Available quantity cannot be negative")

                if quantity_field.current.value:
                    try:
                        total = int(quantity_field.current.value)
                        if available > total:
                            errors.append("Available quantity cannot exceed total quantity")
                    except ValueError:
                        pass
            except ValueError:
                errors.append("Available quantity must be a valid number")

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
            name_field.current, model_field.current, serial_field.current,
            location_field.current, quantity_field.current, available_quantity_field.current,
            purchase_date_field.current, last_calibration_field.current,
            next_calibration_field.current, notes_field.current
        ]

        for field in fields:
            field.value = ""
            field.update()

        category_dropdown.current.value = None
        condition_dropdown.current.value = None
        category_dropdown.current.update()
        condition_dropdown.current.update()

    # Submit handler
    def on_submit(e):
        # Validate form
        errors = validate_form()

        if errors:
            show_message(f"Please fix the following errors: {', '.join(errors)}", True)
            return

        # Prepare tool data for database
        tool_data = {
            "name": name_field.current.value.strip(),
            "model": model_field.current.value.strip(),
            "serial_number": serial_field.current.value.strip(),
            "category": category_dropdown.current.value,
            "condition": condition_dropdown.current.value,
            "location": location_field.current.value.strip(),
            "total_quantity": int(quantity_field.current.value),
            "available_quantity": int(available_quantity_field.current.value),
            "purchase_date": purchase_date_field.current.value.strip() if purchase_date_field.current.value else None,
            "last_calibration": last_calibration_field.current.value.strip() if last_calibration_field.current.value else None,
            "next_calibration": next_calibration_field.current.value.strip() if next_calibration_field.current.value else None,
            "notes": notes_field.current.value.strip() if notes_field.current.value else None,
            "created_by": current_user.get("id") if current_user else None,
        }

        # Call database function
        try:
            success = create_tool(tool_data)

            if success:
                show_message("Tool created successfully!", False)
                clear_form()

                # Log the activity
                try:
                    db.log_activity('tool_created', {
                        'name': tool_data['name'],
                        'model': tool_data['model'],
                        'quantity': tool_data['total_quantity'],
                        'created_by': current_user.get('full_name') if current_user else 'Unknown'
                    }, current_user.get('id') if current_user else None)
                except Exception as le:
                    print(f"Error logging activity: {le}")

            else:
                show_message("Failed to create tool. Please try again.", True)

        except Exception as ex:
            show_message(f"Error: {str(ex)}", True)

    # Cancel/Clear handler
    def on_clear(e):
        clear_form()
        message_container.current.visible = False
        message_container.current.update()

    # Date picker handlers
    def on_purchase_date_click(e):
        today = datetime.now().strftime("%Y-%m-%d")
        purchase_date_field.current.value = today
        purchase_date_field.current.update()

    def on_last_calibration_click(e):
        today = datetime.now().strftime("%Y-%m-%d")
        last_calibration_field.current.value = today
        last_calibration_field.current.update()

    def on_next_calibration_click(e):
        future_date = datetime.now().replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")
        next_calibration_field.current.value = future_date
        next_calibration_field.current.update()

    # Auto-fill available quantity when total changes
    def on_quantity_change(e):
        if quantity_field.current.value and not available_quantity_field.current.value:
            available_quantity_field.current.value = quantity_field.current.value
            available_quantity_field.current.update()

    # Create form fields
    name_field.current = ft.TextField(
        label="Tool Name *",
        hint_text="Enter tool name",
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    model_field.current = ft.TextField(
        label="Model *",
        hint_text="Enter model number/name",
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    serial_field.current = ft.TextField(
        label="Serial Number *",
        hint_text="Enter serial number",
        prefix_icon=ft.Icons.NUMBERS,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    category_dropdown.current = ft.Dropdown(
        label="Category *",
        options=[ft.dropdown.Option(cat) for cat in category_options],
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    condition_dropdown.current = ft.Dropdown(
        label="Condition *",
        options=[ft.dropdown.Option(cond) for cond in condition_options],
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    location_field.current = ft.TextField(
        label="Location *",
        hint_text="Where is this tool stored?",
        prefix_icon=ft.Icons.LOCATION_ON,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
    )

    quantity_field.current = ft.TextField(
        label="Total Quantity *",
        hint_text="Total number of units",
        prefix_icon=ft.Icons.INVENTORY,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        keyboard_type=ft.KeyboardType.NUMBER,
        on_change=on_quantity_change
    )

    available_quantity_field.current = ft.TextField(
        label= "Available Quantity *",
        hint_text="Available units",
        prefix_icon=ft.Icons.EVENT_AVAILABLE_SHARP,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    purchase_date_field.current = ft.TextField(
        label="Purchase Date",
        hint_text="YYYY-MM-DD",
        prefix_icon=ft.Icons.CALENDAR_TODAY,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        on_click=on_purchase_date_click,
        read_only=False,
    )

    last_calibration_field.current = ft.TextField(
        label="Last Calibration",
        hint_text="YYYY-MM-DD",
        prefix_icon=ft.Icons.TUNE,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        on_click=on_last_calibration_click,
        read_only=False,
    )

    next_calibration_field.current = ft.TextField(
        label="Next Calibration",
        hint_text="YYYY-MM-DD",
        prefix_icon=ft.Icons.SCHEDULE,
        border_radius=8,
        bgcolor=WHITE,
        border_color=BORDER_COLOR,
        focused_border_color=GOLD,
        label_style=ft.TextStyle(color="#666666"),
        text_style=ft.TextStyle(color=BLACK),
        on_click=on_next_calibration_click,
        read_only=False,
    )

    notes_field.current = ft.TextField(
        label="Notes",
        hint_text="Additional notes about this tool",
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
        text="Add Tool",
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
                    ft.Icons.BUILD,
                    size=60,
                    color=GOLD
                ),
                padding=ft.padding.only(bottom=10)
            ),
            ft.Text(
                "ADD NEW TOOL",
                size=28,
                weight=ft.FontWeight.BOLD,
                color=DARK_GRAY,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Text(
                "Add new tools to the inventory system",
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

                # Basic Information Section
                ft.Text(
                    "Basic Information",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=BLACK,
                ),
                name_field.current,
                model_field.current,
                serial_field.current,

                ft.Row([
                    ft.Container(category_dropdown.current, expand=True),
                    ft.Container(condition_dropdown.current, expand=True),
                ], spacing=12),

                # Location and Quantity Section
                ft.Container(height=10),
                ft.Text(
                    "Location & Quantity",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=BLACK,
                ),

                location_field.current,
                ft.Row([
                    ft.Container(quantity_field.current, expand=True),
                    ft.Container(available_quantity_field.current, expand=True),
                ], spacing=12),

                # Dates Section
                ft.Container(height=10),
                ft.Text(
                    "Dates & Calibration",
                    size=16,
                    weight=ft.FontWeight.W_600,
                    color=BLACK,
                ),

                purchase_date_field.current,
                ft.Row([
                    ft.Container(last_calibration_field.current, expand=True),
                    ft.Container(next_calibration_field.current, expand=True),
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
        route="/add-tool",
        appbar=create_app_bar("Add New Tool", show_nav=False),
        controls=[content]
    )
