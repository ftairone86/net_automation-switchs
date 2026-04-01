import flet as ft
import threading
import switches_state
import theme_state
import vendor_assets
import colors

CARD_LABELS = {
    "switch_details":     "Switch Details",
    "port_status":        "Port Status",
    "data_visualize":     "Data Visualize",
    "port_status_large":  "Port Status (Large)",
    "vlan_config":        "VLAN Configurations",
}

# ---------- conteúdos dos cards ----------

def _status_icon(icon, color):
    return ft.Container(
        content=ft.Icon(icon, color=color, size=20),
        bgcolor=ft.Colors.with_opacity(0.15, color),
        border_radius=8,
        padding=8,
    )


def _switch_details_content(page: ft.Page):
    ac = colors.accent(page)
    return ft.Column([
        ft.Row([
            ft.Image(
                src="https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg",
                width=32, height=32,
            ),
            ft.Text("Fabricante: Cisco Systems", size=14),
        ], spacing=10),
        ft.Row([
            ft.Icon(ft.Icons.PHONE_IPHONE, size=20, color=ft.Colors.BLUE_ACCENT),
            ft.Text("Versão do iOS: XE 17.6.4", size=14, color=ft.Colors.GREY_400),
        ], spacing=10),
        ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=20, color=ac),
            ft.Text("Status: ", size=14),
            ft.Text("Conectado", size=14, color=ac, weight=ft.FontWeight.BOLD),
        ], spacing=10),
        ft.Row([
            ft.Icon(ft.Icons.ROUTER, size=20, color=ft.Colors.CYAN_ACCENT),
            ft.Text("Switch: Catalyst 9300L 24P", size=14),
        ], spacing=10),
    ], spacing=10, tight=True)


