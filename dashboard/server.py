#!/usr/bin/env python3
"""Watchdog — lightweight system health dashboard.
Runs predefined system checks and surfaces actionable findings.
"""

import os
import subprocess
import json
import time
from flask import Flask, render_template, jsonify, request
from analyzer import analyze_all

app = Flask(__name__)

SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts')

# Whitelist of allowed scripts — no arbitrary command execution
TASKS = {
    # Monitoring
    'system_info': {
        'name': 'System Info',
        'description': 'Hostname, OS, CPU, RAM, disk overview',
        'category': 'monitoring',
        'timeout': 15,
    },
    'failed_services': {
        'name': 'Failed Services',
        'description': 'Systemd units in failed state + recent errors',
        'category': 'monitoring',
        'timeout': 15,
    },
    'boot_analysis': {
        'name': 'Boot Analysis',
        'description': 'Startup time breakdown by service',
        'category': 'monitoring',
        'timeout': 15,
    },
    # Disk
    'disk_audit': {
        'name': 'Disk Audit',
        'description': 'Space hogs, large files, old files',
        'category': 'disk',
        'timeout': 60,
    },
    'journal_usage': {
        'name': 'Journal Logs',
        'description': 'Systemd journal and log file sizes',
        'category': 'disk',
        'timeout': 15,
    },
    'smart_check': {
        'name': 'SMART Check',
        'description': 'Drive health via SMART (may need sudo)',
        'category': 'disk',
        'timeout': 30,
    },
    # Security
    'open_ports': {
        'name': 'Open Ports',
        'description': 'Listening TCP/UDP ports and connections',
        'category': 'security',
        'timeout': 15,
    },
    'ssh_key_audit': {
        'name': 'SSH Key Audit',
        'description': 'SSH keys, authorized keys, GPG inventory',
        'category': 'security',
        'timeout': 15,
    },
    'firewall_status': {
        'name': 'Firewall Status',
        'description': 'UFW / iptables / nftables rules',
        'category': 'security',
        'timeout': 15,
    },
    'updates_check': {
        'name': 'Updates Check',
        'description': 'Available apt, snap, flatpak updates',
        'category': 'security',
        'timeout': 30,
    },
    # Cleanup
    'orphan_cleanup': {
        'name': 'Orphan Packages',
        'description': 'Unused packages and old kernels (dry run)',
        'category': 'cleanup',
        'timeout': 30,
    },
    # Inventory
    'package_list': {
        'name': 'Package Export',
        'description': 'Export all installed package lists to docs/',
        'category': 'inventory',
        'timeout': 30,
    },
    'cron_inventory': {
        'name': 'Cron Jobs',
        'description': 'All scheduled cron jobs and systemd timers',
        'category': 'inventory',
        'timeout': 15,
    },
}

# Track last run times and results in memory
run_history = {}


@app.route('/')
def home():
    return render_template('overview.html')


@app.route('/checks')
def checks():
    return render_template('index.html', tasks=TASKS)


@app.route('/api/tasks')
def list_tasks():
    """Return all available tasks with metadata."""
    result = {}
    for key, task in TASKS.items():
        result[key] = {**task, 'last_run': run_history.get(key, {}).get('timestamp')}
    return jsonify(result)


@app.route('/api/run/<script_name>', methods=['POST'])
def run_script(script_name):
    """Run a whitelisted script and return its output."""
    if script_name not in TASKS:
        return jsonify({'error': f'Unknown task: {script_name}'}), 404

    script_path = os.path.join(SCRIPTS_DIR, f'{script_name}.sh')
    if not os.path.isfile(script_path):
        return jsonify({'error': f'Script not found: {script_name}.sh'}), 404

    timeout = TASKS[script_name].get('timeout', 30)
    start_time = time.time()

    try:
        result = subprocess.run(
            ['bash', script_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, 'TERM': 'dumb'},
        )
        elapsed = round(time.time() - start_time, 1)

        run_history[script_name] = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'returncode': result.returncode,
            'elapsed': elapsed,
        }

        return jsonify({
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode,
            'elapsed': elapsed,
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'error': f'Script timed out after {timeout}s',
            'output': '',
            'returncode': -1,
            'elapsed': timeout,
        }), 504


