#!/usr/bin/env bash
# install.sh — Install WireGuard GUI on Ubuntu
set -euo pipefail

APP_DIR="/opt/wireguard-gui"
BIN="/usr/local/bin/wireguard-gui"
DESKTOP="/usr/share/applications/wireguard-gui.desktop"
SUDOERS="/etc/sudoers.d/wireguard-gui"

# Use sudo only when not already root
if [[ "$EUID" -eq 0 ]]; then
    RUN=""
else
    RUN="sudo"
fi

echo "=== Installation de WireGuard GUI ==="

# ── Dependencies ──────────────────────────────────────────────────────────────
echo "[1/5] Installation des dépendances système..."
$RUN apt-get update -qq
$RUN apt-get install -y \
    python3 \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gtk-3.0 \
    wireguard \
    wireguard-tools \
    polkitd \
    pkexec

# Try AppIndicator variants (Ubuntu 22.04+ uses Ayatana)
$RUN apt-get install -y gir1.2-ayatanaappindicator3-0.1 2>/dev/null \
    || $RUN apt-get install -y gir1.2-appindicator3-0.1 2>/dev/null \
    || echo "  ⚠  AppIndicator non disponible — icône barre système désactivée."

# ── App files ─────────────────────────────────────────────────────────────────
echo "[2/5] Copie des fichiers de l'application..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
$RUN mkdir -p "$APP_DIR"
$RUN cp "$SCRIPT_DIR"/*.py "$APP_DIR/"
$RUN chmod 644 "$APP_DIR"/*.py

# ── Launcher ──────────────────────────────────────────────────────────────────
echo "[3/5] Création du lanceur..."
$RUN tee "$BIN" > /dev/null << 'EOF'
#!/usr/bin/env bash
exec python3 /opt/wireguard-gui/main.py "$@"
EOF
$RUN chmod +x "$BIN"

# ── Desktop entry ─────────────────────────────────────────────────────────────
echo "[4/5] Création de l'entrée de menu..."
$RUN tee "$DESKTOP" > /dev/null << 'EOF'
[Desktop Entry]
Name=WireGuard
GenericName=Gestionnaire VPN
Comment=Gérer les tunnels WireGuard
Exec=wireguard-gui
Icon=network-vpn
Terminal=false
Type=Application
Categories=Network;Security;
Keywords=vpn;wireguard;tunnel;réseau;
StartupNotify=true
EOF

# ── Sudoers (optional but recommended) ───────────────────────────────────────
echo "[5/5] Configuration des permissions sudo..."

# Determine the real (non-root) user to grant permissions to
if [[ "$EUID" -eq 0 && -n "${SUDO_USER:-}" ]]; then
    REAL_USER="$SUDO_USER"
elif [[ "$EUID" -ne 0 ]]; then
    REAL_USER="$USER"
else
    # Running as root without sudo — ask who to configure
    read -r -p "  Nom de l'utilisateur à configurer (laisser vide pour ignorer) : " REAL_USER
fi

if [[ -n "${REAL_USER:-}" && "$REAL_USER" != "root" ]]; then
    cat << 'INFO'

  Pour éviter la saisie du mot de passe à chaque connexion/déconnexion,
  vous pouvez autoriser wg-quick et wg sans mot de passe.

INFO
    read -r -p "  Configurer sudo NOPASSWD pour « $REAL_USER » ? [o/N] " answer
    if [[ "$answer" =~ ^[oOyY]$ ]]; then
        $RUN tee "$SUDOERS" > /dev/null << EOF
# WireGuard GUI — allow managing tunnels without password
$REAL_USER ALL=(root) NOPASSWD: /usr/bin/wg-quick *, /usr/bin/wg show *, /usr/bin/wg show, /bin/ls /etc/wireguard/, /bin/cat /etc/wireguard/*.conf, /bin/cp * /etc/wireguard/*.conf, /bin/chmod 600 /etc/wireguard/*.conf, /bin/rm /etc/wireguard/*.conf
EOF
        $RUN chmod 440 "$SUDOERS"
        echo "  ✓ sudoers configuré pour $REAL_USER"
    else
        echo "  → Ignoré. Une fenêtre d'authentification apparaîtra à chaque action."
    fi
else
    echo "  → Ignoré (pas d'utilisateur non-root identifié)."
fi

echo ""
echo "✓ WireGuard GUI installé avec succès !"
echo "  Lancer depuis le terminal : wireguard-gui"
echo "  Lancer depuis le menu      : cherchez « WireGuard »"
