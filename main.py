"""Application launcher and runtime dependency bootstrapper."""

from __future__ import annotations

import importlib.util
import hashlib
import io
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import zipfile
from pathlib import Path

if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("MohsinSyed.Klipwerk.1.0")
    except Exception:
        pass

APP_DIR = Path(__file__).parent.resolve()
BIN_DIR = APP_DIR / "bin"

_OS = platform.system().lower()
_ARCH = platform.machine().lower()
_IS_WIN = _OS == "windows"
_IS_LINUX = _OS == "linux"

FFMPEG_NAME = "ffmpeg.exe" if _IS_WIN else "ffmpeg"
FFPROBE_NAME = "ffprobe.exe" if _IS_WIN else "ffprobe"
FFMPEG_EXE  = BIN_DIR / FFMPEG_NAME
FFPROBE_EXE = BIN_DIR / FFPROBE_NAME
_WANTED     = {FFMPEG_NAME, FFPROBE_NAME}
_HAS_CONSOLE: bool = sys.stdout is not None


def _log(msg: str) -> None:
    if _HAS_CONSOLE:
        print(msg, flush=True)


# Dependency management
_REQUIRED = [
    ("customtkinter", "customtkinter>=5.2.0", "CustomTkinter"),
    ("yt_dlp",        "yt-dlp",               "yt-dlp"),
    ("PIL",           "Pillow",               "Pillow"),
    ("pyperclip",     "pyperclip",            "pyperclip"),
    ("requests",      "requests",             "requests"),
    ("mutagen",       "mutagen>=1.48.0",      "mutagen"),
    ("resvg_py",      "resvg-py>=0.5.0",      "resvg-py"),
]


def _pip_install(pip_name: str, display: str) -> None:
    _log(f"  Installing {display}…")
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", pip_name, "-q"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def bootstrap_pip() -> None:
    if getattr(sys, "frozen", False):
        return
    missing = [t for t in _REQUIRED if importlib.util.find_spec(t[0]) is None]
    if not missing:
        return
    _log("Klipwerk – Installing Python dependencies (one-time setup)")
    _log("=" * 60)
    for _, pip_name, display in missing:
        try:
            _pip_install(pip_name, display)
        except subprocess.CalledProcessError:
            if _HAS_CONSOLE:
                print(f"\n  ERROR: could not install {display}.")
                print(f"  Please run:  pip install {pip_name}")
                input("\nPress Enter to exit…")
            sys.exit(1)
    _log("  [OK] All Python packages ready.\n")


# ---------------------------------------------------------------------------
# 2 ── ffmpeg bootstrap
# ---------------------------------------------------------------------------

def _ffmpeg_on_path() -> str | None:
    return shutil.which("ffmpeg")


def _local_ok() -> bool:
    return FFMPEG_EXE.exists() and FFPROBE_EXE.exists()


# ── Console mode: progress bar printed to terminal ─────────────────────────

def _console_progress(done: int, total: int, speed_kbps: float) -> None:
    if total <= 0:
        return
    pct   = min(done / total * 100, 100)
    bar   = "█" * int(pct / 5) + "░" * (20 - int(pct / 5))
    mb_d  = done  / 1_048_576
    mb_t  = total / 1_048_576
    print(f"\r  [{bar}] {pct:5.1f}%  {mb_d:.1f}/{mb_t:.1f} MB  {speed_kbps:.0f} KB/s   ",
          end="", flush=True)


# ── No-console mode: tiny tkinter progress window ─────────────────────────

