#!/usr/bin/env bash
# Find orphaned/unused packages (DRY RUN — does not remove anything)
set -uo pipefail

echo "=== ORPHANED PACKAGES (dry run) ==="
echo ""

echo "--- APT autoremovable ---"
if command -v apt &>/dev/null; then
    autoremovable=$(apt list --autoremovable 2>/dev/null | tail -n +2 || true)
    if [ -z "$autoremovable" ]; then
        echo "No autoremovable packages found"
    else
        echo "$autoremovable"
    fi
    autoremove_count=$(echo "$autoremovable" | grep -c . 2>/dev/null || echo 0)
    echo "Count: $autoremove_count"
else
    echo "apt not available"
fi
echo ""

echo "--- APT residual configs ---"
if command -v dpkg &>/dev/null; then
    residual=$(dpkg -l 2>/dev/null | grep '^rc' | awk '{print $2}' | head -20 || true)
    if [ -z "$residual" ]; then
        echo "No residual configs found"
    else
        echo "$residual"
    fi
    rc_count=$(dpkg -l 2>/dev/null | grep -c '^rc' || echo 0)
    echo "Count: $rc_count"
else
    echo "dpkg not available"
fi
echo ""

echo "--- Old kernels ---"
if command -v dpkg &>/dev/null; then
    kernel_list=$(dpkg -l 'linux-image-*' 2>/dev/null | grep '^ii' | awk '{print $2, $3}' || true)
    if [ -z "$kernel_list" ]; then
        echo "No kernel packages found via dpkg"
    else
        echo "$kernel_list"
    fi
else
    echo "dpkg not available"
fi
current_kernel=$(uname -r 2>/dev/null || echo "unknown")
echo "Current kernel: $current_kernel"
echo ""

echo "--- Snap revisions (disabled/old) ---"
if command -v snap &>/dev/null; then
    disabled_snaps=$(snap list --all 2>/dev/null | awk '/disabled/{print $1, $3, $4}' || true)
    if [ -z "$disabled_snaps" ]; then
        echo "No disabled snap revisions found"
    else
        echo "$disabled_snaps"
    fi
else
    echo "snap not installed"
fi
echo ""

echo "--- APT cache size ---"
if [ -d /var/cache/apt/archives ]; then
    timeout 10 du -sh /var/cache/apt/archives 2>/dev/null || echo "Cannot read apt cache size"
else
    echo "APT cache directory not found"
fi
echo ""

echo "=== TO CLEAN (run manually) ==="
echo "  sudo apt autoremove -y"
echo "  sudo apt autoclean"
echo "  sudo dpkg --purge \$(dpkg -l | grep '^rc' | awk '{print \$2}')"
echo "  snap list --all | awk '/disabled/{print \$1, \$3}' | while read name rev; do sudo snap remove \"\$name\" --revision=\"\$rev\"; done"
