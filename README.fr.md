# WireGuard GUI

> Une interface GTK minimaliste pour gérer les tunnels VPN WireGuard sur Ubuntu / Debian — sans ligne de commande.

**[Read in English](README.md)** &nbsp;·&nbsp; [Signaler un bug](../../issues) &nbsp;·&nbsp; [Télécharger le .deb](../../releases)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GTK](https://img.shields.io/badge/GTK-3-4A90D9?logoColor=white)
![Licence](https://img.shields.io/badge/Licence-MIT-brightgreen)
![Plateforme](https://img.shields.io/badge/Plateforme-Ubuntu%20%7C%20Debian-E95420?logo=ubuntu&logoColor=white)

---

## Fonctionnalités

- **Activation en un clic** — activez ou désactivez un tunnel avec un switch
- **Mode exclusif** — activer un tunnel désactive automatiquement celui déjà actif
- **Affichage de l'IP publique** — votre vraie IP s'affiche dès que le VPN est connecté
- **Créer et modifier des configs** — éditeur intégré, pas besoin d'ouvrir un fichier texte
- **Importer un fichier `.conf`** — sélecteur de fichier graphique
- **Statistiques en temps réel** — trafic (↓↑), endpoint, dernier handshake
- **Icône dans la barre système** — menu rapide, la fenêtre se masque sans quitter l'appli
- **Aucune demande de mot de passe** — configuré automatiquement à l'installation

---

## Installation

Téléchargez le dernier `.deb` depuis la [page Releases](../../releases/latest), puis :

```bash
sudo dpkg -i wireguard-gui_*.deb
sudo apt-get install -f
```

L'application apparaît ensuite dans le menu des applications sous le nom **WireGuard**.

L'installateur configure automatiquement l'accès sans mot de passe aux commandes WireGuard — aucune manipulation supplémentaire requise.

---

## Désinstallation

```bash
sudo apt remove wireguard-gui
```

Pour supprimer aussi la règle sudo :

```bash
sudo apt purge wireguard-gui
```

---

## Construire le .deb soi-même

```bash
git clone https://github.com/Derbosoft/wireguard-gui.git
cd wireguard-gui
bash build-deb.sh
```

Nécessite `dpkg` (installé par défaut sur Ubuntu / Debian).

---

## Prérequis

| Dépendance | Rôle |
|---|---|
| Python 3.10+ | Interpréteur |
| `python3-gi` | Bindings GTK pour Python |
| `gir1.2-gtk-3.0` | Bibliothèque GTK 3 |
| `wireguard-tools` | Commandes `wg` et `wg-quick` |
| `sudo` | Élévation de privilèges sans mot de passe |
| `gir1.2-ayatanaappindicator3-0.1` *(recommandé)* | Icône barre système |

Testé sur **Ubuntu 22.04** et **Ubuntu 24.04**.

---

## Fonctionnement

| Action | Commande sous-jacente |
|---|---|
| Activer un tunnel | `wg-quick up <nom>` |
| Désactiver un tunnel | `wg-quick down <nom>` |
| Sauvegarder une config | `tee /etc/wireguard/<nom>.conf` |
| Supprimer une config | `rm /etc/wireguard/<nom>.conf` |
| Lire les statistiques | `/proc/net/dev` (sans droits root) |
| IP publique | `https://api.ipify.org` (HTTPS, aucune donnée stockée) |

Toutes les commandes privilégiées passent par `sudo` avec une règle NOPASSWD limitée aux chemins WireGuard, installée automatiquement par le paquet.

---

## Structure du projet

```
wireguard-gui/
├── main.py        # Point d'entrée — Gtk.Application
├── backend.py     # Opérations WireGuard et récupération de l'IP publique
├── window.py      # Fenêtre principale et lignes de tunnel
├── editor.py      # Dialogue création / modification de tunnel
├── tray.py        # Icône barre système (AppIndicator3 / StatusIcon)
├── wireguard.svg  # Icône de l'application
└── build-deb.sh   # Script de construction du paquet .deb
```

---

## Contribution

Les pull requests sont les bienvenues. Pour des changements importants, ouvrez d'abord une issue.

Si ce projet vous est utile, pensez à lui donner une ⭐ — cela aide les autres à le trouver.

---

## Licence

[MIT](LICENSE)
