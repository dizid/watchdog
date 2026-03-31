#!/usr/bin/env bash
# Check for failed systemd services
set -uo pipefail

echo "=== FAILED SYSTEMD SERVICES ==="
echo ""

if ! command -v systemctl &>/dev/null; then
    echo "systemctl not available — not a systemd system"
    exit 0
fi

failed=$(systemctl --failed --no-legend 2>/dev/null || true)
if [ -z "$failed" ]; then
    echo "No failed services. All clear."
else
    echo "$failed"
    echo ""
    echo "--- Details ---"
    echo "$failed" | awk '{print $1}' | while read -r unit; do
        [ -z "$unit" ] && continue
        echo ""
        echo ">> $unit"
        systemctl status "$unit" --no-pager 2>/dev/null | head -10 || echo "  (status unavailable)"
    done
fi

echo ""
echo "=== RECENTLY CRASHED SERVICES (last 24h) ==="
if command -v journalctl &>/dev/null; then
    recent_errors=$(journalctl --since "24 hours ago" -p err --no-pager -q 2>/dev/null | tail -20 || true)
    if [ -z "$recent_errors" ]; then
        echo "No error-level journal entries in the last 24 hours"
    else
        echo "$recent_errors"
    fi
else
    echo "journalctl not available"
fi
