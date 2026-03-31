#!/usr/bin/env bash
# Firewall rules and status
set -uo pipefail

echo "=== FIREWALL STATUS ==="
echo ""

echo "--- UFW ---"
if command -v ufw &>/dev/null; then
    ufw_status=$(sudo -n ufw status verbose 2>/dev/null || true)
    if [ -z "$ufw_status" ]; then
        echo "Needs sudo. Run: sudo ufw status verbose"
    else
        echo "$ufw_status"
    fi
    echo ""
    echo "UFW app list:"
    sudo -n ufw app list 2>/dev/null || echo "  (needs sudo or no apps registered)"
else
    echo "ufw not installed"
fi
echo ""

echo "--- iptables (summary) ---"
if command -v iptables &>/dev/null; then
    ipt_output=$(sudo -n iptables -L -n --line-numbers 2>/dev/null | head -40 || true)
    if [ -z "$ipt_output" ]; then
        echo "Needs sudo for iptables. Run: sudo iptables -L -n --line-numbers"
    else
        echo "$ipt_output"
    fi
else
    echo "iptables not available"
fi
echo ""

echo "--- nftables ---"
if command -v nft &>/dev/null; then
    nft_output=$(sudo -n nft list ruleset 2>/dev/null | head -40 || true)
    if [ -z "$nft_output" ]; then
        echo "Needs sudo for nftables. Run: sudo nft list ruleset"
    else
        echo "$nft_output"
    fi
else
    echo "nftables not available"
fi
