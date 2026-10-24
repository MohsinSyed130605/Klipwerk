"""Media extraction and download manager using yt-dlp."""

import io
import threading
import urllib.request
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import Callable

try:
    import yt_dlp
    HAS_YT_DLP = True
except ImportError:
    HAS_YT_DLP = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import mutagen
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, ID3NoHeaderError, TIT2, TPE1, TPE2, TALB, TDRC, APIC, PictureType
    from mutagen.mp4 import MP4, MP4Cover
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

QUALITY_OPTIONS: list[str] = [
    "Best (auto)",
    "4K (2160p)",
    "1440p (2K)",
    "1080p Full HD",
    "720p HD",
    "480p SD",
    "360p Low",
    "MP3 Audio",
    "M4A Audio",
    "WAV Audio",
    "FLAC Audio",
    "Opus Audio",
    "Best Audio (auto)",
]

VIDEO_FORMATS: list[str] = ["MP4", "WebM", "AVI", "MKV"]
FORMAT_OPTIONS: list[str] = VIDEO_FORMATS

# Maps quality label -> yt-dlp format selector
_QUALITY_FMT: dict[str, str] = {
    "Best (auto)":       "bestvideo+bestaudio/best",
    "4K (2160p)":        "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
    "1440p (2K)":        "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
    "1080p Full HD":     "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "1080p":             "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p HD":           "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "720p":              "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p SD":           "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "480p":              "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p Low":          "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "360p":              "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "MP3 Audio":         "bestaudio/best",
    "M4A Audio":         "bestaudio[ext=m4a]/bestaudio/best",
    "WAV Audio":         "bestaudio/best",
    "FLAC Audio":        "bestaudio/best",
    "Opus Audio":        "bestaudio/best",
    "Best Audio (auto)": "bestaudio/best",
}

AUDIO_QUALITIES = {
    "MP3 Audio",
    "M4A Audio",
    "WAV Audio",
    "FLAC Audio",
    "Opus Audio",
    "Best Audio (auto)",
}

# ---------------------------------------------------------------------------
# Info fetching (no download)
# ---------------------------------------------------------------------------

def sanitize_filename(name: str) -> str:
    """
    Sanitize a user-provided or video title for use as a Windows/POSIX filename.
    Strips Windows-reserved characters, path traversal tokens, and control characters.
    Truncates to 180 characters to prevent path length overflow on Windows.
    """
    import re
    if not name:
        return ""
    # Strip path separators and reserved characters: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|\x00-\x1f]', "", name)
    # Strip relative path tokens
    cleaned = re.sub(r"\.\.+", ".", cleaned)
    # Strip leading and trailing dots and spaces (disallowed on Windows)
    cleaned = cleaned.strip(". ")
    return cleaned[:180]


def fetch_quick_meta(url: str) -> dict:
    """
    Sub-second metadata retrieval for YouTube and supported media.
    Extracts video ID and queries the fast oEmbed endpoint (~300-400ms).
    Returns dict with title, uploader, thumbnail, or empty dict if not available.
    """
    import re
    import json
    import ssl
    import urllib.request
    import urllib.error

    meta = {}
    yt_m = re.search(r"(?:youtu\.be/|youtube\.com/(?:watch\?v=|embed/|shorts/|v/))([a-zA-Z0-9_-]{11})", url)
    if yt_m:
        vid_id = yt_m.group(1)
        meta["video_id"] = vid_id
        meta["thumbnail"] = f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
        meta["fallback_thumbnail"] = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"

        try:
            req = urllib.request.Request(
                f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid_id}&format=json",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            # Enforce strictly verified SSL certificate context
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=4, context=ctx) as resp:
                data = json.loads(resp.read().decode("utf-8", "ignore"))
                if "title" in data:
                    meta["title"] = data["title"]
                if "author_name" in data:
                    meta["uploader"] = data["author_name"]
                if "thumbnail_url" in data:
                    meta["thumbnail"] = data["thumbnail_url"]
        except ssl.SSLCertVerificationError:
            # Narrow SSL error handling: fail gracefully on certificate verification failure
            # rather than silently downgrading to an insecure unverified (CERT_NONE) connection.
            pass
        except Exception:
            pass

    return meta


