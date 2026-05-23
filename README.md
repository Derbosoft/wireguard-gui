# WireGuard GUI

> A minimal GTK application to manage WireGuard VPN tunnels on Ubuntu / Debian — no terminal needed.

**[Lire en français](README.fr.md)** &nbsp;·&nbsp; [Report a bug](../../issues) &nbsp;·&nbsp; [Download .deb](../../releases)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![GTK](https://img.shields.io/badge/GTK-3-4A90D9?logoColor=white)
![License](https://img.shields.io/badge/License-MIT-brightgreen)
![Platform](https://img.shields.io/badge/Platform-Ubuntu%20%7C%20Debian-E95420?logo=ubuntu&logoColor=white)
![Latest Release](https://img.shields.io/github/v/release/Derbosoft/wireguard-gui)

<!-- GitHub topics to add in repo Settings → About:
     wireguard vpn gtk python linux ubuntu gui network tunnel desktop-app
-->

---

## Screenshot

<!-- Replace with an actual screenshot: ![screenshot](assets/screenshot.png) -->
> *Screenshot coming soon — [contribute one!](../../issues)*

---

## Features

- **One-click toggle** — activate or deactivate any tunnel with a switch
- **Exclusive mode** — enabling a tunnel automatically disconnects the active one
- **Public IP display** — shows your real public IP as soon as the VPN is up
- **Create & edit configs** — full editor built into the UI, no text editor required
- **Import `.conf` files** — drag-and-drop style file picker
- **Real-time stats** — traffic (↓↑), endpoint, and last handshake time
- **System tray icon** — quick toggle menu, window hides instead of closing
- **No terminal needed** — password prompt handled automatically via `pkexec` or `sudo`

---

## Install

### From .deb (recommended)

Download the latest `.deb` from the [Releases page](../../releases), then run:

```bash
sudo dpkg -i wireguard-gui_*.deb
sudo apt-get install -f       # install any missing dependencies
```

That's it. Find the app in your application menu under **WireGuard**.

### From source

```bash
git clone https://github.com/Derbosoft/wireguard-gui.git
cd wireguard-gui
bash install.sh
```

---

## Uninstall

```bash
sudo apt remove wireguard-gui
```

To also remove the optional passwordless-sudo rule:

```bash
sudo apt purge wireguard-gui
```

---

## Optional: skip password prompts

By default, a system authentication dialog appears each time you toggle a tunnel. To allow VPN management without a password prompt:

```bash
sudo bash /opt/wireguard-gui/setup-sudoers.sh
```

This creates `/etc/sudoers.d/wireguard-gui`, scoped only to the `wg-quick` and `wg` commands.

---

## Build the .deb yourself

```bash
git clone https://github.com/Derbosoft/wireguard-gui.git
cd wireguard-gui
bash build-deb.sh
```

Requires `dpkg` (installed by default on Ubuntu / Debian).

---

## Requirements

| Dependency | Role |
|---|---|
| Python 3.10+ | Runtime |
| `python3-gi` | GTK Python bindings |
| `gir1.2-gtk-3.0` | GTK 3 library |
| `wireguard-tools` | `wg` and `wg-quick` commands |
| `pkexec` | Graphical privilege escalation |
| `gir1.2-ayatanaappindicator3-0.1` *(recommended)* | System tray icon |

Tested on **Ubuntu 22.04** and **Ubuntu 24.04**. Should work on any Debian-based distribution with GTK 3.

---

## How it works

| Action | Underlying command |
|---|---|
| Activate a tunnel | `wg-quick up <name>` |
| Deactivate a tunnel | `wg-quick down <name>` |
| Save a config | `cp /tmp/... /etc/wireguard/<name>.conf` |
| Delete a config | `rm /etc/wireguard/<name>.conf` |
| Read traffic stats | `/proc/net/dev` (no root required) |
| Public IP | `https://api.ipify.org` (HTTPS, no data stored) |

---

## Project structure

```
wireguard-gui/
├── main.py        # Entry point — Gtk.Application
├── backend.py     # WireGuard operations and public IP fetch
├── window.py      # Main window and tunnel rows
├── editor.py      # Create / edit tunnel dialog
├── tray.py        # System tray icon (AppIndicator3 / StatusIcon)
├── build-deb.sh   # Package builder
└── install.sh     # Script-based installer (alternative to .deb)
```

---

## Contributing

Pull requests are welcome. For major changes please open an issue first.

If this project is useful to you, please consider giving it a ⭐ — it helps others find it.

---

## License

[MIT](LICENSE)
