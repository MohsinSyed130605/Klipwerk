"""
ui/sidebar.py
Clean 132px fixed navigation sidebar matching reference design:
- Fixed 132px width (no collapsible toggle)
- Exactly two nav items plus Settings: "Queue" and "Failed"
- Amber tint for Queue when selected, Red tint for Failed when count > 0
- Settings pinned below hairline divider at bottom
"""

from __future__ import annotations
import customtkinter as ctk

from ui.theme import (
    BG_SIDEBAR,
    BG_HOVER,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    STATUS_FAILED,
    ROW_BG_QUEUED,
    ROW_BG_FAILED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    FONT_WORDMARK,
    FONT_UI,
    FONT_MONO,
)
from ui.icons import get_icon


class Sidebar(ctk.CTkFrame):
    WIDTH = 132

    def __init__(
        self,
        parent,
        on_nav,
        settings: dict | None = None,
        on_theme_toggle=None,
        on_update_click=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            width=self.WIDTH,
            corner_radius=0,
            fg_color=BG_SIDEBAR,
            border_width=0,
            **kwargs,
        )
        self.on_nav = on_nav
        self.on_theme_toggle = on_theme_toggle
        self.on_update_click = on_update_click

        self._active = "queue"
        self._queue_count = 0
        self._failed_count = 0
        self._latest_version = ""

        self.grid_propagate(False)
        self.pack_propagate(False)

        self._row_frames: dict[str, ctk.CTkFrame] = {}
        self._indicators: dict[str, ctk.CTkFrame] = {}
        self._icons: dict[str, ctk.CTkLabel] = {}
        self._labels: dict[str, ctk.CTkLabel] = {}
        self._counts: dict[str, ctk.CTkLabel] = {}
        self._icon_names: dict[str, str] = {}

        self._build()

    def _build(self) -> None:
        # Right-edge hairline divider
        self._right_border = ctk.CTkFrame(self, width=1, fg_color=BORDER_COLOR, border_width=0)
        self._right_border.place(relx=1.0, rely=0, relheight=1.0, anchor="ne", x=0)

        # App Wordmark (Smooch Sans, Bold)
        self._wordmark = ctk.CTkLabel(
            self,
            text="Klipwerk",
            font=ctk.CTkFont(family=FONT_WORDMARK, size=24, weight="bold"),
            text_color=ACCENT_PRIMARY,
            anchor="center",
        )
        self._wordmark.pack(fill="x", padx=6, pady=(16, 10))

        # Nav items container
        self._nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._nav_frame.pack(fill="x", padx=4, pady=(0, 0))

        # 1. Queue row (active and done together)
        self._create_row("queue", "tray", "Queue", has_count=True)

        # 2. Failed row
        self._create_row("failed", "warning-circle", "Failed", has_count=True)

        # Pinned Bottom Section
        self._bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom_frame.pack(side="bottom", fill="x", padx=4, pady=(0, 10))

        # Hairline divider
        self._bottom_divider = ctk.CTkFrame(self._bottom_frame, height=1, fg_color=BORDER_COLOR, border_width=0)
        self._bottom_divider.pack(fill="x", padx=2, pady=(0, 6))

        # Pinned Settings row
        self._create_row("settings", "gear-six", "Settings", has_count=False, parent=self._bottom_frame)

        self._apply_active_styles()

    def _create_row(self, key: str, icon_name: str, label: str, has_count: bool, parent=None) -> None:
        p = parent if parent is not None else self._nav_frame
        frame = ctk.CTkFrame(
            p,
            height=30,
            corner_radius=0,
            fg_color="transparent",
        )
        frame.pack(fill="x", pady=2)
        frame.pack_propagate(False)

        # Left Accent Border (2px)
        ind = ctk.CTkFrame(
            frame,
            width=2,
            height=30,
            corner_radius=0,
            fg_color="transparent",
        )
        ind.pack(side="left", fill="y")

        # 20px Phosphor Icon
        ico = ctk.CTkLabel(
            frame,
            text="",
            image=get_icon(icon_name, size=20, color=TEXT_SECONDARY),
            width=24,
            anchor="center",
        )
        ico.pack(side="left", padx=(4, 2))

        # Label (Plus Jakarta Sans)
        lbl = ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=TEXT_SECONDARY,
            anchor="w",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=(4, 0))

        cnt = None
        if has_count:
            cnt = ctk.CTkLabel(
                frame,
                text="0",
                font=ctk.CTkFont(family=FONT_MONO, size=11, weight="bold"),
                text_color=TEXT_MUTED,
                anchor="e",
            )
            cnt.pack(side="right", padx=(0, 8))
            self._counts[key] = cnt

        self._row_frames[key] = frame
        self._indicators[key] = ind
        self._icons[key] = ico
        self._labels[key] = lbl
        self._icon_names[key] = icon_name

        elements = [frame, ind, ico, lbl]
        if cnt:
            elements.append(cnt)

        for el in elements:
            el.bind("<Button-1>", lambda _e, k=key: self._row_clicked(k))
            el.bind("<Enter>", lambda _e, k=key: self._on_enter(k))
            el.bind("<Leave>", lambda _e, k=key: self._on_leave(k))

    def _on_enter(self, key: str) -> None:
        if key != self._active and not (key == "failed" and self._failed_count > 0):
            self._row_frames[key].configure(fg_color=BG_HOVER)

    def _on_leave(self, key: str) -> None:
        self._apply_active_styles()

    def _row_clicked(self, key: str) -> None:
        self.set_active(key)
        if self.on_nav:
            self.on_nav(key)

    def set_active(self, key: str) -> None:
        self._active = key
        self._apply_active_styles()

    def _apply_active_styles(self) -> None:
        # Queue item styling
        queue_selected = (self._active == "queue")
        q_frame = self._row_frames.get("queue")
        q_ind = self._indicators.get("queue")
        q_ico = self._icons.get("queue")
        q_lbl = self._labels.get("queue")
        q_cnt = self._counts.get("queue")

        if q_frame and q_ind and q_ico and q_lbl:
            if queue_selected:
                q_frame.configure(fg_color=ROW_BG_QUEUED)
                q_ind.configure(fg_color=ACCENT_PRIMARY)
                q_ico.configure(image=get_icon("tray", size=20, color=ACCENT_PRIMARY))
                q_lbl.configure(text_color=ACCENT_PRIMARY)
                if q_cnt:
                    q_cnt.configure(text_color=ACCENT_PRIMARY)
            else:
                q_frame.configure(fg_color="transparent")
                q_ind.configure(fg_color="transparent")
                q_ico.configure(image=get_icon("tray", size=20, color=TEXT_SECONDARY))
                q_lbl.configure(text_color=TEXT_SECONDARY)
                if q_cnt:
                    q_cnt.configure(text_color=TEXT_MUTED)

        # Failed item styling (active or alert whenever count > 0)
        failed_selected = (self._active == "failed")
        failed_alert = (self._failed_count > 0)
        f_frame = self._row_frames.get("failed")
        f_ind = self._indicators.get("failed")
        f_ico = self._icons.get("failed")
        f_lbl = self._labels.get("failed")
        f_cnt = self._counts.get("failed")

        if f_frame and f_ind and f_ico and f_lbl:
            if failed_selected or failed_alert:
                f_frame.configure(fg_color=ROW_BG_FAILED)
                f_ind.configure(fg_color=STATUS_FAILED)
                f_ico.configure(image=get_icon("warning-circle", size=20, color=STATUS_FAILED))
                f_lbl.configure(text_color=STATUS_FAILED)
                if f_cnt:
                    f_cnt.configure(text_color=STATUS_FAILED)
            else:
                f_frame.configure(fg_color="transparent")
                f_ind.configure(fg_color="transparent")
                f_ico.configure(image=get_icon("warning-circle", size=20, color=TEXT_SECONDARY))
                f_lbl.configure(text_color=TEXT_SECONDARY)
                if f_cnt:
                    f_cnt.configure(text_color=TEXT_MUTED)

        # Settings styling
        set_selected = (self._active == "settings")
        s_frame = self._row_frames.get("settings")
        s_ind = self._indicators.get("settings")
        s_ico = self._icons.get("settings")
        s_lbl = self._labels.get("settings")

        if s_frame and s_ind and s_ico and s_lbl:
            s_frame.configure(fg_color=BG_HOVER if set_selected else "transparent")
            s_ind.configure(fg_color=ACCENT_PRIMARY if set_selected else "transparent")
            s_ico.configure(image=get_icon("gear-six", size=20, color=TEXT_PRIMARY if set_selected else TEXT_SECONDARY))
            s_lbl.configure(text_color=TEXT_PRIMARY if set_selected else TEXT_SECONDARY)

    def update_counts(self, queue_count: int = 0, failed_count: int = 0) -> None:
        self._queue_count = queue_count
        self._failed_count = failed_count

        if "queue" in self._counts:
            self._counts["queue"].configure(text=str(queue_count))
        if "failed" in self._counts:
            self._counts["failed"].configure(text=str(failed_count))

        self._apply_active_styles()
