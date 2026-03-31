#!/usr/bin/env bash
# Boot time analysis using systemd-analyze
set -uo pipefail

echo "=== BOOT TIME OVERVIEW ==="
echo ""

if ! command -v systemd-analyze &>/dev/null; then
    echo "systemd-analyze not available — not a systemd system"
    exit 0
fi

systemd-analyze 2>/dev/null || echo "systemd-analyze failed (may need to be run as user with active session)"
echo ""

echo "=== TOP 20 SLOWEST SERVICES ==="
blame_output=$(systemd-analyze blame 2>/dev/null | head -20 || true)
if [ -z "$blame_output" ]; then
    echo "No blame data available"
else
    echo "$blame_output"
fi
echo ""

echo "=== CRITICAL CHAIN ==="
chain_output=$(systemd-analyze critical-chain --no-pager 2>/dev/null | head -30 || true)
if [ -z "$chain_output" ]; then
    echo "No critical chain data available"
else
    echo "$chain_output"
fi
