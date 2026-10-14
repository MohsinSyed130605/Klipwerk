"""
ui/settings_panel.py
Full-featured settings form with tactile Claymorphic styling,
clay input cards, sliders, switches, and pill action buttons.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk

from core.downloader import QUALITY_OPTIONS, VIDEO_FORMATS
from ui.theme import (
    RADIUS_CARD,
    RADIUS_PILL,
    RADIUS_BUTTON,
    BORDER_WIDTH_CARD,
    BORDER_WIDTH_SUB,
    CLAY_CARD_BG,
    CLAY_CARD_BORDER,
    CLAY_INPUT_BG,
    CLAY_INPUT_BORDER,
    CLAY_PRIMARY,
    CLAY_NEUTRAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_UI,
    FONT_MONO,
    set_base_font_size,
)
from ui.icons import get_icon


class SettingsPanel(ctk.CTkFrame):
    """
    Tactile Claymorphic settings form. Calls on_save(dict) with the new settings when saved.
    """

    def __init__(self, parent, *, settings: dict, on_save, **kwargs):
        super().__init__(
            parent,
            corner_radius=RADIUS_CARD,
            fg_color=CLAY_CARD_BG,
            border_width=BORDER_WIDTH_CARD,
            border_color=CLAY_CARD_BORDER,
            **kwargs,
        )
        self._settings = dict(settings)
        self._on_save  = on_save

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()

    # ------------------------------------------------------------------
    def _build(self) -> None:
        ctk.CTkLabel(
            self,
            text="Settings",
            font=ctk.CTkFont(family=FONT_UI, size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 12))

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(
            self, corner_radius=12, fg_color="transparent"
        )
        self._scroll.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self._scroll.grid_columnconfigure(0, weight=1)

        r = 0

        # ── Downloads ──────────────────────────────────────────────────
        r = self._section("Downloads", r)

        r = self._label("Output folder", r)
        dir_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        dir_row.grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 12))
        dir_row.grid_columnconfigure(0, weight=1)
        r += 1

        self._dir_entry = ctk.CTkEntry(
            dir_row,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            height=36,
            corner_radius=RADIUS_BUTTON,
            fg_color=CLAY_INPUT_BG,
            border_width=BORDER_WIDTH_SUB,
            border_color=CLAY_INPUT_BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        self._dir_entry.insert(0, self._settings.get("output_dir", str(Path.home() / "Downloads")))
        self._dir_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ctk.CTkButton(
            dir_row,
            text=" Browse…",
            image=get_icon("folder-open", size=16, color=CLAY_NEUTRAL["text_color"]),
            compound="left",
            width=106,
            height=36,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            fg_color=CLAY_NEUTRAL["fg_color"],
            hover_color=CLAY_NEUTRAL["hover_color"],
            border_color=CLAY_NEUTRAL["border_color"],
            border_width=CLAY_NEUTRAL["border_width"],
            text_color=CLAY_NEUTRAL["text_color"],
            command=self._browse_dir,
        ).grid(row=0, column=1)

        r = self._label("Max simultaneous downloads", r)
        conc = ctk.CTkFrame(self._scroll, fg_color="transparent")
        conc.grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 14))
        r += 1

        self._conc_var = ctk.IntVar(value=self._settings.get("max_concurrent", 3))
        self._conc_lbl = ctk.CTkLabel(
            conc,
            text=str(self._conc_var.get()),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
            width=28,
        )
        ctk.CTkSlider(
            conc,
            from_=1,
            to=5,
            number_of_steps=4,
            variable=self._conc_var,
            width=220,
            progress_color=CLAY_PRIMARY["fg_color"],
            button_color=CLAY_PRIMARY["border_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
            command=lambda v: self._conc_lbl.configure(text=str(int(v))),
        ).pack(side="left")
        self._conc_lbl.pack(side="left", padx=10)
        ctk.CTkLabel(
            conc, text="(1 – 5 concurrent threads)", font=ctk.CTkFont(size=11), text_color=TEXT_SECONDARY
        ).pack(side="left")

        r = self._label("Default quality", r)
        self._quality_var = ctk.StringVar(value=self._settings.get("default_quality", "Best (auto)"))
        ctk.CTkOptionMenu(
            self._scroll,
            variable=self._quality_var,
            values=QUALITY_OPTIONS,
            width=220,
            height=34,
            corner_radius=RADIUS_BUTTON,
            button_color=CLAY_PRIMARY["fg_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 14))
        r += 1

        r = self._label("Default video container", r)
        self._format_var = ctk.StringVar(value=self._settings.get("default_format", "MP4"))
        ctk.CTkOptionMenu(
            self._scroll,
            variable=self._format_var,
            values=VIDEO_FORMATS,
            width=140,
            height=34,
            corner_radius=RADIUS_BUTTON,
            button_color=CLAY_PRIMARY["fg_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 14))
        r += 1

        # Duplicate links toggle
        self._dup_var = ctk.BooleanVar(value=self._settings.get("allow_duplicates", False))
        ctk.CTkSwitch(
            self._scroll,
            text="Allow duplicate video URLs in the queue",
            variable=self._dup_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            progress_color=CLAY_PRIMARY["fg_color"],
            onvalue=True,
            offvalue=False,
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 10))
        r += 1

        # Add metadata & artwork toggle
        self._meta_var = ctk.BooleanVar(value=self._settings.get("add_metadata", True))
        ctk.CTkSwitch(
            self._scroll,
            text="Embed metadata, contributing artist tags & album artwork",
            variable=self._meta_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            progress_color=CLAY_PRIMARY["fg_color"],
            onvalue=True,
            offvalue=False,
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 16))
        r += 1

        # ── Appearance ─────────────────────────────────────────────────
        r = self._section("Appearance", r)

        # Font size adjuster
        r = self._label("Font size", r)
        self._font_options = ["Small (10px)", "Default (12px)", "Large (14px)", "Extra Large (16px)"]
        self._font_map = {
            10: "Small (10px)",
            12: "Default (12px)",
            14: "Large (14px)",
            16: "Extra Large (16px)",
        }
        self._rev_font_map = {v: k for k, v in self._font_map.items()}
        current_sz = self._settings.get("font_size", 12)
        self._font_var = ctk.StringVar(value=self._font_map.get(current_sz, "Default (12px)"))

        def _on_font_select(val: str):
            sz = self._rev_font_map.get(val, 12)
            self._settings["font_size"] = sz
            set_base_font_size(sz)

        ctk.CTkSegmentedButton(
            self._scroll,
            variable=self._font_var,
            values=self._font_options,
            command=_on_font_select,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            height=32,
            corner_radius=RADIUS_BUTTON,
            selected_color=CLAY_PRIMARY["fg_color"],
            selected_hover_color=CLAY_PRIMARY["hover_color"],
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 16))
        r += 1

        # ── Clipboard Watcher ──────────────────────────────────────────
        r = self._section("Clipboard Watcher", r)
        self._clip_var = ctk.BooleanVar(value=self._settings.get("clipboard_watcher", True))
        ctk.CTkSwitch(
            self._scroll,
            text="Automatically detect video URLs copied to clipboard",
            variable=self._clip_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            progress_color=CLAY_PRIMARY["fg_color"],
            onvalue=True,
            offvalue=False,
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 16))
        r += 1

        # ── Advanced ───────────────────────────────────────────────────
        r = self._section("Advanced", r)

        # Hardware acceleration
        r = self._label("Hardware acceleration (GPU recoding)", r)
        hw_labels = {
            "auto": "Auto (Detect best GPU)",
            "none": "None (CPU Software)",
            "cuda": "NVIDIA CUDA / NVENC",
            "qsv":  "Intel QuickSync (QSV)",
            "amf":  "AMD AMF",
        }
        self._hw_map = hw_labels
        self._hw_rev_map = {v: k for k, v in hw_labels.items()}
        current_hw = self._settings.get("hw_accel", "auto")
        self._hw_var = ctk.StringVar(value=hw_labels.get(current_hw, "Auto (Detect best GPU)"))
        ctk.CTkOptionMenu(
            self._scroll,
            variable=self._hw_var,
            values=list(hw_labels.values()),
            width=240,
            height=34,
            corner_radius=RADIUS_BUTTON,
            button_color=CLAY_PRIMARY["fg_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
        ).grid(row=r, column=0, sticky="w", padx=24, pady=(0, 14))
        r += 1

        # Custom downloader arguments
        r = self._label("Custom yt-dlp arguments (e.g. --proxy=... --cookies=...)", r)
        self._args_entry = ctk.CTkEntry(
            self._scroll,
            height=36,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(size=12),
            fg_color=CLAY_INPUT_BG,
            border_width=BORDER_WIDTH_SUB,
            border_color=CLAY_INPUT_BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            placeholder_text="e.g. --proxy=http://127.0.0.1:8080 --no-check-certificate",
        )
        self._args_entry.insert(0, self._settings.get("custom_args", ""))
        self._args_entry.grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 14))
        r += 1

        r = self._label("ffmpeg executable path  (leave blank to auto-detect on PATH)", r)
        self._ffmpeg_entry = ctk.CTkEntry(
            self._scroll,
            height=36,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(size=12),
            fg_color=CLAY_INPUT_BG,
            border_width=BORDER_WIDTH_SUB,
            border_color=CLAY_INPUT_BORDER,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            placeholder_text="Auto-detected on PATH (or enter custom binary path)",
        )
        self._ffmpeg_entry.insert(0, self._settings.get("ffmpeg_path", ""))
        self._ffmpeg_entry.grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 6))
        r += 1

        ctk.CTkLabel(
            self._scroll,
            text="ffmpeg is required for stream merging and audio extraction. Auto-downloaded if missing.",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_SECONDARY,
            anchor="w",
            wraplength=520,
        ).grid(row=r, column=0, sticky="ew", padx=24, pady=(0, 18))
        r += 1

        # ── Save ───────────────────────────────────────────────────────
        save_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        save_row.grid(row=r, column=0, sticky="ew", padx=24, pady=(6, 24))
        r += 1

        ctk.CTkButton(
            save_row,
            text=" Save Preferences",
            image=get_icon("floppy-disk", size=18, color=CLAY_PRIMARY["text_color"]),
            compound="left",
            width=180,
            height=40,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=CLAY_PRIMARY["fg_color"],
            hover_color=CLAY_PRIMARY["hover_color"],
            border_color=CLAY_PRIMARY["border_color"],
            border_width=CLAY_PRIMARY["border_width"],
            text_color=CLAY_PRIMARY["text_color"],
            command=self._save,
        ).pack(side="left")

        self._saved_lbl = ctk.CTkLabel(
            save_row,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=("#059669", "#34d399"),
        )
        self._saved_lbl.pack(side="left", padx=14)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _section(self, text: str, row: int) -> int:
        f = ctk.CTkFrame(self._scroll, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=16, pady=(12, 6))
        f.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            f,
            text=text,
            font=ctk.CTkFont(family=FONT_UI, size=14, weight="bold"),
            text_color=("#E8A33D", "#E8A33D"),
        ).grid(row=0, column=0, sticky="w", padx=6)
        ctk.CTkFrame(
            f, height=1, fg_color=("#2C3035", "#2C3035"),
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))
        return row + 1

    def _label(self, text: str, row: int) -> int:
        ctk.CTkLabel(
            self._scroll,
            text=text,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).grid(row=row, column=0, sticky="ew", padx=24, pady=(4, 4))
        return row + 1

    def _browse_dir(self) -> None:
        path = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self._dir_entry.get() or str(Path.home()),
        )
        if path:
            self._dir_entry.delete(0, "end")
            self._dir_entry.insert(0, path)

    def _save(self) -> None:
        hw_choice = self._hw_var.get()
        hw_accel = self._hw_rev_map.get(hw_choice, "auto")
        new = {
            "output_dir":        self._dir_entry.get().strip() or str(Path.home() / "Downloads"),
            "max_concurrent":    int(self._conc_var.get()),
            "default_quality":   self._quality_var.get(),
            "default_format":    self._format_var.get(),
            "theme":             "dark",
            "font_size":         self._rev_font_map.get(self._font_var.get(), 12),
            "clipboard_watcher": self._clip_var.get(),
            "ffmpeg_path":       self._ffmpeg_entry.get().strip(),
            "allow_duplicates":  self._dup_var.get(),
            "add_metadata":      self._meta_var.get(),
            "hw_accel":          hw_accel,
            "custom_args":       self._args_entry.get().strip(),
        }
        self._on_save(new)
        self._saved_lbl.configure(text="✓  Preferences Saved!")
        self.after(3000, lambda: self._saved_lbl.configure(text=""))
