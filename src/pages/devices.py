"""
Página de Devices — conectar/desconectar switches.
"""
from __future__ import annotations
import threading
import concurrent.futures
import flet as ft
import switches_state
import connector
import colors
import theme_state
import vendor_assets


_VENDOR_ICONS = {
    "Cisco Systems": ft.Icons.ROUTER,
    "Juniper Networks": ft.Icons.DEVICE_HUB,
    "Arista Networks": ft.Icons.SETTINGS_ETHERNET,
    "Huawei": ft.Icons.ROUTER,
    "Dell": ft.Icons.ROUTER,
    "Aruba": ft.Icons.ROUTER,
    "HP": ft.Icons.ROUTER,
}


def _vendor_mark(vendor: str, size: int = 28, width: int | None = None):
    kwargs = vendor_assets.vendor_logo_kwargs(vendor)
    if kwargs:
        return ft.Image(width=width or size * 2, height=size, fit=ft.BoxFit.CONTAIN, **kwargs)

    icon = _VENDOR_ICONS.get(vendor, ft.Icons.ROUTER)
    return ft.Icon(icon, color=ft.Colors.CYAN_ACCENT, size=size)



def DevicesPage(page: ft.Page):

    # ── lista de entradas pendentes ───────────────────────────────────
    pending: list[dict] = []   # cada item: {host, user, pw, port}
    pending_col = ft.Column(spacing=6, tight=True)

    # ── campos do formulário ─────────────────────────────────────────
    f_host  = ft.TextField(label="IP / Hostname", width=220,
                           border_color=colors.accent(page),
                           prefix_icon=ft.Icons.ROUTER)
    f_user  = ft.TextField(label="Usuário",       width=160,
                           border_color=colors.accent(page),
                           prefix_icon=ft.Icons.PERSON_OUTLINE)
    f_pw    = ft.TextField(label="Senha",         width=160,
                           border_color=colors.accent(page),
                           prefix_icon=ft.Icons.LOCK_OUTLINE,
                           password=True, can_reveal_password=True)
    f_port  = ft.TextField(label="Porta SSH",     width=100,
                           border_color=colors.accent(page),
                           value="22")
    f_vendor  = ft.Dropdown(
        label="Fabricante",
        width=160,
        border_color=colors.accent(page),
        value="Auto",
        options=[
            ft.dropdown.Option("Auto"),
            ft.dropdown.Option("Cisco"),
            ft.dropdown.Option("Huawei"),
            ft.dropdown.Option("HP"),
            ft.dropdown.Option("Aruba"),
            ft.dropdown.Option("Dell"),
        ],
    )
    status_msg = ft.Text("", size=12, color=ft.Colors.GREY_400)

    is_connecting = [False]
    enrich_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def _dispatch(fn):
        """Agenda atualizações de UI na event-loop do Flet (thread-safe)."""
        try:
            loop = page.session.connection.loop
            if loop is not None and not loop.is_closed():
                loop.call_soon_threadsafe(fn)
                return
        except Exception:
            pass
        try:
            fn()
        except Exception:
            pass

    def _submit_enrich(sw: dict):
        hint = sw.get("vendor_hint")
        hint = None if hint in (None, "", "auto") else hint

        def _job():
            ok, full = connector.connect_switch(
                sw["host"], sw["user"], sw["pw"], sw["port"], hint
            )

            def _apply():
                if ok:
                    switches_state.add(full)
                    vendor = (full or {}).get("vendor")
                    status_msg.value = f"{sw['host']}: fabricante identificado — {vendor}."
                    status_msg.color = colors.accent(page)
                else:
                    status_msg.value = str(full)
                    status_msg.color = ft.Colors.ORANGE_ACCENT

                _rebuild_connected()
                page.update()

            _dispatch(_apply)

        enrich_executor.submit(_job)

    def connect_one(sw: dict):
        """Conecta apenas um item da fila."""
        if is_connecting[0]:
            status_msg.value = "Já existe uma conexão em andamento. Aguarde…"
            status_msg.color = ft.Colors.ORANGE_ACCENT
            page.update()
            return

        # remove da fila (se ainda estiver lá)
        try:
            pending.remove(sw)
        except ValueError:
            pass
        _rebuild_pending()

        connect_btn.disabled = True
        spinner.visible = True
        is_connecting[0] = True
        status_msg.value = f"Conectando {sw["host"]}:{sw["port"]}…"
        status_msg.color = ft.Colors.GREY_400
        page.update()

        def _worker_one():
            hint = sw.get("vendor_hint")
            hint = None if hint in (None, "", "auto") else hint

            try:
                ok, result = connector.connect_switch_fast(
                    sw["host"], sw["user"], sw["pw"], sw["port"], hint
                )
            except Exception as exc:
                ok, result = False, f"{sw['host']}: erro inesperado — {exc}"

            def _apply():
                try:
                    if ok:
                        switches_state.add(result)
                        status_msg.value = f"✓ {sw['host']} conectado. Identificando fabricante…"
                        status_msg.color = colors.accent(page)
                        _submit_enrich(sw)
                    else:
                        status_msg.value = str(result)
                        status_msg.color = ft.Colors.RED_ACCENT

                    _rebuild_connected()
                finally:
                    connect_btn.disabled = False
                    spinner.visible = False
                    is_connecting[0] = False
                    page.update()

            _dispatch(_apply)

        threading.Thread(target=_worker_one, daemon=True).start()

    # ── fila de pendentes (UI) ────────────────────────────────────────

    def _rebuild_pending():
        pending_col.controls.clear()
        for s in list(pending):

            def remove_pending(_, item=s):
                try:
                    pending.remove(item)
                except ValueError:
                    return
                _rebuild_pending()
                page.update()

            def connect_pending(_, item=s):
                connect_one(item)

            pending_col.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.PENDING, color=ft.Colors.ORANGE_ACCENT, size=16),
                            ft.Text(f"{s['host']}:{s['port']}", size=13, expand=True),
                            ft.Text(s["user"], size=12, color=ft.Colors.GREY_400),
                            ft.Text(
                                (s.get("vendor_hint") or "auto").upper(),
                                size=11,
                                color=ft.Colors.GREY_500,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.PLAY_ARROW,
                                icon_size=16,
                                tooltip="Conectar somente este",
                                on_click=connect_pending,
                                disabled=is_connecting[0],
                            ),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_size=16,
                                tooltip="Remover",
                                on_click=remove_pending,
                                disabled=is_connecting[0],
                            ),
                        ],
                        spacing=8,
                    ),
                    bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.ORANGE_ACCENT),
                    border_radius=8,
                    padding=ft.padding.symmetric(8, 4),
                    border=ft.border.all(1, ft.Colors.with_opacity(0.2, ft.Colors.ORANGE_ACCENT)),
                )
            )
        page.update()

    def add_to_queue(_):
        host = f_host.value.strip()
        user = f_user.value.strip()
        pw   = f_pw.value
        port = f_port.value.strip() or "22"
        vendor_hint = (f_vendor.value or "Auto").strip().lower()
        if not host or not user or not pw:
            status_msg.value = "Preencha IP, usuário e senha."
            status_msg.color = ft.Colors.RED_ACCENT
            page.update()
            return
        pending.append({"host": host, "user": user, "pw": pw, "port": int(port), "vendor_hint": vendor_hint})
        f_host.value = ""
        status_msg.value = f"✓ {host} adicionado à fila ({len(pending)} aguardando)."
        status_msg.color = colors.accent(page)
        _rebuild_pending()

    # ── cards de switches conectados ──────────────────────────────────
    connected_col = ft.Column(spacing=10, tight=True)

    def _rebuild_connected():
        connected_col.controls.clear()

        for sw in switches_state.get_all().values():
            def on_disconnect(_, sid=sw["id"]):
                switches_state.remove(sid)
                _rebuild_connected()
                page.update()

            connected_col.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Container(
                            content=_vendor_mark(sw["vendor"], size=28),
                            bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.CYAN_ACCENT),
                            border_radius=8, padding=8,
                        ),
                        ft.Column([
                            ft.Text(sw["host"], size=14, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{sw['vendor']}  ·  {sw['model']}", size=12,
                                    color=ft.Colors.GREY_400),
                            ft.Text(f"IOS: {sw['ios_version']}", size=11,
                                    color=ft.Colors.GREY_500),
                            ft.Row([
                                ft.Icon(ft.Icons.SPEED, size=13, color=ft.Colors.CYAN_ACCENT),
                                ft.Text(
                                    f"CPU: {sw.get('cpu_usage', '—')}",
                                    size=11,
                                    color=ft.Colors.GREY_500,
                                ),
                                ft.Icon(ft.Icons.STORAGE, size=13, color=ft.Colors.ORANGE_ACCENT),
                                ft.Text(
                                    f"MEM: {sw.get('mem_usage', '—')}",
                                    size=11,
                                    color=ft.Colors.GREY_500,
                                ),
                            ], spacing=6),
                        ], spacing=2, tight=True, expand=True),
                        ft.Column([
                            ft.Container(
                                content=ft.Row([
                                    ft.Container(width=8, height=8, border_radius=4,
                                                 bgcolor=colors.accent(page)),
                                    ft.Text("Conectado", size=11,
                                            color=colors.accent(page),
                                            weight=ft.FontWeight.BOLD),
                                ], spacing=4, tight=True),
                                bgcolor=colors.accent_dim(page),
                                border_radius=12,
                                padding=ft.padding.symmetric(8, 4),
                            ),
                            ft.Row([
                                ft.Icon(ft.Icons.CABLE, size=14,
                                        color=colors.accent(page)),
                                ft.Text(f"UP: {sw['ports_up']}", size=11,
                                        color=colors.accent(page)),
                                ft.Icon(ft.Icons.CABLE, size=14,
                                        color=ft.Colors.RED_ACCENT),
                                ft.Text(f"DOWN: {sw['ports_down']}", size=11,
                                        color=ft.Colors.RED_ACCENT),
                            ], spacing=6, tight=True),
                        ], spacing=6, tight=True, horizontal_alignment=ft.CrossAxisAlignment.END),
                        ft.IconButton(
                            icon=ft.Icons.POWER_OFF,
                            icon_color=ft.Colors.RED_ACCENT,
                            tooltip="Desconectar",
                            on_click=on_disconnect,
                        ),
                    ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
                    border_radius=12, padding=14,
                    border=ft.border.all(1, ft.Colors.with_opacity(0.3, ft.Colors.CYAN_ACCENT)),
                )
            )
        page.update()

    # ── desconectar tudo ──────────────────────────────────────────────
    def disconnect_all(_):
        for sid in list(switches_state.get_all().keys()):
            switches_state.remove(sid)
        _rebuild_connected()
        status_msg.value = "Todos os switches desconectados."
        status_msg.color = ft.Colors.ORANGE_ACCENT
        page.update()

    disconnect_all_btn = ft.OutlinedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.POWER_OFF, size=16, color=ft.Colors.RED_ACCENT),
            ft.Text("Desconectar Todos", size=13, color=ft.Colors.RED_ACCENT),
        ], spacing=6, tight=True),
        on_click=disconnect_all,
    )

    # ── conectar tudo ─────────────────────────────────────────────────
    connect_btn = ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(ft.Icons.PLAY_ARROW, size=16),
            ft.Text("Conectar Todos", size=13),
        ], spacing=6, tight=True),
    )
    spinner = ft.ProgressRing(width=18, height=18, stroke_width=2, visible=False)

    def connect_all(_):
        if is_connecting[0]:
            status_msg.value = "Já existe uma conexão em andamento. Aguarde…"
            status_msg.color = ft.Colors.ORANGE_ACCENT
            page.update()
            return

        if not pending:
            status_msg.value = "Nenhum switch na fila."
            status_msg.color = ft.Colors.ORANGE_ACCENT
            page.update()
            return

        to_connect = list(pending)
        pending.clear()
        _rebuild_pending()

        connect_btn.disabled = True
        spinner.visible      = True
        is_connecting[0] = True
        status_msg.value     = f"Conectando {len(to_connect)} switch(es)…"
        status_msg.color     = ft.Colors.GREY_400
        page.update()

        def _worker():
            ok_count = err_count = 0
            last_error = None
            last_ok = None
            total = len(to_connect)
            max_workers = min(6, max(1, total))

            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as ex:
                futures = {
                    ex.submit(
                        connector.connect_switch_fast,
                        sw["host"],
                        sw["user"],
                        sw["pw"],
                        sw["port"],
                        None if sw.get("vendor_hint") in (None, "", "auto") else sw.get("vendor_hint"),
                    ): sw
                    for sw in to_connect
                }

                for fut in concurrent.futures.as_completed(futures):
                    sw = futures[fut]
                    try:
                        ok, result = fut.result()
                    except Exception as exc:
                        ok, result = False, f"{sw['host']}: erro inesperado — {exc}"
                    if ok:
                        switches_state.add(result)
                        ok_count += 1
                        last_ok = result
                        _submit_enrich(sw)
                    else:
                        err_count += 1
                        last_error = str(result)

                    msg = f"Conectando {total}… {ok_count} ok, {err_count} erro(s)"
                    _dispatch(lambda m=msg: (
                        setattr(status_msg, "value", m),
                        setattr(status_msg, "color", ft.Colors.GREY_400),
                        page.update(),
                    ))
            def _finalize():
                _rebuild_connected()
                connect_btn.disabled = False
                spinner.visible = False
                is_connecting[0] = False

                if ok_count:
                    extra = ""
                    if isinstance(last_ok, dict):
                        t = last_ok.get("connect_time_s")
                        ts = last_ok.get("connect_timings_s", {})
                        extra = (
                            f"  |  Último ok: {last_ok.get('host', '')} em {t}s"
                            f" (detect {ts.get('detect','-')}s, conn {ts.get('connect','-')}s)"
                        )
                    status_msg.value = (
                        f"✓ {ok_count} conectado(s)"
                        + (f", {err_count} erro(s)" if err_count else "")
                        + "."
                        + extra
                    )
                    status_msg.color = colors.accent(page)
                else:
                    status_msg.value = last_error or "Nenhum switch conectado."
                    status_msg.color = ft.Colors.RED_ACCENT if last_error else ft.Colors.ORANGE_ACCENT

                page.update()
            _dispatch(_finalize)

        threading.Thread(target=_worker, daemon=True).start()

    connect_btn.on_click = connect_all

    # ── registra listeners de estado e tema ───────────────────────────
    def _on_state_change(_):
        _dispatch(_rebuild_connected)

    def _refresh_theme():
        ac = colors.accent(page)
        device_hub_icon.color = ac
        add_link_icon.color   = ac
        connected_box.border  = ft.border.all(1, ft.Colors.with_opacity(0.15, ac))
        form_box.border       = ft.border.all(1, ft.Colors.with_opacity(0.15, ac))
        for f in (f_host, f_user, f_pw, f_port, f_vendor):
            f.border_color = ac
        _rebuild_connected()

    switches_state.on_change(_on_state_change)
    theme_state.on_change(_refresh_theme)

    # ── ícones de seção (refs para troca de tema) ──────────────────────
    device_hub_icon = ft.Icon(ft.Icons.DEVICE_HUB, color=colors.accent(page))
    add_link_icon   = ft.Icon(ft.Icons.ADD_LINK,   color=colors.accent(page))

    # ── layout ────────────────────────────────────────────────────────
    connected_box = ft.Container(
        content=ft.Column([
            ft.Row([
                device_hub_icon,
                ft.Text("Switches Conectados", size=16,
                        weight=ft.FontWeight.BOLD),
                ft.Container(expand=True),
                disconnect_all_btn,
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            connected_col,
        ], spacing=10),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12, padding=16,
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, colors.accent(page))),
    )

    form_box = ft.Container(
        content=ft.Column([
            ft.Row([
                add_link_icon,
                ft.Text("Adicionar Switch", size=16,
                        weight=ft.FontWeight.BOLD),
            ], spacing=8),
            ft.Text("Preencha e clique em + para enfileirar. "
                    "Conecte todos de uma vez.",
                    size=12, color=ft.Colors.GREY_400),
            ft.Divider(height=8, color=ft.Colors.TRANSPARENT),
            ft.Row([f_host, f_user, f_pw], spacing=10, wrap=True),
            ft.Row([f_port, f_vendor], spacing=10, wrap=True),
            ft.Row([
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD, size=16),
                        ft.Text("Adicionar à fila", size=13),
                    ], spacing=6, tight=True),
                    on_click=add_to_queue,
                ),
                ft.Container(expand=True),
                connect_btn,
                spinner,
            ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            status_msg,
            ft.Divider(height=4, color=ft.Colors.TRANSPARENT),
            ft.Text("Fila de conexão:", size=12, color=ft.Colors.GREY_500),
            pending_col,
        ], spacing=10),
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        border_radius=12, padding=16,
        border=ft.border.all(1, ft.Colors.with_opacity(0.15, colors.accent(page))),
    )

    return ft.Column(
        [
            ft.Text("Dispositivos", size=25, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            connected_box,
            form_box,
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=16,
    )
