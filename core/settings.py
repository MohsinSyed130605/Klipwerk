"""
core/settings.py
Persistent user settings stored in OS-appropriate config directory:
  Windows: %APPDATA%/Klipwerk/settings.json
  Linux:   $XDG_CONFIG_HOME/Klipwerk/settings.json (~/.config/Klipwerk/settings.json)
"""

import json
import os
import sys
from pathlib import Path

DEFAULTS: dict = {
    "output_dir": str(Path.home() / "Downloads"),
    "theme": "dark",          # "dark" | "light" | "system"
    "max_concurrent": 3,      # 1-5
    "default_quality": "Best (auto)",
    "default_format": "MP4",
    "clipboard_watcher": True,
    "ffmpeg_path": "",        # empty = auto-detect on PATH
    "allow_duplicates": False,
    "add_metadata": True,     # embed metadata & artwork
    "hw_accel": "auto",       # "auto" | "none" | "cuda" | "qsv" | "amf"
    "custom_args": "",        # custom yt-dlp arguments
    "font_size": 12,          # base UI font size (10-18)
}


def _get_config_dir(app_name: str = "Klipwerk") -> Path:
    """Return OS-appropriate configuration directory for the given app name."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        if base:
            return Path(base) / app_name
    else:
        # Linux (XDG Base Directory specification)
        xdg = os.environ.get("XDG_CONFIG_HOME")
        if xdg:
            return Path(xdg) / app_name
        return Path.home() / ".config" / app_name


def _settings_path() -> Path:
    d = _get_config_dir("Klipwerk")
    d.mkdir(parents=True, exist_ok=True)
    return d / "settings.json"


def load() -> dict:
    """Return merged settings (file values override defaults)."""
    path = _settings_path()
    result = dict(DEFAULTS)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                result.update(data)
        except Exception:
            pass

    # Sanitize and validate constraints
    try:
        result["max_concurrent"] = max(1, min(5, int(result.get("max_concurrent", 3))))
    except (ValueError, TypeError):
        result["max_concurrent"] = DEFAULTS["max_concurrent"]

    try:
        result["font_size"] = max(10, min(18, int(result.get("font_size", 12))))
    except (ValueError, TypeError):
        result["font_size"] = DEFAULTS["font_size"]

    if not result.get("output_dir") or not isinstance(result.get("output_dir"), str):
        result["output_dir"] = DEFAULTS["output_dir"]

    return result


def save(settings: dict) -> None:
    """Persist settings to disk atomically."""
    path = _settings_path()
    tmp_path = path.with_suffix(".tmp")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, path)
    except Exception:
        # Fallback to direct write if replace fails
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass

