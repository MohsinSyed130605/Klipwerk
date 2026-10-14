"""
core/updater.py
Background yt-dlp version checker and one-click updater.
Works both in normal Python mode and as a PyInstaller-bundled .exe.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import urllib.request
from typing import Callable

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"

# True when running from a PyInstaller bundle (frozen exe)
_IS_FROZEN = getattr(sys, "frozen", False)


def parse_version(v_str: str) -> tuple[int, ...]:
    """Parse version string like '2026.08.19' or '2026.8.19' into comparable integer tuple."""
    parts = []
    for chunk in v_str.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        if digits:
            parts.append(int(digits))
    return tuple(parts)


def get_installed_version() -> str:
    try:
        import yt_dlp.version
        return yt_dlp.version.__version__
    except Exception:
        return "unknown"


def _fetch_latest() -> str:
    req = urllib.request.Request(PYPI_URL, headers={"User-Agent": "Klipwerk/1.0"})
    with urllib.request.urlopen(req, timeout=6) as resp:
        data = json.load(resp)
    return data["info"]["version"]


def _find_pip_python() -> list[str] | None:
    """
    Locate a Python interpreter that can run pip.
    When frozen as an .exe, sys.executable is the exe itself — not Python.
    We look for python/python3 on the system PATH instead.
    """
    if not _IS_FROZEN:
        # Normal dev mode: use the same interpreter
        return [sys.executable, "-m", "pip"]

    # Frozen: find system Python
    for name in ("python", "python3", "py"):
        path = shutil.which(name)
        if path:
            try:
                # Quick sanity check
                cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
                subprocess.check_call(
                    [path, "-c", "import pip"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    creationflags=cflags,
                )
                return [path, "-m", "pip"]
            except Exception:
                continue

    return None  # No Python found — update not possible


def check_update_async(
    callback: Callable[[str, str, bool], None]
) -> None:
    """
    Fire-and-forget version check.
    Calls callback(current, latest, update_available) on the background thread.
    The caller must route the result back to the main thread via a queue.
    """
    def _run():
        try:
            current = get_installed_version()
            latest = _fetch_latest()
            if current != "unknown":
                cur_tuple = parse_version(current)
                lat_tuple = parse_version(latest)
                needs = lat_tuple > cur_tuple
            else:
                needs = False
            callback(current, latest, needs)
        except Exception:
            pass  # silently ignore network errors

    threading.Thread(target=_run, daemon=True, name="ytdlp-update-check").start()


def update_ytdlp_async(
    on_done: Callable[[bool, str], None]
) -> None:
    """
    Upgrade yt-dlp via pip in a background thread.
    Calls on_done(success, new_version).

    When running as a bundled .exe the bundled yt-dlp cannot be hot-patched;
    we update the system-installed copy instead so the next run picks it up.
    If no system Python is found the update silently fails with a clear message.
    """
    def _run():
        if _IS_FROZEN:
            try:
                import webbrowser
                webbrowser.open("https://github.com/MohsinSyed130605/Klipwerk/releases")
                on_done(True, "latest release page opened")
            except Exception as exc:
                on_done(False, str(exc))
            return

        pip_cmd = _find_pip_python()
        if pip_cmd is None:
            on_done(
                False,
                "No system Python found. Install Python from python.org to enable updates."
            )
            return
        try:
            cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0
            subprocess.check_call(
                pip_cmd + ["install", "-U", "yt-dlp", "-q"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=cflags,
            )
            new_ver = get_installed_version()
            on_done(True, new_ver)
        except Exception as exc:
            on_done(False, str(exc))

    threading.Thread(target=_run, daemon=True, name="ytdlp-updater").start()
