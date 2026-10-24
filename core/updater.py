"""Version checker and updater for yt-dlp."""
from __future__ import annotations

import json
import sys
import threading
import urllib.request
from typing import Callable

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
_IS_FROZEN = getattr(sys, "frozen", False)


def parse_version(v_str: str) -> tuple[int, ...]:
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
    Open the official Klipwerk release channel in a background thread.
    Calls on_done(success, message).
    """
    def _run():
        try:
            import webbrowser
            webbrowser.open("https://github.com/MohsinSyed130605/Klipwerk/releases")
            if _IS_FROZEN:
                on_done(True, "latest release page opened")
            else:
                on_done(True, "release page opened (use pip manually for source installs)")
        except Exception as exc:
            on_done(False, str(exc))

    threading.Thread(target=_run, daemon=True, name="ytdlp-updater").start()
