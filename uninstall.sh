#!/usr/bin/env bash
# uninstall.sh — Remove a script-based install of WireGuard GUI
# Use this only if you installed with install.sh, not via the .deb package.
# To remove a .deb install use: sudo apt remove wireguard-gui
set -euo pipefail

if [[ "$EUID" -eq 0 ]]; then
    RUN=""
else
    RUN="sudo"
fi

echo "=== Uninstalling WireGuard GUI ==="

$RUN rm -rf /opt/wireguard-gui
$RUN rm -f  /usr/local/bin/wireguard-gui
$RUN rm -f  /usr/share/applications/wireguard-gui.desktop
$RUN rm -f  /usr/share/icons/hicolor/scalable/apps/wireguard-gui.svg
$RUN rm -f  /etc/sudoers.d/wireguard-gui

$RUN update-desktop-database /usr/share/applications 2>/dev/null || true
$RUN gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true

echo "Done. WireGuard GUI has been removed."
