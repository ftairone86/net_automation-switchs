import os
import math
import flet as ft
import flet.canvas as cv
from auth.ldap_auth import load_config, ldap_login

_LOGO_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "buritilabs_logo.png")
_HAS_LOGO  = os.path.exists(_LOGO_PATH)

# ── paletas ──────────────────────────────────────────────────────────
_DARK = dict(
    neon="#00F5FF", neon_dim="#00F5FF44", gold="#E4BB88",
    bg=["#1c1c2e", "#12121e"],
    card="#1e1e30",
    border="#00F5FF", border_op=0.45,
    shadow_blur=70, shadow_spread=6, shadow_op=0.40, shadow_dy=0,
    text="#e0e0f0", sub="#7a7a9a",
    field_bg="#252538", field_text="#e0e0f0", field_label="#7a7a9a",
    btn=["#00c8e0", "#007891"],
    btn_text="#ffffff", btn_shadow_op=0.45,
    badge="#00F5FF",
    logo_text="#00F5FF",
    halo_op=0.20, halo_blur=30, halo_spread=6,
)
_LIGHT = dict(
    neon="#007891", neon_dim="#00789144", gold="#B5720A",
    bg=["#eaf4f7", "#ddeef5"],
    card="#ffffff",
    border="#007891", border_op=0.35,
    shadow_blur=40, shadow_spread=2, shadow_op=0.18, shadow_dy=4,
    text="#1a2a35", sub="#6a8a9a",
    field_bg="#f0f8fb", field_text="#1a2a35", field_label="#6a8a9a",
    btn=["#007891", "#005f75"],
    btn_text="#ffffff", btn_shadow_op=0.30,
    badge="#007891",
    logo_text="#007891",
    halo_op=0.06, halo_blur=20, halo_spread=3,
)


# ── ícone buriti (aceita cores) ───────────────────────────────────────

def _buriti_canvas(size: int = 88, neon: str = "#00F5FF",
                   neon_dim: str = "#00F5FF44", gold: str = "#E4BB88"):
    cx      = size * 0.50
    base_y  = size * 0.92
    crown_y = size * 0.30

    trunk = cv.Path(
        [
            cv.Path.MoveTo(cx - 5, base_y),
            cv.Path.LineTo(cx - 3, crown_y + 8),
            cv.Path.LineTo(cx + 3, crown_y + 8),
            cv.Path.LineTo(cx + 5, base_y),
            cv.Path.Close(),
        ],
        paint=ft.Paint(color=neon, style=ft.PaintingStyle.FILL),
    )

    nervuras = [
        cv.Line(cx - 4, base_y - i * 14, cx + 4, base_y - i * 14 - 3,
                paint=ft.Paint(color=neon_dim, stroke_width=1))
        for i in range(1, 5)
    ]

    fronds = []
    for deg in [-85, -65, -45, -25, -10, 10, 25, 45, 65, 85]:
        rad   = math.radians(deg - 90)
        flen  = size * 0.38
        ex    = cx + flen * math.cos(rad)
        ey    = crown_y + flen * math.sin(rad)
        mx    = cx + (flen * 0.55) * math.cos(rad) + 4 * math.sin(rad)
        my    = crown_y + (flen * 0.55) * math.sin(rad) - 4 * math.cos(rad)
        fronds.append(cv.Path(
            [cv.Path.MoveTo(cx, crown_y), cv.Path.QuadraticTo(mx, my, ex, ey)],
            paint=ft.Paint(color=neon, stroke_width=2.2,
                           style=ft.PaintingStyle.STROKE,
                           stroke_cap=ft.StrokeCap.ROUND),
        ))

    fruits = [
        cv.Circle(cx + dx, crown_y + dy, 2.8,
                  paint=ft.Paint(color=gold, style=ft.PaintingStyle.FILL))
        for dx, dy in [(-7, 6), (-2, 3), (4, 5), (0, 10), (-4, 12), (5, 12)]
    ]

    return cv.Canvas([trunk, *nervuras, *fronds, *fruits],
                     width=float(size), height=float(size))


