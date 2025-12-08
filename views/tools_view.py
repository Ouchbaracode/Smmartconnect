import flet as ft
from db import get_all_tools

def tools_view(page: ft.Page, go_to, create_app_bar, create_bottom_nav, show_snackbar):
    """Create and return the complete tools management content using real data"""

    tools_data = []

    def refresh_tools_data():
        """Refresh tools data from database"""
        nonlocal tools_data
        try:
            tools_data = get_all_tools()
            # Transform database format to match UI expectations
            for tool in tools_data:
                tool['quantity'] = tool.get('total_quantity', 0)
                tool['available'] = tool.get('available_quantity', 0)
                tool['in_use'] = tool['quantity'] - tool['available']
                tool['icon'] = ft.Icons.BUILD  # Default icon
        except Exception as e:
            print(f"Error refreshing tools data: {e}")
            tools_data = []

    # Refresh tools data
    refresh_tools_data()

    # Get status color
    def get_status_color(available, total):
        if available == 0:
            return ft.Colors.RED  # All in use
        elif available == total:
            return ft.Colors.GREEN  # All available
        else:
            return ft.Colors.ORANGE  # Partially available

    def get_status_text(available, total):
        if available == 0:
            return "All In Use"
        elif available == total:
            return "Available"
        else:
            return "Partially Available"

    # Create tool card
    def create_tool_card(tool):
        def show_tool_details(e):
            show_tool_dialog(tool)

        def quick_assign(e):
            print(f"Quick assign tool: {tool['name']}")
            # Here you would implement tool assignment logic

        status = get_status_text(tool['available'], tool['quantity'])
        status_color = get_status_color(tool['available'], tool['quantity'])

        # Status badge
        status_badge = ft.Container(
            content=ft.Text(
                status,
                size=10,
                color=ft.Colors.WHITE,
                weight=ft.FontWeight.BOLD
            ),
            bgcolor=status_color,
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=6, vertical=2)
        )

        # Availability info
        availability_text = f"{tool['available']}/{tool['quantity']} Available"
        availability_color = ft.Colors.GREEN if tool['available'] > 0 else ft.Colors.RED

        return ft.Card(
            content=ft.Container(
                content=ft.Column([
                    # Header row
                    ft.Row([
                        ft.Container(
                            content=ft.Icon(tool.get("icon", ft.Icons.BUILD), size=32, color=ft.Colors.WHITE),
                            width=50,
                            height=50,
                            bgcolor=ft.Colors.BLUE,
                            border_radius=12,
                            alignment=ft.alignment.center
                        ),
                        ft.Column([
                            ft.Text(
                                tool["name"],
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                expand=True
                            ),
                            ft.Text(
                                tool.get("model", "N/A"),
                                size=12,
                                color=ft.Colors.GREY_600
                            ),
                            ft.Text(
                                availability_text,
                                size=12,
                                color=availability_color,
                                weight=ft.FontWeight.W_500
                            )
                        ], spacing=2, expand=True),
                        ft.Column([
                            status_badge
                        ], horizontal_alignment=ft.CrossAxisAlignment.END)
                    ]),

                    # Info row
                    ft.Row([
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.Icons.LOCATION_ON, size=16, color=ft.Colors.GREY_600),
                                ft.Text(tool.get("location", "Unknown"), size=12, color=ft.Colors.GREY_600)
                            ]),
                            expand=True
                        ),
                        ft.Container(
                            content=ft.Text(
                                tool.get("condition", "Good"),
                                size=12,
                                color=ft.Colors.BLUE,
                                weight=ft.FontWeight.W_500
                            )
                        )
                    ]),

                    # Action buttons
                    ft.Row([
                        ft.ElevatedButton(
                            "Details",
                            icon=ft.Icons.INFO,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.BLUE_50,
                                color=ft.Colors.BLUE,
                                shape=ft.RoundedRectangleBorder(radius=8)
                            ),
                            on_click=show_tool_details
                        ),
                        # Removed Assign button per request
                        ft.Container()
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=12),
                padding=16,
                on_click=show_tool_details
            ),
            elevation=2,
            margin=ft.margin.only(bottom=12)
        )

    # Tool detail dialog
    def show_tool_dialog(tool):
        def close_dialog(e):
            dialog.open = False
            page.update()

        def assign_tool(e):
            print(f"Assigning tool: {tool['name']}")
            close_dialog(e)

        def schedule_maintenance(e):
            print(f"Scheduling maintenance for: {tool['name']}")
            close_dialog(e)

        dialog = ft.AlertDialog(
            title=ft.Text(tool["name"], weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(tool.get("icon", ft.Icons.BUILD), size=48, color=ft.Colors.BLUE),
                        ft.Column([
                            ft.Text(f"Model: {tool.get('model', 'N/A')}", size=14),
                            ft.Text(f"Serial: {tool.get('serial_number', 'N/A')}", size=12, color=ft.Colors.GREY_600),
                            ft.Text(f"Condition: {tool.get('condition', 'Good')}", size=12, color=ft.Colors.BLUE)
                        ], spacing=4, expand=True)
                    ]),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Total Quantity:", weight=ft.FontWeight.BOLD),
                        ft.Text(str(tool['quantity']))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Available:", weight=ft.FontWeight.BOLD),
                        ft.Text(str(tool['available']), color=ft.Colors.GREEN if tool['available'] > 0 else ft.Colors.RED)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("In Use:", weight=ft.FontWeight.BOLD),
                        ft.Text(str(tool['in_use']), color=ft.Colors.ORANGE if tool['in_use'] > 0 else ft.Colors.GREY)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Location:", weight=ft.FontWeight.BOLD),
                        ft.Text(tool.get('location', 'Unknown'))
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Text("Calibration Info:", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Last: {tool.get('last_calibration', 'N/A')}", size=12),
                    ft.Text(f"Next: {tool.get('next_calibration', 'N/A')}", size=12),
                ], spacing=8),
                width=300,
                height=400
            ),
            actions=[
                ft.TextButton("Close", on_click=close_dialog),
                # Removed Assign button per request
                ft.ElevatedButton(
                    "Maintenance",
                    icon=ft.Icons.BUILD,
                    on_click=schedule_maintenance,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_50, color=ft.Colors.ORANGE)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )

        page.open(dialog)
        dialog.open = True
        page.update()

    # Initialize filtered data
    filtered_tools = tools_data.copy()

    # Create UI components
    search_field = ft.TextField(
        hint_text="Search tools...",
        prefix_icon=ft.Icons.SEARCH,
        border_radius=12,
        bgcolor=ft.Colors.WHITE,
        expand=True
    )

    status_filter = ft.Dropdown(
        options=[
            ft.dropdown.Option("All Status"),
            ft.dropdown.Option("Available"),
            ft.dropdown.Option("All In Use"),
            ft.dropdown.Option("Partially Available")
        ],
        value="All Status",
        width=150,
        bgcolor=ft.Colors.WHITE,
        border_radius=12
    )

    tools_list = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO)

    # Statistics cards
    def create_stats_cards():
        if not tools_data:
            return ft.Container()

        total_tools = sum(tool['quantity'] for tool in tools_data)
        available_tools = sum(tool['available'] for tool in tools_data)
        in_use_tools = sum(tool['in_use'] for tool in tools_data)
        needs_maintenance = len([tool for tool in tools_data if tool.get('condition') == 'Needs Maintenance'])

        return ft.Row([
            ft.Container(
                content=ft.Column([
                    ft.Text(str(total_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE),
                    ft.Text("Total Tools", size=12, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.BLUE_50,
                padding=12,
                border_radius=8,
                expand=True
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(str(available_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN),
                    ft.Text("Available", size=12, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.GREEN_50,
                padding=12,
                border_radius=8,
                expand=True
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(str(in_use_tools), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.ORANGE),
                    ft.Text("In Use", size=12, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.ORANGE_50,
                padding=12,
                border_radius=8,
                expand=True
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text(str(needs_maintenance), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                    ft.Text("Maintenance", size=12, color=ft.Colors.GREY_600)
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=ft.Colors.RED_50,
                padding=12,
                border_radius=8,
                expand=True
            )
        ], spacing=8)

    # Filter tools
    def filter_tools():
        nonlocal filtered_tools
        search_term = search_field.value.lower() if search_field.value else ""
        status_filter_value = status_filter.value

        filtered_tools = tools_data.copy()

        if search_term:
            filtered_tools = [tool for tool in filtered_tools if
                            search_term in tool['name'].lower() or
                            search_term in tool.get('model', '').lower() or
                            search_term in tool.get('location', '').lower()]

        if status_filter_value and status_filter_value != "All Status":
            if status_filter_value == "Available":
                filtered_tools = [tool for tool in filtered_tools if tool['available'] == tool['quantity']]
            elif status_filter_value == "All In Use":
                filtered_tools = [tool for tool in filtered_tools if tool['available'] == 0]
            elif status_filter_value == "Partially Available":
                filtered_tools = [tool for tool in filtered_tools if 0 < tool['available'] < tool['quantity']]

        update_tools_list()

    # Update tools list
    def update_tools_list():
        tools_list.controls.clear()

        if not filtered_tools:
            tools_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.SEARCH_OFF, size=64, color=ft.Colors.GREY_400),
                        ft.Text("No tools found", size=16, color=ft.Colors.GREY_600)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    alignment=ft.alignment.center,
                    height=200
                )
            )
        else:
            for tool in filtered_tools:
                tools_list.controls.append(create_tool_card(tool))

        page.update()

    # Event handlers
    def on_search_change(e):
        filter_tools()

    def on_status_filter_change(e):
        filter_tools()

    def add_new_tool():
        go_to("/add-tool")
        # Here you would implement tool creation

    def refresh_tools_and_update():
        """Refresh tools data and update the view"""
        refresh_tools_data()
        filter_tools()
        show_snackbar("Tools refreshed", ft.Colors.GREEN)

    # Set event handlers
    search_field.on_change = on_search_change
    status_filter.on_change = on_status_filter_change

    # Initial load
    update_tools_list()

    # Return the complete content
    content = ft.Stack([
        ft.Column([
            # Statistics
            create_stats_cards(),

            # Search and filters
            ft.Row([
                search_field,
                status_filter
            ], spacing=8),

            # Tools list
            ft.Container(
                content=tools_list,
                expand=True,
                margin=ft.margin.only(top=16)
            )
        ], spacing=12),
    ])

    return ft.View(
        route="/tools",
        appbar=create_app_bar(
            "My Tools",
            actions=[
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh Tools",
                    on_click=lambda e: refresh_tools_and_update()
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="Add Tool",
                    on_click=lambda e: add_new_tool()
                )
            ]
        ),
        navigation_bar=create_bottom_nav(2),
        controls=[
            ft.Container(
                content=content,
                expand=True,
                margin=ft.margin.only(left=15)
            )
        ]
    )
