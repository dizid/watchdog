#!/usr/bin/env bash
# Scan for open/listening ports
set -uo pipefail

echo "=== LISTENING PORTS ==="
echo ""

if ! command -v ss &>/dev/null; then
    echo "ss command not available — install iproute2"
    echo ""
else
    echo "--- TCP ---"
    tcp_ports=$(ss -tlnp 2>/dev/null || true)
    if [ -z "$tcp_ports" ]; then
        echo "No TCP listeners found (or ss failed)"
    else
        echo "$tcp_ports" | column -t 2>/dev/null || echo "$tcp_ports"
    fi
    echo ""

    echo "--- UDP ---"
    udp_ports=$(ss -ulnp 2>/dev/null || true)
    if [ -z "$udp_ports" ]; then
        echo "No UDP listeners found (or ss failed)"
    else
        echo "$udp_ports" | column -t 2>/dev/null || echo "$udp_ports"
    fi
    echo ""

    echo "=== ESTABLISHED CONNECTIONS ==="
    established=$(ss -tnp state established 2>/dev/null | head -20 || true)
    if [ -z "$established" ]; then
        echo "No established connections found"
    else
        echo "$established"
    fi
    echo "(showing top 20)"
    echo ""
fi

echo "=== UFW STATUS ==="
if command -v ufw &>/dev/null; then
    sudo -n ufw status verbose 2>/dev/null || echo "Needs sudo. Run: sudo ufw status verbose"
else
    echo "ufw not installed"
fi
