"""Event bus de tema — pages registram callbacks para reagir ao toggle."""
_listeners: list = []


def on_change(cb) -> None:
    if cb not in _listeners:
        _listeners.append(cb)


def off_change(cb) -> None:
    try:
        _listeners.remove(cb)
    except ValueError:
        pass


def notify() -> None:
    for cb in list(_listeners):
        try:
            cb()
        except Exception:
            pass


def clear() -> None:
    _listeners.clear()
