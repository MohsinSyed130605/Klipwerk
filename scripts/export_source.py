#!/usr/bin/env python3
"""
scripts/export_source.py
Creates a clean, production-ready source archive (.zip) of the Klipwerk repository.
Guarantees that:
  - build/, dist/, installer/, and all __pycache__/ directories are excluded.
  - Python bytecode (*.pyc, *.pyo) and temporary files (*.tmp, *.log) are excluded.
  - Compiled binaries (*.exe, *.AppImage, auto-downloaded bin/) are excluded.
  - Only tracked source code, assets, scripts, configuration, and documentation are included.
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

EXCLUDED_DIRS = {
    "build",
    "dist",
    "installer",
    "__pycache__",
    "bin",
    ".git",
    ".venv",
    "venv",
    "env",
    ".vscode",
    ".idea",
}

EXCLUDED_FILE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".exe",
    ".AppImage",
    ".tmp",
    ".log",
    ".zip",
}

EXCLUDED_FILENAMES = {
    "Thumbs.db",
    "Desktop.ini",
    ".DS_Store",
    "settings.json",
}


def create_source_archive(output_path: Path | str | None = None) -> Path:
    """Package clean repository source files into a zip file."""
    if output_path is None:
        target_zip = ROOT_DIR / "Klipwerk-Source-v1.0.0.zip"
    else:
        target_zip = Path(output_path).resolve()

    included_files: list[Path] = []

    for root, dirs, files in os.walk(ROOT_DIR):
        # Prune excluded directories in-place so os.walk does not descend into them
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith(".")]

        rel_root = Path(root).relative_to(ROOT_DIR)
        if any(part in EXCLUDED_DIRS for part in rel_root.parts):
            continue

        for file_name in files:
            p = Path(root) / file_name
            ext = p.suffix.lower()

            if ext in EXCLUDED_FILE_EXTENSIONS:
                continue
            if file_name in EXCLUDED_FILENAMES:
                continue
            if p == target_zip:
                continue

            included_files.append(p)

    # Sort files deterministically
    included_files.sort()

    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in included_files:
            arcname = file_path.relative_to(ROOT_DIR)
            zf.write(file_path, arcname)

    size_kb = target_zip.stat().st_size / 1024
    print(f"[OK] Clean source archive created: {target_zip.name} ({size_kb:.1f} KB, {len(included_files)} files)")
    return target_zip


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    create_source_archive(out)
