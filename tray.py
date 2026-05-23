import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

try:
    gi.require_version("AyatanaAppIndicator3", "0.1")
    from gi.repository import AyatanaAppIndicator3 as AppIndicator3
    GLib.log_set_handler(
        "libayatana-appindicator",
        GLib.LogLevelFlags.LEVEL_WARNING,
        lambda domain, level, msg, data: None,
        None,
    )
    _INDICATOR_MODE = "ayatana"
except (ValueError, ImportError):
    try:
        gi.require_version("AppIndicator3", "0.1")
        from gi.repository import AppIndicator3
        _INDICATOR_MODE = "app"
    except (ValueError, ImportError):
        AppIndicator3 = None
        _INDICATOR_MODE = "status"

import backend


class TrayIcon:
    def __init__(self, window):
        self._window = window
        if _INDICATOR_MODE in ("ayatana", "app"):
            self._setup_indicator()
        else:
            self._setup_status_icon()

    # ── AppIndicator ──────────────────────────────────────────────────────────

    def _setup_indicator(self):
        self._indicator = AppIndicator3.Indicator.new(
            "wireguard-gui",
            "network-vpn",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
        )
        self._indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self._indicator.set_menu(self._build_menu())

    def refresh_menu(self):
        if _INDICATOR_MODE in ("ayatana", "app") and hasattr(self, "_indicator"):
            self._indicator.set_menu(self._build_menu())

    # ── Fallback: Gtk.StatusIcon ──────────────────────────────────────────────

    def _setup_status_icon(self):
        self._icon = Gtk.StatusIcon()
        self._icon.set_from_icon_name("network-vpn")
        self._icon.set_tooltip_text("WireGuard")
        self._icon.connect("activate", self._on_activate)
        self._icon.connect("popup-menu", self._on_popup)

    def _on_activate(self, _):
        if self._window.get_visible():
            self._window.hide()
        else:
            self._window.present()

    def _on_popup(self, icon, button, ts):
        menu = self._build_menu()
        menu.popup(None, None, Gtk.StatusIcon.position_menu, icon, button, ts)

    # ── Menu ──────────────────────────────────────────────────────────────────

    def _build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        show = Gtk.MenuItem(label="Afficher WireGuard")
        show.connect("activate", lambda _: self._window.present())
        menu.append(show)

        menu.append(Gtk.SeparatorMenuItem())

        names = backend.get_tunnel_names()
        for name in names:
            active = backend.is_active(name)
            item = Gtk.CheckMenuItem(label=name)
            item.set_active(active)
            item.connect("toggled", lambda mi, n=name: self._on_tray_toggle(n, mi.get_active()))
            menu.append(item)

        if names:
            menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="Quitter")
        quit_item.connect("activate", lambda _: self._window.get_application().quit())
        menu.append(quit_item)

        menu.show_all()
        return menu

    def _on_tray_toggle(self, name: str, enable: bool):
        def _worker():
            if enable:
                # Enforce exclusive VPN: disable any other active tunnel first
                for other in backend.get_tunnel_names():
                    if other != name and backend.is_active(other):
                        backend.toggle_tunnel(other, False)
            backend.toggle_tunnel(name, enable)
            GLib.idle_add(self.refresh_menu)
            GLib.idle_add(self._window._load_tunnels)

        threading.Thread(target=_worker, daemon=True).start()

    def set_icon_active(self, any_active: bool):
        icon_name = "network-vpn" if any_active else "network-offline"
        try:
            if _INDICATOR_MODE in ("ayatana", "app"):
                self._indicator.set_icon_full(icon_name, "WireGuard")
            elif hasattr(self, "_icon"):
                self._icon.set_from_icon_name(icon_name)
        except Exception:
            pass
