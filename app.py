"""Main application window and coordinator."""

from __future__ import annotations

import queue
import sys
from pathlib import Path

import customtkinter as ctk

import core.settings as settings_module
from core.downloader import Downloader, fetch_info
from core.clipboard_watcher import ClipboardWatcher
from core.updater import check_update_async, update_ytdlp_async, get_installed_version, _IS_FROZEN
from ui.sidebar import Sidebar
from ui.url_input import UrlInputPanel
from ui.queue_panel import QueuePanel
from ui.settings_panel import SettingsPanel
from ui.batch_dialog import BatchDialog
from ui.toast import Toast
from ui.theme import (
    BG_CANVAS,
    BG_SIDEBAR,
    BORDER_COLOR,
    ACCENT_PRIMARY,
    TEXT_MUTED,
    FONT_UI,
    FONT_MONO,
    set_base_font_size,
)
from ui.icons import get_icon

import ctypes
from PIL import Image

class KlipwerkApp(ctk.CTk):

    MIN_W, MIN_H = 960, 640

    def __init__(self, settings: dict | None = None):
        super().__init__()

        self.settings = settings if settings is not None else settings_module.load()
        self._apply_theme()

        self.title("Klipwerk")
        self.geometry("1180x740")
        self.minsize(self.MIN_W, self.MIN_H)

        base_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        self._icon_photo = None
        self._icon_png_path = base_dir / "assets" / "icon.png"
        self._icon_ico_path = base_dir / "assets" / "icon.ico"
        self._set_window_icon()
        self.after(100, self._set_window_icon)

        self._enable_dwm_dark_mode()

        self._update_q: queue.Queue = queue.Queue()
        self._downloader = Downloader(max_workers=self.settings.get("max_concurrent", 3))

        self._build_layout()
        self.bind("<Control-v>", self._on_global_paste)

        self._clip_watcher = ClipboardWatcher(self._on_clipboard_url)
        if self.settings.get("clipboard_watcher", True):
            self._clip_watcher.start()

        self.after(120, self._drain_queue)
        self.after(2000, self._check_ytdlp_update)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_window_icon(self) -> None:
        """Set window and taskbar icon."""
        try:
            if sys.platform == "win32" and self._icon_ico_path.exists():
                ico_path = str(self._icon_ico_path)
                try:
                    self.iconbitmap(ico_path)
                except Exception:
                    pass
                self.update_idletasks()
                try:
                    hwnd = int(self.wm_frame(), 16)
                except Exception:
                    hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
                cx_big = ctypes.windll.user32.GetSystemMetrics(11)
                cy_big = ctypes.windll.user32.GetSystemMetrics(12)
                cx_small = ctypes.windll.user32.GetSystemMetrics(49)
                cy_small = ctypes.windll.user32.GetSystemMetrics(50)
                hicon_big = ctypes.windll.user32.LoadImageW(None, ico_path, 1, cx_big, cy_big, 0x10)
                hicon_small = ctypes.windll.user32.LoadImageW(None, ico_path, 1, cx_small, cy_small, 0x10)
                for h in {hwnd, self.winfo_id(), ctypes.windll.user32.GetParent(self.winfo_id())}:
                    if h:
                        if hicon_big:
                            ctypes.windll.user32.SendMessageW(h, 0x80, 1, hicon_big)
                        if hicon_small:
                            ctypes.windll.user32.SendMessageW(h, 0x80, 0, hicon_small)
            elif self._icon_png_path.exists():
                from PIL import ImageTk
                img = Image.open(self._icon_png_path).resize((64, 64), Image.LANCZOS)
                self._icon_photo = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._icon_photo)
        except Exception:
            pass

    def _enable_dwm_dark_mode(self) -> None:
        if sys.platform != "win32" or not hasattr(ctypes, "windll"):
            return
        try:
            self.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            # DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val), ctypes.sizeof(val))
            # DWMWA_CAPTION_COLOR = 35 (COLORREF 0x001C1917 for #17191C)
            col = ctypes.c_int(0x001C1917)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(col), ctypes.sizeof(col))
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ── Sidebar (132px fixed) ─────────────────────────────────────
        self._sidebar = Sidebar(
            self,
            on_nav=self._switch_view,
            settings=self.settings,
            on_theme_toggle=self._toggle_theme,
            on_update_click=self._on_update_click,
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")

        # ── Main content container ────────────────────────────────────
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(1, weight=1)

        # URL input strip & toolbar (top)
        self._url_input = UrlInputPanel(
            self._content,
            on_add_urls=self._on_add_urls,
            on_batch_click=self._open_batch_dialog,
            on_start_all=self._on_toolbar_start_all,
            on_pause_all=self._on_toolbar_pause_all,
            on_clear_done=self._on_toolbar_clear_done,
            on_format_changed=self._on_toolbar_format_changed,
        )
        self._url_input.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        # Download queue (fills remaining space)
        self._queue_panel = QueuePanel(
            self._content,
            on_download=self._start_download,
            on_remove=self._remove_card,
            on_cancel=self._cancel_download,
        )
        self._queue_panel.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Settings panel – rendered in the same container, hidden initially
        self._settings_panel = SettingsPanel(
            self._content,
            settings=self.settings,
            on_save=self._on_settings_save,
        )

        self.grid_rowconfigure(1, weight=0)

        # ── Status Bar (26px tall, 11px muted text, hairline separated) ──
        self._status_bar = ctk.CTkFrame(
            self,
            height=26,
            corner_radius=0,
            fg_color="#17191C",
            border_width=1,
            border_color="#23262A",
        )
        self._status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self._status_bar.grid_propagate(False)
        self._status_bar.grid_rowconfigure(0, weight=1)
        self._status_bar.grid_columnconfigure(1, weight=1)

        # Left: Active count and combined speed
        self._sb_left = ctk.CTkLabel(
            self._status_bar,
            text="0 active · 0 KB/s",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_MUTED,
            anchor="w",
        )
        self._sb_left.grid(row=0, column=0, padx=12, sticky="w")

        # Middle: Truncated output path
        self._sb_mid = ctk.CTkLabel(
            self._status_bar,
            text=self._format_output_path(),
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_MUTED,
            anchor="center",
        )
        self._sb_mid.grid(row=0, column=1, sticky="ew")

        # Right: yt-dlp version
        ver = get_installed_version()
        self._sb_right = ctk.CTkLabel(
            self._status_bar,
            text=f"yt-dlp {ver}" if ver else "yt-dlp",
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=TEXT_MUTED,
            anchor="e",
        )
        self._sb_right.grid(row=0, column=2, padx=12, sticky="e")

        self._current_view = "downloads"

    def _format_output_path(self) -> str:
        p = self.settings.get("output_dir", str(Path.home() / "Downloads"))
        if len(p) > 42:
            return p[:18] + "..." + p[-21:]
        return p

    def _update_status_bar(self) -> None:
        try:
            cards = self._queue_panel.cards
            active_cards = [c for c in cards if c.status in ("downloading", "converting", "fetching", "active")]
            active_count = len(active_cards)
            total_bps = sum(getattr(c, "_speed_bps", 0.0) for c in active_cards)

            if total_bps <= 0:
                speed_str = "0 KB/s"
            elif total_bps < 1_048_576:
                speed_str = f"{total_bps / 1024:.1f} KB/s"
            else:
                speed_str = f"{total_bps / 1_048_576:.1f} MB/s"

            if active_count > 0:
                self._sb_left.configure(
                    text=f"{active_count} active · {speed_str}",
                    text_color="#6FD1DE",
                )
            else:
                self._sb_left.configure(
                    text=f"0 active · 0 KB/s",
                    text_color="#6C6F73",
                )
            self._sb_mid.configure(text=self._format_output_path())

            if hasattr(self._sidebar, "update_counts"):
                failed_c = sum(1 for c in cards if c.status == "error")
                queue_c = len(cards) - failed_c
                self._sidebar.update_counts(
                    queue_count=queue_c,
                    failed_count=failed_c,
                )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _switch_view(self, view: str) -> None:
        if self._current_view == "settings" and hasattr(self, "_settings_panel"):
            try:
                self._on_settings_save(self._settings_panel.get_current_dict())
            except Exception:
                pass
        if view in ("queue", "failed", "all", "downloads"):
            filter_key = "failed" if view == "failed" else "queue"
            if self._current_view != "downloads":
                self._current_view = "downloads"
                self._settings_panel.grid_remove()
                self._url_input.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
                self._queue_panel.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))
            self._queue_panel.set_filter(filter_key)
        elif view == "settings":
            if self._current_view == "settings":
                return
            self._current_view = "settings"
            self._url_input.grid_remove()
            self._queue_panel.grid_remove()
            self._settings_panel.grid(
                row=0, column=0, rowspan=2, sticky="nsew", padx=16, pady=16
            )

    # ------------------------------------------------------------------
    # Toolbar Actions
    # ------------------------------------------------------------------

    def _on_toolbar_start_all(self) -> None:
        self._queue_panel._download_all()

    def _on_toolbar_pause_all(self) -> None:
        for card in self._queue_panel.cards:
            if card.status in ("downloading", "converting", "fetching", "active"):
                self._downloader.cancel(card.card_id)
                card.stop_download()

    def _on_toolbar_clear_done(self) -> None:
        self._queue_panel._clear_completed()

    def _on_toolbar_format_changed(self, val: str) -> None:
        parts = [p.strip() for p in val.split("·")]
        if len(parts) == 2:
            q_part, f_part = parts[0], parts[1]
            if q_part.lower() == "best":
                q_str = "Best (auto)"
            elif q_part.lower() == "audio":
                q_str = f"{f_part.upper()} Audio"
            elif q_part == "1080p":
                q_str = "1080p Full HD"
            elif q_part == "720p":
                q_str = "720p HD"
            elif q_part == "480p":
                q_str = "480p SD"
            else:
                q_str = q_part
            f_str = f_part.upper()
            self._default_quality = q_str
            self._default_format = f_str
            self.settings["default_quality"] = q_str
            self.settings["default_format"] = f_str
            settings_module.save(self.settings)

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _apply_theme(self) -> None:
        ctk.set_default_color_theme("blue")
        ctk.set_appearance_mode("dark")
        set_base_font_size(self.settings.get("font_size", 12))
        self.configure(fg_color=BG_CANVAS)

    def _toggle_theme(self) -> None:
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG_CANVAS)
        self._sidebar.update_theme_icon("dark")

    # ------------------------------------------------------------------
    # URL / Download flow
    # ------------------------------------------------------------------

    def _open_batch_dialog(self) -> None:
        BatchDialog(self, on_confirm=self._on_batch_confirm)

    def _on_batch_confirm(
        self, urls: list[str], quality: str, video_format: str, auto_start: bool
    ) -> None:
        added_cards = []
        for url in urls:
            url = url.strip()
            if not url:
                continue
            if not self.settings.get("allow_duplicates", False) and self._queue_panel.has_url(url):
                continue
            card = self._queue_panel.add_card(
                url,
                self.settings,
                self._update_q,
                quality=quality,
                video_format=video_format,
            )
            added_cards.append(card)

        if added_cards:
            Toast(self, "Batch Added", f"Added {len(added_cards)} link(s) to queue", "📑")
            if auto_start:
                def _start_all():
                    for card in added_cards:
                        card.start_download()
                self.after(200, _start_all)
        else:
            Toast(self, "No Links Added", "All entered URLs are duplicates or empty", "ℹ")

    def _on_add_urls(self, urls: list[str]) -> None:
        for url in urls:
            url = url.strip()
            if not url:
                continue
            if not self.settings.get("allow_duplicates", False) and self._queue_panel.has_url(url):
                Toast(self, "Duplicate Skipped", f"Already in queue: {url[:35]}...", "ℹ")
                continue

            # Smart Playlist Extraction
            if "list=" in url:
                Toast(self, "Unpacking Playlist", "Analyzing playlist items...", "📑")
                import threading
                def _unpack_worker(p_url=url):
                    try:
                        p_info = fetch_info(p_url, is_playlist=True)
                        entries = p_info.get("entries", []) if p_info else []
                        entry_urls = []
                        for e in entries:
                            if isinstance(e, dict):
                                e_url = e.get("url") or e.get("webpage_url")
                                if e_url:
                                    if not e_url.startswith("http"):
                                        e_url = f"https://www.youtube.com/watch?v={e_url}"
                                    entry_urls.append(e_url)
                        if entry_urls:
                            self._update_q.put(("playlist_unpacked", entry_urls, p_info.get("title", "Playlist")))
                            return
                    except Exception:
                        pass
                    # If flat extract failed or returned no items, fall back to adding single card
                    self._update_q.put(("playlist_fallback", p_url))

                threading.Thread(target=_unpack_worker, daemon=True).start()
            else:
                self._queue_panel.add_card(
                    url,
                    self.settings,
                    self._update_q,
                    quality=getattr(self, "_default_quality", None),
                    video_format=getattr(self, "_default_format", None),
                )

    def _on_global_paste(self, event) -> None:
        # If focus is on an Entry or Textbox widget, allow native paste
        w = self.focus_get()
        if w and (isinstance(w, (ctk.CTkEntry, ctk.CTkTextbox)) or hasattr(w, "_entry")):
            return
        try:
            import pyperclip
            text = pyperclip.paste().strip()
            if text and text.startswith("http"):
                self._on_add_urls([text])
                Toast(self, "Link Added", "URL detected and added to queue", "📋")
        except Exception:
            pass

    def _start_download(
        self, card_id: str, url: str, quality: str, video_format: str, custom_title: str = ""
    ) -> None:
        output_dir = self.settings.get("output_dir", str(Path.home() / "Downloads"))
        ffmpeg_path = self.settings.get("ffmpeg_path", "")
        add_metadata = self.settings.get("add_metadata", True)
        hw_accel = self.settings.get("hw_accel", "auto")
        custom_args = self.settings.get("custom_args", "")

        self._downloader.submit(
            card_id=card_id,
            url=url,
            quality=quality,
            video_format=video_format,
            output_dir=output_dir,
            progress_callback=lambda cid, d: self._update_q.put(("progress", cid, d)),
            done_callback=lambda cid, path="": self._update_q.put(("done", cid, path)),
            error_callback=lambda cid, e: self._update_q.put(("error", cid, e)),
            ffmpeg_path=ffmpeg_path,
            add_metadata=add_metadata,
            hw_accel=hw_accel,
            custom_args=custom_args,
            custom_title=custom_title,
        )

    def _cancel_download(self, card_id: str) -> None:
        self._downloader.cancel(card_id)

    def _remove_card(self, card_id: str) -> None:
        self._downloader.cancel(card_id)
        self._queue_panel.remove_card(card_id)

    # ------------------------------------------------------------------
    # Clipboard watcher callback (called from background thread)
    # ------------------------------------------------------------------

    def _on_clipboard_url(self, url: str) -> None:
        self._update_q.put(("clipboard_url", url))

    # ------------------------------------------------------------------
    # yt-dlp Auto-updater
    # ------------------------------------------------------------------

    def _check_ytdlp_update(self) -> None:
        check_update_async(
            lambda cur, lat, need: self._update_q.put(("yt_update_check", cur, lat, need))
        )

    def _on_update_click(self, latest_ver: str) -> None:
        # Show prompt dialog
        top = ctk.CTkToplevel(self)
        top.title("yt-dlp Update")
        top.geometry("390x220")
        top.resizable(False, False)
        top.transient(self)
        top.grab_set()

        cur_ver = get_installed_version()

        ctk.CTkLabel(
            top,
            text=" yt-dlp Update Available",
            image=get_icon("arrows-clockwise", size=18, color=ACCENT_PRIMARY),
            compound="left",
            font=ctk.CTkFont(family=FONT_UI, size=15, weight="bold"),
        ).pack(pady=(20, 8))

        if _IS_FROZEN:
            desc_text = (
                f"Installed: {cur_ver}\nLatest: {latest_ver}\n\n"
                "To get the latest engine updates, download the latest\n"
                "Klipwerk release package from GitHub."
            )
            btn_text = "Open Releases"
        else:
            desc_text = (
                f"Installed: {cur_ver}\nLatest: {latest_ver}\n\n"
                "For controlled updates, use the official release channel\n"
                "or run pip upgrade commands manually in your environment."
            )
            btn_text = "Open Releases"

        ctk.CTkLabel(
            top,
            text=desc_text,
            font=ctk.CTkFont(family=FONT_MONO, size=11),
            text_color=("gray40", "gray60"),
            justify="center",
        ).pack(pady=(0, 16))

        btn_box = ctk.CTkFrame(top, fg_color="transparent")
        btn_box.pack(pady=(0, 12))

        def _do_up():
            top.destroy()
            Toast(self, "Opening Releases", "Redirecting to official release channel...", "🔗")
            update_ytdlp_async(
                lambda ok, val: self._update_q.put(("yt_update_done", ok, val))
            )

        ctk.CTkButton(
            btn_box,
            text=btn_text,
            width=110,
            height=32,
            font=ctk.CTkFont(family=FONT_UI, size=12, weight="bold"),
            command=_do_up,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_box,
            text="Later",
            width=80,
            height=32,
            font=ctk.CTkFont(family=FONT_UI, size=12),
            fg_color=("gray85", "#263548"),
            hover_color=("gray75", "#33465e"),
            text_color=("gray15", "gray85"),
            command=top.destroy,
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Settings save
    # ------------------------------------------------------------------

    def _on_settings_save(self, new_settings: dict) -> None:
        old_workers = self.settings.get("max_concurrent", 3)
        old_clipboard = self.settings.get("clipboard_watcher", True)

        self.settings.update(new_settings)
        settings_module.save(self.settings)

        self._default_quality = new_settings.get("default_quality", "Best (auto)")
        self._default_format = new_settings.get("default_format", "MP4")

        # Apply theme immediately
        ctk.set_appearance_mode("dark")
        self._sidebar.update_theme_icon("dark")

        # Apply font size immediately
        if "font_size" in new_settings:
            set_base_font_size(new_settings["font_size"])

        # Resize thread pool if needed
        new_workers = self.settings.get("max_concurrent", 3)
        if new_workers != old_workers:
            self._downloader.update_workers(new_workers)

        # Toggle clipboard watcher
        new_clipboard = self.settings.get("clipboard_watcher", True)
        if new_clipboard != old_clipboard:
            if new_clipboard:
                self._clip_watcher.start()
            else:
                self._clip_watcher.stop()

    # ------------------------------------------------------------------
    # Main-thread message drain loop
    # ------------------------------------------------------------------

    def _drain_queue(self) -> None:
        try:
            while True:
                try:
                    msg = self._update_q.get_nowait()
                except queue.Empty:
                    break

                try:
                    kind = msg[0]

                    if kind == "progress":
                        _, cid, data = msg
                        self._queue_panel.update_progress(cid, data)

                    elif kind == "done":
                        cid = msg[1]
                        out_path = msg[2] if len(msg) > 2 else ""
                        self._queue_panel.update_done(cid, out_path)
                        title = self._queue_panel.get_card_title(cid)
                        Toast(self, "Download Complete", f"{title[:40]} ready", "✅")

                    elif kind == "error":
                        _, cid, err = msg
                        self._queue_panel.update_error(cid, err)
                        title = self._queue_panel.get_card_title(cid)
                        Toast(self, "Download Failed", f"{title[:30]}: {str(err)[:40]}", "⚠")

                    elif kind == "info":
                        _, cid, info = msg
                        self._queue_panel.update_info(cid, info)

                    elif kind == "thumbnail":
                        _, cid, img = msg
                        self._queue_panel.update_thumbnail(cid, img)

                    elif kind == "clipboard_url":
                        _, url = msg
                        self._handle_clipboard_url(url)

                    elif kind == "playlist_unpacked":
                        _, entry_urls, pl_title = msg
                        added_count = 0
                        for u in entry_urls:
                            if not self.settings.get("allow_duplicates", False) and self._queue_panel.has_url(u):
                                continue
                            self._queue_panel.add_card(u, self.settings, self._update_q)
                            added_count += 1
                        Toast(self, "Playlist Imported", f"Added {added_count} items from {pl_title[:25]}", "📑")

                    elif kind == "playlist_fallback":
                        _, p_url = msg
                        if self.settings.get("allow_duplicates", False) or not self._queue_panel.has_url(p_url):
                            self._queue_panel.add_card(p_url, self.settings, self._update_q)

                    elif kind == "yt_update_check":
                        _, cur, lat, need = msg
                        if need:
                            self._sidebar.show_update_badge(lat)
                            Toast(self, "Update Available", f"yt-dlp v{lat} is available", "🚀")

                    elif kind == "yt_update_done":
                        _, ok, val = msg
                        if ok:
                            self._sidebar.hide_update_badge()
                            Toast(self, "Release Channel", str(val)[:60], "✅")
                        else:
                            Toast(self, "Update Failed", f"Could not update: {val[:40]}", "⚠")

                    elif kind == "repack":
                        self._queue_panel._repack()
                except Exception:
                    pass

        except Exception:
            pass
        finally:
            try:
                self._update_status_bar()
            except Exception:
                pass
            self.after(120, self._drain_queue)

    def _handle_clipboard_url(self, url: str) -> None:
        if not self.settings.get("clipboard_watcher", True):
            return
        if self._queue_panel.has_url(url):
            return

        # Switch to downloads view and pre-fill URL
        if self._current_view != "downloads":
            self._switch_view("queue")
            self._sidebar.set_active("queue")

        self._url_input.set_url(url)
        self._url_input.flash_notification("📋  Link detected from clipboard!")

    # ------------------------------------------------------------------
    # Clean shutdown
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        try:
            if hasattr(self, "_settings_panel"):
                new_s = self._settings_panel.get_current_dict()
                self._on_settings_save(new_s)
            else:
                settings_module.save(self.settings)
        except Exception:
            pass
        self._clip_watcher.stop()
        self._downloader.shutdown()
        self.destroy()
