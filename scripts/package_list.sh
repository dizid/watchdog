#!/usr/bin/env bash
# Export installed package lists for disaster recovery
set -uo pipefail

EXPORT_DIR="${WATCHDOG_DOCS_DIR:-$HOME/DEV/system-mgt/docs}"
DATE=$(date +%Y-%m-%d)

echo "=== PACKAGE INVENTORY ==="
echo ""

# Verify export directory exists
if [ ! -d "$EXPORT_DIR" ]; then
    echo "Export directory not found: $EXPORT_DIR"
    echo "Creating it..."
    mkdir -p "$EXPORT_DIR" || { echo "Cannot create $EXPORT_DIR — aborting export"; exit 1; }
fi

# APT packages
if command -v dpkg &>/dev/null; then
    apt_count=$(dpkg --get-selections 2>/dev/null | grep -c 'install$' || echo 0)
    echo "APT packages:    $apt_count"
else
    echo "APT packages:    dpkg not available"
fi

# Snap packages
if command -v snap &>/dev/null; then
    snap_count=$(snap list 2>/dev/null | tail -n +2 | wc -l || echo 0)
    echo "Snap packages:   $snap_count"
else
    echo "Snap packages:   snap not installed"
fi

# Flatpak packages
if command -v flatpak &>/dev/null; then
    flat_count=$(flatpak list 2>/dev/null | wc -l || echo 0)
    echo "Flatpak apps:    $flat_count"
else
    echo "Flatpak apps:    flatpak not installed"
fi

# pip packages
if command -v pip3 &>/dev/null; then
    pip_count=$(pip3 list 2>/dev/null | tail -n +3 | wc -l || echo 0)
    echo "Pip3 packages:   $pip_count"
else
    echo "Pip3 packages:   pip3 not installed"
fi

# npm global packages
if command -v npm &>/dev/null; then
    npm_count=$(npm -g list --depth=0 2>/dev/null | tail -n +2 | wc -l || echo 0)
    echo "NPM global:      $npm_count"
else
    echo "NPM global:      npm not installed"
fi

echo ""
echo "=== EXPORTING LISTS ==="
echo "Export dir: $EXPORT_DIR"
echo ""

# APT
if command -v dpkg &>/dev/null; then
    if dpkg --get-selections > "$EXPORT_DIR/apt-packages-${DATE}.txt" 2>/dev/null; then
        echo "Saved: apt-packages-${DATE}.txt"
    else
        echo "Failed: apt-packages (dpkg error)"
    fi
else
    echo "Skipped: apt-packages (dpkg not available)"
fi

# Snap
if command -v snap &>/dev/null; then
    if snap list > "$EXPORT_DIR/snap-packages-${DATE}.txt" 2>/dev/null; then
        echo "Saved: snap-packages-${DATE}.txt"
    else
        echo "Failed: snap-packages (snap error)"
    fi
else
    echo "Skipped: snap-packages (snap not installed)"
fi

# Flatpak
if command -v flatpak &>/dev/null; then
    if flatpak list > "$EXPORT_DIR/flatpak-packages-${DATE}.txt" 2>/dev/null; then
        echo "Saved: flatpak-packages-${DATE}.txt"
    else
        echo "Failed: flatpak-packages (flatpak error)"
    fi
else
    echo "Skipped: flatpak-packages (flatpak not installed)"
fi

# pip3
if command -v pip3 &>/dev/null; then
    if pip3 list > "$EXPORT_DIR/pip3-packages-${DATE}.txt" 2>/dev/null; then
        echo "Saved: pip3-packages-${DATE}.txt"
    else
        echo "Failed: pip3-packages (pip3 error)"
    fi
else
    echo "Skipped: pip3-packages (pip3 not installed)"
fi

# npm
if command -v npm &>/dev/null; then
    if npm -g list --depth=0 > "$EXPORT_DIR/npm-global-${DATE}.txt" 2>/dev/null; then
        echo "Saved: npm-global-${DATE}.txt"
    else
        echo "Failed: npm-global (npm error)"
    fi
else
    echo "Skipped: npm-global (npm not installed)"
fi

echo ""
echo "Package lists exported to: $EXPORT_DIR"
