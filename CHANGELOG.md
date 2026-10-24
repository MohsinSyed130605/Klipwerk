# Changelog

All notable changes to **Klipwerk** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Changed
- Pinned all runtime Python dependencies in `requirements.txt` for reproducible installs and builds.
- Disabled insecure `--no-check-certificate` passthrough from custom yt-dlp arguments.
- Updated yt-dlp in-app update action to open Klipwerk releases instead of mutating runtime packages via pip.

### Added
- GitHub Actions CI workflow (`.github/workflows/ci.yml`) for dependency install and Python compile checks on pushes/PRs.
- AppImage packaging hardening in `scripts/package_appimage.sh`:
  - pinned `appimagetool` release version
  - enforced SHA-256 verification via upstream `SHA256SUMS`

---

## [1.0.0] - 2026-09-24

### Added
- **Initial Release of Klipwerk** — modern, fast, cross-platform desktop video & music downloader.
- **Cross-Platform Support (Windows & Linux)**:
  - Native OS configuration paths: `%APPDATA%/Klipwerk` on Windows, `$XDG_CONFIG_HOME/Klipwerk` (`~/.config/Klipwerk`) on Linux.
  - Cross-platform file revealing in native desktop environments (Windows Explorer `/select`, Linux file managers & `xdg-open`).
  - Native runtime guards for Windows DWM immersive dark mode and GDI font registration.
  - Universal Tkinter window icon handling via PNG.
- **Dynamic Multi-Architecture FFmpeg Auto-Downloader**:
  - Automatically detects OS and CPU architecture on startup.
  - Supports static automated builds for Windows x64 and Linux (x86_64 and arm64/aarch64).
  - Multi-format archive extraction supporting both `.zip` and `.tar.xz`.
  - Sets executable permissions (`chmod +x`) on Unix binaries.
  - Automatic system PATH detection (`shutil.which("ffmpeg")`) avoids unnecessary downloads when installed via package manager.
- **Release Packaging**:
  - **Windows Installer**: `Klipwerk-Setup-x64.exe` via Inno Setup 7, bundling licenses, icons, and start menu/desktop shortcuts.
  - **Windows Standalone**: `Klipwerk-Portable-x64.exe` single-file portable executable.
  - **Linux AppImage**: `Klipwerk-x64.AppImage` portable distribution package with standard AppDir recipe (`scripts/package_appimage.sh`).
- **Launch & Build Automation**:
  - Added `run.sh` and `build.sh` for Linux.
  - Added `run.bat` and `build.bat` for Windows.
- **Documentation**:
  - Platform/Architecture release matrix in `README.md`.
  - Comprehensive `THIRD_PARTY_LICENSES.md` documenting yt-dlp, FFmpeg, CustomTkinter, Mutagen, and Phosphor Icons under BSD 3-Clause license.
