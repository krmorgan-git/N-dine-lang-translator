#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "=== N-dine-lang-translator Setup & Launcher ==="

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is not installed. Please install Python 3.8+ and try again."
    exit 1
fi

python3 bootstrap.py

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment (.venv)..."
    if ! python3 -m venv .venv; then
        echo "Error: Could not create .venv. On Ubuntu/Debian/WSL, run: sudo apt install -y python3-venv"
        exit 1
    fi
fi

echo "Installing/verifying dependencies..."
.venv/bin/python -m pip install --upgrade pip -q
.venv/bin/pip install --prefer-binary -r requirements.txt

echo ""
echo "Starting N-dine-lang-translator at http://127.0.0.1:5000 ..."
echo "(First run downloads the ~777 MB AI model automatically. Press Ctrl+C to stop.)"
echo ""
exec .venv/bin/python app.py
