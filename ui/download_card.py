"""Queue card component for video downloads and format controls."""

from __future__ import annotations

import io
import json
import os
import re
import ssl
import subprocess
import sys
import threading
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable

import customtkinter as ctk
from PIL import Image, ImageOps

from core.downloader import fetch_info, fetch_quick_meta, AUDIO_QUALITIES, QUALITY_OPTIONS, VIDEO_FORMATS, sanitize_filename
from ui.theme import (
    BORDER_COLOR,
    ACCENT_PRIMARY,
    STATUS_ACTIVE,
    STATUS_QUEUED,
    STATUS_DONE,
    STATUS_FAILED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_UI,
    FONT_MONO,
)
from ui.icons import get_icon

FORMAT_PRESETS = [
    "Convert to MP4",
    "Convert to WebM",
    "Convert to AVI",
    "Merge to MKV",
    "Convert to MP3",
    "Convert to M4A",
    "Convert to WAV",
    "Convert to FLAC",
    "Convert to Ogg Vorbis",
    "Best Direct Download",
    "Best Audio-only Download",
    "Custom Download...",
]


def _map_preset_to_format(preset: str) -> tuple[str, str]:
    if "Convert to MP4" in preset:
        return ("Best (auto)", "MP4")
    if "Convert to WebM" in preset:
        return ("Best (auto)", "WebM")
    if "Convert to AVI" in preset:
        return ("Best (auto)", "AVI")
    if "Merge to MKV" in preset:
        return ("Best (auto)", "MKV")
    if "Convert to MP3" in preset:
        return ("MP3 Audio", "MP3")
    if "Convert to M4A" in preset:
        return ("M4A Audio", "M4A")
    if "Convert to WAV" in preset:
        return ("WAV Audio", "WAV")
    if "Convert to FLAC" in preset:
        return ("FLAC Audio", "FLAC")
    if "Convert to Ogg Vorbis" in preset:
        return ("Opus Audio", "Ogg")
    if "Best Direct Download" in preset:
        return ("Best (auto)", "Best")
    if "Best Audio-only Download" in preset:
        return ("Best Audio (auto)", "Best")
    return ("Best (auto)", "MP4")


