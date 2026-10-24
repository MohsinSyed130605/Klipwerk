"""Download queue list container."""

from __future__ import annotations

import uuid
import customtkinter as ctk

from ui.download_card import DownloadCard
from ui.theme import (
    BORDER_COLOR,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_UI,
    FONT_MONO,
)


class QueuePanel(ctk.CTkFrame):
    """
    Queue container hosting rich Vividl DownloadCard items.
    """

    def __init__(self, parent, *, on_download, on_remove, on_cancel=None, **kwargs):
        super().__init__(
            parent,
            corner_radius=0,
            fg_color="transparent",
            border_width=0,
            **kwargs,
        )
        self._on_download = on_download
        self._on_remove_ext = on_remove
        self._on_cancel_ext = on_cancel
        self._cards: dict[str, DownloadCard] = {}
        self._active_filter = "all"

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build()

    def _build(self) -> None:
        # ── Queue Section Header ─────────────────────────────────────
        hdr = ctk.CTkFrame(self, height=26, corner_radius=0, fg_color="transparent")
        hdr.grid(row=0, column=0, sticky="ew", padx=6, pady=(0, 4))
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(1, weight=1)

        self._title_lbl = ctk.CTkLabel(
            hdr,
            text="Queue",
            font=ctk.CTkFont(family=FONT_UI, size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self._title_lbl.grid(row=0, column=0, sticky="w")

        self._count_lbl = ctk.CTkLabel(
            hdr,
            text="0 items",
            font=ctk.CTkFont(family=FONT_MONO, size=12),
            text_color=TEXT_MUTED,
        )
        self._count_lbl.grid(row=0, column=1, sticky="w", padx=(8, 0))

        # ── 1px Divider Line ─────────────────────────────────────────
        hairline = ctk.CTkFrame(self, height=1, fg_color=BORDER_COLOR, border_width=0)
        hairline.grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 4))

        # ── Scrollable Queue Area ────────────────────────────────────
        self._scroll = ctk.CTkScrollableFrame(
            self,
            corner_radius=0,
            fg_color="transparent",
        )
        self._scroll.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self._scroll.grid_columnconfigure(0, weight=1)

        # Empty state label
        self._empty_lbl = ctk.CTkLabel(
            self._scroll,
            text="No downloads in queue. Paste a video link or click + Add above.",
            font=ctk.CTkFont(family=FONT_UI, size=12),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self._empty_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=20)

    # ------------------------------------------------------------------
    # Public: adding / removing cards
    # ------------------------------------------------------------------

    @property
    def cards(self) -> list[DownloadCard]:
        return list(self._cards.values())

    def get_card(self, card_id: str) -> DownloadCard | None:
        return self._cards.get(card_id)

    def add_card(
        self,
        url: str,
        settings: dict,
        update_queue,
        quality: str | None = None,
        video_format: str | None = None,
    ) -> DownloadCard:
        """Create and display a new Vividl-style DownloadCard."""
        if self._empty_lbl.winfo_ismapped():
            self._empty_lbl.grid_remove()

        card_id = str(uuid.uuid4())
        card = DownloadCard(
            self._scroll,
            card_id=card_id,
            url=url,
            settings=settings,
            update_queue=update_queue,
            on_download=self._on_download,
            on_remove=self._remove_card,
            on_cancel=self._on_cancel_ext,
        )
        if quality and video_format:
            card.set_format(quality, video_format)

        self._cards[card_id] = card
        self._repack()
        return card

    def _remove_card(self, card_id: str) -> None:
        """Called by card's own Remove button."""
        self._on_remove_ext(card_id)

    def remove_card(self, card_id: str) -> None:
        """Destroy and unregister a card (called from app.py)."""
        if card_id not in self._cards:
            return
        self._cards[card_id].destroy()
        del self._cards[card_id]
        self._repack()

    def _repack(self) -> None:
        visible_idx = 0
        total = len(self._cards)
        self._count_lbl.configure(text=f"{total} item{'s' if total != 1 else ''}")

        for card in self._cards.values():
            if self._matches_filter(card):
                card.grid(row=visible_idx, column=0, sticky="ew", padx=6, pady=4)
                visible_idx += 1
            else:
                card.grid_remove()

        if not self._cards:
            self._empty_lbl.grid(row=0, column=0, sticky="w", padx=10, pady=20)
        elif self._empty_lbl.winfo_ismapped():
            self._empty_lbl.grid_remove()

    def set_filter(self, filter_key: str) -> None:
        self._active_filter = filter_key
        self._repack()

    def _matches_filter(self, card: DownloadCard) -> bool:
        if self._active_filter in ("queue", "all"):
            return card.status != "error"
        if self._active_filter == "failed":
            return card.status == "error"
        return True

    # ------------------------------------------------------------------
    # Public: status updates (forwarded from app.py's update loop)
    # ------------------------------------------------------------------

    def update_progress(self, card_id: str, data: dict) -> None:
        if card_id in self._cards:
            self._cards[card_id].update_progress(data)

    def update_done(self, card_id: str, output_path: str = "") -> None:
        if card_id in self._cards:
            self._cards[card_id].update_done(output_path)

    def update_error(self, card_id: str, msg: str) -> None:
        if card_id in self._cards:
            self._cards[card_id].update_error(msg)

    def update_info(self, card_id: str, info: dict) -> None:
        if card_id in self._cards:
            self._cards[card_id].apply_info(info)

    def update_thumbnail(self, card_id: str, pil_img) -> None:
        if card_id in self._cards:
            self._cards[card_id].apply_thumbnail(pil_img)

    def get_card_title(self, card_id: str) -> str:
        if card_id in self._cards:
            return self._cards[card_id]._video_title
        return "Video"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_url(u: str) -> str:
        u = u.strip().rstrip("/")
        try:
            from urllib.parse import urlparse, urlunparse
            p = urlparse(u)
            if p.netloc:
                netloc = p.netloc.lower()
                scheme = p.scheme.lower()
                path = p.path.rstrip("/")
                return urlunparse((scheme, netloc, path, p.params, p.query, p.fragment))
        except Exception:
            pass
        return u.lower()

    def has_url(self, url: str) -> bool:
        target = self._normalize_url(url)
        return any(self._normalize_url(c.url) == target for c in self._cards.values())

    def _download_all(self) -> None:
        for card in list(self._cards.values()):
            card.start_download_if_ready()

    def _clear_completed(self) -> None:
        done_ids = [
            cid for cid, card in self._cards.items()
            if card.status == "done"
        ]
        for cid in done_ids:
            self.remove_card(cid)
