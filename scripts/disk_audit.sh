#!/usr/bin/env bash
# Disk usage audit: largest directories, old files, space hogs
set -uo pipefail

echo "=== DISK USAGE BY MOUNT ==="
if command -v df &>/dev/null; then
    df -h --output=target,size,used,avail,pcent -x tmpfs -x devtmpfs -x squashfs 2>/dev/null || \
        df -h 2>/dev/null || echo "Cannot read disk usage"
else
    echo "df command not available"
fi
echo ""

echo "=== TOP 15 LARGEST DIRECTORIES IN /home ==="
if command -v du &>/dev/null; then
    timeout 30 du -h --max-depth=2 "$HOME" 2>/dev/null | sort -rh | head -15 || echo "du timed out or failed"
else
    echo "du command not available"
fi
echo ""

echo "=== LARGE FILES (>100MB) IN /home ==="
large_files=$(timeout 60 find "$HOME" -type f -size +100M 2>/dev/null | head -20)
if [ -z "$large_files" ]; then
    echo "No files larger than 100MB found in $HOME"
else
    echo "$large_files" | while read -r f; do
        ls -lh "$f" 2>/dev/null | awk '{print $5, $9}' || true
    done | sort -rh
fi
echo "(showing top 20)"
echo ""

echo "=== OLD FILES (>365 days, not accessed) IN /home ==="
old_files=$(timeout 60 find "$HOME" -type f -atime +365 \
    -not -path '*/.cache/*' \
    -not -path '*/.local/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/.git/*' \
    2>/dev/null | head -20)
if [ -z "$old_files" ]; then
    echo "No files older than 365 days found (or search timed out)"
else
    echo "$old_files"
fi
echo "(showing top 20)"
echo ""

echo "=== DOCKER DISK USAGE ==="
if command -v docker &>/dev/null; then
    docker system df 2>/dev/null || echo "Docker not running or no permissions"
else
    echo "Docker not installed"
fi
echo ""

echo "=== SNAP DISK USAGE ==="
if command -v snap &>/dev/null; then
    snap_list=$(snap list 2>/dev/null | awk 'NR>1 {print $1}')
    if [ -z "$snap_list" ]; then
        echo "No snap packages installed"
    else
        echo "$snap_list" | while read -r pkg; do
            size=$(snap info "$pkg" 2>/dev/null | grep -i "installed:" | awk '{print $NF}' || echo "?")
            echo "  $pkg: $size"
        done
    fi
else
    echo "Snap not installed"
fi