@app.route('/api/quick-stats')
def quick_stats():
    """Return lightweight system stats for the header bar."""
    stats = {}

    # CPU usage
    try:
        with open('/proc/loadavg') as f:
            parts = f.read().split()
            stats['load'] = f'{parts[0]} / {parts[1]} / {parts[2]}'
    except Exception:
        stats['load'] = '?'

    # Memory
    try:
        with open('/proc/meminfo') as f:
            meminfo = {}
            for line in f:
                key, val = line.split(':')
                meminfo[key.strip()] = int(val.strip().split()[0])
            total = meminfo['MemTotal'] / 1024 / 1024
            available = meminfo['MemAvailable'] / 1024 / 1024
            used = total - available
            stats['ram'] = f'{used:.1f}G / {total:.1f}G'
            stats['ram_pct'] = round((used / total) * 100)
    except Exception:
        stats['ram'] = '?'
        stats['ram_pct'] = 0

    # Disk
    try:
        st = os.statvfs('/')
        total = st.f_blocks * st.f_frsize / (1024 ** 3)
        free = st.f_bavail * st.f_frsize / (1024 ** 3)
        used = total - free
        stats['disk'] = f'{used:.0f}G / {total:.0f}G'
        stats['disk_pct'] = round((used / total) * 100)
    except Exception:
        stats['disk'] = '?'
        stats['disk_pct'] = 0

    # Uptime
    try:
        with open('/proc/uptime') as f:
            seconds = float(f.read().split()[0])
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            mins = int((seconds % 3600) // 60)
            if days > 0:
                stats['uptime'] = f'{days}d {hours}h {mins}m'
            elif hours > 0:
                stats['uptime'] = f'{hours}h {mins}m'
            else:
                stats['uptime'] = f'{mins}m'
    except Exception:
        stats['uptime'] = '?'

    # Hostname
    try:
        stats['hostname'] = os.uname().nodename
    except Exception:
        stats['hostname'] = '?'

    return jsonify(stats)


# ── Overview Page ──

# Whitelisted fix actions — each maps to a specific safe command
FIX_ACTIONS = {
    'fix_apt_autoremove': {
        'label': 'Remove orphaned packages',
        'command': 'sudo apt autoremove -y',
        'confirm': 'This will remove unused dependency packages. Continue?',
        'needs_sudo': True,
    },
    'fix_apt_autoclean': {
        'label': 'Clean APT cache',
        'command': 'sudo apt autoclean',
        'confirm': 'This will remove old cached package files. Continue?',
        'needs_sudo': True,
    },
    'fix_apt_update': {
        'label': 'Update & upgrade packages',
        'command': 'sudo apt update && sudo apt upgrade -y',
        'confirm': 'This will update package lists and upgrade all packages. Continue?',
        'needs_sudo': True,
    },
    'fix_journal_vacuum': {
        'label': 'Vacuum journal logs to 500MB',
        'command': 'sudo journalctl --vacuum-size=500M',
        'confirm': 'This will remove journal logs until total size is under 500MB. Continue?',
        'needs_sudo': True,
    },
    'fix_purge_configs': {
        'label': 'Purge residual config files',
        'command': "dpkg -l | grep '^rc' | awk '{print $2}' | xargs sudo dpkg --purge",
        'confirm': 'This will remove leftover config files from uninstalled packages. Continue?',
        'needs_sudo': True,
    },
    'fix_docker_prune': {
        'label': 'Docker system prune',
        'command': 'docker system prune -f',
        'confirm': 'This will remove unused Docker images, containers, and networks. Continue?',
        'needs_sudo': False,
    },
    'fix_high_cpu': {
        'label': 'Show top CPU processes',
        'command': 'ps aux --sort=-%cpu | head -15',
        'confirm': 'This will show the top CPU-consuming processes.',
        'needs_sudo': False,
    },
    'fix_disk_cleanup': {
        'label': 'Show disk usage breakdown',
        'command': 'du -h --max-depth=1 / 2>/dev/null | sort -rh | head -20',
        'confirm': 'This will show the largest directories on disk.',
        'needs_sudo': False,
    },
    'fix_enable_ufw': {
        'label': 'Enable UFW with default deny incoming',
        'command': 'sudo ufw default deny incoming && sudo ufw default allow outgoing && sudo ufw --force enable',
        'confirm': 'This will enable UFW firewall: deny incoming, allow outgoing. Existing SSH sessions will NOT be interrupted. Continue?',
        'needs_sudo': True,
    },
    'fix_install_ufw': {
        'label': 'Install UFW',
        'command': 'sudo apt install -y ufw',
        'confirm': 'This will install the UFW firewall package. Continue?',
        'needs_sudo': True,
    },
    'fix_install_unattended': {
        'label': 'Install unattended-upgrades',
        'command': 'sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure -plow unattended-upgrades',
        'confirm': 'This will install and enable automatic security updates. Continue?',
        'needs_sudo': True,
    },
    'fix_install_smartmontools': {
        'label': 'Install smartmontools',
        'command': 'sudo apt install -y smartmontools',
        'confirm': 'This will install SMART disk monitoring tools. Continue?',
        'needs_sudo': True,
    },
    # Read-only "show" actions (just re-run the relevant script)
    'show_large_files': {
        'label': 'Show large files',
        'command': 'find $HOME -type f -size +100M -exec ls -lhS {} + 2>/dev/null | head -30',
        'confirm': 'Show files larger than 100MB.',
        'needs_sudo': False,
    },
    'show_failed_services': {
        'label': 'Show failed service details',
        'command': 'systemctl --failed && echo "---" && journalctl -p err --since "24h ago" --no-pager | tail -30',
        'confirm': 'Show failed systemd services and recent errors.',
        'needs_sudo': False,
    },
    'show_open_ports': {
        'label': 'Show listening ports',
        'command': 'ss -tlnp | column -t',
        'confirm': 'Show all listening TCP ports with process info.',
        'needs_sudo': False,
    },
    'show_ssh_keys': {
        'label': 'Show SSH key details',
        'command': 'for f in ~/.ssh/id_*; do [ -f "$f" ] && [[ "$f" != *.pub ]] && ssh-keygen -lf "$f.pub" 2>/dev/null; done; echo "---"; cat ~/.ssh/authorized_keys 2>/dev/null || echo "No authorized_keys"',
        'confirm': 'Show SSH key fingerprints and authorized keys.',
        'needs_sudo': False,
    },
    'show_boot_blame': {
        'label': 'Show slowest boot services',
        'command': 'systemd-analyze blame | head -20',
        'confirm': 'Show the 20 slowest services during boot.',
        'needs_sudo': False,
    },
}


@app.route('/overview')
def overview_redirect():
    """Legacy redirect for bookmarks."""
    from flask import redirect
    return redirect('/')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Run all scripts, analyze outputs, return findings."""
    results = {}
    scripts_to_run = [
        'system_info', 'disk_audit', 'failed_services', 'journal_usage',
        'open_ports', 'updates_check', 'orphan_cleanup', 'firewall_status',
        'ssh_key_audit', 'boot_analysis', 'smart_check',
    ]

    for name in scripts_to_run:
        script_path = os.path.join(SCRIPTS_DIR, f'{name}.sh')
        if not os.path.isfile(script_path):
            continue
        timeout = TASKS.get(name, {}).get('timeout', 30)
        try:
            proc = subprocess.run(
                ['bash', script_path],
                capture_output=True, text=True, timeout=timeout,
                env={**os.environ, 'TERM': 'dumb'},
            )
            results[name] = {
                'output': proc.stdout,
                'error': proc.stderr,
                'returncode': proc.returncode,
            }
        except subprocess.TimeoutExpired:
            results[name] = {'output': '', 'error': f'Timed out ({timeout}s)', 'returncode': -1}

    findings = analyze_all(results)
    return jsonify({
        'findings': findings,
        'scanned': len(results),
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
    })


@app.route('/api/fix/<action_id>', methods=['POST'])
def run_fix(action_id):
    """Run a whitelisted fix action."""
    if action_id not in FIX_ACTIONS:
        return jsonify({'error': f'Unknown action: {action_id}'}), 404

    action = FIX_ACTIONS[action_id]
    try:
        result = subprocess.run(
            ['bash', '-c', action['command']],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, 'TERM': 'dumb'},
        )
        return jsonify({
            'output': result.stdout,
            'error': result.stderr,
            'returncode': result.returncode,
        })
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Action timed out (120s)', 'output': '', 'returncode': -1}), 504


@app.route('/api/fix-info/<action_id>')
def fix_info(action_id):
    """Return info about a fix action (for confirmation dialog)."""
    if action_id not in FIX_ACTIONS:
        return jsonify({'error': 'Unknown action'}), 404
    action = FIX_ACTIONS[action_id]
    return jsonify({
        'label': action['label'],
        'command': action['command'],
        'confirm': action['confirm'],
        'needs_sudo': action['needs_sudo'],
    })


if __name__ == '__main__':
    print('\n  Watchdog — System Health Dashboard')
    print('  http://127.0.0.1:5111\n')
    app.run(host='127.0.0.1', port=5111, debug=False)
