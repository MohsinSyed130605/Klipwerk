"""Background clipboard monitor for media URLs."""

import re
import threading
import time

try:
    import pyperclip
    _HAS_PYPERCLIP = True
except ImportError:
    _HAS_PYPERCLIP = False

# Broad URL pattern covering the most popular video platforms
_URL_RE = re.compile(
    r"https?://(www\.)?"
    r"(youtube\.com|youtu\.be|vimeo\.com|twitter\.com|x\.com|"
    r"instagram\.com|tiktok\.com|twitch\.tv|dailymotion\.com|"
    r"reddit\.com|facebook\.com|fb\.watch|bilibili\.com|"
    r"nicovideo\.jp|soundcloud\.com|rumble\.com|odysee\.com|"
    r"streamable\.com|medal\.tv|clips\.twitch\.tv|vm\.tiktok\.com)"
    r"[^\s\"'<>]*",
    re.IGNORECASE,
)


def extract_first_url(text: str) -> str | None:
    """Return the first video URL found in *text*, or None."""
    if not text:
        return None
    m = _URL_RE.search(text.strip())
    return m.group(0) if m else None


class ClipboardWatcher:
    """Polls the clipboard every *interval* seconds and calls *on_url_detected*
    with any newly-found video URL (called from the watcher thread)."""

    def __init__(self, on_url_detected, interval: float = 1.5):
        self._callback = on_url_detected
        self._interval = interval
        self._last = ""
        self._running = False
        self._thread: threading.Thread | None = None

    # ------------------------------------------------------------------
    def start(self) -> None:
        if not _HAS_PYPERCLIP or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="ClipboardWatcher")
        self._thread.start()

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    def _loop(self) -> None:
        while self._running:
            try:
                text = pyperclip.paste()
                if text and text != self._last:
                    self._last = text
                    url = extract_first_url(text)
                    if url:
                        self._callback(url)
            except Exception:
                pass
            time.sleep(self._interval)
