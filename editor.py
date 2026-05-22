import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango


DEFAULT_CONFIG = """\
[Interface]
PrivateKey =
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey =
Endpoint = serveur:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""


class TunnelEditorDialog(Gtk.Dialog):
    def __init__(self, parent, name: str = "", config: str = ""):
        editing = bool(name)
        title = f"Modifier « {name} »" if editing else "Nouveau tunnel"
        super().__init__(title=title, transient_for=parent, modal=True)
        self.set_default_size(540, 440)
        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.OK,
        )
        self.set_default_response(Gtk.ResponseType.OK)

        content = self.get_content_area()
        content.set_spacing(8)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(8)

        # ── Name field ────────────────────────────────────────────────────────
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        lbl = Gtk.Label(label="Nom du tunnel :")
        lbl.set_width_chars(16)
        lbl.set_halign(Gtk.Align.END)
        name_box.pack_start(lbl, False, False, 0)

        self._name_entry = Gtk.Entry()
        self._name_entry.set_text(name)
        self._name_entry.set_placeholder_text("ex : vpn-maison, bureau…")
        self._name_entry.set_hexpand(True)
        self._name_entry.set_sensitive(not editing)
        self._name_entry.set_activates_default(True)
        name_box.pack_start(self._name_entry, True, True, 0)
        content.add(name_box)

        # ── Config text editor ────────────────────────────────────────────────
        lbl2 = Gtk.Label(label="Fichier de configuration :")
        lbl2.set_halign(Gtk.Align.START)
        lbl2.set_margin_top(4)
        content.add(lbl2)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)

        self._text_view = Gtk.TextView()
        self._text_view.set_monospace(True)
        self._text_view.set_left_margin(8)
        self._text_view.set_right_margin(8)
        self._text_view.set_top_margin(6)
        self._text_view.set_bottom_margin(6)
        buf = self._text_view.get_buffer()
        buf.set_text(config if config else DEFAULT_CONFIG)
        scroll.add(self._text_view)
        content.add(scroll)

        content.show_all()

    def get_name(self) -> str:
        return self._name_entry.get_text().strip()

    def get_config(self) -> str:
        buf = self._text_view.get_buffer()
        return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)

    def validate(self) -> tuple[bool, str]:
        name = self.get_name()
        if not name:
            return False, "Le nom du tunnel ne peut pas être vide."
        if not name.replace("-", "").replace("_", "").isalnum():
            return False, "Le nom ne doit contenir que des lettres, chiffres, - et _."
        config = self.get_config()
        if "[Interface]" not in config or "PrivateKey" not in config:
            return False, "La configuration doit contenir une section [Interface] avec PrivateKey."
        return True, ""
