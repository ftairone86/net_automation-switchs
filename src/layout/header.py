import flet as ft
import switches_state


def build_header(toggle_rail, toggle_theme, page: ft.Page,
                 username: str = "", on_logout=None):
    theme_icon = ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme)

    neon_horizontal = ft.Container(
        height=2,
        gradient=ft.LinearGradient(
            colors=[ft.Colors.CYAN_ACCENT, ft.Colors.PURPLE_ACCENT]
        ),
        expand=False,
    )

    # ── badges dos switches na barra ──────────────────────────────────
    switches_row = ft.Row(
        controls=[],
        scroll=ft.ScrollMode.AUTO,
        spacing=6,
        tight=True,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def _rebuild_badges(sw_dict: dict):
        switches_row.controls.clear()
        for sw in sw_dict.values():
            model_short = (
                sw["model"].split()[-1]
                if sw["model"] != "Desconhecido"
                else sw["vendor"].split()[0]
            )
            switches_row.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            width=7, height=7, border_radius=4,
                            bgcolor=ft.Colors.GREEN_ACCENT,
                        ),
                        ft.Text(
                            sw["host"],
                            size=11,
                            color=ft.Colors.CYAN_ACCENT,
                            weight=ft.FontWeight.W_500,
                            no_wrap=True,
                        ),
                        ft.Text(
                            model_short,
                            size=10,
                            color=ft.Colors.GREY_400,
                            no_wrap=True,
                        ),
                    ], spacing=4, tight=True),
                    bgcolor=ft.Colors.with_opacity(0.10, ft.Colors.CYAN_ACCENT),
                    border_radius=10,
                    padding=ft.padding.symmetric(horizontal=9, vertical=3),
                    border=ft.border.all(
                        1, ft.Colors.with_opacity(0.30, ft.Colors.CYAN_ACCENT)
                    ),
                )
            )
        try:
            page.update()
        except Exception:
            pass

    switches_state.on_change(_rebuild_badges)
    # carrega estado atual (sem update pois a página ainda não foi montada)
    _rebuild_badges(switches_state.get_all())

    # ── badge CONECTADO — cores por tema ─────────────────────────────
    def _badge_color():
        return ft.Colors.PURPLE_ACCENT if page.theme_mode == ft.ThemeMode.LIGHT \
               else ft.Colors.GREEN_600

    badge_dot  = ft.Container(width=8, height=8, border_radius=4,
                               bgcolor=_badge_color())
    badge_text = ft.Text("CONECTADO", color=_badge_color(),
                          weight="bold", size=13)
    badge_box  = ft.Container(
        content=ft.Row([badge_dot, badge_text], spacing=6, tight=True),
        bgcolor=ft.Colors.with_opacity(0.12, _badge_color()),
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
        border=ft.border.all(1, ft.Colors.with_opacity(0.4, _badge_color())),
    )

    def apply_badge_theme():
        c = _badge_color()
        badge_dot.bgcolor  = c
        badge_text.color   = c
        badge_box.bgcolor  = ft.Colors.with_opacity(0.12, c)
        badge_box.border   = ft.border.all(1, ft.Colors.with_opacity(0.4, c))

    # ── layout do header ──────────────────────────────────────────────
    header = ft.Container(
        content=ft.Row(
            [
                ft.IconButton(ft.Icons.MENU, on_click=toggle_rail),
                badge_box,
                ft.Container(width=10),
                # ── área rolável com switches ─────────────────────────
                ft.Container(
                    content=switches_row,
                    expand=True,
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                ),
                # ── ações ─────────────────────────────────────────────
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.MONITOR_HEART, tooltip="Check Status"
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DOWNLOAD, tooltip="Export Config"
                        ),
                        theme_icon,
                        *(
                            [
                                ft.VerticalDivider(width=10),
                                ft.Icon(ft.Icons.PERSON, size=16,
                                        color=ft.Colors.GREY_400),
                                ft.Text(username, size=12,
                                        color=ft.Colors.GREY_400),
                                ft.IconButton(
                                    icon=ft.Icons.LOGOUT, tooltip="Sair",
                                    on_click=on_logout
                                ),
                            ]
                            if on_logout else []
                        ),
                    ],
                    spacing=0,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
    )

    return header, neon_horizontal, theme_icon, _rebuild_badges, apply_badge_theme
