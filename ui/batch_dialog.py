"""Batch URL import and download queue dialog."""

from __future__ import annotations

import re
import customtkinter as ctk

from core.downloader import QUALITY_OPTIONS, VIDEO_FORMATS, AUDIO_QUALITIES
from ui.theme import (
    BG_CANVAS,
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
    ACCENT_PRIMARY,
    FONT_UI,
    FONT_MONO,
)
from ui.icons import get_icon


class BatchDialog(ctk.CTkToplevel):
    """
    Tactile Claymorphic modal dialog to paste and import multiple URLs in bulk.
    """

    def __init__(
        self,
        parent,
        default_quality: str = "Best (auto)",
        default_format: str = "MP4",
        on_confirm=None,
    ):
        super().__init__(parent)
        self._on_confirm = on_confirm

        self.title("Batch Import URLs — Klipwerk")
        self.geometry("560x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.configure(fg_color=BG_CANVAS)

        # Center on parent
        self.update_idletasks()
        try:
            pw = parent.winfo_width()
            ph = parent.winfo_height()
            px = parent.winfo_rootx()
            py = parent.winfo_rooty()
            x = px + (pw - 560) // 2
            y = py + (ph - 520) // 2
            self.geometry(f"560x520+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self._quality_var = ctk.StringVar(value=default_quality)
        self._format_var = ctk.StringVar(value=default_format)
        self._auto_start_var = ctk.BooleanVar(value=False)

        self._build_ui()

    def _build_ui(self) -> None:
        container = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CARD,
            fg_color=CLAY_CARD_BG,
            border_width=BORDER_WIDTH_CARD,
            border_color=CLAY_CARD_BORDER,
        )
        container.pack(fill="both", expand=True, padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(18, 8))

        ctk.CTkLabel(
            header,
            text=" Batch Import URLs",
            image=get_icon("stack", size=20, color=ACCENT_PRIMARY),
            compound="left",
            font=ctk.CTkFont(family=FONT_UI, size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        ctk.CTkLabel(
            header,
            text="Paste multiple video or audio links below (one per line):",
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(2, 0))

        # Text Area for URLs
        self._textbox = ctk.CTkTextbox(
            container,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            fg_color=CLAY_INPUT_BG,
            border_width=BORDER_WIDTH_SUB,
            border_color=CLAY_INPUT_BORDER,
            corner_radius=RADIUS_BUTTON,
            text_color=TEXT_PRIMARY,
            height=180,
        )
        self._textbox.pack(fill="both", expand=True, padx=20, pady=(6, 10))
        self._textbox.bind("<KeyRelease>", lambda _e: self._update_counter())

        # Counter Badge Line
        counter_row = ctk.CTkFrame(container, fg_color="transparent")
        counter_row.pack(fill="x", padx=20, pady=(0, 10))

        self._count_lbl = ctk.CTkLabel(
            counter_row,
            text="0 links recognized",
            font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
            text_color=ACCENT_PRIMARY,
        )
        self._count_lbl.pack(side="left")

        ctk.CTkButton(
            counter_row,
            text=" Paste from Clipboard",
            image=get_icon("clipboard-text", size=18, color=CLAY_NEUTRAL["text_color"]),
            compound="left",
            width=164,
            height=28,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=11, weight="bold"),
            fg_color=CLAY_NEUTRAL["fg_color"],
            hover_color=CLAY_NEUTRAL["hover_color"],
            border_color=CLAY_NEUTRAL["border_color"],
            border_width=CLAY_NEUTRAL["border_width"],
            text_color=CLAY_NEUTRAL["text_color"],
            command=self._paste_clipboard,
        ).pack(side="right")

        # Preset Quality & Format Row
        preset_frame = ctk.CTkFrame(
            container,
            corner_radius=RADIUS_BUTTON,
            fg_color=CLAY_INPUT_BG,
            border_width=BORDER_WIDTH_SUB,
            border_color=CLAY_INPUT_BORDER,
        )
        preset_frame.pack(fill="x", padx=20, pady=(0, 12))

        p_inner = ctk.CTkFrame(preset_frame, fg_color="transparent")
        p_inner.pack(fill="x", padx=14, pady=10)

        # Quality
        ctk.CTkLabel(
            p_inner,
            text="Quality / Type:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))

        self._q_menu = ctk.CTkOptionMenu(
            p_inner,
            values=QUALITY_OPTIONS,
            variable=self._quality_var,
            width=150,
            height=30,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(size=11),
            fg_color=CLAY_NEUTRAL["fg_color"],
            button_color=CLAY_NEUTRAL["border_color"],
            command=self._on_quality_changed,
        )
        self._q_menu.grid(row=0, column=1, padx=(0, 16))

        # Format
        self._fmt_lbl = ctk.CTkLabel(
            p_inner,
            text="Format:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self._fmt_lbl.grid(row=0, column=2, sticky="w", padx=(0, 8))

        self._f_menu = ctk.CTkOptionMenu(
            p_inner,
            values=VIDEO_FORMATS,
            variable=self._format_var,
            width=100,
            height=30,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(size=11),
            fg_color=CLAY_NEUTRAL["fg_color"],
            button_color=CLAY_NEUTRAL["border_color"],
        )
        self._f_menu.grid(row=0, column=3)

        # Download immediately toggle
        opt_row = ctk.CTkFrame(container, fg_color="transparent")
        opt_row.pack(fill="x", padx=20, pady=(0, 14))

        ctk.CTkCheckBox(
            opt_row,
            text="Start downloading immediately upon adding",
            variable=self._auto_start_var,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=TEXT_PRIMARY,
            checkmark_color="#ffffff",
            fg_color=CLAY_PRIMARY["fg_color"],
            hover_color=CLAY_PRIMARY["hover_color"],
            border_color=CLAY_CARD_BORDER,
            corner_radius=4,
        ).pack(side="left")

        # Bottom Action Buttons
        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            width=90,
            height=36,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color=CLAY_NEUTRAL["fg_color"],
            hover_color=CLAY_NEUTRAL["hover_color"],
            border_color=CLAY_NEUTRAL["border_color"],
            border_width=CLAY_NEUTRAL["border_width"],
            text_color=CLAY_NEUTRAL["text_color"],
            command=self.destroy,
        ).pack(side="right", padx=(10, 0))

        self._submit_btn = ctk.CTkButton(
            btn_row,
            text=" Add All to Queue",
            image=get_icon("plus-circle", size=18, color=CLAY_PRIMARY["text_color"]),
            compound="left",
            width=164,
            height=36,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            fg_color=CLAY_PRIMARY["fg_color"],
            hover_color=CLAY_PRIMARY["hover_color"],
            border_color=CLAY_PRIMARY["border_color"],
            border_width=CLAY_PRIMARY["border_width"],
            text_color=CLAY_PRIMARY["text_color"],
            command=self._do_submit,
        )
        self._submit_btn.pack(side="right")

    def _on_quality_changed(self, choice: str) -> None:
        is_audio = choice in AUDIO_QUALITIES
        if is_audio:
            self._fmt_lbl.configure(state="disabled")
            self._f_menu.configure(state="disabled")
        else:
            self._fmt_lbl.configure(state="normal")
            self._f_menu.configure(state="normal")

    def _get_urls(self) -> list[str]:
        content = self._textbox.get("1.0", "end").strip()
        if not content:
            return []
        raw_tokens = re.split(r"[\r\n\s,]+", content)
        urls = []
        for t in raw_tokens:
            t = t.strip()
            if t.startswith("http://") or t.startswith("https://"):
                urls.append(t)
        return urls

    def _update_counter(self) -> None:
        urls = self._get_urls()
        n = len(urls)
        self._count_lbl.configure(
            text=f"{n} {'link' if n == 1 else 'links'} recognized"
        )
        if n > 0:
            self._submit_btn.configure(
                text=f"➕ Add {n} {'Item' if n == 1 else 'Items'} to Queue",
                state="normal",
            )
        else:
            self._submit_btn.configure(
                text="➕ Add All to Queue",
                state="normal",
            )

    def _paste_clipboard(self) -> None:
        try:
            import pyperclip
            clip = pyperclip.paste().strip()
            if clip:
                current = self._textbox.get("1.0", "end").strip()
                if current:
                    self._textbox.insert("end", f"\n{clip}")
                else:
                    self._textbox.insert("1.0", clip)
                self._update_counter()
        except Exception:
            pass

    def _do_submit(self) -> None:
        urls = self._get_urls()
        if not urls:
            return
        quality = self._quality_var.get()
        video_format = self._format_var.get()
        auto_start = self._auto_start_var.get()
        if self._on_confirm:
            self._on_confirm(urls, quality, video_format, auto_start)
        self.destroy()