def _port_status_content(page: ft.Page):
    ac = colors.accent(page)
    return ft.Row([
        ft.Column([
            ft.Icon(ft.Icons.CABLE, size=32, color=ft.Colors.CYAN_ACCENT),
            ft.Text("UP", size=11, color=ac, weight=ft.FontWeight.BOLD),
            ft.Text("18 portas", size=10, color=ft.Colors.GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Column([
            ft.Icon(ft.Icons.CABLE, size=32, color=ft.Colors.GREY_600),
            ft.Text("DOWN", size=11, color=ft.Colors.RED_ACCENT, weight=ft.FontWeight.BOLD),
            ft.Text("6 portas", size=10, color=ft.Colors.GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY)


def _data_visualize_content():
    return ft.Row([
        ft.Stack([
            ft.Container(width=80, height=80, border_radius=40,
                         border=ft.border.all(10, ft.Colors.PURPLE_ACCENT)),
            ft.Container(width=80, height=80,
                         content=ft.Text("75%", size=14, weight=ft.FontWeight.BOLD),
                         alignment=ft.Alignment(0, 0)),
        ]),
        ft.Column([
            ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.PURPLE_ACCENT, border_radius=3),
                    ft.Text("TX", size=12)], spacing=6),
            ft.Row([ft.Container(width=10, height=10, bgcolor=ft.Colors.CYAN_ACCENT, border_radius=3),
                    ft.Text("RX", size=12)], spacing=6),
        ], spacing=8),
    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _port_status_large_content():
    return ft.Column([
        ft.Text("Progressing Tasks", size=12, color=ft.Colors.GREY_400),
        ft.Row([
            ft.ProgressBar(value=0.27, color=ft.Colors.CYAN_ACCENT, bgcolor=ft.Colors.GREY_800, expand=True),
            ft.Text("27%", size=12),
        ], spacing=8),
        ft.Text("Contressing", size=12, color=ft.Colors.GREY_400),
        ft.Row([
            ft.ProgressBar(value=1.0, color=ft.Colors.PURPLE_ACCENT, bgcolor=ft.Colors.GREY_800, expand=True),
            ft.Text("100%", size=12),
        ], spacing=8),
        ft.Container(
            height=50, border_radius=8,
            gradient=ft.LinearGradient(
                colors=[ft.Colors.with_opacity(0.3, ft.Colors.CYAN_ACCENT), ft.Colors.TRANSPARENT],
                begin=ft.Alignment(0, -1), end=ft.Alignment(0, 1),
            ),
            content=ft.Text("~ tráfego ~", size=11, color=ft.Colors.GREY_600),
            alignment=ft.Alignment(0, 0),
        ),
    ], spacing=8, tight=True)


def _vlan_config_content():
    logs = [
        ("[tags] Processing...",             ft.Colors.GREY_400),
        ("[tags] Copying process...",        ft.Colors.GREY_400),
        ("[info] Selecting track status...", ft.Colors.CYAN_ACCENT),
        ("[info] Automation tasks...",       ft.Colors.PURPLE_ACCENT),
    ]
    return ft.Container(
        content=ft.Column([
            ft.Text(text, size=11, color=color, font_family="monospace")
            for text, color in logs
        ], spacing=4),
        bgcolor=ft.Colors.SURFACE_CONTAINER_LOWEST,
        border_radius=8,
        padding=10,
    )


# tamanhos predefinidos (largura, altura)
SIZES = [
    (180, 160),
    (280, 200),
    (380, 240),
    (500, 280),
]


# ---------- card arrastável com tamanho por barras ----------

def _build_card(card_id, content_fn, left, top, page: ft.Page,
                init_w=320, init_h=220):
    size_idx = [min(range(len(SIZES)), key=lambda i: abs(SIZES[i][0] - init_w))]

    def on_drag(e: ft.DragUpdateEvent):
        if e.local_delta:
            wrapper.left = max(0, (wrapper.left or 0) + e.local_delta.x)
            wrapper.top  = max(0, (wrapper.top  or 0) + e.local_delta.y)
            wrapper.update()

    def set_size(idx):
        size_idx[0] = idx
        w, h = SIZES[idx]
        card_body.width  = w
        card_body.height = h
        for i, bar in enumerate(size_bars):
            bar.bgcolor = ft.Colors.CYAN_ACCENT if i <= idx else ft.Colors.GREY_700
        card_body.update()

    size_bars = [
        ft.Container(
            width=12, height=10,
            bgcolor=ft.Colors.CYAN_ACCENT if i <= size_idx[0] else ft.Colors.GREY_700,
            border_radius=2,
            on_click=lambda e, i=i: set_size(i),
        )
        for i in range(4)
    ]

    drag_handle = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.MOVE,
        drag_interval=30,
        on_pan_update=on_drag,
        content=ft.Row([
            ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.GREY_500, size=16),
            ft.Text(CARD_LABELS[card_id], weight=ft.FontWeight.BOLD, size=13, expand=True),
            ft.Row(size_bars, spacing=3),
        ], spacing=6),
    )

    # inner_ct guarda o conteúdo temático — substituído no refresh
    inner_ct = ft.Container(
        content=content_fn(page),
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    w0, h0 = SIZES[size_idx[0]]
    card_body = ft.Container(
        content=ft.Column([
            drag_handle,
            ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
            inner_ct,
        ], tight=True, spacing=2),
        width=w0, height=h0,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12, padding=12,
        shadow=ft.BoxShadow(blur_radius=10,
                             color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK)),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    def refresh_content():
        inner_ct.content = content_fn(page)
        inner_ct.update()

    wrapper = ft.Container(content=card_body, left=left, top=top)
    return wrapper, refresh_content


# ---------- card de switch conectado (dinâmico) ----------

_VENDOR_ICONS = {
    "Cisco Systems": ft.Icons.ROUTER,
    "Juniper Networks": ft.Icons.DEVICE_HUB,
    "Arista Networks": ft.Icons.SETTINGS_ETHERNET,
    "Huawei": ft.Icons.SETTINGS_INPUT_ANTENNA,
    "Dell": ft.Icons.DEVICE_HUB,
    "Aruba": ft.Icons.WIFI,
    "HP": ft.Icons.LAN,
}


def _vendor_mark(vendor: str, size: int = 22, width: int | None = None):
    kwargs = vendor_assets.vendor_logo_kwargs(vendor)
    if kwargs:
        return ft.Image(width=width or size * 2, height=size, fit=ft.BoxFit.CONTAIN, **kwargs)

    icon = _VENDOR_ICONS.get(vendor, ft.Icons.ROUTER)
    return ft.Icon(icon, color=ft.Colors.CYAN_ACCENT, size=size)



def _usage_ring(value, color, label: str):
    """Mini anel de uso com percentual centralizado."""
    size = 52
    if not isinstance(value, (int, float)):
        return ft.Column([
            ft.Container(
                width=size, height=size,
                border_radius=size / 2,
                border=ft.border.all(5, ft.Colors.GREY_800),
                content=ft.Text("—", size=10, color=ft.Colors.GREY_600),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Text(label, size=9, color=ft.Colors.GREY_600),
        ], tight=True, spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    pct = max(0, min(100, int(value)))
    return ft.Column([
        ft.Stack([
            ft.ProgressRing(
                value=pct / 100,
                width=size, height=size,
                stroke_width=6,
                color=color,
                bgcolor=ft.Colors.with_opacity(0.15, color),
            ),
            ft.Container(
                width=size, height=size,
                content=ft.Text(
                    f"{pct}%", size=10,
                    weight=ft.FontWeight.BOLD,
                    color=color,
                ),
                alignment=ft.Alignment(0, 0),
            ),
        ]),
        ft.Text(label, size=9, color=ft.Colors.GREY_500),
    ], tight=True, spacing=3, horizontal_alignment=ft.CrossAxisAlignment.CENTER)


def _switch_card_content(sw: dict, page: ft.Page, on_disconnect_cb):
    """Conteúdo interno do card de um switch conectado."""
    ac = colors.accent(page)

    vendor      = sw.get("vendor") or "Detectando…"
    model       = sw.get("model") or "—"
    ios_version = sw.get("ios_version") or "—"
    cpu         = sw.get("cpu_usage")
    mem         = sw.get("mem_usage")
    ports_up    = sw.get("ports_up", 0)
    ports_down  = sw.get("ports_down", 0)

    status_text  = "Conectado"   if vendor != "Detectando…" else "Identificando"
    status_color = ac            if vendor != "Detectando…" else ft.Colors.ORANGE_ACCENT

    return ft.Column([
        # ── cabeçalho: logo + fabricante + botão desconectar ──
        ft.Row([
            _vendor_mark(vendor, size=28),
            ft.Text(f"Fabricante: {vendor}", size=13, expand=True),
            ft.IconButton(
                icon=ft.Icons.POWER_OFF,
                icon_color=ft.Colors.RED_ACCENT,
                icon_size=16,
                tooltip="Desconectar",
                on_click=lambda _: on_disconnect_cb(sw.get("id")),
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),

        # ── iOS ──
        ft.Row([
            ft.Icon(ft.Icons.PHONE_IPHONE, size=18, color=ft.Colors.BLUE_ACCENT),
            ft.Text(f"Versão do iOS: {ios_version}", size=13, color=ft.Colors.GREY_400),
        ], spacing=8),

        # ── status ──
        ft.Row([
            ft.Icon(ft.Icons.CHECK_CIRCLE, size=18, color=status_color),
            ft.Text("Status: ", size=13),
            ft.Text(status_text, size=13, color=status_color, weight=ft.FontWeight.BOLD),
        ], spacing=8),

        # ── modelo ──
        ft.Row([
            ft.Icon(ft.Icons.ROUTER, size=18, color=ft.Colors.CYAN_ACCENT),
            ft.Text(f"Switch: {model}", size=13),
        ], spacing=8),

        ft.Divider(height=6, color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),

        # ── CPU / MEM (gauges) + portas ──
        ft.Row([
            _usage_ring(cpu, ft.Colors.CYAN_ACCENT,   "CPU"),
            _usage_ring(mem, ft.Colors.ORANGE_ACCENT, "MEM"),
            ft.Container(expand=True),
            ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CABLE, size=14, color=ac),
                    ft.Text(f"UP", size=11, color=ft.Colors.GREY_500),
                    ft.Text(str(ports_up), size=14, weight=ft.FontWeight.BOLD, color=ac),
                ], spacing=4, tight=True),
                ft.Row([
                    ft.Icon(ft.Icons.CABLE, size=14, color=ft.Colors.RED_ACCENT),
                    ft.Text(f"DOWN", size=11, color=ft.Colors.GREY_500),
                    ft.Text(str(ports_down), size=14, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.RED_ACCENT),
                ], spacing=4, tight=True),
            ], spacing=6, tight=True, horizontal_alignment=ft.CrossAxisAlignment.END),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
    ], spacing=8, tight=True)



def _build_switch_card(sw: dict, left: int, top: int, page: ft.Page, on_disconnect_cb):
    label = f"Switch · {sw.get('host', '')}"

    def on_drag(e: ft.DragUpdateEvent):
        if e.local_delta:
            wrapper.left = max(0, (wrapper.left or 0) + e.local_delta.x)
            wrapper.top = max(0, (wrapper.top or 0) + e.local_delta.y)
            wrapper.update()

    size_idx = [1]

    def set_size(idx):
        size_idx[0] = idx
        w, h = SIZES[idx]
        card_body.width = w
        card_body.height = h
        for i, bar in enumerate(size_bars):
            bar.bgcolor = ft.Colors.CYAN_ACCENT if i <= idx else ft.Colors.GREY_700
        card_body.update()

    size_bars = [
        ft.Container(
            width=12,
            height=10,
            bgcolor=ft.Colors.CYAN_ACCENT if i <= size_idx[0] else ft.Colors.GREY_700,
            border_radius=2,
            on_click=lambda e, i=i: set_size(i),
        )
        for i in range(4)
    ]

    title_text = ft.Text(label, weight=ft.FontWeight.BOLD, size=12, expand=True)

    drag_handle = ft.GestureDetector(
        mouse_cursor=ft.MouseCursor.MOVE,
        drag_interval=30,
        on_pan_update=on_drag,
        content=ft.Row(
            [
                ft.Icon(ft.Icons.DRAG_INDICATOR, color=ft.Colors.GREY_500, size=16),
                title_text,
                ft.Row(size_bars, spacing=3),
            ],
            spacing=6,
        ),
    )

    body_ct = ft.Container(
        content=_switch_card_content(sw, page, on_disconnect_cb),
        expand=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    def refresh(new_sw: dict):
        body_ct.content = _switch_card_content(new_sw, page, on_disconnect_cb)
        body_ct.update()

    w0, h0 = SIZES[size_idx[0]]
    card_body = ft.Container(
        content=ft.Column(
            [
                drag_handle,
                ft.Divider(height=6, color=ft.Colors.TRANSPARENT),
                body_ct,
            ],
            tight=True,
            spacing=2,
        ),
        width=w0,
        height=h0,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12,
        padding=12,
        shadow=ft.BoxShadow(
            blur_radius=10, color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK)
        ),
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.CYAN_ACCENT)),
    )

    wrapper = ft.Container(content=card_body, left=left, top=top)
    wrapper.data = {"refresh": refresh}
    return wrapper


# ---------- página principal ----------

def DashboardPage(page: ft.Page):
    visibility = {k: True for k in CARD_LABELS}
    def _dispatch(fn):
        """Agenda atualizações de UI na event-loop do Flet."""
        try:
            loop = page.session.connection.loop
            if loop is not None and not getattr(loop, "is_closed", lambda: False)():
                loop.call_soon_threadsafe(fn)
                return
        except Exception as exc:
            if "event loop is closed" in str(exc).lower():
                return
        try:
            async def _runner():
                fn()
            page.run_task(_runner)
            return
        except Exception as exc:
            if "event loop is closed" in str(exc).lower():
                return
        try:
            fn()
        except Exception:
            return


    card_configs = [
        ("switch_details",    _switch_details_content,    0,   0,   340, 240),
        ("port_status",       _port_status_content,       360, 0,   240, 180),
        ("data_visualize",    _data_visualize_content,    360, 200, 240, 200),  # type: ignore
        ("port_status_large", _port_status_large_content, 0,   260, 340, 240),
        ("vlan_config",       _vlan_config_content,       0,   520, 340, 200),
    ]

    card_refs     = {}
    refresh_fns   = []   # funções de refresh de tema dos cards estáticos
    stack_controls = []

    for card_id, content_fn, l, t, w, h in card_configs:
        # apenas switch_details e port_status têm cores temáticas
        needs_theme = content_fn in (_switch_details_content, _port_status_content)
        if needs_theme:
            card, refresh_fn = _build_card(card_id, content_fn, l, t, page, w, h)
            refresh_fns.append(refresh_fn)
        else:
            # funções que não aceitam page — wrapper compatível
            def _wrap(fn=content_fn):
                def _fn(_page): return fn()
                return _fn
            card, _ = _build_card(card_id, _wrap(), l, t, page, w, h)
        card_refs[card_id] = card
        stack_controls.append(card)

    # cards dinâmicos de switches { switch_id: wrapper }
    sw_card_refs: dict[str, ft.Container] = {}

    dash_stack = ft.Stack(stack_controls, height=900)

    def _next_position() -> tuple[int, int]:
        """Posição para o próximo card de switch (empilha a partir de x=620)."""
        n = len(sw_card_refs)
        return 620, n * 260

    def _on_disconnect(switch_id: str):
        switches_state.remove(switch_id)

    def _on_state_change(switches: dict):
        def _apply():
            # adiciona cards de novos switches
            for sid, sw in switches.items():
                if sid not in sw_card_refs:
                    left, top = _next_position()
                    card = _build_switch_card(sw, left, top, page, _on_disconnect)
                    sw_card_refs[sid] = card
                    dash_stack.controls.append(card)
                else:
                    card = sw_card_refs[sid]
                    refresh = getattr(card, 'data', {}).get('refresh') if hasattr(card, 'data') else None
                    if callable(refresh):
                        refresh(sw)
            
            # remove cards de switches desconectados
            removed = [sid for sid in list(sw_card_refs) if sid not in switches]
            for sid in removed:
                card = sw_card_refs.pop(sid)
                if card in dash_stack.controls:
                    dash_stack.controls.remove(card)
            
            page.update()

        _dispatch(_apply)

    switches_state.on_change(_on_state_change)

    # carrega switches já conectados (se houver ao navegar de volta)
    for sid, sw in switches_state.get_all().items():
        left, top = _next_position()
        card = _build_switch_card(sw, left, top, page, _on_disconnect)
        sw_card_refs[sid] = card
        dash_stack.controls.append(card)

    # refresh de tema — atualiza cards estáticos e switch cards
    def _refresh_theme():
        for fn in refresh_fns:
            fn()
        # rebuild switch cards (cores dinâmicas)
        _on_state_change(switches_state.get_all())

    theme_state.on_change(_refresh_theme)

    # ---------- menu de cards ----------
    def open_menu(e):
        def on_toggle(card_id, value):
            card_refs[card_id].visible = value
            visibility[card_id] = value
            page.update()

        rows = [
            ft.Row([
                ft.Checkbox(
                    value=visibility[cid],
                    on_change=lambda e, cid=cid: on_toggle(cid, e.control.value),
                ),
                ft.Text(label, size=14),
            ])
            for cid, label in CARD_LABELS.items()
        ]

        def close_dlg(e):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Gerenciar Cards"),
            content=ft.Column(rows, tight=True, spacing=4),
            actions=[ft.TextButton(content=ft.Text("Fechar"), on_click=close_dlg)],
            open=True,
        )
        page.overlay.append(dlg)
        page.update()

    manage_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.DASHBOARD_CUSTOMIZE, size=16),
            ft.Text("Gerenciar Cards", size=13),
        ], spacing=6, tight=True),
        on_click=open_menu,
    )

    return ft.Column(
        [
            ft.Row([
                ft.Text("Dashboard", size=25, weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                manage_btn,
            ]),
            ft.Text("Arraste pelo ícone ⠿ · Redimensione pelas barras · "
                    "⏻ para desconectar switch",
                    size=11, color=ft.Colors.GREY_500),
            dash_stack,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=10,
    )
