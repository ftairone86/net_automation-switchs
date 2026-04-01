from __future__ import annotations

import re
from pathlib import Path

_ASSETS_VENDOR_DIR = Path(__file__).resolve().parent / "assets" / "vendors"

# URLs SVG públicos usados como fallback quando não há arquivo local
_VENDOR_LOGO_URLS: dict[str, str] = {
    "cisco":   "https://upload.wikimedia.org/wikipedia/commons/6/64/Cisco_logo.svg",
    "huawei":  "https://upload.wikimedia.org/wikipedia/commons/e/e8/Huawei.svg",
    "hp":      "https://upload.wikimedia.org/wikipedia/commons/a/ad/HP_logo_2012.svg",
    "dell":    "https://upload.wikimedia.org/wikipedia/commons/4/48/Dell_Logo.svg",
    "juniper": "https://upload.wikimedia.org/wikipedia/commons/3/31/Juniper_Networks_logo.svg",
    "arista":  "https://upload.wikimedia.org/wikipedia/commons/3/37/Arista-networks-logo.svg",
    "aruba":   "https://upload.wikimedia.org/wikipedia/commons/3/3f/Aruba_Networks_logo.svg",
}


def normalize_vendor_key(vendor: str) -> str:
    v = (vendor or "").strip().lower()

    if not v:
        return "unknown"

    if "cisco" in v:
        return "cisco"

    if "huawei" in v or "vrp" in v:
        return "huawei"

    if "dell" in v or "force10" in v or "os10" in v or "dnos" in v or "powerswitch" in v:
        return "dell"

    if "aruba" in v:
        return "aruba"

    if re.search(r"\bhp\b|hewlett|hpe|procurve|comware", v):
        return "hp"

    if "juniper" in v:
        return "juniper"

    if "arista" in v:
        return "arista"

    return "unknown"


def vendor_logo_src(vendor: str) -> str | None:
    """Retorna o `src` do asset (ex.: `/assets/vendors/cisco.png`) ou None."""
    key = normalize_vendor_key(vendor)
    for ext in ("png", "svg", "jpg", "jpeg", "webp"):
        candidate = _ASSETS_VENDOR_DIR / f"{key}.{ext}"
        if candidate.exists():
            return f"/assets/vendors/{candidate.name}"
    return None



def vendor_logo_kwargs(vendor: str) -> dict:
    """
    Retorna kwargs para `ft.Image(**kwargs)`.

    Prioridade (conforme pedido: usar `img/`):
    1) pasta do repo: `img/<key>.<ext>` ou `img/vendors/<key>.<ext>` -> usa `src_base64=...`
    2) assets do Flet: `src/assets/vendors/<key>.<ext>` -> usa `src=/assets/...`

    Retorna `{}` se não houver logo.
    """
    key = normalize_vendor_key(vendor)
    repo_root = Path(__file__).resolve().parent.parent

    # busca base64 — inclui src/assets/vendors/ (onde o Flet serve os assets)
    candidates = []
    for ext in ("png", "jpg", "jpeg", "webp"):
        candidates.append(_ASSETS_VENDOR_DIR / f"{key}.{ext}")
        candidates.append(_ASSETS_VENDOR_DIR.parent / f"{key}.{ext}")
        candidates.append(repo_root / "assets" / f"{key}.{ext}")
        candidates.append(repo_root / "assets" / "vendors" / f"{key}.{ext}")

    for candidate in candidates:
        if candidate.exists():
            return {"src": candidate.read_bytes()}

    # fallback: procura por nomes "quase iguais" (ex.: "Cisco .png")
    def _norm(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (s or "").lower())

    for folder in (_ASSETS_VENDOR_DIR, _ASSETS_VENDOR_DIR.parent,
                   repo_root / "assets", repo_root / "assets" / "vendors"):
        if not folder.exists():
            continue
        for path in folder.iterdir():
            if not path.is_file():
                continue
            if path.suffix.lower().lstrip(".") not in ("png", "jpg", "jpeg", "webp"):
                continue
            if _norm(path.stem) == _norm(key):
                return {"src": path.read_bytes()}

    # fallback: URL SVG pública por fabricante
    url = _VENDOR_LOGO_URLS.get(key)
    if url:
        return {"src": url}

    return {}
