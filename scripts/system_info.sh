#!/usr/bin/env bash
# System information overview: hostname, OS, kernel, CPU, RAM, swap, uptime
set -uo pipefail

echo "=== SYSTEM INFORMATION ==="
echo ""

hostname_val=$(hostname 2>/dev/null || echo "unknown")
user_val=$(whoami 2>/dev/null || echo "unknown")
os_val=$(lsb_release -ds 2>/dev/null || grep PRETTY_NAME /etc/os-release 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "unknown")
kernel_val=$(uname -r 2>/dev/null || echo "unknown")
arch_val=$(uname -m 2>/dev/null || echo "unknown")
uptime_val=$(uptime -p 2>/dev/null || uptime 2>/dev/null || echo "unknown")
boot_val=$(who -b 2>/dev/null | awk '{print $3, $4}' || echo "unknown")

echo "Hostname:    $hostname_val"
echo "User:        $user_val"
echo "OS:          $os_val"
echo "Kernel:      $kernel_val"
echo "Arch:        $arch_val"
echo "Uptime:      $uptime_val"
echo "Boot time:   $boot_val"
echo ""

echo "=== CPU ==="
cpu_model=$(grep 'model name' /proc/cpuinfo 2>/dev/null | head -1 | cut -d: -f2 | xargs || echo "unknown")
cpu_cores=$(nproc 2>/dev/null || grep -c '^processor' /proc/cpuinfo 2>/dev/null || echo "unknown")
cpu_usage=$(top -bn1 2>/dev/null | grep 'Cpu(s)' | awk '{print $2}' || echo "unknown")
load_avg=$(awk '{print $1, $2, $3}' /proc/loadavg 2>/dev/null || echo "unknown")

echo "Model:       $cpu_model"
echo "Cores:       $cpu_cores"
echo "Usage:       ${cpu_usage}%"
echo "Load avg:    $load_avg"
echo ""

echo "=== MEMORY ==="
if command -v free &>/dev/null; then
    free -h 2>/dev/null | awk '
    /^Mem:/ {
        printf "RAM:         %s used / %s total (%s available)\n", $3, $2, $7
    }
    /^Swap:/ {
        printf "Swap:        %s used / %s total\n", $3, $2
    }' || echo "Cannot read memory info"
else
    echo "free command not available"
fi
echo ""

echo "=== DISK ==="
if command -v df &>/dev/null; then
    df -h --output=target,size,used,avail,pcent -x tmpfs -x devtmpfs -x squashfs 2>/dev/null | head -20 || \
        df -h 2>/dev/null | head -20 || echo "Cannot read disk info"
else
    echo "df command not available"
fi
