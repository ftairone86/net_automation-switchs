"""Cores temáticas compartilhadas entre todas as páginas."""
import flet as ft


def accent(page: ft.Page):
    """Verde escuro → roxo neon no tema claro, verde neon no tema escuro."""
    return (ft.Colors.PURPLE_ACCENT
            if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.Colors.GREEN_ACCENT)


def accent_dim(page: ft.Page, opacity: float = 0.1):
    return ft.Colors.with_opacity(opacity, accent(page))