class DownloadCard(ctk.CTkFrame):
    """
    Vividl-inspired download queue card:
    Thumbnail | [Title + ✏ / Dropdown + 🔧 + ℹ + Duration] | [Metrics + ⭳ / 🗑]
    """

    def __init__(
        self,
        parent,
        *,
        card_id: str,
        url: str,
        settings: dict,
        update_queue,
        on_download: Callable,
        on_remove: Callable,
        on_cancel: Callable | None = None,
        **kwargs,
    ):
        super().__init__(
            parent,
            corner_radius=6,
            height=72,
            fg_color="#17191C",
            border_width=1,
            border_color="#262A2E",
            **kwargs,
        )
        self.card_id = card_id
        self.url = url
        self._settings = settings
        self._update_queue = update_queue
        self._on_download = on_download
        self._on_remove = on_remove
        self._on_cancel = on_cancel

        self.status = "queued"
        self._custom_title = ""
        self._video_title = "Loading video information..."
        self._duration_str = "--:--"
        self._uploader_str = ""
        self._output_path = ""
        self._speed_bps = 0.0
        self._size_bytes = 0
        self._error_msg = ""
        self._has_custom_thumb = False
        self._raw_info = {}

        # Default format mapping
        default_q = self._settings.get("default_quality", "Best (auto)")
        default_f = self._settings.get("default_format", "MP4")
        self.quality = default_q
        self.video_format = default_f

        # Determine initial preset
        self._selected_preset = "Convert to MP4"
        if default_q in AUDIO_QUALITIES or default_f.upper() == "MP3":
            self._selected_preset = "Convert to MP3"
        elif default_f.upper() == "WEBM":
            self._selected_preset = "Convert to WebM"
        elif default_f.upper() == "MKV":
            self._selected_preset = "Merge to MKV"
        elif default_f.upper() == "AVI":
            self._selected_preset = "Convert to AVI"

        self.grid_propagate(False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)  # Middle flex area

        self._build()
        self._fetch_metadata_pipeline()

    @property
    def id(self) -> str:
        return self.card_id

    def _build(self) -> None:
        # ── Left 3px Status Indicator Bar ────────────────────────────
        self._status_bar = ctk.CTkFrame(
            self,
            width=3,
            corner_radius=2,
            fg_color=STATUS_QUEUED,
            border_width=0,
        )
        self._status_bar.place(x=0, y=0, relheight=1.0)

        # ── Column 0: 90x50 Thumbnail Container ───────────────────────
        self._thumb_frame = ctk.CTkFrame(
            self,
            width=90,
            height=50,
            corner_radius=4,
            fg_color="#24272C",
            border_width=0,
        )
        self._thumb_frame.grid(row=0, column=0, sticky="w", padx=(10, 10), pady=10)
        self._thumb_frame.grid_propagate(False)
        self._thumb_frame.grid_columnconfigure(0, weight=1)
        self._thumb_frame.grid_rowconfigure(0, weight=1)

        self._thumb_lbl = ctk.CTkLabel(
            self._thumb_frame,
            text="",
            image=get_icon("film-strip", size=48, color=ACCENT_PRIMARY),
        )
        self._thumb_lbl.grid(row=0, column=0)

        # ── Column 1: Middle Info & Controls (2 Rows) ─────────────────
        self._mid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._mid_frame.grid(row=0, column=1, sticky="nsew", pady=8, padx=(0, 10))
        self._mid_frame.grid_columnconfigure(0, weight=1)
        self._mid_frame.grid_rowconfigure(0, weight=1)
        self._mid_frame.grid_rowconfigure(1, weight=1)

        # ── Row 1.0 (Top): Title + Rename Pencil Icon ────────────────
        self._top_row = ctk.CTkFrame(self._mid_frame, fg_color="transparent")
        self._top_row.grid(row=0, column=0, sticky="ew")
        self._top_row.grid_columnconfigure(0, weight=0)

        self._title_lbl = ctk.CTkLabel(
            self._top_row,
            text=self._video_title,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
            anchor="w",
        )
        self._title_lbl.pack(side="left", padx=(0, 6))

        self._edit_btn = ctk.CTkButton(
            self._top_row,
            text="",
            image=get_icon("pencil-simple", size=14, color=TEXT_MUTED),
            width=22,
            height=22,
            corner_radius=3,
            fg_color="transparent",
            hover_color="#282C32",
            command=self._show_rename_dialog,
        )
        self._edit_btn.pack(side="left")

        # ── Row 1.1 (Bottom): Dropdown + Tools + Info + Duration ───────
        self._bot_row = ctk.CTkFrame(self._mid_frame, fg_color="transparent")
        self._bot_row.grid(row=1, column=0, sticky="ew", pady=(4, 0))

        # Format Dropdown Menu
        self._fmt_var = ctk.StringVar(value=self._selected_preset)
        self._fmt_menu = ctk.CTkOptionMenu(
            self._bot_row,
            variable=self._fmt_var,
            values=FORMAT_PRESETS,
            width=180,
            height=26,
            corner_radius=4,
            font=ctk.CTkFont(family=FONT_UI, size=11),
            dropdown_font=ctk.CTkFont(family=FONT_UI, size=11),
            fg_color="#1E2126",
            button_color="#24282F",
            button_hover_color="#2F343C",
            dropdown_fg_color="#181B1F",
            dropdown_hover_color="#252A32",
            dropdown_text_color="#E8E9EA",
            text_color="#E8E9EA",
            command=self._on_preset_selected,
        )
        self._fmt_menu.pack(side="left", padx=(0, 6))

        # Wrench Button (Tools / Custom settings)
        self._wrench_btn = ctk.CTkButton(
            self._bot_row,
            text="",
            image=get_icon("wrench", size=15, color=TEXT_SECONDARY),
            width=26,
            height=26,
            corner_radius=4,
            fg_color="#1E2126",
            hover_color="#2A2F37",
            command=self._show_custom_options_dialog,
        )
        self._wrench_btn.pack(side="left", padx=(0, 6))

        # Info Button (Metadata dialog)
        self._info_btn = ctk.CTkButton(
            self._bot_row,
            text="",
            image=get_icon("info", size=15, color=TEXT_SECONDARY),
            width=26,
            height=26,
            corner_radius=4,
            fg_color="#1E2126",
            hover_color="#2A2F37",
            command=self._show_info_dialog,
        )
        self._info_btn.pack(side="left", padx=(0, 8))

        # Duration Text (JetBrains Mono)
        self._dur_lbl = ctk.CTkLabel(
            self._bot_row,
            text=self._duration_str,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_MUTED,
        )
        self._dur_lbl.pack(side="left")

        # ── Column 2: Right Actions & Metrics ─────────────────────────
        self._right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._right_frame.grid(row=0, column=2, sticky="e", padx=(0, 12), pady=8)

        # 1. Idle / Queued Action Container
        self._idle_actions = ctk.CTkFrame(self._right_frame, fg_color="transparent")
        self._idle_actions.pack(side="right")

        self._dl_btn = ctk.CTkButton(
            self._idle_actions,
            text="",
            image=get_icon("download-simple", size=16, color=STATUS_ACTIVE),
            width=32,
            height=28,
            corner_radius=4,
            fg_color="#20242A",
            hover_color="#2A3038",
            command=self.start_download,
        )
        self._dl_btn.pack(side="left", padx=(0, 6))

        self._del_btn = ctk.CTkButton(
            self._idle_actions,
            text="",
            image=get_icon("trash", size=16, color=TEXT_SECONDARY),
            width=32,
            height=28,
            corner_radius=4,
            fg_color="#20242A",
            hover_color="#3B2225",
            command=self._on_remove_click,
        )
        self._del_btn.pack(side="left")

        # 2. Downloading / Active Container (Hidden at rest)
        self._active_box = ctk.CTkFrame(self._right_frame, fg_color="transparent")

        self._active_stats = ctk.CTkFrame(self._active_box, fg_color="transparent")
        self._active_stats.pack(fill="x", pady=(0, 4))

        self._speed_lbl = ctk.CTkLabel(
            self._active_stats,
            text="0 KB/s",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_SECONDARY,
        )
        self._speed_lbl.pack(side="left", padx=(0, 6))

        self._size_lbl = ctk.CTkLabel(
            self._active_stats,
            text="—",
            font=ctk.CTkFont(family=FONT_MONO, size=10),
            text_color=TEXT_MUTED,
        )
        self._size_lbl.pack(side="left", padx=(0, 6))

        self._cancel_btn = ctk.CTkButton(
            self._active_stats,
            text="",
            image=get_icon("x-circle", size=15, color=TEXT_MUTED),
            width=18,
            height=18,
            corner_radius=3,
            fg_color="transparent",
            hover_color="#3B2225",
            command=self._on_cancel_click,
        )
        self._cancel_btn.pack(side="right")

        self._prog_bar = ctk.CTkProgressBar(
            self._active_box,
            width=150,
            height=4,
            corner_radius=2,
            fg_color="#24282F",
            progress_color=STATUS_ACTIVE,
        )
        self._prog_bar.set(0)
        self._prog_bar.pack(fill="x")

        # 3. Done Container (Hidden at rest)
        self._done_box = ctk.CTkFrame(self._right_frame, fg_color="transparent")

        self._done_badge = ctk.CTkLabel(
            self._done_box,
            text="✓ Done",
            font=ctk.CTkFont(family=FONT_UI, size=11, weight="bold"),
            text_color=STATUS_DONE,
        )
        self._done_badge.pack(side="left", padx=(0, 8))

        self._folder_btn = ctk.CTkButton(
            self._done_box,
            text="",
            image=get_icon("folder", size=16, color=TEXT_SECONDARY),
            width=30,
            height=28,
            corner_radius=4,
            fg_color="#20242A",
            hover_color="#2A3038",
            command=self._open_folder,
        )
        self._folder_btn.pack(side="left", padx=(0, 6))

        self._done_del_btn = ctk.CTkButton(
            self._done_box,
            text="",
            image=get_icon("trash", size=16, color=TEXT_SECONDARY),
            width=30,
            height=28,
            corner_radius=4,
            fg_color="#20242A",
            hover_color="#3B2225",
            command=self._on_remove_click,
        )
        self._done_del_btn.pack(side="left")

        # Hover highlights
        self.bind("<Enter>", lambda _e: self.configure(fg_color="#1C1F24"))
        self.bind("<Leave>", lambda _e: self.configure(fg_color="#17191C"))

        self._apply_status_styling()

    # ------------------------------------------------------------------
    # Fast-Path Metadata Resolution
    # ------------------------------------------------------------------

    def _fetch_metadata_pipeline(self) -> None:
        """
        Two-tier metadata resolution:
        Tier 1: Instant sub-second oEmbed/direct thumbnail (< 400ms).
        Tier 2: Background yt-dlp enrichment with extract_flat=True (1-2s).
        """
        def _pipeline_worker():
            # ── Tier 1: Instant Fast-Path (<400ms) ────────────────────
            try:
                quick = fetch_quick_meta(self.url)
                if quick:
                    if "title" in quick:
                        self._update_queue.put(("info", self.card_id, quick))
                    thumb_url = quick.get("thumbnail") or quick.get("fallback_thumbnail")
                    if thumb_url:
                        self._download_and_post_thumb(thumb_url)
            except Exception:
                pass

            # ── Tier 2: Background Enrichment (yt-dlp extract_flat) ───
            try:
                info = fetch_info(self.url, is_playlist=False, extract_flat=True)
                if info:
                    self._update_queue.put(("info", self.card_id, info))
                    if not self._has_custom_thumb:
                        thumb_url = info.get("thumbnail")
                        thumbs = info.get("thumbnails")
                        if not thumb_url and thumbs and isinstance(thumbs, list):
                            last_item = thumbs[-1]
                            if isinstance(last_item, dict):
                                thumb_url = last_item.get("url")
                        if thumb_url:
                            self._download_and_post_thumb(thumb_url)
            except Exception:
                pass

        threading.Thread(target=_pipeline_worker, daemon=True).start()

    def _download_and_post_thumb(self, thumb_url: str) -> None:
        try:
            req = urllib.request.Request(
                thumb_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            )
            try:
                # Primary: secure verified SSL context
                ctx = ssl.create_default_context()
                resp = urllib.request.urlopen(req, timeout=6, context=ctx)
            except (ssl.SSLError, urllib.error.URLError):
                # Fallback only if local system certificate store fails
                fallback_ctx = ssl.create_default_context()
                fallback_ctx.check_hostname = False
                fallback_ctx.verify_mode = ssl.CERT_NONE
                resp = urllib.request.urlopen(req, timeout=6, context=fallback_ctx)

            with resp:
                data = resp.read()
            raw_img = Image.open(io.BytesIO(data)).convert("RGB")
            fitted_img = ImageOps.fit(raw_img, (90, 50), Image.Resampling.LANCZOS)
            self._update_queue.put(("thumbnail", self.card_id, fitted_img))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Event Handlers & Dialogs
    # ------------------------------------------------------------------

    def _on_preset_selected(self, choice: str) -> None:
        if choice in ("Custom Download...", "🔧 Custom Download"):
            self._show_custom_options_dialog()
            return

        self._selected_preset = choice
        q, f = _map_preset_to_format(choice)
        self.quality = q
        self.video_format = f

        if self.status in ("done", "error"):
            self._reset_for_new_download()

    def _reset_for_new_download(self) -> None:
        """Reset a completed or failed card back to queued state for a new download session."""
        self.status = "queued"
        self._speed_bps = 0.0
        self._size_bytes = 0
        self._error_msg = ""
        self._output_path = ""
        self._prog_bar.set(0)
        self._size_lbl.configure(text="—")
        self._speed_lbl.configure(text="0 KB/s")
        self._fmt_menu.configure(state="normal")
        self._wrench_btn.configure(state="normal")
        self._edit_btn.configure(state="normal")
        self._dl_btn.configure(
            image=get_icon("download-simple", size=16, color=STATUS_ACTIVE),
            text="",
        )
        self._show_idle_controls()
        self._apply_status_styling()
        try:
            self._update_queue.put(("repack",))
        except Exception:
            pass

    def _show_rename_dialog(self) -> None:
        top = ctk.CTkToplevel(self)
        top.title("Edit Download Title")
        top.geometry("440x160")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        ctk.CTkLabel(
            top,
            text="Rename Download File:",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 8))

        entry = ctk.CTkEntry(
            top,
            height=32,
            font=ctk.CTkFont(family="Segoe UI", size=12),
        )
        entry.pack(fill="x", padx=20, pady=(0, 16))
        entry.insert(0, self._custom_title or self._video_title)
        entry.focus_set()

        btn_box = ctk.CTkFrame(top, fg_color="transparent")
        btn_box.pack(fill="x", padx=20)

        def _save():
            val = entry.get().strip()
            clean_val = sanitize_filename(val)
            if clean_val:
                self._custom_title = clean_val
                self._video_title = clean_val
                disp = clean_val[:50] + "…" if len(clean_val) > 52 else clean_val
                self._title_lbl.configure(text=disp)
            top.destroy()

        ctk.CTkButton(
            btn_box,
            text="Save",
            width=90,
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#E8A33D",
            hover_color="#CF8F30",
            text_color="#18191B",
            command=_save,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=80,
            height=30,
            fg_color="#262A2E",
            hover_color="#33383F",
            command=top.destroy,
        ).pack(side="right")

        entry.bind("<Return>", lambda _e: _save())
        entry.bind("<Escape>", lambda _e: top.destroy())

    def _show_info_dialog(self) -> None:
        top = ctk.CTkToplevel(self)
        top.title("Video Information")
        top.geometry("480x360")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        ctk.CTkLabel(
            top,
            text=" Video Metadata",
            image=get_icon("info", size=18, color=ACCENT_PRIMARY),
            compound="left",
            font=ctk.CTkFont(family=FONT_UI, size=15, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 12))

        box = ctk.CTkFrame(top, fg_color="#1A1C20", corner_radius=6)
        box.pack(fill="both", expand=True, padx=20, pady=(0, 14))

        title = self._video_title
        uploader = self._uploader_str or self._raw_info.get("uploader") or self._raw_info.get("channel") or "Unknown"
        dur = self._duration_str
        view_c = self._raw_info.get("view_count")
        views_str = f"{view_c:,}" if view_c else "—"

        lines = [
            f"Title: {title}",
            f"Uploader: {uploader}",
            f"Duration: {dur}",
            f"Views: {views_str}",
            f"URL: {self.url}",
        ]
        text_box = ctk.CTkTextbox(box, wrap="word", font=ctk.CTkFont(family=FONT_MONO, size=11))
        text_box.pack(fill="both", expand=True, padx=10, pady=10)
        text_box.insert("1.0", "\n\n".join(lines))
        text_box.configure(state="disabled")

        btn_row = ctk.CTkFrame(top, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 14))

        def _copy_url():
            try:
                import pyperclip
                pyperclip.copy(self.url)
            except Exception:
                pass

        ctk.CTkButton(
            btn_row,
            text=" Copy Link",
            image=get_icon("copy", size=16, color=TEXT_SECONDARY),
            compound="left",
            width=110,
            height=30,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            fg_color="#262A2E",
            hover_color="#33383F",
            command=_copy_url,
        ).pack(side="left")

        ctk.CTkButton(
            btn_row,
            text="Close",
            width=80,
            height=30,
            fg_color="#E8A33D",
            hover_color="#CF8F30",
            text_color="#18191B",
            command=top.destroy,
        ).pack(side="right")

    def _show_custom_options_dialog(self) -> None:
        top = ctk.CTkToplevel(self)
        top.title("Custom Download Options")
        top.geometry("420x300")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        ctk.CTkLabel(
            top,
            text=" Custom Format & Quality",
            image=get_icon("wrench", size=18, color=ACCENT_PRIMARY),
            compound="left",
            font=ctk.CTkFont(family=FONT_UI, size=14, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(16, 12))

        # Quality selector
        ctk.CTkLabel(top, text="Quality / Resolution:", font=ctk.CTkFont(family=FONT_UI, size=11), text_color=TEXT_SECONDARY).pack(anchor="w", padx=20)
        q_menu = ctk.CTkOptionMenu(top, values=QUALITY_OPTIONS, width=380, height=28, font=ctk.CTkFont(family=FONT_UI, size=11))
        q_menu.pack(padx=20, pady=(2, 10))
        q_menu.set(self.quality if self.quality in QUALITY_OPTIONS else "Best (auto)")

        # Format selector
        ctk.CTkLabel(top, text="Output Container Format:", font=ctk.CTkFont(family=FONT_UI, size=11), text_color=TEXT_SECONDARY).pack(anchor="w", padx=20)
        f_menu = ctk.CTkOptionMenu(top, values=VIDEO_FORMATS + ["MP3", "M4A", "WAV", "FLAC", "Opus"], width=380, height=28, font=ctk.CTkFont(family=FONT_UI, size=11))
        f_menu.pack(padx=20, pady=(2, 16))
        f_menu.set(self.video_format)

        btn_box = ctk.CTkFrame(top, fg_color="transparent")
        btn_box.pack(fill="x", padx=20, pady=(0, 16))

        def _apply():
            self.quality = q_menu.get()
            self.video_format = f_menu.get()
            self._selected_preset = "Custom Download..."
            self._fmt_var.set("Custom Download...")
            if self.status in ("done", "error"):
                self._reset_for_new_download()
            top.destroy()

        def _cancel():
            self._fmt_var.set(self._selected_preset)
            top.destroy()

        ctk.CTkButton(
            btn_box,
            text="Apply",
            width=90,
            height=30,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#E8A33D",
            hover_color="#CF8F30",
            text_color="#18191B",
            command=_apply,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_box,
            text="Cancel",
            width=80,
            height=30,
            fg_color="#262A2E",
            hover_color="#33383F",
            command=_cancel,
        ).pack(side="right")

        top.protocol("WM_DELETE_WINDOW", _cancel)
        top.bind("<Escape>", lambda _e: _cancel())
        top.bind("<Return>", lambda _e: _apply())

    # ------------------------------------------------------------------
    # Progress & State Updates
    # ------------------------------------------------------------------

    def update_progress(self, data: dict) -> None:
        status = data.get("status", "")

        if status == "downloading":
            self.status = "downloading"
            self._fmt_menu.configure(state="disabled")
            self._wrench_btn.configure(state="disabled")
            self._edit_btn.configure(state="disabled")
            self._show_active_controls()

            total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            done = data.get("downloaded_bytes", 0)
            speed = data.get("speed") or 0
            self._speed_bps = float(speed)

            if total > 0:
                self._size_bytes = total
                self._size_lbl.configure(text=f"{_fmt_bytes(done)} / {_fmt_bytes(total)}")
                pct = done / total
                self._prog_bar.set(pct)
            else:
                self._size_lbl.configure(text=_fmt_bytes(done))
                self._prog_bar.set(0.5)

            self._speed_lbl.configure(text=_fmt_speed(speed))
            if "filename" in data:
                self._output_path = data["filename"]

            self._apply_status_styling()

        elif status == "finished":
            self.status = "converting"
            self._fmt_menu.configure(state="disabled")
            self._wrench_btn.configure(state="disabled")
            self._edit_btn.configure(state="disabled")
            self._speed_lbl.configure(text="Converting...")
            self._prog_bar.set(1.0)
            if "filename" in data:
                self._output_path = data["filename"]
            self._apply_status_styling()

    def update_done(self, output_path: str = "") -> None:
        if output_path:
            self._output_path = output_path
        self.status = "done"
        self._speed_bps = 0.0
        self._fmt_menu.configure(state="normal")
        self._wrench_btn.configure(state="normal")
        self._edit_btn.configure(state="normal")
        self._show_done_controls()
        self._apply_status_styling()

    def update_error(self, err: str) -> None:
        self.status = "error"
        self._error_msg = str(err)
        self._speed_bps = 0.0
        self._fmt_menu.configure(state="normal")
        self._wrench_btn.configure(state="normal")
        self._edit_btn.configure(state="normal")
        self._show_idle_controls()
        self._dl_btn.configure(
            image=get_icon("arrows-clockwise", size=16, color=STATUS_FAILED),
            text="",
        )
        self._apply_status_styling()

    def apply_info(self, info: dict) -> None:
        self._raw_info.update(info)
        title = info.get("title") or self.url
        if not self._custom_title:
            self._video_title = title
            display_title = title[:50] + "…" if len(title) > 52 else title
            self._title_lbl.configure(text=display_title)

        uploader = info.get("uploader") or info.get("channel") or info.get("creator") or ""
        if uploader:
            self._uploader_str = uploader

        dur = info.get("duration")
        if dur:
            mins, secs = divmod(int(dur), 60)
            hours, mins = divmod(mins, 60)
            dur_str = f"{hours:02d}:{mins:02d}:{secs:02d}" if hours else f"{mins:02d}:{secs:02d}"
            self._duration_str = dur_str
            self._dur_lbl.configure(text=dur_str)

    def apply_thumbnail(self, pil_img) -> None:
        try:
            if pil_img.size != (90, 50):
                pil_img = ImageOps.fit(pil_img, (90, 50), Image.Resampling.LANCZOS)
            self._thumb_img = ctk.CTkImage(
                light_image=pil_img,
                dark_image=pil_img,
                size=(90, 50),
            )
            self._thumb_lbl.configure(image=self._thumb_img, text="")
            self._has_custom_thumb = True
        except Exception:
            pass

    def _show_idle_controls(self) -> None:
        self._active_box.pack_forget()
        self._done_box.pack_forget()
        self._idle_actions.pack(side="right")

    def _show_active_controls(self) -> None:
        self._idle_actions.pack_forget()
        self._done_box.pack_forget()
        self._active_box.pack(side="right")

    def _show_done_controls(self) -> None:
        self._idle_actions.pack_forget()
        self._active_box.pack_forget()
        self._done_box.pack(side="right")

    def _apply_status_styling(self) -> None:
        if self.status in ("downloading", "active", "converting"):
            color = STATUS_ACTIVE
        elif self.status == "done":
            color = STATUS_DONE
        elif self.status == "error":
            color = STATUS_FAILED
        else:
            color = STATUS_QUEUED

        self._status_bar.configure(fg_color=color)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def set_format(self, quality: str, video_format: str) -> None:
        self.quality = quality
        self.video_format = video_format

    def start_download(self) -> None:
        if self.status in ("downloading", "converting", "active"):
            return
        self.status = "active"
        self._apply_status_styling()
        self._show_active_controls()
        self._speed_lbl.configure(text="Starting...")
        self._size_lbl.configure(text="—")
        self._prog_bar.set(0)
        self._fmt_menu.configure(state="disabled")
        self._wrench_btn.configure(state="disabled")
        self._edit_btn.configure(state="disabled")
        self._on_download(
            self.card_id,
            self.url,
            self.quality,
            self.video_format,
            self._custom_title,
        )

    def start_download_if_ready(self) -> None:
        if self.status in ("ready", "idle", "queued", "error"):
            self.start_download()

    def _on_cancel_click(self) -> None:
        if self._on_cancel:
            self._on_cancel(self.card_id)
        self.stop_download()

    def stop_download(self) -> None:
        if self.status in ("downloading", "converting", "queued", "active"):
            self.status = "queued"
            self._speed_bps = 0.0
            self._size_lbl.configure(text="—")
            self._speed_lbl.configure(text="0 KB/s")
            self._prog_bar.set(0)
            self._fmt_menu.configure(state="normal")
            self._wrench_btn.configure(state="normal")
            self._edit_btn.configure(state="normal")
            self._dl_btn.configure(
                image=get_icon("download-simple", size=16, color=STATUS_ACTIVE),
                text="",
            )
            self._show_idle_controls()
            self._apply_status_styling()
            try:
                self._update_queue.put(("repack",))
            except Exception:
                pass

    def _on_remove_click(self) -> None:
        self._on_remove(self.card_id)

    def _open_folder(self) -> None:
        target = self._output_path
        default_dir = self._settings.get("output_dir", str(Path.home() / "Downloads"))
        if not default_dir or not Path(default_dir).exists():
            default_dir = str(Path.home() / "Downloads")
        if not Path(default_dir).exists():
            default_dir = str(Path.home())

        p = Path(target) if target else None

        if p and p.exists() and p.is_file():
            if os.name == "nt":
                try:
                    # Windows Explorer syntax: explorer.exe /select,"<filepath>"
                    cmd = f'explorer.exe /select,"{str(p.resolve())}"'
                    cflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                    subprocess.Popen(cmd, creationflags=cflags)
                    return
                except Exception:
                    pass
            folder = p.parent
        elif p and p.exists() and p.is_dir():
            folder = p
        elif p and p.parent.exists():
            folder = p.parent
        else:
            folder = Path(default_dir)

        try:
            if os.name == "nt":
                os.startfile(str(folder.resolve()))
            else:
                subprocess.Popen(["xdg-open", str(folder.resolve())])
        except Exception:
            pass


def _fmt_bytes(b: int) -> str:
    if b <= 0:
        return "—"
    if b < 1024:
        return f"{b} B"
    if b < 1_048_576:
        return f"{b / 1024:.0f} KB"
    if b < 1_073_741_824:
        return f"{b / 1_048_576:.0f} MB"
    return f"{b / 1_073_741_824:.2f} GB"


def _fmt_speed(bps: float) -> str:
    if bps <= 0:
        return "—"
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1_048_576:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps / 1_048_576:.1f} MB/s"
