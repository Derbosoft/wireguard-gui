import threading
import time
import os

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

import backend
from editor import TunnelEditorDialog

_ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wireguard.svg")


# ── Tunnel row widget ─────────────────────────────────────────────────────────

class TunnelRow(Gtk.ListBoxRow):
    def __init__(self, name: str, active: bool, callbacks: dict):
        super().__init__()
        self.name = name
        self._cb = callbacks

        self.set_margin_start(6)
        self.set_margin_end(6)
        self.set_margin_top(3)
        self.set_margin_bottom(3)

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(12)
        box.set_margin_end(8)
        box.set_margin_top(10)
        box.set_margin_bottom(10)

        # Status dot
        self._dot = Gtk.Label()
        box.pack_start(self._dot, False, False, 0)

        # Name
        self._name_lbl = Gtk.Label(label=name)
        self._name_lbl.set_halign(Gtk.Align.START)
        self._name_lbl.set_hexpand(True)
        attrs = Pango.AttrList()
        attrs.insert(Pango.attr_weight_new(Pango.Weight.SEMIBOLD))
        self._name_lbl.set_attributes(attrs)
        box.pack_start(self._name_lbl, True, True, 0)

        # Inline stats
        self._stats_lbl = Gtk.Label()
        self._stats_lbl.get_style_context().add_class("dim-label")
        self._stats_lbl.set_xalign(1.0)
        box.pack_start(self._stats_lbl, False, False, 0)

        # Spinner (shown while toggling)
        self._spinner = Gtk.Spinner()
        self._spinner.set_size_request(20, 20)
        box.pack_start(self._spinner, False, False, 0)

        # Edit
        edit_btn = Gtk.Button()
        edit_btn.set_image(Gtk.Image.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.BUTTON))
        edit_btn.set_relief(Gtk.ReliefStyle.NONE)
        edit_btn.set_tooltip_text("Modifier")
        edit_btn.connect("clicked", lambda _: self._cb["edit"](self.name))
        box.pack_start(edit_btn, False, False, 0)

        # Delete
        del_btn = Gtk.Button()
        del_btn.set_image(Gtk.Image.new_from_icon_name("user-trash-symbolic", Gtk.IconSize.BUTTON))
        del_btn.set_relief(Gtk.ReliefStyle.NONE)
        del_btn.set_tooltip_text("Supprimer")
        del_btn.connect("clicked", lambda _: self._cb["delete"](self.name))
        box.pack_start(del_btn, False, False, 0)

        # Toggle switch
        self._switch = Gtk.Switch()
        self._switch.set_valign(Gtk.Align.CENTER)
        self._switch.connect("state-set", self._on_switch)
        box.pack_start(self._switch, False, False, 0)

        self.add(box)
        self._set_active_ui(active)

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, active: bool, stats: backend.NetStats | None):
        self._set_active_ui(active)
        if stats and active:
            rx = backend.format_bytes(stats.rx_bytes)
            tx = backend.format_bytes(stats.tx_bytes)
            self._stats_lbl.set_markup(f"<small>↓{rx}  ↑{tx}</small>")
        else:
            self._stats_lbl.set_text("")

    def set_busy(self, busy: bool):
        self._switch.set_sensitive(not busy)
        if busy:
            self._spinner.start()
            self._spinner.show()
        else:
            self._spinner.stop()
            self._spinner.hide()

    # ── Private ───────────────────────────────────────────────────────────────

    def _set_active_ui(self, active: bool):
        color = "#4caf50" if active else "#9e9e9e"
        self._dot.set_markup(f'<span foreground="{color}" size="large">●</span>')
        # Avoid retriggering the state-set signal
        self._switch.handler_block_by_func(self._on_switch)
        self._switch.set_active(active)
        self._switch.handler_unblock_by_func(self._on_switch)

    def _on_switch(self, switch, state):
        self._cb["toggle"](self.name, state)
        return True  # prevent GTK from updating state automatically


# ── Main window ───────────────────────────────────────────────────────────────

