"""
ui/theme.py
Design system tokens, metrics, and theme values for Klipwerk.
Strictly adheres to:
- Surfaces: #0E1013 page background, #15181C for bars and panels, #1B1F24 for hover states
- Borders: 1px solid rgba(255,255,255,0.08) (solid #272A2E)
- Text: #E6E8EB primary, #9BA1A8 secondary, #6B7178 muted
- Accent: #4f46e5 reserved strictly for:
    1) The single primary button
    2) Progress bar fill
    3) Focus rings
    4) Selected sidebar indicator
  Accent stripped from everywhere else.
- Radius: 6px on controls (buttons, inputs), 10px on the window shell. Nothing else gets rounded.
- Font sizes: 12px for UI text, 11px for metadata, 10px for table headers.
- Font weights: only 400 and 500 exist. Removed every 600 and 700.
- All spacing values snap to a 4px grid.
- Control height is 28px everywhere (buttons, inputs, dropdowns).
- Hard rules: No gradients, no glows, no blur, no drop shadows. Nothing has both border-radius and box-shadow. No pill shapes.
"""

from __future__ import annotations

import sys
import os
import ctypes
from pathlib import Path
import customtkinter as ctk

def init_fonts() -> None:
    """Register custom bundled TTF fonts with Windows GDI so Tkinter/CustomTkinter can use them."""
    if os.name != "nt":
        return
    try:
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            fonts_dir = Path(sys._MEIPASS) / "assets" / "fonts"
        else:
            fonts_dir = Path(__file__).resolve().parent.parent / "assets" / "fonts"

        if fonts_dir.is_dir():
            for ttf in fonts_dir.glob("*.ttf"):
                ctypes.windll.gdi32.AddFontResourceExW(str(ttf.resolve()), 0x10, 0)
    except Exception:
        pass

init_fonts()

# ─────────────────────────────────────────────────────────────────────────────
# 1. Geometry & Radii Metrics
# ─────────────────────────────────────────────────────────────────────────────

# Radius: 6px on controls (buttons, inputs), 10px on the window shell, 4px thumbnails
RADIUS_WINDOW     = 10   # Window shell
RADIUS_MODAL      = 10   # Dialogs and modals
RADIUS_BUTTON     = 6    # Controls (buttons)
RADIUS_INPUT      = 6    # Controls (inputs)
RADIUS_CONTROL    = 6    # Generic controls
RADIUS_TOAST      = 6    # Controls / notifications
RADIUS_PILL       = 6    # Pill shapes: clamped to 6px
RADIUS_THUMB      = 4    # Media thumbnail container (4px radius)
RADIUS_CARD       = 0    # Panels & cards (no rounding)
RADIUS_DOCK       = 0    # Top search / URL dock (no rounding)

# Borders
BORDER_WIDTH      = 1
BORDER_WIDTH_CARD = 1
BORDER_WIDTH_BTN  = 1
BORDER_WIDTH_SUB  = 1

# Control height: 28-32px (32px main controls, 28px toolbar)
CONTROL_HEIGHT    = 32
HEIGHT_BUTTON     = 32
HEIGHT_INPUT      = 32
HEIGHT_DROPDOWN   = 28

# ─────────────────────────────────────────────────────────────────────────────
# 2. Spacing Grid (All spacing values snap to a 4px grid)
# ─────────────────────────────────────────────────────────────────────────────

SPACING_4  = 4
SPACING_8  = 8
SPACING_12 = 12
SPACING_16 = 16
SPACING_20 = 20
SPACING_24 = 24
SPACING_28 = 28
SPACING_32 = 32

# ─────────────────────────────────────────────────────────────────────────────
# 3. Typography Specs & Metrics
# ─────────────────────────────────────────────────────────────────────────────

# Font Family Tokens
FONT_WORDMARK = "Smooch Sans"        # Reserved exclusively for the app wordmark "Klipwerk"
FONT_UI       = "Plus Jakarta Sans"  # Functional UI text: labels, buttons, dialogs
FONT_MONO     = "JetBrains Mono"     # Numeric / technical: speeds, paths, percentages, versions

