"""src.connector

Conecta a switches via SSH com auto-detecção de vendor/device_type.

Foco em performance:
- Faz um probe TCP curto antes do SSH (fail-fast)
- Tenta comandos de versão/interfaces "curtos" por vendor
- Evita `show interfaces` completo por padrão (pode demorar muito)
- Opcionalmente aceita `vendor_hint` para tentar conectar sem autodetect
"""
from __future__ import annotations

import re
import socket
import time
from typing import Any


def connect_switch(
    host: str,
    username: str,
    password: str,
    port: int = 22,
    vendor_hint: str | None = None,
    device_type_override: str | None = None,
) -> tuple[bool, dict | str]:
    """
    Retorna (True, info_dict) ou (False, mensagem_de_erro).

    `vendor_hint` (opcional) ajuda a evitar o autodetect, tentando um ou mais
    `device_type` conhecidos antes de cair no SSHDetect.
    """
    started = time.perf_counter()
    timings: dict[str, float] = {}

    try:
        from netmiko import SSHDetect, ConnectHandler
        from netmiko.exceptions import (
            NetmikoAuthenticationException,
            NetmikoTimeoutException,
        )
    except ImportError:
        return False, "netmiko não instalado. Execute: pip install netmiko"

    t0 = time.perf_counter()
    ok, msg = _tcp_probe(host, port, timeout=2.5)
    timings["tcp"] = time.perf_counter() - t0
    if not ok:
        return False, f"{host}: {msg}"

    base_params: dict[str, Any] = dict(
        host=host,
        username=username,
        password=password,
        port=port,
        fast_cli=True,
        timeout=8,
        conn_timeout=6,
        banner_timeout=6,
        auth_timeout=6,
    )

    best_match = ""
    conn = None

    hint = (vendor_hint or "").strip().lower()
    override = (device_type_override or "").strip()

    # ── fast-path: device_type já conhecido ─────────────────────
    if override:
        timings["detect"] = 0.0
        t0 = time.perf_counter()
        try:
            conn = ConnectHandler(**base_params, device_type=override)
            best_match = override
        except NetmikoAuthenticationException:
            return False, f"{host}: falha de autenticação."
        except NetmikoTimeoutException:
            return False, f"{host}: timeout ao conectar."
        except Exception as exc:
            return False, f"{host}: {exc}"
        finally:
            timings["connect"] = time.perf_counter() - t0

    # ── fast-path: tenta pelo vendor_hint ────────────────────────
    if conn is None:
        hint_candidates = _device_type_candidates_for_hint(hint)
        if hint_candidates:
            timings["detect"] = 0.0
            for dt in hint_candidates:
                t0 = time.perf_counter()
                try:
                    conn = ConnectHandler(**base_params, device_type=dt)
                    timings["connect"] = time.perf_counter() - t0
                    best_match = dt
                    break
                except (NetmikoAuthenticationException, NetmikoTimeoutException):
                    timings["connect"] = time.perf_counter() - t0
                    conn = None
                except Exception:
                    timings["connect"] = time.perf_counter() - t0
                    conn = None

    # ── autodetect fallback ──────────────────────────────────────────
    if conn is None:
        t0 = time.perf_counter()
        try:
            guesser = SSHDetect(**base_params, device_type="autodetect")
            best_match = guesser.autodetect() or "cisco_ios"
        except NetmikoAuthenticationException:
            return False, f"{host}: falha de autenticação."
        except NetmikoTimeoutException:
            return False, f"{host}: timeout ao conectar."
        except Exception as exc:
            return False, f"{host}: {exc}"
        finally:
            timings["detect"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        try:
            conn = ConnectHandler(**base_params, device_type=best_match)
        except NetmikoAuthenticationException:
            return False, f"{host}: falha de autenticação."
        except NetmikoTimeoutException:
            return False, f"{host}: timeout ao conectar."
        except Exception as exc:
            return False, f"{host}: {exc}"
        finally:
            timings["connect"] = time.perf_counter() - t0

    ver_out = ""
    iface_out = ""
    cpu_usage = None
    mem_usage = None
    try:
        # versão: tenta comandos comuns por fabricante (Huawei usa `display ...`)
        t0 = time.perf_counter()
        for cmd in _pick_version_commands(best_match, hint):
            out = _send_command(conn, cmd, use_textfsm=False, read_timeout=20)
            if out and not _looks_invalid_command(out):
                ver_out = out
                break
        timings["version"] = time.perf_counter() - t0

        vendor = _extract_vendor(ver_out, best_match)

        # interfaces: preferir comandos curtos; se falhar, não roda o comando
        # completo por padrão (muito pesado e faz parecer "travado").
        t0 = time.perf_counter()
        for cmd in _pick_interfaces_command(vendor, best_match, hint):
            out = _send_command(conn, cmd, use_textfsm=False, read_timeout=25)
            if out and not _looks_invalid_command(out):
                iface_out = out
                break
        timings["interfaces"] = time.perf_counter() - t0

        t0 = time.perf_counter()
        cpu_usage, mem_usage = _collect_resources(conn, vendor, best_match, hint)
        timings["resources"] = time.perf_counter() - t0

    except Exception as exc:
        try:
            conn.disconnect()
        except Exception:
            pass
        return False, f"{host}: erro ao executar comando — {exc}"
    finally:
        try:
            conn.disconnect()
        except Exception:
            pass

    info = _parse_info(host, best_match, ver_out, iface_out)
    if cpu_usage is not None:
        info["cpu_usage"] = cpu_usage
    if mem_usage is not None:
        info["mem_usage"] = mem_usage
    info["connect_time_s"] = round(time.perf_counter() - started, 3)
    info["connect_timings_s"] = {k: round(v, 3) for k, v in timings.items()}
    if hint:
        info["vendor_hint"] = hint
    return True, info

    


def connect_switch_fast(
    host: str,
    username: str,
    password: str,
    port: int = 22,
    vendor_hint: str | None = None,
) -> tuple[bool, dict | str]:
    """Conecta o mais rápido possível (handshake SSH) e retorna um card básico.

    Não executa comandos de coleta e tenta evitar autodetect.
    """
    started = time.perf_counter()
    timings: dict[str, float] = {}

    try:
        from netmiko import ConnectHandler
        from netmiko.exceptions import (
            NetmikoAuthenticationException,
            NetmikoTimeoutException,
        )
    except ImportError:
        return False, "netmiko não instalado. Execute: pip install netmiko"

    t0 = time.perf_counter()
    ok, msg = _tcp_probe(host, port, timeout=2.5)
    timings["tcp"] = time.perf_counter() - t0
    if not ok:
        return False, f"{host}: {msg}"

    hint = (vendor_hint or "").strip().lower()
    candidates = _device_type_candidates_for_hint(hint)
    if not candidates:
        # lista curta para tentar sem autodetect
        candidates = [
            "cisco_ios",
            "huawei",
            "hp_procurve",
            "hp_comware",
            "aruba_os",
            "dell_os10",
            "dell_force10",
        ]

    base_params: dict[str, Any] = dict(
        host=host,
        username=username,
        password=password,
        port=port,
        fast_cli=True,
        timeout=6,
        conn_timeout=5,
        banner_timeout=5,
        auth_timeout=5,
    )

    last_exc: Exception | None = None
    for dt in candidates:
        t0 = time.perf_counter()
        try:
            conn = ConnectHandler(**base_params, device_type=dt)
            timings["connect"] = time.perf_counter() - t0
            ver_out = ""
            try:
                t1 = time.perf_counter()
                # tenta identificar o vendor sem "puxar" interfaces (rápido)
                for cmd in _pick_version_commands(dt, hint)[:2]:
                    out = _send_command(conn, cmd, use_textfsm=False, read_timeout=8)
                    if out and not _looks_invalid_command(out):
                        ver_out = out
                        break
                timings["version"] = time.perf_counter() - t1
            except Exception:
                # se travar/der erro, mantém "Detectando…" e segue
                pass
            finally:
                try:
                    conn.disconnect()
                except Exception:
                    pass

            info = {
                "id": host,
                "host": host,
                "vendor": _extract_vendor(ver_out, dt) if ver_out else "Detectando…",
                "model": _extract_model(ver_out) if ver_out else "—",
                "ios_version": _extract_version(ver_out) if ver_out else "—",
                "device_type": dt,
                "status": "connected",
                "ports_up": 0,
                "ports_down": 0,
                "connect_time_s": round(time.perf_counter() - started, 3),
                "connect_timings_s": {k: round(v, 3) for k, v in timings.items()},
            }
            if hint:
                info["vendor_hint"] = hint
            return True, info
        except (NetmikoAuthenticationException, NetmikoTimeoutException) as exc:
            timings["connect"] = time.perf_counter() - t0
            last_exc = exc
            continue
        except Exception as exc:
            timings["connect"] = time.perf_counter() - t0
            last_exc = exc
            continue

    if last_exc is not None:
        return False, f"{host}: {last_exc}"
    return False, f"{host}: não foi possível conectar."



def identify_switch(
    host: str,
    username: str,
    password: str,
    port: int = 22,
    vendor_hint: str | None = None,
    device_type_override: str | None = None,
) -> tuple[bool, dict | str]:
    """Identifica rapidamente vendor/model/versão (sem interfaces/CPU/MEM).

    Usado para atualizar o card cedo (ícone/logo) e deixar o restante para depois.
    """
    started = time.perf_counter()
    timings: dict[str, float] = {}

    try:
        from netmiko import SSHDetect, ConnectHandler
        from netmiko.exceptions import (
            NetmikoAuthenticationException,
            NetmikoTimeoutException,
        )
    except ImportError:
        return False, "netmiko não instalado. Execute: pip install netmiko"

    t0 = time.perf_counter()
    ok, msg = _tcp_probe(host, port, timeout=2.5)
    timings["tcp"] = time.perf_counter() - t0
    if not ok:
        return False, f"{host}: {msg}"

    base_params: dict[str, Any] = dict(
        host=host,
        username=username,
        password=password,
        port=port,
        fast_cli=True,
        timeout=6,
        conn_timeout=5,
        banner_timeout=5,
        auth_timeout=5,
    )

    hint = (vendor_hint or "").strip().lower()
    override = (device_type_override or "").strip()

    best_match = ""
    conn = None

    try:
        # 1) override
        if override:
            timings["detect"] = 0.0
            t0 = time.perf_counter()
            conn = ConnectHandler(**base_params, device_type=override)
            timings["connect"] = time.perf_counter() - t0
            best_match = override

        # 2) hint candidates
        if conn is None:
            hint_candidates = _device_type_candidates_for_hint(hint)
            if hint_candidates:
                timings["detect"] = 0.0
                for dt in hint_candidates:
                    t0 = time.perf_counter()
                    try:
                        conn = ConnectHandler(**base_params, device_type=dt)
                        timings["connect"] = time.perf_counter() - t0
                        best_match = dt
                        break
                    except (NetmikoAuthenticationException, NetmikoTimeoutException):
                        timings["connect"] = time.perf_counter() - t0
                        conn = None

        # 3) autodetect (último recurso)
        if conn is None:
            t0 = time.perf_counter()
            guesser = SSHDetect(**base_params, device_type="autodetect")
            best_match = guesser.autodetect() or "cisco_ios"
            timings["detect"] = time.perf_counter() - t0

            t0 = time.perf_counter()
            conn = ConnectHandler(**base_params, device_type=best_match)
            timings["connect"] = time.perf_counter() - t0

        # versão apenas
        t0 = time.perf_counter()
        ver_out = ""
        for cmd in _pick_version_commands(best_match, hint):
            out = _send_command(conn, cmd, use_textfsm=False, read_timeout=12)
            if out and not _looks_invalid_command(out):
                ver_out = out
                break
        timings["version"] = time.perf_counter() - t0

        vendor = _extract_vendor(ver_out, best_match)
        model = _extract_model(ver_out)
        version = _extract_version(ver_out)

        info = {
            "id": host,
            "host": host,
            "vendor": vendor,
            "model": model,
            "ios_version": version,
            "device_type": best_match,
            "status": "connected",
            # manter compatibilidade com a UI (evita KeyError ao renderizar)
            "ports_up": 0,
            "ports_down": 0,
            "connect_time_s": round(time.perf_counter() - started, 3),
            "connect_timings_s": {k: round(v, 3) for k, v in timings.items()},
        }
        if hint:
            info["vendor_hint"] = hint

        return True, info

    except NetmikoAuthenticationException:
        return False, f"{host}: falha de autenticação."
    except NetmikoTimeoutException:
        return False, f"{host}: timeout ao conectar."
    except Exception as exc:
        return False, f"{host}: {exc}"
    finally:
        try:
            if conn is not None:
                conn.disconnect()
        except Exception:
            pass


# ── parsers ──────────────────────────────────────────────────────────


def _parse_info(host: str, device_type: str, ver: str, ifaces: str) -> dict:
    vendor = _extract_vendor(ver, device_type)
    model = _extract_model(ver)
    version = _extract_version(ver)
    up, dn = _count_ports(ifaces)

    return {
        "id": host,
        "host": host,
        "vendor": vendor,
        "model": model,
        "ios_version": version,
        "device_type": device_type,
        "status": "connected",
        "ports_up": up,
        "ports_down": dn,
    }


def _extract_vendor(ver: str, device_type: str) -> str:
    if re.search(r"Cisco", ver, re.I) or "cisco" in device_type:
        return "Cisco Systems"

    if re.search(r"Huawei|VRP", ver, re.I) or "huawei" in device_type:
        return "Huawei"

    if re.search(r"Dell|Force10|OS10|DNOS|PowerSwitch", ver, re.I) or "dell" in device_type:
        return "Dell"

    if re.search(r"Aruba", ver, re.I) or "aruba" in device_type:
        return "Aruba"

    if re.search(r"\bHP\b|HPE|Hewlett|ProCurve|Comware", ver, re.I):
        return "HP"

    if re.search(r"Juniper", ver, re.I) or "juniper" in device_type:
        return "Juniper Networks"

    if re.search(r"Arista", ver, re.I) or "arista" in device_type:
        return "Arista Networks"

    return "Desconhecido"


def _extract_model(ver: str) -> str:
    m = re.search(r"cisco\s+([\w\-]+(?:\s+[\w\-]+){0,5})", ver, re.I)
    if m:
        return m.group(1).strip()

    m = re.search(r"[Mm]odel\s*(?:[Nn]umber)?\s*:\s*(\S+)", ver)
    if m:
        return m.group(1)

    m = re.search(r"Model:\s*(\S+)", ver)
    if m:
        return m.group(1)

    m = re.search(r"\bS\d{4}\S*\b", ver)
    if m:
        return m.group(0)

    return "Desconhecido"


def _extract_version(ver: str) -> str:
    m = re.search(r"[Vv]ersion\s+([\d\.A-Za-z()\-]+)", ver)
    if m:
        return m.group(1).rstrip(",")

    m = re.search(r"Junos:\s*([\d\.A-Za-z]+)", ver)
    if m:
        return m.group(1)

    m = re.search(r"VRP\s*\(.*?\)\s*software,\s*Version\s*([\w\.\-]+)", ver, re.I)
    if m:
        return m.group(1)

    return "Desconhecido"


def _count_ports(ifaces: str) -> tuple[int, int]:
    up, dn = _count_ports_from_interfaces_status(ifaces)
    if up or dn:
        return up, dn

    up, dn = _count_ports_from_ip_int_brief(ifaces)
    if up or dn:
        return up, dn

    up, dn = _count_ports_from_junos_terse(ifaces)
    if up or dn:
        return up, dn

    up, dn = _count_ports_from_huawei_int_brief(ifaces)
    if up or dn:
        return up, dn

    up = len(re.findall(r"line protocol is up", ifaces, re.I))
    down = len(re.findall(r"line protocol is down", ifaces, re.I))
    return up, down


# ── helpers ──────────────────────────────────────────────────────────


def _tcp_probe(host: str, port: int, timeout: float) -> tuple[bool, str]:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True, ""
    except socket.timeout:
        return False, "timeout de rede (porta SSH não respondeu)."
    except OSError as exc:
        return False, f"não foi possível abrir TCP {host}:{port} — {exc}"


def _send_command(conn, command: str, **kwargs) -> str:
    """Compatibilidade entre versões do Netmiko: alguns kwargs mudam."""
    try:
        return conn.send_command(command, **kwargs)
    except TypeError:
        safe_kwargs = dict(kwargs)
        safe_kwargs.pop("read_timeout", None)
        return conn.send_command(command, **safe_kwargs)


def _looks_invalid_command(output: str) -> bool:
    return bool(
        re.search(
            r"(%\s*Invalid input|Unknown command|Invalid command|syntax error|Unrecognized command|Incomplete command|Unknown keyword|^Error:)",
            output,
            re.I | re.M,
        )
    )


def _device_type_candidates_for_hint(hint: str) -> list[str]:
    # Lista enxuta de tipos comuns do Netmiko. Se errar, cai no autodetect.
    if hint in ("auto", "", "unknown"):
        return []
    if hint in ("cisco", "cisco systems"):
        return ["cisco_ios", "cisco_xe"]
    if hint in ("huawei",):
        return ["huawei"]
    if hint in ("hp", "hpe"):
        return ["hp_procurve", "hp_comware"]
    if hint in ("aruba",):
        return ["aruba_os", "hp_procurve"]
    if hint in ("dell",):
        return ["dell_os10", "dell_force10"]
    return []


def _pick_version_commands(device_type: str, hint: str) -> list[str]:
    dt = (device_type or "").lower()
    if "huawei" in dt or hint == "huawei":
        return ["display version", "show version"]
    if "juniper" in dt:
        return ["show version"]
    if "aruba" in dt or hint == "aruba":
        return ["show version", "show system"]
    if "hp" in dt or hint in ("hp", "hpe"):
        return ["show system information", "show version", "display version"]
    if "dell" in dt or "force10" in dt or "os10" in dt or hint == "dell":
        return ["show version", "show system"]
    return ["show version", "display version", "show system", "show system information"]


def _pick_interfaces_command(vendor: str, device_type: str, hint: str) -> list[str]:
    v = (vendor or "").lower()
    dt = (device_type or "").lower()

    if "huawei" in v or "huawei" in dt or hint == "huawei":
        return ["display interface brief", "display interface brief description"]

    if "juniper" in v or "juniper" in dt:
        return ["show interfaces terse", "show interfaces"]

    if "cisco" in v or "arista" in v or "cisco" in dt or "arista" in dt or hint == "cisco":
        return ["show interfaces status", "show ip interface brief"]

    if "dell" in v or "force10" in dt or "os10" in dt or hint == "dell":
        return ["show interfaces status", "show interface status", "show ip interface brief"]

    if "aruba" in v or "hp" in v or "aruba" in dt or "hp" in dt or hint in ("aruba", "hp", "hpe"):
        return ["show interfaces brief", "show interface brief", "show interfaces status"]

    return ["show interfaces status", "show ip interface brief", "display interface brief", "show interfaces brief"]


# ── port counters ────────────────────────────────────────────────────


def _count_ports_from_interfaces_status(output: str) -> tuple[int, int]:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return 0, 0

    header_idx = None
    for i, ln in enumerate(lines[:12]):
        if re.search(r"\bStatus\b", ln) and re.search(r"\bVlan\b", ln, re.I):
            header_idx = i
            break

    if header_idx is None:
        return 0, 0

    up = down = 0
    for ln in lines[header_idx + 1 :]:
        parts = re.split(r"\s+", ln)
        if len(parts) < 3:
            continue
        status = parts[2].lower()
        if status == "connected":
            up += 1
        else:
            down += 1
    return up, down


def _count_ports_from_ip_int_brief(output: str) -> tuple[int, int]:
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return 0, 0

    if not re.search(r"\bInterface\b", lines[0]) or not re.search(r"\bProtocol\b", lines[0]):
        return 0, 0

    up = down = 0
    for ln in lines[1:]:
        parts = re.split(r"\s+", ln.strip())
        if len(parts) < 6:
            continue
        status = parts[-2].lower()
        proto = parts[-1].lower()
        if status == "up" and proto == "up":
            up += 1
        else:
            down += 1
    return up, down


def _count_ports_from_junos_terse(output: str) -> tuple[int, int]:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return 0, 0

    if not any(re.search(r"\bAdmin\b", ln) and re.search(r"\bLink\b", ln) for ln in lines[:3]):
        return 0, 0

    up = down = 0
    for ln in lines:
        if ln.lower().startswith("interface "):
            continue
        parts = re.split(r"\s+", ln)
        if len(parts) < 3:
            continue
        iface = parts[0]
        admin = parts[1].lower()
        link = parts[2].lower()
        if not re.match(r"^(ge|xe|et|ae|em|fxp)-", iface):
            continue
        if admin == "up" and link == "up":
            up += 1
        else:
            down += 1
    return up, down


def _count_ports_from_huawei_int_brief(output: str) -> tuple[int, int]:
    lines = [ln.strip() for ln in output.splitlines() if ln.strip()]
    if not lines:
        return 0, 0

    header_ok = any(
        re.search(r"\bInterface\b", ln, re.I)
        and re.search(r"\bPHY\b", ln)
        and re.search(r"\bProtocol\b", ln)
        for ln in lines[:6]
    )
    if not header_ok:
        return 0, 0

    up = down = 0
    for ln in lines:
        if re.search(r"\bInterface\b", ln, re.I) and re.search(r"\bPHY\b", ln) and re.search(r"\bProtocol\b", ln):
            continue
        parts = re.split(r"\s+", ln)
        if len(parts) < 3:
            continue
        iface = parts[0]
        phy = parts[1].lower()
        proto = parts[2].lower()
        if not re.match(
            r"^(ge|xge|eth|gigabitethernet|ten-gigabitethernet|trunk|vlanif|xgigabitethernet)",
            iface,
            re.I,
        ):
            continue
        if phy == "up" and proto == "up":
            up += 1
        else:
            down += 1
    return up, down



def _collect_resources(conn, vendor: str, device_type: str, hint: str):
    """Best-effort de CPU/Memória (percentual)."""
    v = (vendor or "").lower()
    dt = (device_type or "").lower()

    cpu = None
    mem = None

    # Cisco/Arista-like
    if "cisco" in v or "cisco" in dt or "arista" in v or hint == "cisco":
        cpu = _parse_cisco_cpu(_send_command(conn, "show processes cpu | include CPU utilization", use_textfsm=False, read_timeout=12))
        mem = _parse_cisco_mem(_send_command(conn, "show processes memory | include Processor Pool", use_textfsm=False, read_timeout=12))
        return cpu, mem

    # Huawei VRP
    if "huawei" in v or "huawei" in dt or hint == "huawei":
        cpu = _parse_percent_generic(_send_command(conn, "display cpu-usage", use_textfsm=False, read_timeout=12))
        mem = _parse_percent_generic(_send_command(conn, "display memory-usage", use_textfsm=False, read_timeout=12))
        return cpu, mem

    # Dell/HP/Aruba best-effort generic
    for cmd in (
        "show system", "show system resources", "show processes cpu", "show processes memory",
        "show cpu", "show memory", "display cpu-usage", "display memory-usage",
    ):
        try:
            out = _send_command(conn, cmd, use_textfsm=False, read_timeout=10)
        except Exception:
            continue
        if not out or _looks_invalid_command(out):
            continue
        if cpu is None:
            cpu = _parse_percent_generic(out)
        if mem is None:
            mem = _parse_percent_generic(out, memory=True)
        if cpu is not None and mem is not None:
            break

    return cpu, mem


def _parse_cisco_cpu(output: str):
    # CPU utilization for five seconds: 3%/0%; one minute: 4%; five minutes: 5%
    m = re.search(r"one minute:\s*(\d+)%", output, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"five seconds:\s*(\d+)%", output, re.I)
    if m:
        return int(m.group(1))
    return None


def _parse_cisco_mem(output: str):
    # Processor Pool Total:  123456 Used:  23456 Free:  100000
    m = re.search(r"Total:\s*(\d+)\s+Used:\s*(\d+)", output, re.I)
    if m:
        total = int(m.group(1))
        used = int(m.group(2))
        if total > 0:
            return int(round((used / total) * 100))
    return None


def _parse_percent_generic(output: str, memory: bool = False):
    # Tenta pegar algo como "CPU utilization" / "Memory utilization" / "Utilization" / "Usage".
    if memory:
        pats = [r"memory\s+utilization\s*[:=]\s*(\d+)%", r"mem\w*\s+utilization\s*[:=]\s*(\d+)%"]
    else:
        pats = [r"cpu\s+utilization\s*[:=]\s*(\d+)%", r"cpu\s+usage\s*[:=]\s*(\d+)%"]

    for p in pats:
        m = re.search(p, output, re.I)
        if m:
            return int(m.group(1))

    # fallback: primeiro percentual do texto
    m = re.search(r"\b(\d{1,3})%\b", output)
    if m:
        val = int(m.group(1))
        if 0 <= val <= 100:
            return val

    return None
