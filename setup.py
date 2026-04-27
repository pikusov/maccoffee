from setuptools import setup

APP = ["src/app.py"]
DATA_FILES = [
    ("", ["com.pixel.maccoffee.plist"]),
]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "src/MacCoffee.icns",
    "plist": {
        "CFBundleName": "MacCoffee",
        "CFBundleDisplayName": "MacCoffee",
        "CFBundleIdentifier": "com.pixel.maccoffee",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0",
        "LSUIElement": True,
        "NSHumanReadableCopyright": "© 2026",
        "LSMinimumSystemVersion": "10.14",
        "NSPrincipalClass": "NSApplication",
    },
    "packages": ["rumps"],
}

setup(
    app=APP,
    name="MacCoffee",
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