FONT_SIZE_HEADER    = 13  # Table column headers
FONT_SIZE_BUTTON    = 13  # Button labels
FONT_SIZE_METADATA  = 11  # Metadata
FONT_SIZE_UI        = 12  # UI text
FONT_SIZE_DURATION  = 9   # Thumbnail duration badge

FONT_WEIGHT_REGULAR = "normal"
FONT_WEIGHT_MEDIUM  = "normal"
FONT_WEIGHT_BOLD    = "bold"

def get_wordmark_font(size: int = 24, weight: str = "bold") -> ctk.CTkFont:
    """Smooch Sans - strictly for the app wordmark."""
    return ctk.CTkFont(family=FONT_WORDMARK, size=size, weight=weight)

def get_ui_font(size: int = 12, weight: str = "normal") -> ctk.CTkFont:
    """Plus Jakarta Sans - for general UI text."""
    return ctk.CTkFont(family=FONT_UI, size=size, weight=weight)

def get_mono_font(size: int = 11, weight: str = "normal") -> ctk.CTkFont:
    """JetBrains Mono - for numbers, speeds, timestamps, and paths."""
    return ctk.CTkFont(family=FONT_MONO, size=size, weight=weight)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Color Palette Tokens
# ─────────────────────────────────────────────────────────────────────────────

# Surfaces
BG_CANVAS         = ("#0F1113", "#0F1113")  # Page background
BG_PANEL          = ("#17191C", "#17191C")  # Panel/bar background
BG_SIDEBAR        = ("#131518", "#131518")  # Sidebar background
BG_ELEVATED       = ("#1B1E22", "#1B1E22")  # Elevated control background
CLAY_CARD_BG      = ("#17191C", "#17191C")
CLAY_CARD_HOVER   = ("#1B1F24", "#1B1F24")
CLAY_INPUT_BG     = ("#17191C", "#17191C")
HOVER_BG          = ("#1B1F24", "#1B1F24")
BG_HOVER          = ("#1B1F24", "#1B1F24")

# Borders
BORDER_COLOR      = ("#23262A", "#23262A")  # 1px solid rgba(255,255,255,0.08)
BORDER_STRONG     = ("#2C3035", "#2C3035")  # rgba(255,255,255,0.1)
SIDEBAR_BORDER    = ("#23262A", "#23262A")
CLAY_CARD_BORDER  = ("#23262A", "#23262A")
CLAY_INPUT_BORDER = ("#23262A", "#23262A")

# Text
TEXT_PRIMARY      = ("#E8E9EA", "#E8E9EA")  # Primary #E8E9EA
TEXT_SECONDARY    = ("#9A9DA1", "#9A9DA1")  # Secondary #9A9DA1
TEXT_MUTED        = ("#6C6F73", "#6C6F73")  # Muted #6C6F73
TEXT_ON_ACCENT    = ("#2A1B04", "#2A1B04")  # Text on amber accent

# Status colors (bright, for text/icons/progress fill)
STATUS_ACTIVE     = ("#6FD1DE", "#6FD1DE")
STATUS_QUEUED     = ("#F0B85E", "#F0B85E")
STATUS_DONE       = ("#6FD98F", "#6FD98F")
STATUS_FAILED     = ("#EF7A70", "#EF7A70")
COLOR_SUCCESS     = STATUS_DONE
COLOR_DANGER      = STATUS_FAILED
COLOR_WARNING     = STATUS_QUEUED

# Status row backgrounds (tinted washes, ~6-8% opacity)
ROW_BG_ACTIVE     = ("#161F22", "#161F22")  # rgba(111,209,222,0.07)
ROW_BG_QUEUED     = ("#1C1A14", "#1C1A14")  # rgba(232,163,61,0.06)
ROW_BG_DONE       = ("#151E19", "#151E19")  # rgba(111,217,143,0.06)
ROW_BG_FAILED     = ("#201A1A", "#201A1A")  # rgba(239,122,112,0.08)

