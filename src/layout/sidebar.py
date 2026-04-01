import flet as ft


def build_sidebar(page: ft.Page, on_nav_change):
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        extended=False,
        min_width=70,
        min_extended_width=200,
        group_alignment=-0.9,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD_OUTLINED,
                selected_icon=ft.Icons.DASHBOARD,
                label="Dashboard",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.DEVICES_OUTLINED,
                selected_icon=ft.Icons.DEVICES,
                label="Devices",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.SETTINGS_OUTLINED,
                selected_icon=ft.Icons.SETTINGS,
                label="Config",
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.ARTICLE_OUTLINED,
                selected_icon=ft.Icons.ARTICLE,
                label="Logs",
            ),
        ],
        on_change=lambda e: on_nav_change(e.control.selected_index),
    )

    neon_vertical = ft.Container(
        width=2,
        gradient=ft.LinearGradient(
            colors=[ft.Colors.PURPLE_ACCENT, ft.Colors.CYAN_ACCENT]
        ),
    )

    def toggle_rail(e):
        rail.extended = not rail.extended
        page.update()

    return rail, neon_vertical, toggle_rail
