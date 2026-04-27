#!/usr/bin/env python3
"""
MacCoffee — macOS menu bar app to toggle lid-close sleep behavior.

Toolbar icons: ☕ = sleep prevented, 🌙 = normal sleep on lid close.

The app reads the real pmset state on launch AND polls every 60 s,
so the icon always reflects the actual system state even if pmset
was changed externally (e.g. another app or terminal command).
"""

import os
import subprocess

import rumps
from AppKit import NSApplication

VERSION = "1.0"

_LAUNCHAGENT = os.path.expanduser(
    "~/Library/LaunchAgents/com.pixel.maccoffee.plist"
)


# ── pmset ─────────────────────────────────────────────────────────────────────
def get_sleep_disabled() -> bool:
    """Read current SleepDisabled value from pmset. Returns True = lid won't sleep."""
    try:
        out = subprocess.check_output(["pmset", "-g"], text=True)
        for line in out.splitlines():
            if "SleepDisabled" in line:
                return line.strip().split()[-1] == "1"
    except Exception:
        pass
    return False


def set_sleep_disabled(disabled: bool):
    """Change SleepDisabled via pmset, prompts for admin password via GUI."""
    val = "1" if disabled else "0"
    cmd = f"pmset -a disablesleep {val}"
    result = subprocess.run(
        ["osascript", "-e", f'do shell script "{cmd}" with administrator privileges']
    )
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)


# ── app ───────────────────────────────────────────────────────────────────────
class MacCoffeeApp(rumps.App):

    _EMOJI_AWAKE = "☕"
    _EMOJI_SLEEP = "🌙"

    def __init__(self):
        self._sleep_disabled = get_sleep_disabled()

        super().__init__(
            name="MacCoffee",
            title=self._EMOJI_AWAKE if self._sleep_disabled else self._EMOJI_SLEEP,
            quit_button=None,
        )

        self._build_menu()

        self._timer = rumps.Timer(self._poll, 60)
        self._timer.start()

    # ── icon & state ──────────────────────────────────────────────────────────
    def _sync_icon(self):
        """Update toolbar icon and menu checkmarks to match current state."""
        self.title = self._EMOJI_AWAKE if self._sleep_disabled else self._EMOJI_SLEEP
        self._item_awake.state = int(self._sleep_disabled)
        self._item_sleep.state = int(not self._sleep_disabled)

    def _poll(self, _):
        """Periodic sync — fires every 60 s to catch external pmset changes."""
        current = get_sleep_disabled()
        if current != self._sleep_disabled:
            self._sleep_disabled = current
        self._sync_icon()

    # ── menu (built once) ─────────────────────────────────────────────────────
    def _build_menu(self):
        self._item_sleep = rumps.MenuItem(
            "Sleep on lid close", callback=self._cmd_sleep
        )
        self._item_awake = rumps.MenuItem(
            "Stay awake on lid close", callback=self._cmd_awake
        )
        self.menu = [
            self._item_sleep,
            self._item_awake,
            None,
            rumps.MenuItem("About / Help", callback=self._show_help),
            None,
            rumps.MenuItem("Quit MacCoffee", callback=self._quit),
        ]

    # ── commands ──────────────────────────────────────────────────────────────
    def _apply(self, disabled: bool):
        try:
            set_sleep_disabled(disabled)
        except subprocess.CalledProcessError:
            rumps.notification(
                "MacCoffee",
                "Error",
                "Could not change setting — admin password required.",
            )
            return
        self._sleep_disabled = disabled
        self._sync_icon()

    def _cmd_sleep(self, _):
        if not self._sleep_disabled:
            return
        self._apply(False)

    def _cmd_awake(self, _):
        if self._sleep_disabled:
            return
        self._apply(True)

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
                "Changing the setting requires administrator password (pmset).\n\n"
                "The icon always reflects the real system state. "
                "If another app changes the setting, MacCoffee updates automatically."
            ),
            ok="Got it",
        )

    def _quit(self, _):
        self._timer.stop()
        # Restore normal sleep behaviour before quitting
        if self._sleep_disabled:
            try:
                set_sleep_disabled(False)
            except Exception:
                pass
        # Unload LaunchAgent so it won't restart the process immediately
        if os.path.exists(_LAUNCHAGENT):
            subprocess.run(
                ["launchctl", "unload", _LAUNCHAGENT],
                capture_output=True,
            )
        NSApplication.sharedApplication().terminate_(None)


if __name__ == "__main__":
    MacCoffeeApp().run()
