import flet as ft

def settings_view(page: ft.Page, create_app_bar, create_bottom_nav, current_user, show_snackbar):
    """Create and return the complete settings page content"""

    # App information
    app_info = {
        "name": "SmartConnect Manager",
        "version": "V1.0.0",
        "developer": "Mohamed Ouchbara"
    }

    # Settings sections
    def create_section_header(title):
        return ft.Container(
            content=ft.Text(
                title,
                size=18,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_700
            ),
            margin=ft.margin.only(top=20, bottom=10)
        )

    def create_setting_item(icon, title, subtitle=None, trailing_widget=None, on_click=None):
        content = [
            ft.Row([
                ft.Icon(icon, size=24, color=ft.Colors.BLUE_600),
                ft.Column([
                    ft.Text(title, size=16, weight=ft.FontWeight.W_500),
                    ft.Text(subtitle, size=12, color=ft.Colors.GREY_600) if subtitle else ft.Container()
                ], spacing=2, expand=True),
                trailing_widget if trailing_widget else ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=ft.Colors.GREY_400)
            ])
        ]

        return ft.Card(
            content=ft.Container(
                content=ft.Column(content, spacing=0),
                padding=16,
                on_click=on_click if on_click else lambda e: print(f"Clicked: {title}")
            ),
            elevation=1,
            margin=ft.margin.only(bottom=8)
        )

    # Theme settings
    dark_mode_switch = ft.Switch(
        value=False,
        active_color=ft.Colors.BLUE,
        on_change=lambda e: toggle_theme(e.control.value)
    )

    # Notification settings
    notifications_switch = ft.Switch(
        value=True,
        active_color=ft.Colors.BLUE,
        on_change=lambda e: toggle_notifications(e.control.value)
    )

    # Language dropdown
    language_dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("English"),
            ft.dropdown.Option("French")

        ],
        value="English",
        width=120,
        bgcolor=ft.Colors.WHITE,
        border_radius=8,
        on_change=lambda e: change_language(e.control.value)
    )

    # Event handlers
    def toggle_theme(is_dark):
        theme_mode = ft.ThemeMode.DARK if is_dark else ft.ThemeMode.LIGHT
        page.theme_mode = theme_mode
        page.update()
        print(f"Dark mode: {'On' if is_dark else 'Off'}")

    def toggle_notifications(is_enabled):
        show_snackbar(f"Notifications: {'Enabled' if is_enabled else 'Disabled'}",ft.Colors.GREEN_300)

    def change_language(language):
        show_snackbar(f"Language changed to: {language}", ft.Colors.GREEN_300)

    def show_about():
        dialog = ft.AlertDialog(
            title=ft.Text("About SmartConnect Manager"),
            content=ft.Column([
                ft.Text(f"Version: {app_info['version']}", size=14),
                ft.Text(f"Developer: {app_info['developer']}", size=14),
                ft.Text("A comprehensive management system for telecom and field operations.", size=12),
            ], tight=True),
            actions=[ft.TextButton("Close", on_click=lambda e: close_dialog())],
        )

        def close_dialog():
            dialog.open = False
            page.update()

        page.open(dialog)
        dialog.open = True
        page.update()

    def show_privacy():
        print("Privacy policy would open here")

    def show_terms():
        print("Terms of service would open here")

    def contact_support():
        print("Contact support would open here")

    def export_data():
        show_snackbar("Export feature coming soon", ft.Colors.BLUE)

    def import_data():
        show_snackbar("Import feature coming soon", ft.Colors.BLUE)

    def backup_data():
        show_snackbar("Backup started", ft.Colors.GREEN)

    def reset_app():
        dialog = ft.AlertDialog(
            title=ft.Text("Reset Application", color=ft.Colors.RED),
            content=ft.Text("This will delete all your data. Are you sure?"),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.ElevatedButton(
                    "Reset",
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE,
                    on_click=lambda e: confirm_reset()
                ),
            ],
        )

        def close_dialog():
            dialog.open = False
            page.update()

        def confirm_reset():
            close_dialog()
            show_snackbar("Reset cancelled - Feature disabled for safety", ft.Colors.ORANGE)

        page.open(dialog)
        dialog.open = True
        page.update()

    # Create settings content
    content = ft.Column([
        # Scrollable content
        ft.Container(
            content=ft.Column([
                # App Information Section
                create_section_header("App Information"),
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Icon(ft.Icons.APP_REGISTRATION, size=48, color=ft.Colors.BLUE),
                                ft.Column([
                                    ft.Text(
                                        app_info["name"],
                                        size=20,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.Colors.BLUE_700
                                    ),
                                    ft.Text(
                                        f"Version {app_info['version']}",
                                        size=14,
                                        color=ft.Colors.GREY_600
                                    ),
                                    ft.Text(
                                        f"Developer: {app_info['developer']}",
                                        size=12,
                                        color=ft.Colors.GREY_500
                                    ),
                                    ft.Text(
                                        f"User: {current_user.get('full_name', 'Guest') if current_user else 'Guest'}",
                                        size=12,
                                        color=ft.Colors.GREY_500
                                    )
                                ], spacing=2, expand=True)
                            ])
                        ]),
                        padding=16,
                        bgcolor=ft.Colors.BLUE_50,
                        border_radius=8
                    ),
                    elevation=2,
                    margin=ft.margin.only(bottom=8)
                ),

                # Appearance Section
                create_section_header("Appearance"),
                create_setting_item(
                    ft.Icons.DARK_MODE,
                    "Dark Mode",
                    "Switch between light and dark theme",
                    dark_mode_switch
                ),
                create_setting_item(
                    ft.Icons.LANGUAGE,
                    "Language",
                    "Choose your preferred language",
                    language_dropdown
                ),

                # Notifications Section
                create_section_header("Notifications"),
                create_setting_item(
                    ft.Icons.NOTIFICATIONS,
                    "Push Notifications",
                    "Receive notifications about updates",
                    notifications_switch
                ),
                create_setting_item(
                    ft.Icons.EMAIL,
                    "Email Notifications",
                    "Get notified via email"
                ),

                # Data Management Section
                create_section_header("Data Management"),
                create_setting_item(
                    ft.Icons.BACKUP,
                    "Backup Data",
                    "Create a backup of your data",
                    on_click=lambda e: backup_data()
                ),
                create_setting_item(
                    ft.Icons.CLOUD_UPLOAD,
                    "Export Data",
                    "Export your data to file",
                    on_click=lambda e: export_data()
                ),
                create_setting_item(
                    ft.Icons.CLOUD_DOWNLOAD,
                    "Import Data",
                    "Import data from file",
                    on_click=lambda e: import_data()
                ),

                # Support Section
                create_section_header("Support & Information"),
                create_setting_item(
                    ft.Icons.HELP,
                    "Help & Support",
                    "Get help and contact support",
                    on_click=lambda e: contact_support()
                ),
                create_setting_item(
                    ft.Icons.INFO,
                    "About",
                    "Learn more about the app",
                    on_click=lambda e: show_about()
                ),
                create_setting_item(
                    ft.Icons.PRIVACY_TIP,
                    "Privacy Policy",
                    "Read our privacy policy",
                    on_click=lambda e: show_privacy()
                ),
                create_setting_item(
                    ft.Icons.DESCRIPTION,
                    "Terms of Service",
                    "Read terms and conditions",
                    on_click=lambda e: show_terms()
                ),

                # Danger Zone Section
                create_section_header("Danger Zone"),
                ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING, size=24, color=ft.Colors.RED),
                            ft.Column([
                                ft.Text("Reset App", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.RED),
                                ft.Text("This will delete all your data", size=12, color=ft.Colors.RED_300)
                            ], spacing=2, expand=True),
                            ft.Icon(ft.Icons.ARROW_FORWARD_IOS, size=16, color=ft.Colors.RED_300)
                        ]),
                        padding=16,
                        on_click=lambda e: reset_app()
                    ),
                    elevation=1,
                    margin=ft.margin.only(bottom=8),
                    color=ft.Colors.RED_50
                ),

                # Footer
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            f"© 2024 {app_info['developer']} All rights reserved",
                            size=12,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    margin=ft.margin.only(top=20, bottom=20)
                )
            ], scroll=ft.ScrollMode.AUTO),
            expand=True
        )
    ], spacing=0)

    return ft.View(
        route="/settings",
        appbar=create_app_bar("Settings"),
        navigation_bar=create_bottom_nav(3),
        controls=[
            ft.Container(
                content=content,
                expand=True,
                margin=ft.margin.only(left=15)
            )
        ]
    )