class MainWindow(Gtk.ApplicationWindow):
    REFRESH_INTERVAL = 5  # seconds

    def __init__(self, app):
        super().__init__(application=app, title="WireGuard")
        self.set_default_size(620, 520)
        if os.path.exists(_ICON_PATH):
            self.set_icon_from_file(_ICON_PATH)
        else:
            self.set_icon_name("wireguard-gui")

        self._rows: dict[str, TunnelRow] = {}
        self._tray = None  # injected after construction

        self.connect("delete-event", self._on_close)
        self._build_ui()
        self._load_tunnels()
        GLib.timeout_add_seconds(self.REFRESH_INTERVAL, self._on_tick)

    def _on_close(self, _window, _event) -> bool:
        self.hide()
        return True  # empêche la destruction de la fenêtre

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # Header bar
        hbar = Gtk.HeaderBar()
        hbar.set_show_close_button(True)
        hbar.set_title("WireGuard")
        hbar.set_subtitle("Gestionnaire VPN")
        self.set_titlebar(hbar)

        add_btn = Gtk.Button()
        add_btn.set_image(Gtk.Image.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON))
        add_btn.set_tooltip_text("Nouveau tunnel")
        add_btn.connect("clicked", self._on_add)
        hbar.pack_start(add_btn)

        import_btn = Gtk.Button()
        import_btn.set_image(Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.BUTTON))
        import_btn.set_tooltip_text("Importer un fichier .conf")
        import_btn.connect("clicked", self._on_import)
        hbar.pack_start(import_btn)

        refresh_btn = Gtk.Button()
        refresh_btn.set_image(Gtk.Image.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON))
        refresh_btn.set_tooltip_text("Actualiser")
        refresh_btn.connect("clicked", lambda _: self._load_tunnels())
        hbar.pack_end(refresh_btn)

        # Root container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # Tunnel list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._listbox = Gtk.ListBox()
        self._listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._listbox.get_style_context().add_class("rich-list")
        self._listbox.connect("row-selected", self._on_row_selected)
        scroll.add(self._listbox)
        vbox.pack_start(scroll, True, True, 0)

        # Empty state label (shown when no tunnels)
        self._empty_lbl = Gtk.Label()
        self._empty_lbl.set_markup(
            '<span size="large" foreground="gray">Aucun tunnel configuré</span>\n'
            '<span foreground="gray">Cliquez sur  <b>+</b>  pour ajouter un tunnel</span>'
        )
        self._empty_lbl.set_justify(Gtk.Justification.CENTER)
        self._empty_lbl.set_vexpand(True)
        self._empty_lbl.set_valign(Gtk.Align.CENTER)
        vbox.pack_start(self._empty_lbl, True, True, 0)

        # Stats panel
        self._stats_bar = self._build_stats_bar()
        vbox.pack_end(self._stats_bar, False, False, 0)

        # show_all() must cover the window itself so the HeaderBar buttons appear
        self.show_all()
        self._empty_lbl.hide()
        self._stats_bar.hide()

    def _build_stats_bar(self) -> Gtk.Box:
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        bar.get_style_context().add_class("toolbar")
        bar.set_margin_start(16)
        bar.set_margin_end(16)
        bar.set_margin_top(6)
        bar.set_margin_bottom(6)

        self._si_name = Gtk.Label()
        self._si_name.get_style_context().add_class("dim-label")
        bar.pack_start(self._si_name, False, False, 0)

        self._si_endpoint = Gtk.Label()
        self._si_endpoint.get_style_context().add_class("dim-label")
        bar.pack_start(self._si_endpoint, False, False, 0)

        self._si_rx = Gtk.Label()
        bar.pack_start(self._si_rx, False, False, 0)

        self._si_tx = Gtk.Label()
        bar.pack_start(self._si_tx, False, False, 0)

        self._si_hs = Gtk.Label()
        self._si_hs.get_style_context().add_class("dim-label")
        bar.pack_end(self._si_hs, False, False, 0)

        self._si_public_ip = Gtk.Label()
        bar.pack_end(self._si_public_ip, False, False, 0)

        return bar

    # ── Data loading & refresh ────────────────────────────────────────────────

    def _load_tunnels(self):
        names = backend.get_tunnel_names()
        existing = set(self._rows.keys())

        # Remove stale rows
        for name in existing - set(names):
            self._listbox.remove(self._rows.pop(name))

        # Add or update rows
        for name in names:
            active = backend.is_active(name)
            stats = backend.get_net_stats(name) if active else None
            if name in self._rows:
                self._rows[name].update(active, stats)
            else:
                row = TunnelRow(name, active, {
                    "toggle": self._on_toggle,
                    "edit": self._on_edit,
                    "delete": self._on_delete,
                })
                self._rows[name] = row
                self._listbox.add(row)
                row.show_all()
                row.set_busy(False)

        has = bool(names)
        self._listbox.set_visible(has)
        self._empty_lbl.set_visible(not has)

        if self._tray:
            any_active = any(backend.is_active(n) for n in names)
            self._tray.set_icon_active(any_active)
            self._tray.refresh_menu()

    def _on_tick(self) -> bool:
        self._load_tunnels()
        return True

    # ── Toggle ────────────────────────────────────────────────────────────────

    def _on_toggle(self, name: str, enable: bool):
        row = self._rows.get(name)
        if row is None:
            return
        row.set_busy(True)

        to_disable = []
        if enable:
            for other_name, other_row in self._rows.items():
                if other_name != name and backend.is_active(other_name):
                    to_disable.append(other_name)
                    other_row.set_busy(True)

        def _worker():
            for other_name in to_disable:
                backend.toggle_tunnel(other_name, False)
                GLib.idle_add(self._after_disable, other_name)
            ok, err = backend.toggle_tunnel(name, enable)
            GLib.idle_add(self._after_toggle, name, enable, ok, err)

        threading.Thread(target=_worker, daemon=True).start()

    def _after_disable(self, name: str):
        row = self._rows.get(name)
        if row:
            row.update(False, None)
            row.set_busy(False)

    def _after_toggle(self, name: str, enable: bool, ok: bool, err: str):
        row = self._rows.get(name)
        if row is None:
            return
        active = backend.is_active(name)
        row.update(active, None)
        row.set_busy(False)
        if not ok:
            self._show_error(
                f"Impossible de {'démarrer' if enable else 'arrêter'} « {name} »",
                err,
            )
            return
        if enable and active:
            self._si_name.set_markup(f"<b>{name}</b>")
            self._si_endpoint.set_text("")
            self._si_rx.set_text("")
            self._si_tx.set_text("")
            self._si_hs.set_text("")
            self._si_public_ip.set_text("IP publique: …")
            self._stats_bar.show()

            def _fetch():
                info = backend.get_wg_info(name)
                GLib.idle_add(self._show_stats, name, info)
                ip = backend.get_public_ip()
                GLib.idle_add(self._update_public_ip_label, ip)

            threading.Thread(target=_fetch, daemon=True).start()

    # ── Add / Import ──────────────────────────────────────────────────────────

    def _on_add(self, _):
        dlg = TunnelEditorDialog(self)
        while True:
            resp = dlg.run()
            if resp != Gtk.ResponseType.OK:
                break
            ok, msg = dlg.validate()
            if not ok:
                self._show_error("Configuration invalide", msg)
                continue
            name = dlg.get_name()
            content = dlg.get_config()
            saved, err = backend.save_config(name, content)
            if saved:
                self._load_tunnels()
                break
            self._show_error("Impossible de sauvegarder", err)
        dlg.destroy()

    def _on_import(self, _):
        fc = Gtk.FileChooserDialog(
            title="Importer une configuration WireGuard",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        fc.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        filt = Gtk.FileFilter()
        filt.set_name("Configurations WireGuard (*.conf)")
        filt.add_pattern("*.conf")
        fc.add_filter(filt)

        if fc.run() == Gtk.ResponseType.OK:
            path = fc.get_filename()
            ok, err, name = backend.import_config(path)
            if ok:
                self._load_tunnels()
                self._show_info(f"Tunnel « {name} » importé avec succès.")
            else:
                self._show_error("Erreur lors de l'importation", err)
        fc.destroy()

    # ── Edit / Delete ─────────────────────────────────────────────────────────

    def _on_edit(self, name: str):
        config = backend.read_config(name)
        dlg = TunnelEditorDialog(self, name=name, config=config)
        while True:
            resp = dlg.run()
            if resp != Gtk.ResponseType.OK:
                break
            ok, msg = dlg.validate()
            if not ok:
                self._show_error("Configuration invalide", msg)
                continue
            content = dlg.get_config()
            saved, err = backend.save_config(name, content)
            if saved:
                self._load_tunnels()
                break
            self._show_error("Impossible de sauvegarder", err)
        dlg.destroy()

    def _on_delete(self, name: str):
        conf = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK_CANCEL,
            text=f"Supprimer le tunnel « {name} » ?",
        )
        conf.format_secondary_text("Cette action est irréversible.")
        resp = conf.run()
        conf.destroy()
        if resp != Gtk.ResponseType.OK:
            return
        if backend.is_active(name):
            backend.toggle_tunnel(name, False)
        ok, err = backend.delete_config(name)
        if ok:
            self._load_tunnels()
        else:
            self._show_error("Impossible de supprimer la configuration", err)

    # ── Stats panel ───────────────────────────────────────────────────────────

    def _on_row_selected(self, _listbox, row):
        if row is None:
            self._stats_bar.hide()
            return
        name = row.name
        if not backend.is_active(name):
            self._stats_bar.hide()
            return

        def _fetch():
            info = backend.get_wg_info(name)
            GLib.idle_add(self._show_stats, name, info)
            ip = backend.get_public_ip()
            GLib.idle_add(self._update_public_ip_label, ip)

        threading.Thread(target=_fetch, daemon=True).start()

    def _show_stats(self, name: str, info: backend.WgInfo | None):
        if info is None:
            self._stats_bar.hide()
            return
        self._si_name.set_markup(f"<b>{name}</b>")
        ep = info.endpoint or "—"
        self._si_endpoint.set_markup(f'<span foreground="gray">→ {ep}</span>')
        self._si_rx.set_markup(f"↓ <b>{backend.format_bytes(info.rx_bytes)}</b>")
        self._si_tx.set_markup(f"↑ <b>{backend.format_bytes(info.tx_bytes)}</b>")
        if info.latest_handshake > 0:
            elapsed = int(time.time()) - info.latest_handshake
            self._si_hs.set_text(f"Handshake: {backend.format_elapsed(elapsed)}")
        else:
            self._si_hs.set_text("Pas encore de handshake")
        self._si_public_ip.set_text("IP publique: …")
        self._stats_bar.show()

    def _update_public_ip_label(self, ip: str):
        if ip:
            self._si_public_ip.set_markup(f"IP publique: <b>{ip}</b>")
        else:
            self._si_public_ip.set_text("IP publique: indisponible")

    # ── Dialogs ───────────────────────────────────────────────────────────────

    def _show_error(self, title: str, details: str = ""):
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        if details:
            dlg.format_secondary_text(details)
        dlg.run()
        dlg.destroy()

    def _show_info(self, message: str):
        dlg = Gtk.MessageDialog(
            transient_for=self, modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dlg.run()
        dlg.destroy()
