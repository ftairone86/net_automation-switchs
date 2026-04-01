import flet as ft
from auth.ldap_auth import load_config, save_config, test_ldap_connection
import colors
import theme_state


def ConfigPage(page: ft.Page):
    cfg = load_config()

    # ── campos LDAP ──
    f_host    = ft.TextField(label="Servidor LDAP / AD", value=cfg.get("ldap_host", ""),
                              border_color=ft.Colors.CYAN_ACCENT, width=400)
    f_port    = ft.TextField(label="Porta", value=cfg.get("ldap_port", "389"),
                              border_color=ft.Colors.CYAN_ACCENT, width=100)
    f_domain  = ft.TextField(label="Domínio (ex: empresa.local)", value=cfg.get("ldap_domain", ""),
                              border_color=ft.Colors.CYAN_ACCENT, width=300)
    f_base    = ft.TextField(label="Base DN (ex: DC=empresa,DC=local)", value=cfg.get("ldap_base_dn", ""),
                              border_color=ft.Colors.CYAN_ACCENT, width=400)
    f_bind    = ft.TextField(label="Bind DN (conta de serviço)", value=cfg.get("ldap_bind_dn", ""),
                              border_color=ft.Colors.CYAN_ACCENT, width=400)
    f_bindpw  = ft.TextField(label="Senha do Bind DN", value=cfg.get("ldap_bind_password", ""),
                              password=True, can_reveal_password=True,
                              border_color=ft.Colors.CYAN_ACCENT, width=400)
    f_filter  = ft.TextField(label="Filtro de usuário", value=cfg.get("ldap_user_filter", "(sAMAccountName={username})"),
                              border_color=ft.Colors.CYAN_ACCENT, width=400)
    f_ssl     = ft.Checkbox(label="Usar SSL/TLS (LDAPS)", value=cfg.get("ldap_use_ssl", False))

    ldap_form = ft.Column([
        ft.Row([f_host, ft.Container(width=12), f_port]),
        ft.Row([f_domain]),
        f_base,
        f_bind,
        f_bindpw,
        f_filter,
        f_ssl,
    ], spacing=12)

    status_text = ft.Text("", size=13)

    def toggle_ldap(e):
        ldap_form.visible = e.control.value
        page.update()

    ldap_switch = ft.Switch(
        label="Ativar autenticação via LDAP/AD",
        value=cfg.get("ldap_enabled", False),
        active_color=colors.accent(page),
        on_change=toggle_ldap,
    )

    ldap_form.visible = cfg.get("ldap_enabled", False)

    def save(e):
        new_cfg = {
            "ldap_enabled":       ldap_switch.value,
            "ldap_host":          f_host.value.strip(),
            "ldap_port":          f_port.value.strip(),
            "ldap_domain":        f_domain.value.strip(),
            "ldap_base_dn":       f_base.value.strip(),
            "ldap_bind_dn":       f_bind.value.strip(),
            "ldap_bind_password": f_bindpw.value,
            "ldap_user_filter":   f_filter.value.strip(),
            "ldap_use_ssl":       f_ssl.value,
        }
        save_config(new_cfg)
        status_text.value = "✓ Configurações salvas com sucesso."
        status_text.color = colors.accent(page)
        page.update()

    def test_conn(e):
        status_text.value = "Testando conexão..."
        status_text.color = ft.Colors.GREY_400
        page.update()
        cfg_now = {
            "ldap_host":          f_host.value.strip(),
            "ldap_port":          f_port.value.strip(),
            "ldap_bind_dn":       f_bind.value.strip(),
            "ldap_bind_password": f_bindpw.value,
            "ldap_use_ssl":       f_ssl.value,
        }
        ok, msg = test_ldap_connection(cfg_now)
        status_text.value = msg
        status_text.color = colors.accent(page) if ok else ft.Colors.RED_ACCENT
        page.update()

    shield_icon = ft.Icon(ft.Icons.SHIELD, color=colors.accent(page))

    def _refresh_config():
        shield_icon.color = colors.accent(page)
        ldap_switch.active_color = colors.accent(page)
        page.update()

    theme_state.on_change(_refresh_config)

    save_btn = ft.ElevatedButton(
        content=ft.Row([ft.Icon(ft.Icons.SAVE, size=16), ft.Text("Salvar", size=13)], spacing=6, tight=True),
        on_click=save,
    )
    test_btn = ft.OutlinedButton(
        content=ft.Row([ft.Icon(ft.Icons.WIFI_FIND, size=16), ft.Text("Testar Conexão", size=13)], spacing=6, tight=True),
        on_click=test_conn,
    )

    return ft.Column(
        [
            ft.Text("Configurações", size=25, weight=ft.FontWeight.BOLD),
            ft.Divider(),

            # ── seção LDAP ──
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        shield_icon,
                        ft.Text("Integração LDAP / Active Directory",
                                size=16, weight=ft.FontWeight.BOLD),
                    ], spacing=8),
                    ft.Text(
                        "Permite autenticar usuários diretamente no seu AD corporativo.",
                        size=12, color=ft.Colors.GREY_400,
                    ),
                    ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                    ldap_switch,
                    ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
                    ldap_form,
                    ft.Divider(height=12, color=ft.Colors.TRANSPARENT),
                    ft.Row([save_btn, test_btn, ft.Container(expand=True), status_text], spacing=10),
                ], spacing=8),
                bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                border_radius=12,
                padding=20,
                border=ft.border.all(1, ft.Colors.with_opacity(0.2, colors.accent(page))),
            ),
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=16,
    )
