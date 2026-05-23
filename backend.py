import subprocess
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

CONFIG_DIR  = Path.home() / ".config" / "wireguard-gui"
VPN_HELPER  = "/opt/wireguard-gui/vpn-helper"


@dataclass
class NetStats:
    rx_bytes: int = 0
    tx_bytes: int = 0


@dataclass
class WgInfo:
    endpoint: str = ""
    allowed_ips: str = ""
    latest_handshake: int = 0
    rx_bytes: int = 0
    tx_bytes: int = 0


def _run(args: list, input_data: str = None, privileged: bool = False) -> subprocess.CompletedProcess:
    cmd = (["sudo", "-n"] + args) if privileged else args
    return subprocess.run(cmd, capture_output=True, text=True, input=input_data, timeout=30)


def _config_dir() -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_DIR


def format_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


def format_elapsed(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}min {seconds % 60}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}min"


# ── Tunnel discovery (no root needed) ────────────────────────────────────────

def get_tunnel_names() -> list[str]:
    return sorted(f.stem for f in _config_dir().glob("*.conf"))


# ── Status & stats (no root needed) ──────────────────────────────────────────

def get_public_ip() -> str:
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except Exception:
        return ""


def is_active(name: str) -> bool:
    r = subprocess.run(["ip", "link", "show", "dev", name], capture_output=True)
    return r.returncode == 0


def get_net_stats(name: str) -> Optional[NetStats]:
    try:
        with open("/proc/net/dev") as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith(name + ":"):
                    parts = stripped.split()
                    return NetStats(rx_bytes=int(parts[1]), tx_bytes=int(parts[9]))
    except Exception:
        pass
    return None


# ── WireGuard detail info (needs root) ───────────────────────────────────────

def get_wg_info(name: str) -> Optional[WgInfo]:
    r = _run([VPN_HELPER, "wg-show", name], privileged=True)
    if r.returncode != 0:
        return None
    lines = [l for l in r.stdout.strip().splitlines() if l]
    if len(lines) < 2:
        return None
    peer = lines[1].split("\t")
    if len(peer) < 7:
        return None
    return WgInfo(
        endpoint=peer[2] if peer[2] != "(none)" else "",
        allowed_ips=peer[3] if peer[3] != "(none)" else "",
        latest_handshake=int(peer[4]),
        rx_bytes=int(peer[5]),
        tx_bytes=int(peer[6]),
    )


# ── Tunnel lifecycle (needs root) ─────────────────────────────────────────────

def toggle_tunnel(name: str, enable: bool) -> tuple[bool, str]:
    if enable:
        conf_path = str(_config_dir() / f"{name}.conf")
        r = _run([VPN_HELPER, "up", conf_path], privileged=True)
    else:
        r = _run([VPN_HELPER, "down", name], privileged=True)
    if r.returncode == 0:
        return True, ""
    return False, (r.stderr or r.stdout).strip()


# ── Config file management (no root needed — stored in ~/.config/wireguard-gui/) ──

def read_config(name: str) -> str:
    try:
        return (_config_dir() / f"{name}.conf").read_text()
    except Exception:
        return ""


def save_config(name: str, content: str) -> tuple[bool, str]:
    try:
        path = _config_dir() / f"{name}.conf"
        path.write_text(content)
        path.chmod(0o600)
        return True, ""
    except Exception as e:
        return False, str(e)


def delete_config(name: str) -> tuple[bool, str]:
    try:
        (_config_dir() / f"{name}.conf").unlink()
        return True, ""
    except Exception as e:
        return False, str(e)


def import_config(src_path: str) -> tuple[bool, str, str]:
    src = Path(src_path)
    if not src.exists():
        return False, "Fichier introuvable.", ""
    if src.suffix.lower() != ".conf":
        return False, "Le fichier doit avoir l'extension .conf", ""
    name = src.stem
    try:
        content = src.read_text()
    except Exception as e:
        return False, str(e), ""
    ok, err = save_config(name, content)
    return ok, err, name if ok else ""
