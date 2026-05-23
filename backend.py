import subprocess
import os
import urllib.request
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

WIREGUARD_DIR = Path("/etc/wireguard")
WG_QUICK = "/usr/bin/wg-quick"
WG      = "/usr/bin/wg"


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
    """Run a command, optionally via sudo -n (never pkexec — no password prompt ever)."""
    cmd = (["sudo", "-n"] + args) if privileged else args
    return subprocess.run(cmd, capture_output=True, text=True, input=input_data, timeout=30)


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


# ── Tunnel discovery ──────────────────────────────────────────────────────────

def get_tunnel_names() -> list[str]:
    try:
        if os.access(WIREGUARD_DIR, os.R_OK):
            return sorted(f.stem for f in WIREGUARD_DIR.glob("*.conf"))
    except Exception:
        pass
    r = _run(["/usr/bin/ls", str(WIREGUARD_DIR)], privileged=True)
    if r.returncode == 0:
        return sorted(f[:-5] for f in r.stdout.split() if f.endswith(".conf"))
    return []


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


# ── WireGuard detail info ─────────────────────────────────────────────────────

def get_wg_info(name: str) -> Optional[WgInfo]:
    r = _run([WG, "show", name, "dump"], privileged=True)
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


# ── Tunnel lifecycle ──────────────────────────────────────────────────────────

def toggle_tunnel(name: str, enable: bool) -> tuple[bool, str]:
    action = "up" if enable else "down"
    r = _run([WG_QUICK, action, name], privileged=True)
    if r.returncode == 0:
        return True, ""
    return False, (r.stderr or r.stdout).strip()


# ── Config file management ────────────────────────────────────────────────────

def read_config(name: str) -> str:
    path = WIREGUARD_DIR / f"{name}.conf"
    try:
        return path.read_text()
    except PermissionError:
        r = _run(["/usr/bin/cat", str(path)], privileged=True)
        return r.stdout if r.returncode == 0 else ""


def save_config(name: str, content: str) -> tuple[bool, str]:
    dest = str(WIREGUARD_DIR / f"{name}.conf")
    # tee reads from stdin and writes to the file as root — single call, no temp file
    r = _run(["/usr/bin/tee", dest], input_data=content, privileged=True)
    if r.returncode != 0:
        return False, "Impossible d'écrire dans /etc/wireguard/. Réinstallez l'application."
    _run(["/usr/bin/chmod", "600", dest], privileged=True)
    return True, ""


def delete_config(name: str) -> tuple[bool, str]:
    path = str(WIREGUARD_DIR / f"{name}.conf")
    r = _run(["/usr/bin/rm", path], privileged=True)
    if r.returncode == 0:
        return True, ""
    return False, (r.stderr or r.stdout).strip()


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