class _FfmpegDialog:
    """Lightweight tkinter window shown when no console is attached."""

    def __init__(self) -> None:
        import tkinter as tk
        from tkinter import ttk

        self._root = tk.Tk()
        self._root.title("Klipwerk – First-time Setup")
        self._root.geometry("500x160")
        self._root.resizable(False, False)
        self._root.configure(bg="#1e293b")
        self._root.protocol("WM_DELETE_WINDOW", lambda: None)  # block X button

        # Center on screen
        self._root.update_idletasks()
        sw, sh = self._root.winfo_screenwidth(), self._root.winfo_screenheight()
        self._root.geometry(f"500x160+{(sw-500)//2}+{(sh-160)//2}")

        tk.Label(
            self._root, text="Downloading ffmpeg  (one-time, ~120 MB)",
            font=("Segoe UI", 12, "bold"), bg="#1e293b", fg="white",
        ).pack(pady=(18, 4))

        self._status = tk.StringVar(value="Connecting…")
        tk.Label(
            self._root, textvariable=self._status,
            font=("Segoe UI", 10), bg="#1e293b", fg="#94a3b8",
        ).pack(pady=(0, 8))

        self._pct = tk.DoubleVar(value=0)
        style = ttk.Style(self._root)
        style.theme_use("clam")
        style.configure("S.Horizontal.TProgressbar",
                        troughcolor="#0f172a", background="#3b5bdb",
                        bordercolor="#0f172a", lightcolor="#3b5bdb", darkcolor="#3b5bdb")

        ttk.Progressbar(
            self._root, length=440, mode="determinate",
            variable=self._pct, style="S.Horizontal.TProgressbar",
        ).pack(padx=30)

        tk.Label(
            self._root,
            text="ffmpeg is needed for merging streams and audio extraction.",
            font=("Segoe UI", 9), bg="#1e293b", fg="#475569",
        ).pack(pady=(8, 0))

        self._root.update()

    def update(self, done: int, total: int, speed_kbps: float) -> None:
        if total > 0:
            self._pct.set(min(done / total * 100, 100))
            self._status.set(
                f"{done/1_048_576:.1f} / {total/1_048_576:.1f} MB"
                f"  ·  {speed_kbps:.0f} KB/s"
            )
        try:
            self._root.update()
        except Exception:
            pass

    def finish(self) -> None:
        self._pct.set(100)
        self._status.set("✓  ffmpeg installed successfully!")
        try:
            self._root.update()
            self._root.after(1500, self._root.destroy)
            self._root.mainloop()
        except Exception:
            pass

    def show_error(self, msg: str) -> None:
        self._status.set(f"Warning: {msg[:80]}")
        try:
            self._root.update()
            self._root.after(3500, self._root.destroy)
            self._root.mainloop()
        except Exception:
            pass


# ── Shared download core ───────────────────────────────────────────────────

def _get_ffmpeg_download_info() -> tuple[str, str] | None:
    """Return (download_url, archive_type) based on platform/architecture."""
    if _IS_WIN:
        return (
            "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
            "zip",
        )
    elif _IS_LINUX:
        if "aarch64" in _ARCH or "arm64" in _ARCH:
            return (
                "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linuxarm64-gpl.tar.xz",
                "tar.xz",
            )
        else:
            return (
                "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz",
                "tar.xz",
            )
    return None


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a local file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65_536):
            h.update(chunk)
    return h.hexdigest().lower()


