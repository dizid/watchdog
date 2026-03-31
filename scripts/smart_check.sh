#!/usr/bin/env bash
# SMART drive health check — requires smartmontools (sudo apt install smartmontools)
set -uo pipefail

echo "=== SMART DRIVE HEALTH ==="
echo ""

if ! command -v smartctl &>/dev/null; then
    echo "smartmontools not installed."
    echo "  Install with: sudo apt install smartmontools"
    exit 0
fi

found_disk=false

# Check SATA/SAS drives
for disk in /dev/sd?; do
    [ -b "$disk" ] || continue
    found_disk=true
    echo "--- $disk ---"
    if sudo -n smartctl -H "$disk" 2>/dev/null; then
        echo ""
        sudo -n smartctl -A "$disk" 2>/dev/null \
            | grep -E '(Temperature|Reallocated|Wear_Leveling|Power_On|Media_and_Data)' \
            || echo "  No SMART attributes matched"
    else
        echo "  Needs sudo. Run: sudo smartctl -H $disk"
    fi
    echo ""
done

# Check NVMe drives
for disk in /dev/nvme?n?; do
    [ -b "$disk" ] || continue
    found_disk=true
    echo "--- $disk ---"
    if sudo -n smartctl -H "$disk" 2>/dev/null; then
        echo ""
        sudo -n smartctl -A "$disk" 2>/dev/null \
            | grep -E '(Temperature|Reallocated|Wear_Leveling|Power_On|Media_and_Data|Available_Spare|Percentage_Used)' \
            || echo "  No SMART attributes matched"
    else
        echo "  Needs sudo. Run: sudo smartctl -H $disk"
    fi
    echo ""
done

if [ "$found_disk" = false ]; then
    echo "No block devices found at /dev/sd* or /dev/nvme*n*"
fi
