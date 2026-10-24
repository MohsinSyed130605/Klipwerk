#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Klipwerk — AppImage Packaging Script (x86_64 & arm64/aarch64)
#  Packages dist/Klipwerk into Klipwerk-x64.AppImage or Klipwerk-arm64.AppImage
# ═══════════════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${ROOT_DIR}"

APP_NAME="Klipwerk"
APP_DIR="${ROOT_DIR}/build/AppDir"
APPIMAGETOOL_VERSION="13"
APPIMAGETOOL_RELEASE_BASE="https://github.com/AppImage/appimagetool/releases/download/${APPIMAGETOOL_VERSION}"

# Determine architecture (allows override via TARGET_ARCH or argument)
RAW_ARCH="${TARGET_ARCH:-${1:-$(uname -m)}}"
case "${RAW_ARCH}" in
    x86_64|amd64|x64)
        APPIMAGE_ARCH="x86_64"
        RELEASE_ARCH="x64"
        APPIMAGETOOL_FILE="appimagetool-x86_64.AppImage"
        ;;
    aarch64|arm64)
        APPIMAGE_ARCH="aarch64"
        RELEASE_ARCH="arm64"
        APPIMAGETOOL_FILE="appimagetool-aarch64.AppImage"
        ;;
    *)
        echo "[ERROR] Unsupported architecture for AppImage: ${RAW_ARCH}"
        exit 1
        ;;
esac

APPIMAGETOOL_URL="${APPIMAGETOOL_RELEASE_BASE}/${APPIMAGETOOL_FILE}"
APPIMAGETOOL_SUMS_URL="${APPIMAGETOOL_RELEASE_BASE}/SHA256SUMS"

OUTPUT_APPIMAGE="${ROOT_DIR}/Klipwerk-${RELEASE_ARCH}.AppImage"

# Verify binary exists
if [ ! -f "dist/${APP_NAME}" ] && [ ! -f "${APP_NAME}" ]; then
    echo "[ERROR] ${APP_NAME} binary not found. Run PyInstaller first (e.g. ./build.sh)."
    exit 1
fi

BIN_PATH="dist/${APP_NAME}"
if [ ! -f "${BIN_PATH}" ]; then
    BIN_PATH="${APP_NAME}"
fi

echo "  Target architecture: ${RELEASE_ARCH} (${APPIMAGE_ARCH})"
echo "  Creating AppDir structure..."
rm -rf "${APP_DIR}"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"

# 1. Copy binary
cp "${BIN_PATH}" "${APP_DIR}/usr/bin/${APP_NAME}"
chmod +x "${APP_DIR}/usr/bin/${APP_NAME}"

# 2. Desktop entry
cat << 'EOF' > "${APP_DIR}/${APP_NAME}.desktop"
[Desktop Entry]
Name=Klipwerk
GenericName=Video Downloader
Comment=Fast, modern, cross-platform video & audio downloader
Exec=Klipwerk %U
Icon=Klipwerk
Type=Application
Categories=AudioVideo;Network;AudioVideoEditing;
Terminal=false
StartupWMClass=Klipwerk
MimeType=x-scheme-handler/http;x-scheme-handler/https;
EOF

cp "${APP_DIR}/${APP_NAME}.desktop" "${APP_DIR}/usr/share/applications/${APP_NAME}.desktop"

# 3. Icons
if [ -f "assets/icon.png" ]; then
    cp "assets/icon.png" "${APP_DIR}/${APP_NAME}.png"
    cp "assets/icon.png" "${APP_DIR}/.DirIcon"
    cp "assets/icon.png" "${APP_DIR}/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png"
fi

# 4. AppRun entry script
cat << 'EOF' > "${APP_DIR}/AppRun"
#!/bin/sh
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
export XDG_DATA_DIRS="${HERE}/usr/share:${XDG_DATA_DIRS}"
exec "${HERE}/usr/bin/Klipwerk" "$@"
EOF
chmod +x "${APP_DIR}/AppRun"

# 5. Fetch / Run appimagetool
APPIMAGETOOL="${ROOT_DIR}/build/appimagetool-${APPIMAGE_ARCH}"
verify_checksum() {
    local file_path="$1"
    local expected
    local actual
    local sums_data

    if command -v curl &>/dev/null; then
        sums_data="$(curl -fsSL "${APPIMAGETOOL_SUMS_URL}")" || return 1
    elif command -v wget &>/dev/null; then
        sums_data="$(wget -qO- "${APPIMAGETOOL_SUMS_URL}")" || return 1
    else
        echo "[ERROR] curl or wget is required for checksum verification."
        return 1
    fi

    expected="$(printf '%s\n' "${sums_data}" | awk -v f="${APPIMAGETOOL_FILE}" '$2==f {print $1; exit}')"
    if [ -z "${expected}" ]; then
        echo "[ERROR] Could not find checksum entry for ${APPIMAGETOOL_FILE}."
        return 1
    fi

    if command -v sha256sum &>/dev/null; then
        actual="$(sha256sum "${file_path}" | awk '{print $1}')"
    elif command -v shasum &>/dev/null; then
        actual="$(shasum -a 256 "${file_path}" | awk '{print $1}')"
    else
        echo "[ERROR] sha256sum or shasum is required for checksum verification."
        return 1
    fi

    if [ "${actual}" != "${expected}" ]; then
        echo "[ERROR] appimagetool checksum mismatch."
        echo "        expected: ${expected}"
        echo "        actual:   ${actual}"
        return 1
    fi
}

if ! command -v appimagetool &>/dev/null; then
    if [ ! -f "${APPIMAGETOOL}" ]; then
        echo "  Downloading appimagetool ${APPIMAGETOOL_VERSION} for ${APPIMAGE_ARCH}..."
        mkdir -p "${ROOT_DIR}/build"
        wget -q "${APPIMAGETOOL_URL}" -O "${APPIMAGETOOL}" || \
        curl -sL "${APPIMAGETOOL_URL}" -o "${APPIMAGETOOL}"
    fi
    echo "  Verifying appimagetool checksum..."
    verify_checksum "${APPIMAGETOOL}" || exit 1
    chmod +x "${APPIMAGETOOL}"
    TOOL="${APPIMAGETOOL}"
else
    TOOL="appimagetool"
fi

echo "  Generating ${OUTPUT_APPIMAGE}..."
ARCH="${APPIMAGE_ARCH}" "${TOOL}" --appimage-extract-and-run "${APP_DIR}" "${OUTPUT_APPIMAGE}" 2>/dev/null || \
ARCH="${APPIMAGE_ARCH}" "${TOOL}" "${APP_DIR}" "${OUTPUT_APPIMAGE}"

echo "  [OK] Successfully packaged: ${OUTPUT_APPIMAGE}"