def fetch_info(url: str, is_playlist: bool = False, extract_flat: bool = True) -> dict:
    """
    Extract metadata for *url* without downloading.
    Returns the yt-dlp info dict.  Raises on error.
    """
    if not HAS_YT_DLP:
        raise RuntimeError("yt-dlp is not installed.")
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": not is_playlist,
        "extract_flat": extract_flat,
        "socket_timeout": 10,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


# ---------------------------------------------------------------------------
# Download options builder
# ---------------------------------------------------------------------------

def _build_opts(
    quality: str,
    video_format: str,
    output_dir: str,
    progress_hook: Callable,
    post_hook: Callable | None = None,
    ffmpeg_path: str = "",
    add_metadata: bool = True,
    hw_accel: str = "auto",
    custom_args: str = "",
    custom_title: str = "",
) -> dict:
    is_audio = quality in AUDIO_QUALITIES or video_format.upper() in ("MP3", "M4A", "WAV", "FLAC", "OPUS", "OGG")
    if is_audio and quality not in AUDIO_QUALITIES:
        fmt = "bestaudio/best"
    else:
        fmt = _QUALITY_FMT.get(quality, "bestvideo+bestaudio/best")

    safe_title = sanitize_filename(custom_title) if custom_title else ""
    out_tmpl = f"{safe_title}.%(ext)s" if safe_title else "%(title)s.%(ext)s"
    opts: dict = {
        "format": fmt,
        "outtmpl": str(Path(output_dir) / out_tmpl),
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "overwrites": True,
        "windows_filenames": True,
        "postprocessors": [],
    }

    if post_hook:
        opts["post_hooks"] = [post_hook]

    if ffmpeg_path:
        opts["ffmpeg_location"] = ffmpeg_path

    if is_audio:
        codec_map = {
            "MP3 Audio": ("mp3", "320"),
            "M4A Audio": ("m4a", "0"),
            "WAV Audio": ("wav", "0"),
            "FLAC Audio": ("flac", "0"),
            "Opus Audio": ("opus", "0"),
            "mp3": ("mp3", "320"),
            "m4a": ("m4a", "0"),
            "wav": ("wav", "0"),
            "flac": ("flac", "0"),
            "opus": ("opus", "0"),
            "ogg": ("vorbis", "0"),
        }
        codec_info = codec_map.get(quality) or codec_map.get(video_format.lower())
        if codec_info:
            codec, quality_val = codec_info
            opts["postprocessors"].append({
                "key": "FFmpegExtractAudio",
                "preferredcodec": codec,
                "preferredquality": quality_val,
            })

        if add_metadata:
            opts["writethumbnail"] = True
            opts["postprocessors"].append({
                "key": "FFmpegThumbnailsConvertor",
                "format": "jpg",
            })
            opts["postprocessors"].append({
                "key": "FFmpegMetadata",
                "add_metadata": True,
                "add_chapters": True,
            })
            if quality in ("MP3 Audio", "M4A Audio", "FLAC Audio") or video_format.upper() in ("MP3", "M4A", "FLAC"):
                opts["postprocessors"].append({
                    "key": "EmbedThumbnail",
                    "already_have_thumbnail": False,
                })
    else:
        ext = video_format.lower()
        if ext and ext != "best":
            opts["merge_output_format"] = ext
            if video_format.upper() != "MP4":
                # Force conversion for non-default containers
                opts["postprocessors"].append({
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": ext,
                })
        if add_metadata:
            opts["postprocessors"].append({
                "key": "FFmpegMetadata",
                "add_metadata": True,
                "add_chapters": True,
            })

        # Hardware acceleration
        if hw_accel == "cuda":
            opts.setdefault("postprocessor_args", {})
            opts["postprocessor_args"]["ffmpeg"] = ["-vcodec", "h264_nvenc"]
        elif hw_accel == "qsv":
            opts.setdefault("postprocessor_args", {})
            opts["postprocessor_args"]["ffmpeg"] = ["-vcodec", "h264_qsv"]
        elif hw_accel == "amf":
            opts.setdefault("postprocessor_args", {})
            opts["postprocessor_args"]["ffmpeg"] = ["-vcodec", "h264_amf"]

    # Custom arguments
    if custom_args:
        import shlex
        try:
            for token in shlex.split(custom_args):
                if token.startswith("--proxy="):
                    opts["proxy"] = token.split("=", 1)[1]
                elif token.startswith("--cookies="):
                    opts["cookiefile"] = token.split("=", 1)[1]
                elif token.startswith("--user-agent="):
                    opts["user_agent"] = token.split("=", 1)[1]
        except Exception:
            pass

    return opts


