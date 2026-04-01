import os

import flet as ft
import switches_state
import theme_state

from layout.header import build_header
from layout.sidebar import build_sidebar
from pages.login import LoginPage
from pages.dashboard import DashboardPage
from pages.devices import DevicesPage
from pages.config import ConfigPage
from pages.logs import LogsPage


def main(page: ft.Page):
    page.title = "Gerenciador de Switch's · BuritiLabs"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.spacing = 0

    # ── mostra o app principal após login ──
    def show_app(username: str):
        page.controls.clear()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START

        page_controls = [DashboardPage(page), DevicesPage(page), ConfigPage(page), LogsPage()]

        # All pages stay mounted at all times so that updates to any page
        # (e.g. new switch cards added to the dashboard while the user is on
        # the Devices page) are always included in page.update() traversals.
        # Visibility is toggled instead of swapping content_area.content.
        for i, p in enumerate(page_controls):
            p.visible = (i == 0)

        content_area = ft.Container(
            content=ft.Stack(page_controls, fit=ft.StackFit.EXPAND),
            expand=True,
            padding=20,
        )

        def on_nav_change(index):
            for i, p in enumerate(page_controls):
                p.visible = (i == index)
            page.update()

        rail, neon_vertical, toggle_rail = build_sidebar(page, on_nav_change)

        def _layout_height():
            return page.height if page.height is not None else 600

        rail.height = _layout_height()

        def on_resize(e):
            rail.height = _layout_height()
            layout.height = _layout_height()
            page.update()

        page.on_resize = on_resize

        def toggle_theme(e):
            page.theme_mode = (
                ft.ThemeMode.LIGHT
                if page.theme_mode == ft.ThemeMode.DARK
                else ft.ThemeMode.DARK
            )
            theme_icon.icon = (
                ft.Icons.LIGHT_MODE
                if page.theme_mode == ft.ThemeMode.LIGHT
                else ft.Icons.DARK_MODE
            )
            _apply_badge()
            theme_state.notify()   # avisa todas as páginas
            page.update()

        def logout(e):
            page.on_resize = None
            switches_state.off_change(_badges_listener)
            theme_state.clear()    # remove todos os listeners das páginas
            show_login()

        header, neon_horizontal, theme_icon, _badges_listener, _apply_badge = \
            build_header(toggle_rail, toggle_theme, page=page,
                         username=username, on_logout=logout)

        layout = ft.Row(
            [
                rail,
                neon_vertical,
                ft.Column(
                    [header, neon_horizontal, content_area],
                    expand=True,
                ),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )

        layout.height = _layout_height()
        page.add(layout)
        page.update()

    # ── mostra a tela de login ──
    def show_login():
        page.controls.clear()
        page.theme_mode = ft.ThemeMode.DARK   # login sempre inicia escuro
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.START
        page.add(LoginPage(page, on_login_success=show_app))
        page.update()

    show_login()


ft.run(main, view=ft.AppView.FLET_APP, port=int(os.getenv("PORT", "8080")))



