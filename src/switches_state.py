"""
Estado global dos switches conectados.
Qualquer página importa este módulo e chama add/remove.
Os listeners são notificados a cada mudança.

Nota: este módulo pode ser acessado por threads (ex.: conexões paralelas).
"""
from __future__ import annotations

import threading

_switches: dict[str, dict] = {}  # { switch_id: info_dict }
_listeners: list = []  # callables(switches_dict)
_lock = threading.Lock()


def add(info: dict) -> None:
    with _lock:
        _switches[info["id"]] = info
        snapshot = dict(_switches)
        listeners = list(_listeners)
    _notify(listeners, snapshot)


def remove(switch_id: str) -> None:
    with _lock:
        _switches.pop(switch_id, None)
        snapshot = dict(_switches)
        listeners = list(_listeners)
    _notify(listeners, snapshot)


def get_all() -> dict[str, dict]:
    with _lock:
        return dict(_switches)


def on_change(callback) -> None:
    """Registra um listener chamado sempre que a lista muda."""
    with _lock:
        if callback not in _listeners:
            _listeners.append(callback)


def off_change(callback) -> None:
    """Remove um listener."""
    with _lock:
        try:
            _listeners.remove(callback)
        except ValueError:
            pass


def _notify(listeners: list, snapshot: dict[str, dict]) -> None:
    for cb in listeners:
        try:
            cb(snapshot)
        except Exception:
            pass