def _tag_media_file(file_path: str, info: dict) -> None:
    """
    Ensure ID3v2.3 (MP3) or MP4 (M4A) metadata and album cover artwork
    are permanently embedded so Windows Media Player, Windows Explorer,
    and other music players show the title, contributing artist, album, and picture.
    """
    if not file_path:
        return
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        return

    ext = p.suffix.lower()
    title = info.get("track") or info.get("title") or p.stem
    artist = (
        info.get("artist")
        or info.get("creator")
        or info.get("uploader")
        or info.get("channel")
        or info.get("uploader_id")
        or ""
    )
    album = info.get("album") or info.get("title") or ""
    year = info.get("release_year") or (info.get("upload_date")[:4] if info.get("upload_date") else "")

    def _load_cover_bytes() -> tuple[bytes | None, str]:
        # 1. Search for any downloaded companion thumbnail file in the same directory
        parent = p.parent
        stem = p.stem
        for img_ext in (".jpg", ".jpeg", ".png", ".webp"):
            candidate = parent / f"{stem}{img_ext}"
            if candidate.exists():
                try:
                    data = candidate.read_bytes()
                    if img_ext in (".jpg", ".jpeg"):
                        return data, "image/jpeg"
                    elif img_ext == ".png":
                        return data, "image/png"
                    elif HAS_PIL:
                        buf = io.BytesIO()
                        im = Image.open(io.BytesIO(data)).convert("RGB")
                        im.save(buf, format="JPEG", quality=95)
                        return buf.getvalue(), "image/jpeg"
                except Exception:
                    pass

        # 2. If not found locally, fetch from thumbnail URL
        thumb_url = info.get("thumbnail")
        if not thumb_url:
            thumbs = info.get("thumbnails")
            if thumbs and isinstance(thumbs, list) and len(thumbs) > 0:
                last_thumb = thumbs[-1]
                if isinstance(last_thumb, dict):
                    thumb_url = last_thumb.get("url")

        if thumb_url:
            try:
                req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    raw_data = resp.read()
                if HAS_PIL:
                    buf = io.BytesIO()
                    im = Image.open(io.BytesIO(raw_data)).convert("RGB")
                    im.save(buf, format="JPEG", quality=95)
                    return buf.getvalue(), "image/jpeg"
                return raw_data, "image/jpeg"
            except Exception:
                pass
        return None, ""

    if ext == ".mp3" and HAS_MUTAGEN:
        try:
            tags = None
            save_cb = None
            try:
                audio = MP3(p, ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                tags = audio.tags
                save_cb = lambda: audio.save(v2_version=3)
            except Exception:
                try:
                    tags = ID3(p)
                    save_cb = lambda: tags.save(p, v2_version=3)
                except ID3NoHeaderError:
                    tags = ID3()
                    save_cb = lambda: tags.save(p, v2_version=3)

            if tags is not None:
                # Ensure Title (TIT2)
                if "TIT2" not in tags or not tags["TIT2"].text:
                    tags["TIT2"] = TIT2(encoding=3, text=[title])

                # Ensure Contributing Artist (TPE1) - this is what Windows Media Player and Explorer show!
                if ("TPE1" not in tags or not tags["TPE1"].text) and artist:
                    tags["TPE1"] = TPE1(encoding=3, text=[artist])

                # Ensure Album Artist (TPE2)
                if ("TPE2" not in tags or not tags["TPE2"].text) and artist:
                    tags["TPE2"] = TPE2(encoding=3, text=[artist])

                # Ensure Album (TALB)
                if ("TALB" not in tags or not tags["TALB"].text) and album:
                    tags["TALB"] = TALB(encoding=3, text=[album])

                # Ensure Year (TDRC)
                if ("TDRC" not in tags or not tags["TDRC"].text) and year:
                    tags["TDRC"] = TDRC(encoding=3, text=[str(year)])

                # Ensure APIC Cover Art
                has_cover = any(isinstance(f, APIC) for f in tags.values())
                if not has_cover:
                    c_bytes, mime = _load_cover_bytes()
                    if c_bytes:
                        tags["APIC:Cover"] = APIC(
                            encoding=3,
                            mime=mime,
                            type=PictureType.COVER_FRONT,
                            desc="Cover",
                            data=c_bytes,
                        )

                # Save explicitly as ID3v2.3 for 100% Windows Media Player and Explorer support
                if save_cb:
                    save_cb()
        except Exception:
            pass

    elif ext == ".m4a" and HAS_MUTAGEN:
        try:
            audio = MP4(p)
            if "\xa9nam" not in audio or not audio["\xa9nam"]:
                audio["\xa9nam"] = [title]
            if ("\xa9ART" not in audio or not audio["\xa9ART"]) and artist:
                audio["\xa9ART"] = [artist]
            if ("aART" not in audio or not audio["aART"]) and artist:
                audio["aART"] = [artist]
            if ("\xa9alb" not in audio or not audio["\xa9alb"]) and album:
                audio["\xa9alb"] = [album]
            if ("\xa9day" not in audio or not audio["\xa9day"]) and year:
                audio["\xa9day"] = [str(year)]
            if "covr" not in audio or not audio["covr"]:
                c_bytes, mime = _load_cover_bytes()
                if c_bytes:
                    c_fmt = MP4Cover.FORMAT_PNG if mime == "image/png" else MP4Cover.FORMAT_JPEG
                    audio["covr"] = [MP4Cover(c_bytes, imageformat=c_fmt)]
            audio.save()
        except Exception:
            pass

    elif ext == ".flac" and HAS_MUTAGEN:
        try:
            from mutagen.flac import FLAC, Picture
            audio = FLAC(p)
            if "title" not in audio and title:
                audio["title"] = [title]
            if "artist" not in audio and artist:
                audio["artist"] = [artist]
            if "album" not in audio and album:
                audio["album"] = [album]
            if "date" not in audio and year:
                audio["date"] = [str(year)]
            if not audio.pictures:
                c_bytes, mime = _load_cover_bytes()
                if c_bytes:
                    pic = Picture()
                    pic.data = c_bytes
                    pic.type = 3
                    pic.mime = mime
                    pic.desc = "Cover"
                    audio.add_picture(pic)
            audio.save()
        except Exception:
            pass

    # Clean up stray thumbnail image files matching the file stem
    try:
        parent = p.parent
        stem = p.stem
        for img_ext in (".jpg", ".jpeg", ".png", ".webp"):
            stray = parent / f"{stem}{img_ext}"
            if stray.exists():
                stray.unlink(missing_ok=True)
    except Exception:
        pass



# ---------------------------------------------------------------------------
# Downloader class
# ---------------------------------------------------------------------------

ProgressCallback = Callable[[str, dict], None]   # (card_id, progress_data)
DoneCallback     = Callable[[str, str], None]    # (card_id, final_file_or_dir)
ErrorCallback    = Callable[[str, str], None]     # (card_id, error_message)


class Downloader:
    """Manages a pool of download threads with active cancellation support."""

    def __init__(self, max_workers: int = 3):
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dl")
        self._futures: dict[str, Future] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def submit(
        self,
        card_id: str,
        url: str,
        quality: str,
        video_format: str,
        output_dir: str,
        progress_callback: ProgressCallback,
        done_callback: DoneCallback,
        error_callback: ErrorCallback,
        ffmpeg_path: str = "",
        add_metadata: bool = True,
        hw_accel: str = "auto",
        custom_args: str = "",
        custom_title: str = "",
    ) -> Future:
        with self._lock:
            self._cancelled.discard(card_id)
        future = self._executor.submit(
            self._run,
            card_id, url, quality, video_format, output_dir,
            progress_callback, done_callback, error_callback, ffmpeg_path,
            add_metadata, hw_accel, custom_args, custom_title,
        )
        with self._lock:
            self._futures[card_id] = future
        return future

    def cancel(self, card_id: str) -> None:
        with self._lock:
            self._cancelled.add(card_id)
            f = self._futures.get(card_id)
        if f:
            f.cancel()

    def is_cancelled(self, card_id: str) -> bool:
        with self._lock:
            return card_id in self._cancelled

    def update_workers(self, max_workers: int) -> None:
        self._executor.shutdown(wait=False)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="dl")

    def shutdown(self) -> None:
        with self._lock:
            self._cancelled.update(self._futures.keys())
        self._executor.shutdown(wait=False, cancel_futures=True)

    # ------------------------------------------------------------------
    def _run(
        self,
        card_id, url, quality, video_format, output_dir,
        progress_cb, done_cb, error_cb, ffmpeg_path,
        add_metadata: bool = True,
        hw_accel: str = "auto",
        custom_args: str = "",
        custom_title: str = "",
    ) -> None:
        import glob
        last_filename: list[str] = [""]
        final_filepath: list[str] = [""]

        def hook(d: dict) -> None:
            if self.is_cancelled(card_id):
                if HAS_YT_DLP and hasattr(yt_dlp.utils, "DownloadCancelled"):
                    raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
                raise RuntimeError("Download cancelled by user")
            if "filename" in d:
                last_filename[0] = d["filename"]
            progress_cb(card_id, d)

        def post_hook(filepath: str) -> None:
            if self.is_cancelled(card_id):
                if HAS_YT_DLP and hasattr(yt_dlp.utils, "DownloadCancelled"):
                    raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
                raise RuntimeError("Download cancelled by user")
            final_filepath[0] = filepath

        try:
            if self.is_cancelled(card_id):
                return

            opts = _build_opts(
                quality, video_format, output_dir, hook, post_hook,
                ffmpeg_path, add_metadata, hw_accel, custom_args, custom_title
            )
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    info = {}
                elif "entries" in info and info["entries"]:
                    info = info["entries"][0] or {}

            if self.is_cancelled(card_id):
                return

            resolved = final_filepath[0] or last_filename[0]
            if resolved and not Path(resolved).exists():
                stem = Path(resolved).stem.split(".")[0]
                parent = Path(resolved).parent
                if parent.exists():
                    candidates = list(parent.glob(f"{glob.escape(stem)}.*"))
                    valid = [c for c in candidates if not c.name.endswith((".part", ".temp", ".ytdl"))]
                    if valid:
                        resolved = str(valid[-1])

            if resolved and add_metadata and not self.is_cancelled(card_id):
                _tag_media_file(resolved, info)

            if not self.is_cancelled(card_id):
                done_cb(card_id, resolved or output_dir)
        except Exception as exc:
            if self.is_cancelled(card_id):
                return
            if HAS_YT_DLP and isinstance(exc, getattr(yt_dlp.utils, "DownloadCancelled", ())) or "cancelled" in str(exc).lower():
                return
            error_cb(card_id, str(exc)[:200])
        finally:
            with self._lock:
                self._cancelled.discard(card_id)
                self._futures.pop(card_id, None)