def _logo_col(t: dict):
    """Coluna do logo para uma paleta."""
    if _HAS_LOGO:
        icon_widget = ft.Image(src="/assets/buritilabs_logo.png",
                               width=90, height=90, fit=ft.BoxFit.CONTAIN)
    else:
        icon_widget = ft.Stack([
            ft.Container(width=88, height=88, border_radius=44,
                         shadow=ft.BoxShadow(blur_radius=t["halo_blur"],
                                             spread_radius=t["halo_spread"],
                                             color=t["neon_dim"])),
            ft.Container(width=88, height=88, border_radius=44,
                         bgcolor=ft.Colors.with_opacity(t["halo_op"], t["neon"]),
                         border=ft.border.all(1.5,
                             ft.Colors.with_opacity(0.6, t["neon"]))),
            _buriti_canvas(88, t["neon"], t["neon_dim"], t["gold"]),
        ])

    return ft.Column(
        [
            icon_widget,
            ft.Text("BuritiLabs", size=17, weight=ft.FontWeight.BOLD,
                    color=t["logo_text"], font_family="monospace"),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=8, tight=True,
    )


# ── página de login ───────────────────────────────────────────────────

def LoginPage(page: ft.Page, on_login_success):

    def _h(): return page.height or 600
    def _w(): return page.width  or 800

    is_dark = [page.theme_mode == ft.ThemeMode.DARK]   # lista mutável

    def t(): return _DARK if is_dark[0] else _LIGHT

    # ── logos (uma por paleta) ───────────────────────────────────────
    logo_dark  = _logo_col(_DARK);  logo_dark.visible  = True
    logo_light = _logo_col(_LIGHT); logo_light.visible = False
    logo_slot  = ft.Stack([logo_dark, logo_light],
                           width=90 if _HAS_LOGO else 88,
                           height=118 if _HAS_LOGO else 118)

    # ── textos do cabeçalho ─────────────────────────────────────────
    title_txt    = ft.Text("Gerenciador de Switch's", size=20,
                           weight=ft.FontWeight.BOLD, color=_DARK["text"])
    subtitle_txt = ft.Text("Automação de Redes · BuritiLabs", size=12,
                           color=_DARK["sub"])

    # ── campos ──────────────────────────────────────────────────────
    def _mk_field(label, icon, **kw):
        return ft.TextField(
            label=label,
            prefix_icon=icon,
            border_color=_DARK["neon"],
            focused_border_color=_DARK["neon"],
            cursor_color=_DARK["neon"],
            label_style=ft.TextStyle(color=_DARK["field_label"]),
            color=_DARK["field_text"],
            bgcolor=_DARK["field_bg"],
            filled=True,
            width=320,
            **kw,
        )

    username = _mk_field("Usuário",  ft.Icons.PERSON_OUTLINE)
    password = _mk_field("Senha",    ft.Icons.LOCK_OUTLINE,
                          password=True, can_reveal_password=True,
                          on_submit=lambda _: do_login())

    error_msg = ft.Text("", color=ft.Colors.RED_ACCENT, size=12, visible=False)

    # ── botão entrar ─────────────────────────────────────────────────
    btn_text = ft.Text("ENTRAR", color="#ffffff",
                       weight=ft.FontWeight.BOLD, size=14)
    login_btn = ft.Container(
        content=btn_text,
        width=320, height=45,
        border_radius=8,
        alignment=ft.Alignment(0, 0),
        gradient=ft.LinearGradient(colors=_DARK["btn"],
                                   begin=ft.Alignment(-1, 0),
                                   end=ft.Alignment(1, 0)),
        shadow=ft.BoxShadow(blur_radius=18, spread_radius=1,
                             color=ft.Colors.with_opacity(
                                 _DARK["btn_shadow_op"], _DARK["neon"])),
        on_click=lambda _: do_login(),
    )

    # ── badge LDAP ───────────────────────────────────────────────────
    cfg          = load_config()
    badge_label  = "Autenticação via LDAP/AD ativa" if cfg.get("ldap_enabled") else "Login local"
    badge_icon   = ft.Icon(ft.Icons.SHIELD, size=12, color=_DARK["badge"])
    badge_text   = ft.Text(badge_label, size=11,  color=_DARK["badge"])
    ldap_badge   = ft.Row([badge_icon, badge_text], spacing=4, tight=True)

    # ── toggle de tema ───────────────────────────────────────────────
    theme_btn = ft.IconButton(
        icon=ft.Icons.DARK_MODE,
        icon_color=_DARK["neon"],
        tooltip="Alternar tema",
        style=ft.ButtonStyle(shadow_color=ft.Colors.with_opacity(0.3, _DARK["neon"]),
                              elevation=4),
    )

    # ── aplica paleta ────────────────────────────────────────────────
    def apply_theme():
        p = t()
        # logos
        logo_dark.visible  = is_dark[0]
        logo_light.visible = not is_dark[0]
        # títulos
        title_txt.color    = p["text"]
        subtitle_txt.color = p["sub"]
        # campos
        for f in [username, password]:
            f.border_color         = p["neon"]
            f.focused_border_color = p["neon"]
            f.cursor_color         = p["neon"]
            f.label_style          = ft.TextStyle(color=p["field_label"])
            f.color                = p["field_text"]
            f.bgcolor              = p["field_bg"]
        # botão
        login_btn.gradient = ft.LinearGradient(
            colors=p["btn"], begin=ft.Alignment(-1, 0), end=ft.Alignment(1, 0))
        login_btn.shadow = ft.BoxShadow(
            blur_radius=18 if is_dark[0] else 14, spread_radius=1,
            color=ft.Colors.with_opacity(p["btn_shadow_op"], p["neon"]))
        # badge
        badge_icon.color = p["badge"]
        badge_text.color = p["badge"]
        # theme button
        theme_btn.icon       = ft.Icons.DARK_MODE if is_dark[0] else ft.Icons.LIGHT_MODE
        theme_btn.icon_color = p["neon"]
        # card
        card.bgcolor = p["card"]
        card.border  = ft.border.all(1, ft.Colors.with_opacity(p["border_op"], p["border"]))
        card.shadow  = ft.BoxShadow(
            blur_radius=p["shadow_blur"], spread_radius=p["shadow_spread"],
            color=ft.Colors.with_opacity(p["shadow_op"], p["border"]),
            offset=ft.Offset(0, p["shadow_dy"]))
        # fundo
        outer.gradient = ft.LinearGradient(
            colors=p["bg"], begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1))
        page.update()

    def toggle_theme(_):
        is_dark[0] = not is_dark[0]
        page.theme_mode = ft.ThemeMode.DARK if is_dark[0] else ft.ThemeMode.LIGHT
        apply_theme()

    theme_btn.on_click = toggle_theme

    # ── login ────────────────────────────────────────────────────────
    def do_login():
        u = username.value.strip()
        p = password.value
        if not u or not p:
            error_msg.value   = "Preencha usuário e senha."
            error_msg.visible = True
            page.update()
            return
        cfg2 = load_config()
        if cfg2.get("ldap_enabled"):
            ok, msg = ldap_login(u, p, cfg2)
        else:
            ok  = (u == "admin" and p == "admin")
            msg = "Credenciais inválidas. (padrão: admin/admin)" if not ok else ""
        if ok:
            on_login_success(u)
        else:
            error_msg.value   = msg
            error_msg.visible = True
            page.update()

    # ── card ─────────────────────────────────────────────────────────
    card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    logo_slot,
                    ft.Container(height=6),
                    title_txt,
                    subtitle_txt,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                margin=ft.margin.only(bottom=20),
            ),
            username,
            ft.Container(height=10),
            password,
            ft.Container(height=6),
            error_msg,
            ft.Container(height=14),
            login_btn,
            ft.Container(height=8),
            ldap_badge,
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True),
        width=390, padding=36, border_radius=18,
        bgcolor=_DARK["card"],
        border=ft.border.all(1, ft.Colors.with_opacity(_DARK["border_op"], _DARK["border"])),
        shadow=ft.BoxShadow(
            blur_radius=_DARK["shadow_blur"], spread_radius=_DARK["shadow_spread"],
            color=ft.Colors.with_opacity(_DARK["shadow_op"], _DARK["border"]),
            offset=ft.Offset(0, _DARK["shadow_dy"])),
    )

    # ── barra de tema ────────────────────────────────────────────────
    top_bar = ft.Container(
        content=ft.Row([ft.Container(expand=True), theme_btn],
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
    )

    # ── container externo ────────────────────────────────────────────
    outer = ft.Container(
        width=_w(), height=_h(),
        alignment=ft.Alignment(0, 0),
        gradient=ft.LinearGradient(
            colors=_DARK["bg"],
            begin=ft.Alignment(0, -1),
            end=ft.Alignment(0, 1),
        ),
        content=ft.Stack(
            [
                ft.Container(expand=True, alignment=ft.Alignment(0, 0), content=card),
                ft.Container(content=top_bar, top=0, right=0, left=0),
            ],
            expand=True,
        ),
    )

    def on_resize(_):
        outer.width  = _w()
        outer.height = _h()
        outer.update()

    page.on_resize = on_resize

    return outer
