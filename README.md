# Klipwerk

<div align="center">

![Klipwerk Icon](assets/icon.png)

**A modern, fast, cross-platform desktop app for downloading videos and music from YouTube and 1000+ sites.**

[![GitHub release](https://img.shields.io/github/v/release/MohsinSyed130605/Klipwerk?style=flat-square)](https://github.com/MohsinSyed130605/Klipwerk/releases)
[![License: BSD-3-Clause](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg?style=flat-square)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-blue?style=flat-square)](https://github.com/MohsinSyed130605/Klipwerk/releases)

</div>

---

## 📥 Downloads & Releases

Choose the appropriate package for your operating system from [Releases](https://github.com/MohsinSyed130605/Klipwerk/releases):

| Operating System | Architecture | Package Type | Filename | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Windows** | x64 (64-bit) | **Setup Installer** | `Klipwerk-Setup-x64.exe` | Recommended for Windows 10 & 11 (includes desktop & Start menu shortcuts) |
| **Windows** | x64 (64-bit) | **Portable Standalone** | `Klipwerk-Portable-x64.exe` | Single-file executable, zero installation required |
| **Linux** | x86_64 (64-bit) | **AppImage** | `Klipwerk-x64.AppImage` | Universal standalone package for 64-bit Intel/AMD Linux systems |
| **Linux** | arm64 / aarch64 | **AppImage** | `Klipwerk-arm64.AppImage` | Standalone portable package for 64-bit ARM Linux devices & distributions |

> **Note:** On first launch, Klipwerk automatically detects your operating system and CPU architecture, downloading the required static FFmpeg binaries into its local directory if not already available on your system `PATH`.

---

## ✨ Features

- 🎬 **Download from 1000+ sites** — YouTube, YouTube Music, Vimeo, Twitch, SoundCloud, TikTok, Reddit, and more (powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- 📐 **Comprehensive Video Formats** — 4K Ultra HD (2160p), 1440p (2K), 1080p Full HD, 720p HD, 480p SD, 360p Low across MP4, WebM, AVI, and MKV containers
- 🎵 **Hi-Fi Audio Extraction** — MP3, M4A, FLAC, WAV, Opus, and Best Audio with ID3v2.3 metadata, contributing artists, album info, and embedded artwork
- 📑 **Batch URL Import** — Multi-line URL import modal with clipboard paste, real-time link counter, quality presets, and auto-download
- 📜 **Smart Playlist Extraction** — Paste any playlist link and Klipwerk automatically unpacks all videos into individual items in seconds
- 🚀 **Hardware Acceleration (GPU)** — NVIDIA NVENC (CUDA), Intel QuickSync (QSV), and AMD AMF video encoding presets
- 📋 **Live Clipboard Watcher** — Instantly detects copied video links and prompts you to add them
- ⚡ **Multi-threaded Downloads** — Up to 5 concurrent downloads with individual progress, speed, ETA, and cooperative cancellation
- ⚙️ **Custom yt-dlp Arguments & Proxies** — Pass custom proxy, user-agent, or cookies for geo-blocked streams
- 🛡️ **Duplicate Detection** — Configurable duplicate protection to avoid accidental re-downloads
- 🚀 **Built-in yt-dlp Auto-Updater** — One-click update in the sidebar to maintain continuous compatibility with site changes
- 🎨 **Claymorphic Tactile Design** — Ergonomic soft-clay buttons, smooth badges, and Dark/Light mode toggle
- 🔔 **Interactive Toast Notifications** — Desktop notifications with direct file reveal in Windows Explorer and Linux file managers

---

## 🚀 Getting Started

### Windows
1. Download **`Klipwerk-Setup-x64.exe`** from [Releases](https://github.com/MohsinSyed130605/Klipwerk/releases).
2. Run the installer and launch Klipwerk from your Start menu or Desktop.
3. Alternatively, download **`Klipwerk-Portable-x64.exe`** and run it from anywhere with zero setup.

### Linux
1. Download **`Klipwerk-x64.AppImage`** (or **`Klipwerk-arm64.AppImage`**) from [Releases](https://github.com/MohsinSyed130605/Klipwerk/releases).
2. Make it executable:
   ```bash
   chmod +x Klipwerk-*.AppImage
   ./Klipwerk-*.AppImage
   ```

*(Optional)* For clipboard watching on Linux, ensure `xclip` or `wl-clipboard` is installed:
```bash
sudo apt install xclip      # Debian / Ubuntu / Mint
sudo dnf install xclip      # Fedora
```

---

## 💻 Run from Source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/MohsinSyed130605/Klipwerk.git
cd Klipwerk
pip install -r requirements.txt
```

- **Windows:** Double-click `run.bat` or run `python main.py`
- **Linux:** Run `./run.sh` or `python3 main.py`
  *(On Linux, ensure Tkinter is installed: `sudo apt install python3-tk`)*

---

## 🔨 Building Releases

### Windows (EXE & Installer)
Run:
```cmd
build.bat
```
Produces:
- `.\Klipwerk-Portable-x64.exe` (Standalone portable executable)
- `.\Klipwerk-Setup-x64.exe` (Inno Setup installer wizard)

### Linux (AppImage & Binary)
Run:
```bash
chmod +x build.sh
./build.sh
```
Produces:
- `.\Klipwerk` (Standalone Linux executable)
- `.\Klipwerk-x64.AppImage` (Universal Linux AppImage)

---

## 📋 Supported Sites

Any site supported by yt-dlp, including:
YouTube • YouTube Music • Vimeo • Twitch • SoundCloud • Twitter/X • TikTok • Instagram • Reddit • Dailymotion • and [1000+ more](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

---

## 📄 License

Klipwerk is open-source software licensed under the [BSD 3-Clause License](LICENSE).

Third-party libraries, engines (such as yt-dlp and FFmpeg), and font assets retain their respective open-source licenses as documented in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

---

## 🙏 Credits

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — the core download engine
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) — modern Python UI framework
- [Phosphor Icons](https://phosphoricons.com) — crisp vector icon system
- [Vividl](https://github.com/Bluegrams/Vividl) — UX inspiration
