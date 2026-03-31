#!/usr/bin/env bash
# Journal log disk usage and rotation info
set -uo pipefail

echo "=== JOURNAL LOG USAGE ==="
echo ""

if ! command -v journalctl &>/dev/null; then
    echo "journalctl not available — not a systemd system"
else
    journalctl --disk-usage 2>/dev/null || echo "Cannot read journal disk usage"
fi
echo ""

echo "=== JOURNAL FILES ==="
if [ -d /var/log/journal ]; then
    journal_files=$(ls -lh /var/log/journal/*/ 2>/dev/null | tail -20 || true)
    if [ -z "$journal_files" ]; then
        echo "Journal directory is empty or not readable"
    else
        echo "$journal_files"
    fi
else
    echo "Journal directory /var/log/journal not found (volatile journal may be in /run/log/journal)"
    ls -lh /run/log/journal/*/ 2>/dev/null | tail -20 || echo "No journal files accessible"
fi
echo ""

echo "=== SYSLOG SIZE ==="
syslog_files=$(ls -lh /var/log/syslog* /var/log/kern.log* /var/log/auth.log* 2>/dev/null || true)
if [ -z "$syslog_files" ]; then
    echo "Standard syslog files not found"
else
    echo "$syslog_files"
fi
echo ""

echo "=== TOTAL /var/log SIZE ==="
if [ -d /var/log ]; then
    timeout 15 du -sh /var/log 2>/dev/null || echo "Cannot read /var/log size (timed out or permission denied)"
else
    echo "/var/log directory not found"
fi
echo ""

echo "=== LARGEST LOG FILES ==="
if [ -d /var/log ]; then
    largest=$(timeout 15 find /var/log -type f 2>/dev/null | xargs ls -lhS 2>/dev/null | head -15 || true)
    if [ -z "$largest" ]; then
        echo "Cannot scan /var/log (permission denied or timed out)"
    else
        echo "$largest"
    fi
else
    echo "/var/log directory not found"
fi
echo ""

echo "To vacuum journals: sudo journalctl --vacuum-size=500M"
echo "To vacuum by time:  sudo journalctl --vacuum-time=30d"
