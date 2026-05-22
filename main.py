#!/usr/bin/env python3
import sys

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio

from window import MainWindow
from tray import TrayIcon


class WireGuardApp(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="com.github.wireguard-gui",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self._window = None

    def do_startup(self):
        Gtk.Application.do_startup(self)
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Primary>q"])

    def do_activate(self):
        if self._window is None:
            self._window = MainWindow(self)
            tray = TrayIcon(self._window)
            self._window._tray = tray
        self._window.present()


if __name__ == "__main__":
    app = WireGuardApp()
    sys.exit(app.run(sys.argv))
