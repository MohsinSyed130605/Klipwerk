"""
ui/url_input.py
Header & Toolbar components with separate action buttons ("tabs") for:
Add, Paste, Batch, Import from file, Start all, Pause, Clear done, and Quality dropdown.
"""

from __future__ import annotations

import re
from tkinter import filedialog
import customtkinter as ctk

from ui.theme import (
    BG_HOVER,
    BG_PANEL,
    BG_ELEVATED,
    BORDER_COLOR,
    BORDER_STRONG,
    ACCENT_PRIMARY,
    ACCENT_HOVER,
    STATUS_ACTIVE,
    CLAY_INPUT_BG,
    CLAY_INPUT_BORDER,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_ON_ACCENT,
    RADIUS_BUTTON,
    FONT_UI,
)
from ui.icons import get_icon


class UrlInputPanel(ctk.CTkFrame):
    """
    Header & Toolbar panel containing URL input bar with dedicated action buttons
    and lower toolbar matching reference design.
    """

    def __init__(
        self,
        parent,
        *,
        on_add_urls,
        on_batch_click=None,
        on_start_all=None,
        on_pause_all=None,
        on_clear_done=None,
        on_format_changed=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            corner_radius=0,
            fg_color="transparent",
            border_width=0,
            **kwargs,
        )
        self._on_add_urls = on_add_urls
        self._on_batch_click = on_batch_click
        self._on_start_all = on_start_all
        self._on_pause_all = on_pause_all
        self._on_clear_done = on_clear_done
        self._on_format_changed = on_format_changed

        self._notify_job = None
        self._selected_format = "1080p · mp4"

        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self) -> None:
        # ── 1. URL Bar Row (32px tall) ────────────────────────────────
        url_row = ctk.CTkFrame(self, height=32, fg_color="transparent")
        url_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        url_row.grid_propagate(False)
        url_row.grid_columnconfigure(0, weight=1)

        # Flex-1 Input Box with Inside Link Icon (32px tall)
        input_box = ctk.CTkFrame(
            url_row,
            height=32,
            corner_radius=RADIUS_BUTTON,
            fg_color="#131518",
            border_width=1,
            border_color=BORDER_COLOR,
        )
        input_box.grid(row=0, column=0, sticky="ew")
        input_box.grid_propagate(False)

        # Inside left: Link icon (Phosphor link-simple-horizontal)
        self._link_lbl = ctk.CTkLabel(
            input_box,
            text="",
            image=get_icon("link-simple-horizontal", size=18, color=TEXT_MUTED),
            width=26,
            anchor="center",
        )
        self._link_lbl.pack(side="left", padx=(6, 0))

        # Flex text entry
        self._entry = ctk.CTkEntry(
            input_box,
            placeholder_text="Paste a video or playlist URL",
            font=ctk.CTkFont(family=FONT_UI, size=12),
            border_width=0,
            fg_color="transparent",
            height=30,
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
        )
        self._entry.pack(side="left", fill="both", expand=True, padx=(2, 6))
        self._entry.bind("<Return>", lambda _e: self._do_add())

        # Notification label overlay (shown when clipboard link detected)
        self._notify_lbl = ctk.CTkLabel(
            input_box,
            text="",
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=ACCENT_PRIMARY,
        )

        # Buttons container on right side of URL bar
        btns_box = ctk.CTkFrame(url_row, fg_color="transparent")
        btns_box.grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Filled Accent Button: + Add (Amber #E8A33D, text #2A1B04, 32px)
        self._add_btn = ctk.CTkButton(
            btns_box,
            text=" Add",
            image=get_icon("plus-circle", size=18, color=TEXT_ON_ACCENT),
            compound="left",
            width=76,
            height=32,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=ACCENT_PRIMARY,
            hover_color=ACCENT_HOVER,
            text_color=TEXT_ON_ACCENT,
            border_width=0,
            command=self._do_add,
        )
        self._add_btn.pack(side="left", padx=(0, 6))

        # Elevated Secondary Button: Paste
        self._paste_btn = ctk.CTkButton(
            btns_box,
            text=" Paste",
            image=get_icon("clipboard-text", size=18, color=TEXT_SECONDARY),
            compound="left",
            width=82,
            height=32,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=BG_ELEVATED,
            hover_color=BG_HOVER,
            border_width=1,
            border_color=BORDER_STRONG,
            text_color=TEXT_SECONDARY,
            command=self._paste_clipboard,
        )
        self._paste_btn.pack(side="left", padx=(0, 6))

        # Elevated Secondary Button: Batch
        self._batch_btn = ctk.CTkButton(
            btns_box,
            text=" Batch",
            image=get_icon("stack", size=18, color=TEXT_SECONDARY),
            compound="left",
            width=84,
            height=32,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=BG_ELEVATED,
            hover_color=BG_HOVER,
            border_width=1,
            border_color=BORDER_STRONG,
            text_color=TEXT_SECONDARY,
            command=self._handle_batch,
        )
        self._batch_btn.pack(side="left", padx=(0, 6))

        # Elevated Secondary Button: Import
        self._import_btn = ctk.CTkButton(
            btns_box,
            text=" Import",
            image=get_icon("folder-open", size=18, color=TEXT_SECONDARY),
            compound="left",
            width=90,
            height=32,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            fg_color=BG_ELEVATED,
            hover_color=BG_HOVER,
            border_width=1,
            border_color=BORDER_STRONG,
            text_color=TEXT_SECONDARY,
            command=self._import_file,
        )
        self._import_btn.pack(side="left")

        # ── 2. Toolbar Row (28px tall, directly below) ────────────────
        toolbar = ctk.CTkFrame(self, height=28, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 2))
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(1, weight=1)

        # Left: Action buttons
        left_actions = ctk.CTkFrame(toolbar, fg_color="transparent")
        left_actions.grid(row=0, column=0, sticky="w")

        self._start_btn = ctk.CTkButton(
            left_actions,
            text=" Start all",
            image=get_icon("play", size=16, color=STATUS_ACTIVE),
            compound="left",
            height=28,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            fg_color="transparent",
            hover_color=BG_HOVER,
            border_width=0,
            text_color=STATUS_ACTIVE,
            command=self._handle_start_all,
        )
        self._start_btn.pack(side="left", padx=(0, 6))

        self._pause_btn = ctk.CTkButton(
            left_actions,
            text=" Pause",
            image=get_icon("pause", size=16, color=TEXT_MUTED),
            compound="left",
            height=28,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            fg_color="transparent",
            hover_color=BG_HOVER,
            border_width=0,
            text_color=TEXT_MUTED,
            command=self._handle_pause_all,
        )
        self._pause_btn.pack(side="left", padx=(0, 6))

        self._clear_btn = ctk.CTkButton(
            left_actions,
            text=" Clear done",
            image=get_icon("trash", size=16, color=TEXT_MUTED),
            compound="left",
            height=28,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            fg_color="transparent",
            hover_color=BG_HOVER,
            border_width=0,
            text_color=TEXT_MUTED,
            command=self._handle_clear_done,
        )
        self._clear_btn.pack(side="left", padx=(0, 6))

        # Right: Quality selector styled like Paste/Batch
        fmt_options = [
            "1080p · mp4",
            "720p · mp4",
            "480p · mp4",
            "Best · mp4",
            "Best · webm",
            "Audio · mp3",
            "Audio · m4a",
            "Audio · flac",
        ]
        self._fmt_var = ctk.StringVar(value=self._selected_format)
        self._fmt_dropdown = ctk.CTkOptionMenu(
            toolbar,
            variable=self._fmt_var,
            values=fmt_options,
            width=116,
            height=28,
            corner_radius=RADIUS_BUTTON,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            dropdown_font=ctk.CTkFont(family=FONT_UI, size=12),
            fg_color=BG_ELEVATED,
            button_color=BG_ELEVATED,
            button_hover_color=BG_HOVER,
            text_color=TEXT_SECONDARY,
            dropdown_fg_color=BG_PANEL,
            dropdown_hover_color=BG_HOVER,
            dropdown_text_color=TEXT_PRIMARY,
            command=self._on_format_select,
        )
        self._fmt_dropdown.grid(row=0, column=2, sticky="e")

    def _handle_batch(self) -> None:
        if self._on_batch_click:
            self._on_batch_click()

    def _import_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Import URLs from text file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                lines = f.readlines()
            urls = []
            for line in lines:
                u = line.strip()
                if not u or u.startswith("#"):
                    continue
                if u.startswith("http://") or u.startswith("https://"):
                    urls.append(u)
                elif "." in u and ("youtube" in u or "youtu.be" in u or "/" in u):
                    urls.append("https://" + u)
            if urls and self._on_add_urls:
                self._on_add_urls(urls)
        except Exception:
            pass

    def _handle_start_all(self) -> None:
        if self._on_start_all:
            self._on_start_all()

    def _handle_pause_all(self) -> None:
        if self._on_pause_all:
            self._on_pause_all()

    def _handle_clear_done(self) -> None:
        if self._on_clear_done:
            self._on_clear_done()

    def _on_format_select(self, val: str) -> None:
        self._selected_format = val
        if self._on_format_changed:
            self._on_format_changed(val)

    def get_selected_format(self) -> str:
        return self._selected_format

    def _do_add(self) -> None:
        raw = self._entry.get().strip()
        if not raw:
            return

        tokens = [u.strip() for u in re.split(r"[\s,\n]+", raw) if u.strip()]
        urls = []
        for t in tokens:
            if t.startswith("http://") or t.startswith("https://"):
                urls.append(t)
            elif "." in t and not t.startswith("#"):
                urls.append("https://" + t)

        if not urls and raw:
            urls = [raw if raw.startswith("http") else ("https://" + raw if "." in raw else raw)]

        if urls:
            self._on_add_urls(urls)
            self._entry.delete(0, "end")
            self._entry.focus_set()

    def _paste_clipboard(self) -> None:
        try:
            import pyperclip
            text = pyperclip.paste().strip()
            if text:
                self._entry.delete(0, "end")
                self._entry.insert(0, text)
                self._entry.focus_set()
        except Exception:
            pass

    def set_url(self, url: str) -> None:
        self._entry.delete(0, "end")
        self._entry.insert(0, url.strip())

    def flash_notification(self, message: str, duration_ms: int = 4000) -> None:
        self._notify_lbl.configure(text=message)
        self._notify_lbl.pack(side="left", fill="both", expand=True, padx=(2, 6))
        self._entry.pack_forget()

        if self._notify_job:
            self.after_cancel(self._notify_job)

        def _restore():
            self._notify_lbl.pack_forget()
            self._entry.pack(side="left", fill="both", expand=True, padx=(2, 6))

        self._notify_job = self.after(duration_ms, _restore)
