# MacCoffee ☕

> Keep your MacBook awake when the lid is closed — right from the menu bar.

![macOS](https://img.shields.io/badge/macOS-10.14%2B-blue)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

MacCoffee sits in your menu bar and lets you toggle whether your MacBook sleeps when you close the lid. One click, no Terminal needed.

| Icon | State |
|------|-------|
| ☕ | **Caffeinated** — lid close does nothing |
| 🌙 | **Normal** — lid close triggers sleep |

The icon always reflects the **real system state** — even if another app or `pmset` changed it externally.

---

## Install

### Option A — drag & drop (simplest)

1. Download `MacCoffee.app` from [Releases](../../releases)
2. Drag it to `/Applications`
3. Launch via Spotlight (**⌘ Space** → `MacCoffee`) or double-click in Finder

> macOS may show a security warning on first launch. Go to  
> **System Settings → Privacy & Security → Open Anyway**.

### Option B — auto-start at login (LaunchAgent)

```bash
cp com.pixel.maccoffee.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.pixel.maccoffee.plist
```

---

## Usage

Click the menu bar icon:

- **Sleep on lid close** — restore normal sleep behaviour
- **Stay awake on lid close** — prevent sleep on lid close
- **About / Help** — show this information inside the app
- **Quit MacCoffee** — quit and restore normal sleep

Changing the setting requires your **administrator password** (the app uses `pmset -a disablesleep`).

---

## Uninstall

### Simple (no LaunchAgent)

Drag `MacCoffee.app` out of `/Applications` into Trash. That's it.

### Full removal (with LaunchAgent)

```bash
bash uninstall.sh
```

Or manually:

```bash
launchctl unload ~/Library/LaunchAgents/com.pixel.maccoffee.plist 2>/dev/null
rm -f  ~/Library/LaunchAgents/com.pixel.maccoffee.plist
rm -rf /Applications/MacCoffee.app
sudo pmset -a disablesleep 0
```

---

## Build from source

### Requirements

- macOS 10.14+
- Python 3.9+

### Steps

```bash
# 1. Clone
git clone https://github.com/YOUR_USERNAME/maccoffee.git
cd maccoffee

# 2. Create virtualenv and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install rumps py2app

# 3. Generate app icon (requires macOS — uses AppKit to render ☕ emoji)
python3 make_icon.py

# 4. Build the .app bundle
python3 setup.py py2app

# 5. Install
cp -rf dist/MacCoffee.app /Applications/
```

---

## What it touches on the system

| What | When |
|------|------|
| `pmset -a disablesleep 1` | When you select "Stay awake" |
| `pmset -a disablesleep 0` | When you select "Sleep" or quit |
| `~/Library/LaunchAgents/com.pixel.maccoffee.plist` | Only if you install the LaunchAgent manually |
| `/tmp/maccoffee.log` | Only if using LaunchAgent |

No preferences files, no background daemons, no network access.

---

## License

MIT