def _fetch_upstream_checksums() -> dict[str, str]:
    """
    Fetch and parse upstream checksums.sha256 if available.
    Returns mapping of {filename: sha256_hex}.
    """
    checksum_url = (
        "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/checksums.sha256"
    )
    mapping: dict[str, str] = {}
    try:
        req = urllib.request.Request(checksum_url, headers={"User-Agent": "Klipwerk/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read().decode("utf-8", "ignore")
            for line in raw.splitlines():
                parts = line.strip().split()
                if len(parts) >= 2:
                    sha = parts[0].strip().lower()
                    fname = parts[1].strip().lstrip("*")
                    mapping[fname] = sha
    except Exception as exc:
        _log(f"  [INFO] Could not retrieve upstream checksums.sha256: {exc}")
    return mapping


def _verify_archive_checksum(archive_path: Path, download_url: str) -> None:
    """
    Verify SHA-256 checksum of downloaded archive against upstream source.
    Raises RuntimeError on hash mismatch. Logs warning if no checksum is available.
    """
    actual_hash = _compute_sha256(archive_path)
    filename = Path(download_url).name

    checksums = _fetch_upstream_checksums()
    expected_hash = checksums.get(filename)

    if expected_hash:
        if actual_hash != expected_hash:
            raise RuntimeError(
                f"Security verification failed: SHA-256 mismatch for {filename}!\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual:   {actual_hash}\n"
                "Aborting extraction — archive may be corrupted or tampered with."
            )
        _log(f"  ✓  SHA-256 verified: {actual_hash[:16]}… (matches upstream release)")
    else:
        _log(f"  [SECURITY WARNING] No upstream SHA-256 checksum verified for {filename}.")
        _log(f"  Computed SHA-256: {actual_hash}")
        _log("  Proceeding with caution.")


def _download_ffmpeg(notify) -> None:
    """
    Download and extract static ffmpeg + ffprobe for current OS/architecture.
    *notify* is either (_console_progress) or an _FfmpegDialog instance.
    """
    dl_info = _get_ffmpeg_download_info()
    if not dl_info:
        raise RuntimeError("No automated static ffmpeg build available for this platform.")

    url, archive_type = dl_info
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    req   = urllib.request.Request(url, headers={"User-Agent": "Klipwerk/1.0"})
    start = time.monotonic()
    temp_archive = BIN_DIR / f"ffmpeg_temp.{archive_type}"

    try:
        with urllib.request.urlopen(req, timeout=120) as resp, open(temp_archive, "wb") as f_out:
            total = int(resp.headers.get("Content-Length", 0))
            done  = 0
            chunk = 65_536
            while True:
                block = resp.read(chunk)
                if not block:
                    break
                f_out.write(block)
                done += len(block)
                elapsed   = max(time.monotonic() - start, 0.001)
                speed_kbps = done / elapsed / 1024
                if callable(notify):
                    notify(done, total, speed_kbps)
                else:
                    notify.update(done, total, speed_kbps)

        if _HAS_CONSOLE:
            print()  # newline after progress bar
            print("  Verifying archive integrity…", flush=True)

        _verify_archive_checksum(temp_archive, url)

        if _HAS_CONSOLE:
            print("  Extracting executables…", flush=True)

        if archive_type == "zip":
            with zipfile.ZipFile(temp_archive) as zf:
                for entry in zf.namelist():
                    fname = Path(entry).name
                    if fname in _WANTED:
                        dest = BIN_DIR / fname
                        dest.write_bytes(zf.read(entry))
                        if not _IS_WIN:
                            try:
                                dest.chmod(dest.stat().st_mode | 0o755)
                            except Exception:
                                pass
                        _log(f"    ✓  {fname}  ({dest.stat().st_size // 1024:,} KB, sha256: {_compute_sha256(dest)[:12]}…)")
        elif archive_type.startswith("tar"):
            with tarfile.open(temp_archive, "r:*") as tf:
                for member in tf.getmembers():
                    fname = Path(member.name).name
                    if fname in _WANTED and member.isfile():
                        dest = BIN_DIR / fname
                        extracted = tf.extractfile(member)
                        if extracted:
                            dest.write_bytes(extracted.read())
                            if not _IS_WIN:
                                try:
                                    dest.chmod(dest.stat().st_mode | 0o755)
                                except Exception:
                                    pass
                            _log(f"    ✓  {fname}  ({dest.stat().st_size // 1024:,} KB, sha256: {_compute_sha256(dest)[:12]}…)")
    finally:
        temp_archive.unlink(missing_ok=True)

    if not FFMPEG_EXE.exists():
        raise RuntimeError(f"{FFMPEG_NAME} was not found in the downloaded archive.")


def bootstrap_ffmpeg(settings: dict) -> None:
    """Ensure ffmpeg is available, downloading if needed."""
    # Already in settings and file exists?
    configured = settings.get("ffmpeg_path", "")
    if configured and Path(configured).exists():
        return

    # On system PATH?
    path_loc = _ffmpeg_on_path()
    if path_loc:
        settings["ffmpeg_path"] = path_loc
        return

    # Already in bin/?
    if _local_ok():
        settings["ffmpeg_path"] = str(FFMPEG_EXE)
        return

    # ── Need to download ───────────────────────────────────────────────
    try:
        if _HAS_CONSOLE:
            _log("─" * 60)
            _log("  ffmpeg not found — downloading automatically (~120 MB).")
            _log("─" * 60)
            _download_ffmpeg(_console_progress)
            _log(f"\n  [OK] ffmpeg installed to: {FFMPEG_EXE}\n")
        else:
            dialog = _FfmpegDialog()
            try:
                _download_ffmpeg(dialog)
                dialog.finish()
            except Exception as exc:
                dialog.show_error(str(exc)[:120])
                return

        settings["ffmpeg_path"] = str(FFMPEG_EXE)

    except Exception as exc:
        _log(f"\n  [WARNING] Could not auto-download ffmpeg: {exc}")
        _log("  Audio extraction and stream merging will be unavailable.")
        _log("  You can install ffmpeg using your package manager (e.g. apt/brew)")
        _log("  or set the path manually in Settings → Advanced.\n")


def main() -> None:
    bootstrap_pip()

    import core.settings as settings_module

    settings = settings_module.load()
    bootstrap_ffmpeg(settings)
    settings_module.save(settings)

    from app import KlipwerkApp
    app = KlipwerkApp(settings=settings)
    app.mainloop()


if __name__ == "__main__":
    main()
