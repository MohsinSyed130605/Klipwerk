"""Format and quality selection dialog."""

from __future__ import annotations

import customtkinter as ctk
from core.downloader import QUALITY_OPTIONS, VIDEO_FORMATS, AUDIO_QUALITIES
from ui.theme import (
    BG_CANVAS,
    RADIUS_CARD,
    RADIUS_PILL,
    RADIUS_BUTTON,
    BORDER_WIDTH_CARD,
    CLAY_CARD_BG,
    CLAY_CARD_BORDER,
    CLAY_PRIMARY,
    CLAY_NEUTRAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    ACCENT_PRIMARY,
    FONT_UI,
)
from ui.icons import get_icon


class FormatDialog(ctk.CTkToplevel):
    """
    Tactile Claymorphic modal dialog for configuring format & quality for a video.
    """

    def __init__(
        self,
        parent,
        title: str,
        current_quality: str,
        current_format: str,
        available_formats: list[str] | None = None,
        on_confirm=None,
    ):
        super().__init__(parent)
        self._on_confirm = on_confirm
        self._confirmed = False

        self.title("Select Format & Quality")
        self.geometry("480x380")
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
            x = px + (pw - 480) // 2
            y = py + (ph - 380) // 2
            self.geometry(f"480x380+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        self._type_var = ctk.StringVar(
            value="Audio" if current_quality in AUDIO_QUALITIES else "Video"
        )
        self._quality_var = ctk.StringVar(value=current_quality)
        self._format_var = ctk.StringVar(value=current_format)

        # Video quality options
        self._video_qualities = [q for q in QUALITY_OPTIONS if q not in AUDIO_QUALITIES]
        self._audio_qualities = [q for q in QUALITY_OPTIONS if q in AUDIO_QUALITIES]

        # Container formats
        self._video_containers = VIDEO_FORMATS
        self._audio_containers = ["MP3", "M4A", "WAV", "FLAC", "Opus"]

        self._build_ui(title)
        self._update_choices()

    def _build_ui(self, video_title: str) -> None:
        self.grid_columnconfigure(0, weight=1)

        # Title Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(22, 12))

        ctk.CTkLabel(
            header,
            text=" Download Options",
            image=get_icon("gear-six", size=20, color=ACCENT_PRIMARY),
            compound="left",
            font=ctk.CTkFont(family=FONT_UI, size=18, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(anchor="w")

        # Truncate video title if needed
        display_title = video_title if len(video_title) <= 55 else video_title[:52] + "..."
        ctk.CTkLabel(
            header,
            text=display_title,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Content Clay Card
        card = ctk.CTkFrame(
            self,
            corner_radius=RADIUS_CARD,
            fg_color=CLAY_CARD_BG,
            border_width=BORDER_WIDTH_CARD,
            border_color=CLAY_CARD_BORDER,
        )
        card.pack(fill="x", padx=24, pady=(0, 20))
        card.grid_columnconfigure(1, weight=1)

        # Segmented button: Video vs Audio
        ctk.CTkLabel(
            card,
            text="Type:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
            width=80,
            anchor="w",
        ).grid(row=0, column=0, padx=(18, 8), pady=(18, 12), sticky="w")

        self._type_seg = ctk.CTkSegmentedButton(
            card,
            values=["Video", "Audio"],
            variable=self._type_var,
            command=self._on_type_changed,
            height=34,
            corner_radius=RADIUS_BUTTON,
            selected_color=CLAY_PRIMARY["fg_color"],
            selected_hover_color=CLAY_PRIMARY["hover_color"],
        )
        self._type_seg.grid(row=0, column=1, padx=(0, 18), pady=(18, 12), sticky="ew")

        # Quality dropdown
        self._quality_lbl = ctk.CTkLabel(
            card,
            text="Quality:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
            width=80,
            anchor="w",
        )
        self._quality_lbl.grid(row=1, column=0, padx=(18, 8), pady=8, sticky="w")

        self._quality_menu = ctk.CTkOptionMenu(
            card,
            variable=self._quality_var,
            values=self._video_qualities,
            height=34,
            corner_radius=RADIUS_BUTTON,
            button_color=CLAY_PRIMARY["fg_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
        )
        self._quality_menu.grid(row=1, column=1, padx=(0, 18), pady=8, sticky="ew")

        # Container / Format dropdown
        self._format_lbl = ctk.CTkLabel(
            card,
            text="Format:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=TEXT_PRIMARY,
            width=80,
            anchor="w",
        )
        self._format_lbl.grid(row=2, column=0, padx=(18, 8), pady=(8, 18), sticky="w")

        self._format_menu = ctk.CTkOptionMenu(
            card,
            variable=self._format_var,
            values=self._video_containers,
            height=34,
            corner_radius=RADIUS_BUTTON,
            button_color=CLAY_PRIMARY["fg_color"],
            button_hover_color=CLAY_PRIMARY["hover_color"],
        )
        self._format_menu.grid(row=2, column=1, padx=(0, 18), pady=(8, 18), sticky="ew")

        # Bottom buttons (Clay Pills)
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=24, pady=(0, 20), side="bottom")

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            width=100,
            height=36,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            fg_color=CLAY_NEUTRAL["fg_color"],
            hover_color=CLAY_NEUTRAL["hover_color"],
            border_color=CLAY_NEUTRAL["border_color"],
            border_width=CLAY_NEUTRAL["border_width"],
            text_color=CLAY_NEUTRAL["text_color"],
            command=self.destroy,
        ).pack(side="right", padx=(10, 0))

        ctk.CTkButton(
            btn_bar,
            text=" Confirm",
            image=get_icon("plus-circle", size=16, color=CLAY_PRIMARY["text_color"]),
            compound="left",
            width=116,
            height=36,
            corner_radius=RADIUS_PILL,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            fg_color=CLAY_PRIMARY["fg_color"],
            hover_color=CLAY_PRIMARY["hover_color"],
            border_color=CLAY_PRIMARY["border_color"],
            border_width=CLAY_PRIMARY["border_width"],
            text_color=CLAY_PRIMARY["text_color"],
            command=self._do_confirm,
        ).pack(side="right")

    def _on_type_changed(self, choice: str) -> None:
        self._update_choices()

    def _update_choices(self) -> None:
        is_audio = self._type_var.get() == "Audio"
        if is_audio:
            self._quality_menu.configure(values=self._audio_qualities)
            if self._quality_var.get() not in self._audio_qualities:
                self._quality_var.set(self._audio_qualities[0])

            self._format_menu.configure(values=self._audio_containers)
            if self._format_var.get() not in self._audio_containers:
                self._format_var.set("MP3")
        else:
            self._quality_menu.configure(values=self._video_qualities)
            if self._quality_var.get() not in self._video_qualities:
                self._quality_var.set(self._video_qualities[0])

            self._format_menu.configure(values=self._video_containers)
            if self._format_var.get() not in self._video_containers:
                self._format_var.set("MP4")

    def _do_confirm(self) -> None:
        quality = self._quality_var.get()
        fmt = self._format_var.get()
        self._confirmed = True
        if self._on_confirm:
            self._on_confirm(quality, fmt)
        self.destroy()
