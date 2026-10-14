#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Klipwerk — Linux Build & Packaging Script
#  Produces:
#    1. Standalone Binary: dist/Klipwerk
#    2. Portable AppImage: Klipwerk-x64.AppImage
# ═══════════════════════════════════════════════════════════════════

set -e

cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════╗"
echo "║          Klipwerk v1.0.0 — Linux Build System         ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# 1. Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 not found. Please install Python 3.10+."
    exit 1
fi

echo "Python: $(python3 --version)"
echo ""

# 2. Check / install dependencies
echo "[1/4] Checking Python dependencies..."
python3 -m pip install -r requirements.txt pyinstaller --quiet --disable-pip-version-check

# 3. Clean previous build artifacts
echo "[2/4] Cleaning previous builds..."
rm -rf build dist

# 4. Run PyInstaller
echo "[3/4] Compiling Klipwerk with PyInstaller..."
python3 -m PyInstaller Klipwerk.spec --noconfirm

if [ ! -f "dist/Klipwerk" ]; then
    echo "[ERROR] Build failed — dist/Klipwerk was not produced."
    exit 1
fi

chmod +x dist/Klipwerk
cp dist/Klipwerk ./Klipwerk
echo "       [OK] Standalone binary: ./Klipwerk"

# 5. Build AppImage
echo "[4/4] Building Linux AppImage..."
if [ -f "scripts/package_appimage.sh" ]; then
    bash scripts/package_appimage.sh
else
    echo "[INFO] scripts/package_appimage.sh not found, skipping AppImage."
fi

# Clean intermediate build directories
rm -rf build dist

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  ✓ LINUX BUILD COMPLETED SUCCESSFULLY!                ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
for appimg in ./Klipwerk-*.AppImage; do
    if [ -f "${appimg}" ]; then
        echo "  ▶ AppImage: ${appimg}"
    fi
done
echo "  ▶ Binary:   ./Klipwerk"
echo ""
