#!/usr/bin/env bash
# Check for available system updates
set -uo pipefail

echo "=== AVAILABLE UPDATES ==="
echo ""

echo "--- APT updates ---"
if command -v apt &>/dev/null; then
    upgradable=$(apt list --upgradable 2>/dev/null | tail -n +2 || true)
    if [ -z "$upgradable" ]; then
        echo "No APT upgrades available (or apt update not run recently)"
    else
        echo "$upgradable"
    fi
    apt_count=$(echo "$upgradable" | grep -c . 2>/dev/null || echo 0)
    echo "Upgradable: $apt_count packages"
else
    echo "apt not available"
fi
echo ""

echo "--- Security updates ---"
if command -v unattended-upgrades &>/dev/null; then
    echo "Unattended-upgrades: installed"
    if command -v systemctl &>/dev/null; then
        svc_state=$(systemctl is-active unattended-upgrades 2>/dev/null || echo "unknown")
        echo "Service: $svc_state"
    fi
    if [ -d /var/log/unattended-upgrades ]; then
        ls -lt /var/log/unattended-upgrades/ 2>/dev/null | head -5 || echo "  (log directory empty)"
    else
        echo "  (no log directory found)"
    fi
else
    echo "Unattended-upgrades: not installed"
    echo "  Install with: sudo apt install unattended-upgrades"
fi
echo ""

echo "--- Snap updates ---"
if command -v snap &>/dev/null; then
    snap_updates=$(snap refresh --list 2>/dev/null || true)
    if [ -z "$snap_updates" ]; then
        echo "All snaps up to date"
    else
        echo "$snap_updates"
    fi
else
    echo "snap not installed"
fi
echo ""

echo "--- Flatpak updates ---"
if command -v flatpak &>/dev/null; then
    flatpak_updates=$(flatpak remote-ls --updates 2>/dev/null || true)
    if [ -z "$flatpak_updates" ]; then
        echo "All flatpaks up to date"
    else
        echo "$flatpak_updates"
    fi
else
    echo "flatpak not installed"
fi
echo ""

echo "--- Kernel ---"
running_kernel=$(uname -r 2>/dev/null || echo "unknown")
echo "Running: $running_kernel"
if command -v dpkg &>/dev/null; then
    latest_kernel=$(dpkg -l 'linux-image-*' 2>/dev/null | grep '^ii' | awk '{print $2}' | sort -V | tail -1 || echo "unknown")
    echo "Latest installed: $latest_kernel"
else
    echo "Latest installed: (dpkg not available)"
fi
echo ""

echo "--- Last APT update ---"
if [ -f /var/cache/apt/pkgcache.bin ]; then
    stat -c '%y' /var/cache/apt/pkgcache.bin 2>/dev/null | cut -d. -f1 || echo "Cannot read timestamp"
else
    echo "APT cache not found — run: sudo apt update"
fi
echo ""
echo "To update: sudo apt update && sudo apt upgrade"
