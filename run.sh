#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
#  Klipwerk — Portable Linux Launcher
# ═══════════════════════════════════════════════════════════════════

set -e

# Change directory to project root
cd "$(dirname "$0")"

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] python3 could not be found."
    echo "Please install Python 3 (e.g. sudo apt install python3 python3-pip python3-tk)"
    exit 1
fi

# Ensure requirements are installed
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt --quiet --disable-pip-version-check 2>/dev/null || true
fi

# Launch Klipwerk
exec python3 main.py "$@"
