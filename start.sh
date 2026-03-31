#!/usr/bin/env bash
# Start Watchdog — system health dashboard
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
    echo "Installing dependencies..."
    "$VENV_DIR/bin/pip" install -q -r "$SCRIPT_DIR/requirements.txt"
    echo "Done."
fi

# Activate and run
echo ""
echo "  Starting Watchdog..."
echo "  http://127.0.0.1:5111"
echo ""
exec "$VENV_DIR/bin/python" "$SCRIPT_DIR/dashboard/server.py"
