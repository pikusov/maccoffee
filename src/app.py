#!/usr/bin/env python3
"""
MacCoffee — macOS menu bar app to toggle lid-close sleep behavior.

☕ = sleep prevented (lid close does nothing)
🌙 = normal (lid close triggers sleep)

Polls pmset every 5 s so the icon always reflects the real system state.
"""

import fcntl
import os
import subprocess
import sys

import rumps
from AppKit import NSApplication

VERSION = "1.0"

_PLIST_NAME = "com.pixel.maccoffee.plist"
_PLIST_PATH = os.path.expanduser(f"~/Library/LaunchAgents/{_PLIST_NAME}")
_APP_PATH   = "/Applications/MacCoffee.app"
_LOCK_FILE  = "/tmp/com.pixel.maccoffee.lock"


def _acquire_lock():
    """Ensure only one instance runs. Exits immediately if another is running."""
    lock = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit(0)
    return lock  # keep reference so GC doesn't close/release it


# ── pmset ─────────────────────────────────────────────────────────────────────
def get_sleep_disabled() -> bool:
    """Return True if lid-close sleep is currently disabled."""
    try:
        out = subprocess.check_output(["pmset", "-g"], text=True)
        for line in out.splitlines():
            if "SleepDisabled" in line:
                return line.strip().split()[-1] == "1"
    except Exception:
        pass
    return False


def set_sleep_disabled(disabled: bool):
    """Toggle SleepDisabled via pmset — prompts for admin password via GUI."""
    val = "1" if disabled else "0"
    cmd = f"pmset -a disablesleep {val}"
    result = subprocess.run(
        ["osascript", "-e", f'do shell script "{cmd}" with administrator privileges']
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)


# ── LaunchAgent helpers ───────────────────────────────────────────────────────
def launch_at_login_enabled() -> bool:
    """Return True if the LaunchAgent is currently loaded."""
    result = subprocess.run(
        ["launchctl", "list", "com.pixel.maccoffee"],
        capture_output=True,
    )
    return result.returncode == 0


def set_launch_at_login(enabled: bool):
    """Install or remove the LaunchAgent for auto-start at login."""
    if enabled:
        # Copy plist from app bundle to LaunchAgents and load it
        src = os.path.join(
            _APP_PATH, "Contents", "Resources", _PLIST_NAME
        )
        if not os.path.exists(src):
            raise FileNotFoundError(f"Plist not found inside app bundle: {src}")
        subprocess.run(["cp", src, _PLIST_PATH], check=True)
        subprocess.run(["launchctl", "load", _PLIST_PATH], check=True)
    else:
        subprocess.run(["launchctl", "unload", _PLIST_PATH], capture_output=True)
        try:
            os.remove(_PLIST_PATH)
        except OSError:
            pass


# ── app ───────────────────────────────────────────────────────────────────────
class MacCoffeeApp(rumps.App):

    _EMOJI_AWAKE = "☕"
    _EMOJI_SLEEP = "🌙"

    def __init__(self):
        self._lock = _acquire_lock()
        # Read system state before any UI initialisation
        self._sleep_disabled = get_sleep_disabled()

        super().__init__(
            name="MacCoffee",
            title=self._EMOJI_AWAKE if self._sleep_disabled else self._EMOJI_SLEEP,
            quit_button=None,
        )

        self._build_menu()

        # Poll every 5 s — pmset -g is a fast local read, negligible CPU
        self._timer = rumps.Timer(self._poll, 5)
        self._timer.start()

    # ── state sync ────────────────────────────────────────────────────────────
    def _sync_ui(self):
        """Update icon and checkmarks to match self._sleep_disabled."""
        self.title = self._EMOJI_AWAKE if self._sleep_disabled else self._EMOJI_SLEEP
        self._item_awake.state = int(self._sleep_disabled)
        self._item_sleep.state = int(not self._sleep_disabled)

    def _poll(self, _):
        """Fires every 5 s — syncs icon if pmset was changed externally."""
        current = get_sleep_disabled()
        if current != self._sleep_disabled:
            self._sleep_disabled = current
            self._sync_ui()

    # ── menu ──────────────────────────────────────────────────────────────────
    def _build_menu(self):
        self._item_sleep = rumps.MenuItem(
            "Sleep on lid close", callback=self._cmd_sleep
        )
        self._item_awake = rumps.MenuItem(
            "Stay awake on lid close", callback=self._cmd_awake
        )
        self._item_login = rumps.MenuItem(
            "Launch at Login", callback=self._cmd_toggle_login
        )
        self._item_login.state = int(launch_at_login_enabled())

        self.menu = [
            self._item_sleep,
            self._item_awake,
            None,
            self._item_login,
            None,
            rumps.MenuItem("About / Help", callback=self._show_help),
            None,
            rumps.MenuItem("Quit MacCoffee", callback=self._quit),
        ]
        self._sync_ui()

    # ── commands ──────────────────────────────────────────────────────────────
    def _apply(self, disabled: bool):
        try:
            set_sleep_disabled(disabled)
        except subprocess.CalledProcessError:
            rumps.notification(
                "MacCoffee", "Error",
                "Could not change setting — admin password required.",
            )
            return
        self._sleep_disabled = disabled
        self._sync_ui()

    def _cmd_sleep(self, _):
        if not self._sleep_disabled:
            return
        self._apply(False)

    def _cmd_awake(self, _):
        if self._sleep_disabled:
            return
        self._apply(True)

    def _cmd_toggle_login(self, _):
        want = not launch_at_login_enabled()
        try:
            set_launch_at_login(want)
        except Exception as e:
            rumps.notification("MacCoffee", "Error", str(e))
            return
        self._item_login.state = int(want)

    def _show_help(self, _):
        rumps.alert(
            title=f"MacCoffee {VERSION}",
            message=(
                "MacCoffee lets you control whether your MacBook sleeps "
                "when the lid is closed.\n\n"
                "☕  Stay awake on lid close\n"
                "    The system will NOT sleep when you close the lid.\n\n"
                "🌙  Sleep on lid close\n"
                "    Normal behaviour — the system sleeps on lid close.\n\n"
                "Changing the setting requires your administrator password.\n\n"
                "Use 'Launch at Login' to start MacCoffee automatically "
                "when you log in.\n\n"
                "The icon always reflects the real system state and updates "
                "automatically if another app changes the setting."
            ),
            ok="Got it",
        )

    def _quit(self, _):
        self._timer.stop()
        if self._sleep_disabled:
            try:
                set_sleep_disabled(False)
            except Exception:
                pass
        NSApplication.sharedApplication().terminate_(None)


if __name__ == "__main__":
    MacCoffeeApp().run()
