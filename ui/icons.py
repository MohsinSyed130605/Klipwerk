"""
ui/icons.py
Centralized Phosphor Icon loader, runtime SVG rasterizer, and in-memory cache.
- Uses high-performance Rust-based `resvg-py` for pixel-perfect runtime rasterization.
- Automatically handles high-DPI scaling (2x rasterization).
- Renders Bold weight for UI controls (<24px) and Duotone for large placeholders.
- Dynamically tints icons using the app's amber accent (#E8A33D) or neutral UI tones.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Dict, Tuple, Union

from PIL import Image
import customtkinter as ctk
import resvg_py

from ui.theme import ACCENT_HUE, TEXT_SECONDARY, TEXT_MUTED, TEXT_PRIMARY, STATUS_FAILED, STATUS_DONE

# Cache for rendered PIL.Image instances: (icon_name, width, height, color_hex) -> PIL.Image
_PIL_CACHE: Dict[Tuple[str, int, int, str], Image.Image] = {}

# Cache for raw SVG string templates
_SVG_CACHE: Dict[str, str] = {}


def _get_icons_dir() -> Path:
    """Resolve the icons directory both in development and PyInstaller bundled environment."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS) / "assets" / "icons_svg"
    else:
        base = Path(__file__).resolve().parent.parent / "assets" / "icons_svg"
    return base


def _load_svg_text(name: str) -> str:
    """Load and cache the raw SVG source template."""
    clean_name = name.removesuffix(".svg")
    if clean_name in _SVG_CACHE:
        return _SVG_CACHE[clean_name]

    icons_dir = _get_icons_dir()
    svg_path = icons_dir / f"{clean_name}.svg"

    if not svg_path.is_file():
        # Fallback check for alternate naming
        for candidate in icons_dir.glob(f"*{clean_name}*.svg"):
            svg_path = candidate
            break

    if not svg_path.is_file():
        raise FileNotFoundError(f"Phosphor SVG icon '{clean_name}' not found at {icons_dir}")

    text = svg_path.read_text(encoding="utf-8")
    _SVG_CACHE[clean_name] = text
    return text


def get_icon(
    name: str,
    size: Union[Tuple[int, int], int] = (18, 18),
    color: Union[str, Tuple[str, str], None] = None,
) -> ctk.CTkImage:
    """
    Retrieve or rasterize a Phosphor icon as a ctk.CTkImage.
    
    :param name: Base icon name (e.g. 'tray', 'film-strip', 'gear-six', etc.)
    :param size: Dimension in pixels as (width, height) or single int (e.g. 20 -> (20, 20)).
    :param color: Color hex string (e.g. '#E8A33D') or tuple. Defaults to app accent ACCENT_HUE.
    """
    if isinstance(size, int):
        w, h = size, size
    else:
        w, h = size

    # Resolve color hex
    if color is None:
        color_hex = ACCENT_HUE
    elif isinstance(color, (tuple, list)):
        color_hex = color[0]
    else:
        color_hex = str(color)

    cache_key = (name, w, h, color_hex)
    if cache_key in _PIL_CACHE:
        pil_img = _PIL_CACHE[cache_key]
    else:
        try:
            raw_svg = _load_svg_text(name)

            # Tint the SVG by replacing Phosphor's currentColor with our resolved color
            # In duotone icons like film-strip, opacity="0.2" layers remain intact
            colored_svg = raw_svg.replace("currentColor", color_hex)

            # 2x rasterization for crystal-clear rendering on Retina / Windows 125%/150%/200% displays
            scale = 2
            raster_w = max(16, int(w * scale))
            raster_h = max(16, int(h * scale))

            png_bytes = resvg_py.svg_to_bytes(colored_svg, width=raster_w, height=raster_h)
            pil_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            _PIL_CACHE[cache_key] = pil_img

        except Exception:
            pil_img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            _PIL_CACHE[cache_key] = pil_img

    return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))


def get_accent_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with the app accent color (#E8A33D)."""
    return get_icon(name, size=size, color=ACCENT_HUE)


def get_neutral_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with neutral secondary text color (#9A9DA1)."""
    return get_icon(name, size=size, color=TEXT_SECONDARY[0])


def get_muted_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with muted text color (#6C6F73)."""
    return get_icon(name, size=size, color=TEXT_MUTED[0])


def get_primary_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with primary text color (#E8E9EA)."""
    return get_icon(name, size=size, color=TEXT_PRIMARY[0])


def get_danger_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with danger status color (e.g. for failed/retry)."""
    return get_icon(name, size=size, color=STATUS_FAILED[0])


def get_success_icon(name: str, size: Union[Tuple[int, int], int] = 18) -> ctk.CTkImage:
    """Return an icon tinted with success status color (e.g. for done)."""
    return get_icon(name, size=size, color=STATUS_DONE[0])
