#!/bin/bash
# Completely remove MacCoffee from the system.

set -e

echo "Stopping MacCoffee..."
launchctl unload ~/Library/LaunchAgents/com.pixel.maccoffee.plist 2>/dev/null || true
pkill -f MacCoffee 2>/dev/null || true

echo "Restoring sleep-on-lid-close..."
sudo pmset -a disablesleep 0 2>/dev/null || true

echo "Removing files..."
rm -f  ~/Library/LaunchAgents/com.pixel.maccoffee.plist
rm -rf /Applications/MacCoffee.app
rm -f  /tmp/maccoffee.log

echo "Done. MacCoffee fully removed."
