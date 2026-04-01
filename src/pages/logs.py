import flet as ft


def LogsPage():
    return ft.Column(
        [
            ft.Text("Logs", size=25, weight="bold"),
            ft.Text(
                "Logs do sistema serão exibidos aqui.",
                color=ft.Colors.GREY_400,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )
