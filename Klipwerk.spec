# Klipwerk.spec
# ─────────────────────────────────────────────────────────────────────
# PyInstaller build configuration - Optimized for minimal binary size
# Run with:  python -m PyInstaller Klipwerk.spec --noconfirm
# Or on Windows: build.bat
# Or on Linux:   ./build.sh
# ─────────────────────────────────────────────────────────────────────

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files

# Only collect necessary data files from customtkinter (assets, themes)
ctk_datas = collect_data_files("customtkinter")

block_cipher = None

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=ctk_datas + [("assets", "assets")],
    hiddenimports=[
        "PIL._tkinter_finder",
        "PIL.Image",
        "PIL.ImageTk",
        "pyperclip",
        "requests",
        "urllib.request",
        "mutagen",
        "mutagen.mp3",
        "mutagen.id3",
        "mutagen.mp4",
        "mutagen.flac",
        "resvg_py",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude heavy test/dev/doc/REPL modules not needed in GUI app
        "pytest",
        "setuptools",
        "unittest",
        "pydoc",
        "tkinter.test",
        "lib2to3",
        "sqlite3",
        "_sqlite3",
        "_pyrepl",
        "PIL._avif",
        "curses",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Filter out heavy unneeded extension binaries and libraries
# (e.g. PIL._avif is 7.5MB, sqlite3 is 1.5MB)
EXCLUDED_BINARY_PATTERNS = ("_avif", "sqlite3")
filtered_binaries = [
    b for b in a.binaries
    if not any(pat in b[0].lower() for pat in EXCLUDED_BINARY_PATTERNS)
]

# Filter out test/demo/messages from Tcl/Tk data files
EXCLUDED_DATA_PATTERNS = ("tcl8.6\\demos", "tcl8.6\\msgs", "tk8.6\\demos", "tk8.6\\msgs",
                          "tcl8.6/demos", "tcl8.6/msgs", "tk8.6/demos", "tk8.6/msgs")
filtered_datas = [
    d for d in a.datas
    if not any(pat in d[0].lower() for pat in EXCLUDED_DATA_PATTERNS)
]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Platform-specific icon & version resources
icon_file = "assets/icon.ico" if sys.platform == "win32" else "assets/icon.png"
version_file = "version_info.txt" if sys.platform == "win32" else None

exe = EXE(
    pyz,
    a.scripts,
    filtered_binaries,
    a.zipfiles,
    filtered_datas,
    [],
    name="Klipwerk",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,     # No terminal window — pure GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    version=version_file,
)
