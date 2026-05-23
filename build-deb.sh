#!/usr/bin/env bash
# build-deb.sh — Build a .deb package for WireGuard GUI
set -euo pipefail

PKG="wireguard-gui"
VERSION="1.0.0"
ARCH="all"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${SCRIPT_DIR}/${PKG}_${VERSION}_${ARCH}.deb"
BUILD="$(mktemp -d)"
trap 'rm -rf "$BUILD"' EXIT

# Check for dpkg-deb
if ! command -v dpkg-deb &>/dev/null; then
    echo "Error: dpkg-deb not found. Install it with: sudo apt install dpkg"
    exit 1
fi

echo "Building ${PKG}_${VERSION}_${ARCH}.deb ..."

# ── Directory layout ──────────────────────────────────────────────────────────
install -d "$BUILD/DEBIAN"
install -d "$BUILD/opt/wireguard-gui"
install -d "$BUILD/usr/local/bin"
install -d "$BUILD/usr/share/applications"
install -d "$BUILD/usr/share/doc/wireguard-gui"

# ── App files ─────────────────────────────────────────────────────────────────
install -m 644 "$SCRIPT_DIR"/*.py "$BUILD/opt/wireguard-gui/"

# ── setup-sudoers.sh (optional helper bundled with the package) ───────────────
cat > "$BUILD/opt/wireguard-gui/setup-sudoers.sh" <<'SUDOERS_SCRIPT'
#!/usr/bin/env bash
set -euo pipefail
SUDOERS=/etc/sudoers.d/wireguard-gui
if [[ "$EUID" -ne 0 ]]; then
    echo "Please run as root: sudo bash $0"
    exit 1
fi
TARGET="${SUDO_USER:-}"
read -r -p "Configure passwordless sudo for which user? [${TARGET}] " INPUT
TARGET="${INPUT:-$TARGET}"
if [[ -z "$TARGET" || "$TARGET" == "root" ]]; then
    echo "No user configured."
    exit 0
fi
cat > "$SUDOERS" <<EOF
# WireGuard GUI — allow managing tunnels without password prompt
$TARGET ALL=(root) NOPASSWD: /usr/bin/wg-quick *, /usr/bin/wg show *, /usr/bin/wg show, /bin/ls /etc/wireguard/, /bin/cat /etc/wireguard/*.conf, /bin/cp * /etc/wireguard/*.conf, /bin/chmod 600 /etc/wireguard/*.conf, /bin/rm /etc/wireguard/*.conf
EOF
chmod 440 "$SUDOERS"
echo "Done. Passwordless sudo configured for $TARGET."
SUDOERS_SCRIPT
chmod 755 "$BUILD/opt/wireguard-gui/setup-sudoers.sh"

# ── Launcher ──────────────────────────────────────────────────────────────────
cat > "$BUILD/usr/local/bin/wireguard-gui" <<'EOF'
#!/usr/bin/env bash
exec python3 /opt/wireguard-gui/main.py "$@"
EOF
chmod 755 "$BUILD/usr/local/bin/wireguard-gui"

# ── Desktop entry ─────────────────────────────────────────────────────────────
cat > "$BUILD/usr/share/applications/wireguard-gui.desktop" <<'EOF'
[Desktop Entry]
Name=WireGuard
GenericName=VPN Manager
Comment=Manage WireGuard VPN tunnels
Exec=wireguard-gui
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
Keywords=vpn;wireguard;tunnel;network;
StartupNotify=true
EOF

# ── Copyright ─────────────────────────────────────────────────────────────────
install -m 644 "$SCRIPT_DIR/LICENSE" "$BUILD/usr/share/doc/wireguard-gui/copyright"

# ── DEBIAN/control ────────────────────────────────────────────────────────────
cat > "$BUILD/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Architecture: $ARCH
Maintainer: Sévag Derboghossian <derboghossiansevag@gmail.com>
Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, wireguard-tools, pkexec
Recommends: gir1.2-ayatanaappindicator3-0.1 | gir1.2-appindicator3-0.1
Homepage: https://github.com/Derbosoft/wireguard-gui
Description: GTK graphical interface for WireGuard VPN tunnels
 Manage your WireGuard VPN tunnels with a clean, minimal GTK interface.
 Toggle tunnels on/off, create, edit and import configurations,
 view real-time traffic statistics, see your public IP when connected,
 and get a system tray icon — all without touching the terminal.
EOF

# ── DEBIAN/postinst ───────────────────────────────────────────────────────────
cat > "$BUILD/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e
update-desktop-database /usr/share/applications 2>/dev/null || true
echo ""
echo "WireGuard GUI installed successfully!"
echo "  Launch from terminal : wireguard-gui"
echo "  Launch from menu     : search for 'WireGuard'"
echo ""
echo "Optional — skip password prompt on every VPN toggle:"
echo "  sudo bash /opt/wireguard-gui/setup-sudoers.sh"
EOF
chmod 755 "$BUILD/DEBIAN/postinst"

# ── DEBIAN/postrm ─────────────────────────────────────────────────────────────
cat > "$BUILD/DEBIAN/postrm" <<'EOF'
#!/bin/bash
set -e
if [ "$1" = "purge" ]; then
    rm -f /etc/sudoers.d/wireguard-gui
    rm -rf /opt/wireguard-gui
fi
update-desktop-database /usr/share/applications 2>/dev/null || true
EOF
chmod 755 "$BUILD/DEBIAN/postrm"

# ── Build ─────────────────────────────────────────────────────────────────────
dpkg-deb --build --root-owner-group "$BUILD" "$OUT"

echo ""
echo "Package ready: $(basename "$OUT")"
echo ""
echo "  Install : sudo dpkg -i $OUT"
echo "            sudo apt-get install -f   # fix any missing dependencies"
echo "  Remove  : sudo apt remove wireguard-gui"
