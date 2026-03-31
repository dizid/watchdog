#!/usr/bin/env bash
# Watchdog installer — sets up venv, deps, and optional systemd user service
set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$INSTALL_DIR/.venv"
PORT="${WATCHDOG_PORT:-5111}"

echo ""
echo "  Watchdog Installer"
echo "  ==================="
echo ""

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: Python 3 is required but not found."
    echo "  Install: sudo apt install python3 python3-venv"
    exit 1
fi

# Check python3-venv
if ! python3 -m venv --help &>/dev/null 2>&1; then
    echo "ERROR: python3-venv is required but not found."
    echo "  Install: sudo apt install python3-venv"
    exit 1
fi

# Create venv
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/3] Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "[1/3] Virtual environment exists."
fi

# Install deps
echo "[2/3] Installing dependencies..."
"$VENV_DIR/bin/pip" install -q -r "$INSTALL_DIR/requirements.txt"

# Make scripts executable
echo "[3/3] Making scripts executable..."
chmod +x "$INSTALL_DIR"/scripts/*.sh

echo ""
echo "  Installation complete!"
echo ""
echo "  To start Watchdog:"
echo "    $INSTALL_DIR/start.sh"
echo ""
echo "  Then open: http://127.0.0.1:$PORT"
echo ""

# Offer systemd user service
read -rp "  Create systemd user service for easy start/stop? [y/N] " answer
if [[ "${answer,,}" == "y" ]]; then
    SERVICE_DIR="$HOME/.config/systemd/user"
    mkdir -p "$SERVICE_DIR"

    cat > "$SERVICE_DIR/watchdog.service" << EOF
[Unit]
Description=Watchdog — System Health Dashboard
After=default.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$VENV_DIR/bin/python $INSTALL_DIR/dashboard/server.py
Restart=on-failure
RestartSec=5
Environment=WATCHDOG_PORT=$PORT

[Install]
WantedBy=default.target
EOF

    systemctl --user daemon-reload
    systemctl --user enable watchdog.service

    echo ""
    echo "  Systemd user service created!"
    echo "    Start:   systemctl --user start watchdog"
    echo "    Stop:    systemctl --user stop watchdog"
    echo "    Status:  systemctl --user status watchdog"
    echo "    Logs:    journalctl --user -u watchdog -f"
    echo ""
fi
