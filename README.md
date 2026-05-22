# WireGuard GUI

Interface graphique GTK pour gérer les tunnels WireGuard sur Ubuntu / Linux.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![GTK](https://img.shields.io/badge/GTK-3-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

## Fonctionnalités

- **Lister** tous les tunnels configurés dans `/etc/wireguard/`
- **Activer / désactiver** un tunnel en un clic (switch on/off)
- **Créer et modifier** des configurations directement dans l'interface
- **Importer** un fichier `.conf` existant
- **Supprimer** un tunnel (avec confirmation)
- **Statistiques en temps réel** : octets reçus/envoyés, endpoint, dernier handshake
- **Icône dans la barre système** (AppIndicator3 / Ayatana) avec menu rapide
- **Fermer la fenêtre sans quitter** : l'application reste active en tâche de fond

## Prérequis

- Ubuntu 22.04 / 24.04 (ou toute distribution avec GTK 3)
- Python 3.10+
- WireGuard installé (`wg-quick`, `wg`)
- Droits administrateur pour gérer les tunnels

## Installation

```bash
git clone https://github.com/votre-utilisateur/wireguard-gui.git
cd wireguard-gui
bash install.sh
```

Le script d'installation :

1. Installe les dépendances système (`python3-gi`, `wireguard-tools`, `pkexec`…)
2. Copie les fichiers dans `/opt/wireguard-gui/`
3. Crée le lanceur `/usr/local/bin/wireguard-gui`
4. Ajoute une entrée dans le menu applications GNOME
5. Propose (optionnel) de configurer `sudo NOPASSWD` pour éviter la saisie du mot de passe à chaque connexion

## Lancement

```bash
wireguard-gui
```

Ou depuis le menu Applications → **WireGuard**.

## Permissions

Les opérations suivantes nécessitent des droits root (une fenêtre d'authentification `pkexec` s'affiche si `sudo` n'est pas configuré) :

| Action | Commande sous-jacente |
|---|---|
| Activer un tunnel | `wg-quick up <nom>` |
| Désactiver un tunnel | `wg-quick down <nom>` |
| Sauvegarder une config | `cp /tmp/... /etc/wireguard/<nom>.conf` |
| Supprimer une config | `rm /etc/wireguard/<nom>.conf` |

La lecture des statistiques (octets) se fait via `/proc/net/dev` **sans** droits root.

Pour éviter les confirmations répétées, le script `install.sh` peut créer automatiquement `/etc/sudoers.d/wireguard-gui`.

## Structure du projet

```
wireguard-gui/
├── main.py       # Point d'entrée — Gtk.Application
├── backend.py    # Opérations WireGuard (wg-quick, /proc/net/dev…)
├── window.py     # Fenêtre principale et lignes de tunnel
├── editor.py     # Dialogue création / modification de tunnel
├── tray.py       # Icône barre système (AppIndicator3 / StatusIcon)
└── install.sh    # Script d'installation
```

## Dépendances

| Paquet | Rôle |
|---|---|
| `python3-gi` | Bindings GTK pour Python |
| `gir1.2-gtk-3.0` | Bibliothèque GTK 3 |
| `gir1.2-ayatanaappindicator3-0.1` | Icône barre système (Ubuntu 22.04+) |
| `wireguard-tools` | Commandes `wg` et `wg-quick` |
| `pkexec` | Élévation de privilèges graphique |

## Licence

MIT — voir [LICENSE](LICENSE)
