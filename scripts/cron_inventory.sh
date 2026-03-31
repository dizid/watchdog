#!/usr/bin/env bash
# List all cron jobs across the system
set -uo pipefail

echo "=== CRON JOB INVENTORY ==="
echo ""

echo "--- User crontab ($(whoami 2>/dev/null || echo unknown)) ---"
user_cron=$(crontab -l 2>/dev/null || true)
if [ -z "$user_cron" ]; then
    echo "(empty — no user crontab)"
else
    echo "$user_cron"
fi
echo ""

echo "--- System crontab (/etc/crontab) ---"
if [ -f /etc/crontab ]; then
    sys_cron=$(grep -v '^#' /etc/crontab 2>/dev/null | grep -v '^$' || true)
    if [ -z "$sys_cron" ]; then
        echo "(empty — no active entries)"
    else
        echo "$sys_cron"
    fi
else
    echo "/etc/crontab not found"
fi
echo ""

echo "--- /etc/cron.d/ ---"
if [ -d /etc/cron.d ]; then
    cron_d_files=$(ls /etc/cron.d/ 2>/dev/null || true)
    if [ -z "$cron_d_files" ]; then
        echo "(empty — no files in /etc/cron.d/)"
    else
        for f in /etc/cron.d/*; do
            [ -f "$f" ] || continue
            echo ">> $f"
            entries=$(grep -v '^#' "$f" 2>/dev/null | grep -v '^$' || true)
            if [ -z "$entries" ]; then
                echo "  (no active entries)"
            else
                echo "$entries"
            fi
            echo ""
        done
    fi
else
    echo "/etc/cron.d/ not found"
fi

echo "--- Cron directories ---"
for dir in /etc/cron.hourly /etc/cron.daily /etc/cron.weekly /etc/cron.monthly; do
    echo ">> $dir/"
    if [ -d "$dir" ]; then
        dir_contents=$(ls -1 "$dir" 2>/dev/null || true)
        if [ -z "$dir_contents" ]; then
            echo "  (empty)"
        else
            echo "$dir_contents" | while read -r item; do echo "  $item"; done
        fi
    else
        echo "  (directory not found)"
    fi
done
echo ""

echo "--- Systemd timers (active) ---"
if command -v systemctl &>/dev/null; then
    timers=$(systemctl list-timers --no-pager 2>/dev/null | head -20 || true)
    if [ -z "$timers" ]; then
        echo "No active systemd timers found"
    else
        echo "$timers"
    fi
else
    echo "systemctl not available"
fi
