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
install -d "$BUILD/usr/share/icons/hicolor/scalable/apps"

# ── App files ─────────────────────────────────────────────────────────────────
install -m 644 "$SCRIPT_DIR"/*.py        "$BUILD/opt/wireguard-gui/"
install -m 644 "$SCRIPT_DIR/wireguard.svg" "$BUILD/opt/wireguard-gui/wireguard.svg"

# ── Icon ──────────────────────────────────────────────────────────────────────
install -m 644 "$SCRIPT_DIR/wireguard.svg" \
    "$BUILD/usr/share/icons/hicolor/scalable/apps/wireguard-gui.svg"

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
Icon=wireguard-gui
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
Depends: python3 (>= 3.10), python3-gi, python3-gi-cairo, gir1.2-gtk-3.0, wireguard-tools, sudo
Recommends: gir1.2-ayatanaappindicator3-0.1 | gir1.2-appindicator3-0.1
Homepage: https://github.com/Derbosoft/wireguard-gui
Description: GTK graphical interface for WireGuard VPN tunnels
 Manage your WireGuard VPN tunnels with a clean, minimal GTK interface.
 Toggle tunnels on/off, create, edit and import configurations,
 view real-time traffic statistics, see your public IP when connected,
 and get a system tray icon — all without touching the terminal.
 No password prompt required after installation.
EOF

# ── DEBIAN/postinst ───────────────────────────────────────────────────────────
cat > "$BUILD/DEBIAN/postinst" <<'EOF'
#!/bin/bash
set -e

# ── Sudoers: auto-configure passwordless access for the installing user ────────
SUDOERS_FILE=/etc/sudoers.d/wireguard-gui

# Detect the real (non-root) user who ran sudo to install the package
REAL_USER="${SUDO_USER:-}"

if [[ -z "$REAL_USER" || "$REAL_USER" == "root" ]]; then
    REAL_USER="$(logname 2>/dev/null || true)"
fi
if [[ -z "$REAL_USER" || "$REAL_USER" == "root" ]]; then
    REAL_USER="$(who | grep -E '\(:[0-9]' | awk '{print $1}' | head -1 2>/dev/null || true)"
fi

if [[ -n "$REAL_USER" && "$REAL_USER" != "root" ]]; then
    cat > "$SUDOERS_FILE" <<SUDOERS
# WireGuard GUI — passwordless tunnel management
$REAL_USER ALL=(root) NOPASSWD: /usr/bin/wg-quick up *, /usr/bin/wg-quick down *, /usr/bin/wg show * dump, /usr/bin/wg show, /usr/bin/ls /etc/wireguard, /usr/bin/cat /etc/wireguard/*.conf, /usr/bin/tee /etc/wireguard/*.conf, /usr/bin/chmod 600 /etc/wireguard/*.conf, /usr/bin/rm /etc/wireguard/*.conf
SUDOERS
    chmod 440 "$SUDOERS_FILE"
fi

# ── Desktop integration ───────────────────────────────────────────────────────
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo ""
echo "WireGuard GUI installed successfully!"
echo "  Launch from terminal : wireguard-gui"
echo "  Launch from menu     : search for 'WireGuard'"
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
rm -f /usr/share/icons/hicolor/scalable/apps/wireguard-gui.svg
update-desktop-database /usr/share/applications 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
EOF
chmod 755 "$BUILD/DEBIAN/postrm"

# ── Build ─────────────────────────────────────────────────────────────────────
dpkg-deb --build --root-owner-group "$BUILD" "$OUT"

echo ""
echo "Package ready: $(basename "$OUT")"
echo ""
echo "  Install : sudo dpkg -i \"$OUT\""
echo "            sudo apt-get install -f"
echo "  Remove  : sudo apt remove wireguard-gui"
