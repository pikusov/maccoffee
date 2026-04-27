#!/usr/bin/env python3
"""Generate MacCoffee.icns using the ☕ emoji rendered via AppKit."""
import os
import subprocess
from AppKit import NSImage, NSAttributedString, NSFont, NSColor
from AppKit import NSRectFill, NSPNGFileType, NSBitmapImageRep
from Foundation import NSDictionary

ICONSET_DIR = os.path.join(os.path.dirname(__file__), "MacCoffee.iconset")
ICNS_PATH   = os.path.join(os.path.dirname(__file__), "src", "MacCoffee.icns")
EMOJI       = "☕"
SIZES       = [16, 32, 64, 128, 256, 512]


def render_emoji_png(size: int, path: str):
    img = NSImage.alloc().initWithSize_((size, size))
    img.lockFocus()
    NSColor.clearColor().set()
    NSRectFill(((0, 0), (size, size)))
    font  = NSFont.systemFontOfSize_(size * 0.85)
    attrs = NSDictionary.dictionaryWithObject_forKey_(font, "NSFont")
    ns_str = NSAttributedString.alloc().initWithString_attributes_(EMOJI, attrs)
    bounds = ns_str.size()
    ns_str.drawAtPoint_(((size - bounds.width) / 2, (size - bounds.height) / 2))
    img.unlockFocus()
    rep = NSBitmapImageRep.imageRepWithData_(img.TIFFRepresentation())
    rep.representationUsingType_properties_(NSPNGFileType, None).writeToFile_atomically_(path, True)
    print(f"  {os.path.basename(path)}")


def build():
    os.makedirs(ICONSET_DIR, exist_ok=True)
    for size in SIZES:
        render_emoji_png(size,     os.path.join(ICONSET_DIR, f"icon_{size}x{size}.png"))
        render_emoji_png(size * 2, os.path.join(ICONSET_DIR, f"icon_{size}x{size}@2x.png"))
    subprocess.run(["iconutil", "-c", "icns", ICONSET_DIR, "-o", ICNS_PATH], check=True)
    print(f"\nICNS → {ICNS_PATH}")


if __name__ == "__main__":
    build()