# Row hover colors
ROW_HOVER_ACTIVE  = ("#1A2529", "#1A2529")
ROW_HOVER_QUEUED  = ("#221F17", "#221F17")
ROW_HOVER_DONE    = ("#19241E", "#19241E")
ROW_HOVER_FAILED  = ("#261E1E", "#261E1E")

# Accent: Amber #E8A33D
ACCENT_HUE               = "#E8A33D"
ACCENT_PRIMARY           = ("#E8A33D", "#E8A33D")
ACCENT_HOVER             = ("#D99632", "#D99632")
ACCENT_FOCUS             = ("#E8A33D", "#E8A33D")
ACCENT_SIDEBAR_INDICATOR = ("#E8A33D", "#E8A33D")
SIDEBAR_ACTIVE_BORDER    = ("#E8A33D", "#E8A33D")
SIDEBAR_ACTIVE_TEXT      = ("#E8A33D", "#E8A33D")

# 1) The single primary button (Add)
CLAY_PRIMARY = {
    "fg_color":      ("#E8A33D", "#E8A33D"),
    "hover_color":   ("#D99632", "#D99632"),
    "border_color":  ("#23262A", "#23262A"),
    "border_width":  0,
    "corner_radius": RADIUS_BUTTON,
    "text_color":    ("#2A1B04", "#2A1B04"),
    "height":        CONTROL_HEIGHT,
}

# 2) Elevated secondary control (Paste, Batch, Import, Quality)
ELEVATED_CONTROL = {
    "fg_color":      ("#1B1E22", "#1B1E22"),
    "hover_color":   ("#22262B", "#22262B"),
    "border_color":  ("#2C3035", "#2C3035"),
    "border_width":  1,
    "corner_radius": RADIUS_BUTTON,
    "text_color":    ("#C9CBCE", "#C9CBCE"),
    "height":        CONTROL_HEIGHT,
}

# Progress bar fill
CLAY_PROGRESS = {
    "height":         3,
    "corner_radius":  0,
    "progress_color": ("#6FD1DE", "#6FD1DE"),
    "fg_color":       ("#25282C", "#25282C"),
    "border_width":   0,
    "border_color":   ("#23262A", "#23262A"),
}

CLAY_SUCCESS = ELEVATED_CONTROL
CLAY_NEUTRAL = ELEVATED_CONTROL
CLAY_WARNING = ELEVATED_CONTROL
CLAY_DANGER = ELEVATED_CONTROL
CLAY_PILL_CHIP = ELEVATED_CONTROL

# ─────────────────────────────────────────────────────────────────────────────
# 5. Global Runtime Enforcement (ThemeManager, CTkFont, Controls)
# ─────────────────────────────────────────────────────────────────────────────

