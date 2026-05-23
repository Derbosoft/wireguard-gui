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
- **Sans terminal** — l'élévation de privilèges passe par `pkexec` ou `sudo` automatiquement

---

## Installation

### Via le paquet .deb (recommandé)

Téléchargez le dernier `.deb` depuis la [page Releases](../../releases), puis :

```bash
sudo dpkg -i wireguard-gui_*.deb
sudo apt-get install -f       # installer les dépendances manquantes
```

L'application apparaît ensuite dans le menu des applications sous le nom **WireGuard**.

### Depuis les sources

```bash
git clone https://github.com/Derbosoft/wireguard-gui.git
cd wireguard-gui
bash install.sh
```

---

## Désinstallation

```bash
sudo apt remove wireguard-gui
```

Pour supprimer aussi la règle sudo optionnelle :

```bash
sudo apt purge wireguard-gui
```

---

## Optionnel : éviter les saisies de mot de passe

Par défaut, une fenêtre d'authentification système apparaît à chaque connexion/déconnexion. Pour éviter cela :

```bash
sudo bash /opt/wireguard-gui/setup-sudoers.sh
```

Cela crée `/etc/sudoers.d/wireguard-gui`, limité uniquement aux commandes `wg-quick` et `wg`.

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
| `pkexec` | Élévation de privilèges graphique |
| `gir1.2-ayatanaappindicator3-0.1` *(recommandé)* | Icône barre système |

Testé sur **Ubuntu 22.04** et **Ubuntu 24.04**. Compatible avec toute distribution basée sur Debian avec GTK 3.

---

## Fonctionnement

| Action | Commande sous-jacente |
|---|---|
| Activer un tunnel | `wg-quick up <nom>` |
| Désactiver un tunnel | `wg-quick down <nom>` |
| Sauvegarder une config | `cp /tmp/... /etc/wireguard/<nom>.conf` |
| Supprimer une config | `rm /etc/wireguard/<nom>.conf` |
| Lire les statistiques | `/proc/net/dev` (sans droits root) |
| IP publique | `https://api.ipify.org` (HTTPS, aucune donnée stockée) |

---

## Structure du projet

```
wireguard-gui/
├── main.py        # Point d'entrée — Gtk.Application
├── backend.py     # Opérations WireGuard et récupération de l'IP publique
├── window.py      # Fenêtre principale et lignes de tunnel
├── editor.py      # Dialogue création / modification de tunnel
├── tray.py        # Icône barre système (AppIndicator3 / StatusIcon)
├── build-deb.sh   # Script de construction du paquet .deb
└── install.sh     # Installateur alternatif (sans .deb)
```

---

## Contribution

Les pull requests sont les bienvenues. Pour des changements importants, ouvrez d'abord une issue.

Si ce projet vous est utile, pensez à lui donner une ⭐ — cela aide les autres à le trouver.

---

## Licence

[MIT](LICENSE)
