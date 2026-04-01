import flet as ft


def SwitchesPage():
    return ft.Column(
        [
            ft.Text("Switches", size=25, weight="bold"),
            ft.Text(
                "Lista de switches será exibida aqui.",
                color=ft.Colors.GREY_400,
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
    )