# Update CustomTkinter global theme defaults
try:
    tm = ctk.ThemeManager.theme
    if tm:
        tm["CTk"]["fg_color"] = ["#0E1013", "#0E1013"]
        tm["CTkToplevel"]["fg_color"] = ["#0E1013", "#0E1013"]

        tm["CTkFrame"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkFrame"]["top_fg_color"] = ["#15181C", "#15181C"]
        tm["CTkFrame"]["border_color"] = ["#272A2E", "#272A2E"]
        tm["CTkFrame"]["border_width"] = 1
        tm["CTkFrame"]["corner_radius"] = 0
        if "CTkScrollableFrame" in tm:
            tm["CTkScrollableFrame"]["label_fg_color"] = ["#15181C", "#15181C"]

        tm["CTkButton"]["corner_radius"] = 6
        tm["CTkButton"]["border_width"] = 1
        tm["CTkButton"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkButton"]["hover_color"] = ["#1B1F24", "#1B1F24"]
        tm["CTkButton"]["border_color"] = ["#272A2E", "#272A2E"]
        tm["CTkButton"]["text_color"] = ["#E6E8EB", "#E6E8EB"]

        tm["CTkEntry"]["corner_radius"] = 6
        tm["CTkEntry"]["border_width"] = 1
        tm["CTkEntry"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkEntry"]["border_color"] = ["#272A2E", "#272A2E"]
        tm["CTkEntry"]["text_color"] = ["#E6E8EB", "#E6E8EB"]
        tm["CTkEntry"]["placeholder_text_color"] = ["#6B7178", "#6B7178"]

        tm["CTkOptionMenu"]["corner_radius"] = 6
        tm["CTkOptionMenu"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkOptionMenu"]["button_color"] = ["#15181C", "#15181C"]
        tm["CTkOptionMenu"]["button_hover_color"] = ["#1B1F24", "#1B1F24"]
        tm["CTkOptionMenu"]["text_color"] = ["#E6E8EB", "#E6E8EB"]

        tm["CTkComboBox"]["corner_radius"] = 6
        tm["CTkComboBox"]["border_width"] = 1
        tm["CTkComboBox"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkComboBox"]["border_color"] = ["#272A2E", "#272A2E"]
        tm["CTkComboBox"]["button_color"] = ["#15181C", "#15181C"]
        tm["CTkComboBox"]["button_hover_color"] = ["#1B1F24", "#1B1F24"]
        tm["CTkComboBox"]["text_color"] = ["#E6E8EB", "#E6E8EB"]

        tm["CTkProgressBar"]["corner_radius"] = 0
        tm["CTkProgressBar"]["border_width"] = 0
        tm["CTkProgressBar"]["fg_color"] = ["#15181C", "#15181C"]
        tm["CTkProgressBar"]["progress_color"] = ["#4f46e5", "#4f46e5"]

        tm["CTkLabel"]["text_color"] = ["#E6E8EB", "#E6E8EB"]
        tm["DropdownMenu"]["fg_color"] = ["#15181C", "#15181C"]
        tm["DropdownMenu"]["hover_color"] = ["#1B1F24", "#1B1F24"]
        tm["DropdownMenu"]["text_color"] = ["#E6E8EB", "#E6E8EB"]
except Exception:
    pass

# ─────────────────────────────────────────────────────────────────────────────
# Dynamic Font Size Adjuster & Enforcement
# ─────────────────────────────────────────────────────────────────────────────
import weakref

_CURRENT_BASE_FONT_SIZE = 12
_FONT_REGISTRY: list[weakref.ref] = []

def _register_font(font: ctk.CTkFont, base_s: int) -> None:
    font._theme_base_size = base_s
    def _remover(r):
        try:
            _FONT_REGISTRY.remove(r)
        except (ValueError, Exception):
            pass
    _FONT_REGISTRY.append(weakref.ref(font, _remover))

def set_base_font_size(size: int) -> None:
    """Dynamically updates the base UI font size across all active CTkFont instances."""
    global _CURRENT_BASE_FONT_SIZE
    try:
        size = int(size)
    except (ValueError, TypeError):
        size = 12
    _CURRENT_BASE_FONT_SIZE = max(10, min(18, size))
    offset = _CURRENT_BASE_FONT_SIZE - 12

    for r in list(_FONT_REGISTRY):
        font = r()
        if font is not None:
            base_s = getattr(font, "_theme_base_size", 12)
            try:
                scaled = max(8, base_s + offset)
                font.configure(size=scaled)
            except Exception:
                pass

def get_base_font_size() -> int:
    return _CURRENT_BASE_FONT_SIZE

_orig_font_init = ctk.CTkFont.__init__
def _patched_font_init(self, *args, **kwargs):
    # Route font families to the typography system
    fam = kwargs.get("family")
    if not fam or fam in ("Segoe UI", "system-ui", "Arial", "sans-serif"):
        kwargs["family"] = FONT_UI
    elif fam in ("Consolas", "Courier New", "Courier", "monospace"):
        kwargs["family"] = FONT_MONO

    base_s = 12
    if "size" in kwargs and kwargs["size"] is not None:
        base_s = kwargs["size"]
    offset = _CURRENT_BASE_FONT_SIZE - 12
    kwargs["size"] = max(8, base_s + offset)
    _orig_font_init(self, *args, **kwargs)
    _register_font(self, base_s)

ctk.CTkFont.__init__ = _patched_font_init

# Enforce control defaults (readable high-contrast text and clean dark styling)
_orig_entry_init = ctk.CTkEntry.__init__
def _patched_entry_init(self, *args, **kwargs):
    kwargs.setdefault("text_color", ("#E8E9EA", "#E8E9EA"))
    kwargs.setdefault("placeholder_text_color", ("#7A7E85", "#7A7E85"))
    kwargs.setdefault("fg_color", ("#17191C", "#17191C"))
    kwargs.setdefault("border_color", ("#262A2E", "#262A2E"))
    kwargs.setdefault("corner_radius", 6)
    kwargs.setdefault("height", 32)
    return _orig_entry_init(self, *args, **kwargs)
ctk.CTkEntry.__init__ = _patched_entry_init

_orig_tb_init = ctk.CTkTextbox.__init__
def _patched_tb_init(self, *args, **kwargs):
    kwargs.setdefault("text_color", ("#E8E9EA", "#E8E9EA"))
    kwargs.setdefault("fg_color", ("#17191C", "#17191C"))
    kwargs.setdefault("border_color", ("#262A2E", "#262A2E"))
    kwargs.setdefault("corner_radius", 6)
    return _orig_tb_init(self, *args, **kwargs)
ctk.CTkTextbox.__init__ = _patched_tb_init

_orig_opt_init = ctk.CTkOptionMenu.__init__
def _patched_opt_init(self, *args, **kwargs):
    kwargs.setdefault("text_color", ("#E8E9EA", "#E8E9EA"))
    kwargs.setdefault("dropdown_text_color", ("#E8E9EA", "#E8E9EA"))
    kwargs.setdefault("corner_radius", 6)
    return _orig_opt_init(self, *args, **kwargs)
ctk.CTkOptionMenu.__init__ = _patched_opt_init

_orig_combo_init = ctk.CTkComboBox.__init__
def _patched_combo_init(self, *args, **kwargs):
    kwargs.setdefault("text_color", ("#E8E9EA", "#E8E9EA"))
    kwargs.setdefault("corner_radius", 6)
    return _orig_combo_init(self, *args, **kwargs)
ctk.CTkComboBox.__init__ = _patched_combo_init

_orig_btn_init = ctk.CTkButton.__init__
def _patched_btn_init(self, *args, **kwargs):
    kwargs.setdefault("corner_radius", 6)
    return _orig_btn_init(self, *args, **kwargs)
ctk.CTkButton.__init__ = _patched_btn_init

# Frames default to 0 corner radius unless explicitly set
_orig_frame_init = ctk.CTkFrame.__init__
def _patched_frame_init(self, *args, **kwargs):
    kwargs.setdefault("corner_radius", 0)
    return _orig_frame_init(self, *args, **kwargs)
ctk.CTkFrame.__init__ = _patched_frame_init

_orig_scroll_init = ctk.CTkScrollableFrame.__init__
def _patched_scroll_init(self, *args, **kwargs):
    kwargs.setdefault("corner_radius", 0)
    return _orig_scroll_init(self, *args, **kwargs)
ctk.CTkScrollableFrame.__init__ = _patched_scroll_init

_orig_prog_init = ctk.CTkProgressBar.__init__
def _patched_prog_init(self, *args, **kwargs):
    kwargs.setdefault("corner_radius", 0)
    return _orig_prog_init(self, *args, **kwargs)
ctk.CTkProgressBar.__init__ = _patched_prog_init
