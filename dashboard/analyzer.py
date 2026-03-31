"""Analyze raw script output and produce structured, actionable findings."""

import re
import os


def analyze_all(results: dict) -> list[dict]:
    """Take dict of {script_name: {output, error, returncode}} and return findings."""
    findings = []

    if 'system_info' in results:
        findings.extend(_analyze_system_info(results['system_info']))
    if 'disk_audit' in results:
        findings.extend(_analyze_disk_audit(results['disk_audit']))
    if 'failed_services' in results:
        findings.extend(_analyze_failed_services(results['failed_services']))
    if 'journal_usage' in results:
        findings.extend(_analyze_journal(results['journal_usage']))
    if 'open_ports' in results:
        findings.extend(_analyze_ports(results['open_ports']))
    if 'updates_check' in results:
        findings.extend(_analyze_updates(results['updates_check']))
    if 'orphan_cleanup' in results:
        findings.extend(_analyze_orphans(results['orphan_cleanup']))
    if 'firewall_status' in results:
        findings.extend(_analyze_firewall(results['firewall_status']))
    if 'ssh_key_audit' in results:
        findings.extend(_analyze_ssh(results['ssh_key_audit']))
    if 'boot_analysis' in results:
        findings.extend(_analyze_boot(results['boot_analysis']))
    if 'smart_check' in results:
        findings.extend(_analyze_smart(results['smart_check']))
    if 'cron_inventory' in results:
        findings.extend(_analyze_cron(results['cron_inventory']))

    # Sort: critical first, then warning, then info
    severity_order = {'critical': 0, 'warning': 1, 'info': 2}
    findings.sort(key=lambda f: severity_order.get(f['severity'], 3))
    return findings


def _out(result):
    """Extract stdout text from a result dict."""
    return result.get('output', '') if isinstance(result, dict) else ''


# ── System Info ──

def _analyze_system_info(result):
    findings = []
    out = _out(result)

    # High CPU — try multiple formats:
    # "Usage: 42.3%", "cpu: 42.3%", "CPU Usage: 42%", plain percentage line
    cpu = None
    for pattern in [
        r'[Cc][Pp][Uu]\s*[Uu]sage[:\s]+([0-9.]+)\s*%',
        r'[Uu]sage[:\s]+([0-9.]+)\s*%',
        r'us,\s*([0-9.]+)\s*%\s*sy',  # top/vmstat style "10.0% us, 5.0% sy"
        r'([0-9.]+)\s*%\s*us',         # "42.3% us"
    ]:
        m = re.search(pattern, out)
        if m:
            cpu = float(m.group(1))
            break

    if cpu is not None:
        if cpu > 90:
            findings.append(_finding('critical', 'cpu', 'CPU usage critical',
                f'CPU at {cpu:.0f}%. Check for runaway processes.',
                'fix_high_cpu', 'Show top CPU processes'))
        elif cpu > 70:
            findings.append(_finding('warning', 'cpu', 'CPU usage elevated',
                f'CPU at {cpu:.0f}%. Worth monitoring.',
                'fix_high_cpu', 'Show top CPU processes'))

    # Load average vs. core count
    # Handles: "load average: 1.23, 1.45, 1.56" (uptime) or "Load: 1.23 1.45 1.56"
    load_avg = None
    core_count = None

    load_m = re.search(
        r'load\s+average[s]?[:\s]+([0-9.]+)[,\s]+([0-9.]+)[,\s]+([0-9.]+)',
        out, re.IGNORECASE
    )
    if load_m:
        load_avg = float(load_m.group(1))  # 1-minute load

    # Try multiple patterns for CPU/core count
    for pattern in [
        r'[Cc]ore[s]?[:\s]+(\d+)',
        r'[Cc][Pp][Uu]\(s\)[:\s]+(\d+)',
        r'(\d+)\s+core[s]?',
        r'[Cc][Pp][Uu]s?[:\s]+(\d+)',
    ]:
        m = re.search(pattern, out)
        if m:
            core_count = int(m.group(1))
            break

    if load_avg is not None and core_count is not None and core_count > 0:
        ratio = load_avg / core_count
        if ratio > 2.0:
            findings.append(_finding('critical', 'cpu', f'System load critically high ({load_avg:.2f})',
                f'Load average {load_avg:.2f} is {ratio:.1f}x the {core_count} CPU core(s). System is overloaded.',
                'fix_high_cpu', 'Show top CPU processes'))
        elif ratio > 1.0:
            findings.append(_finding('warning', 'cpu', f'System load above capacity ({load_avg:.2f})',
                f'Load average {load_avg:.2f} exceeds {core_count} core(s). Performance may degrade.',
                'fix_high_cpu', 'Show top CPU processes'))

    # RAM usage — try multiple formats:
    # "RAM: 3.2G used / 8.0G total", "Mem: 3200M used", "MemTotal: 8192 kB" + "MemAvailable: 1024 kB"
    ram_used_gb = None
    ram_total_gb = None
    swap_used_gb = None
    swap_total_gb = None

    # Format: "RAM: 3.2G used / 8.0G total" or "Memory: 3.2G / 8.0G"
    ram_m = re.search(
        r'(?:[Rr][Aa][Mm]|[Mm]em(?:ory)?)[:\s]+([0-9.]+\s*[GMKgmk][Bi]?)[^/]*/\s*([0-9.]+\s*[GMKgmk][Bi]?)',
        out
    )
    if ram_m:
        ram_used_gb = _parse_size_gb(ram_m.group(1))
        ram_total_gb = _parse_size_gb(ram_m.group(2))
    else:
        # "used / total" on same line: "3.2G used / 8.0G total"
        ram_m2 = re.search(
            r'([0-9.]+\s*[GMKgmk][Bi]?)\s+used\s*/\s*([0-9.]+\s*[GMKgmk][Bi]?)\s+total',
            out
        )
        if ram_m2:
            ram_used_gb = _parse_size_gb(ram_m2.group(1))
            ram_total_gb = _parse_size_gb(ram_m2.group(2))

    # Swap: "Swap: 500M used / 2.0G total"
    swap_m = re.search(
        r'[Ss]wap[:\s]+([0-9.]+\s*[GMKgmk][Bi]?)\s+used\s*/\s*([0-9.]+\s*[GMKgmk][Bi]?)\s+total',
        out
    )
    if not swap_m:
        swap_m = re.search(
            r'[Ss]wap[:\s]+([0-9.]+\s*[GMKgmk][Bi]?)[^/]*/\s*([0-9.]+\s*[GMKgmk][Bi]?)',
            out
        )
    if swap_m:
        swap_used_gb = _parse_size_gb(swap_m.group(1))
        swap_total_gb = _parse_size_gb(swap_m.group(2))

    if ram_used_gb is not None and ram_total_gb is not None and ram_total_gb > 0:
        ram_pct = ram_used_gb / ram_total_gb * 100
        swap_ratio = (swap_used_gb / swap_total_gb) if (swap_total_gb and swap_total_gb > 0) else 0

        ram_used_str = f'{ram_used_gb:.1f}G'
        ram_total_str = f'{ram_total_gb:.1f}G'

        if ram_pct > 95:
            # Even at 95%+ flag critical — swap ratio doesn't excuse this
            findings.append(_finding('critical', 'memory', f'RAM usage critical ({ram_pct:.0f}%)',
                f'{ram_used_str} used of {ram_total_str}. System is severely memory-constrained.',
                'fix_high_cpu', 'Show top memory processes'))
        elif ram_pct > 85:
            # Reduce false positive: if swap is barely used (<10%), system is coping
            if swap_ratio < 0.1:
                findings.append(_finding('info', 'memory', f'RAM usage high ({ram_pct:.0f}%)',
                    f'{ram_used_str} used of {ram_total_str}. Swap barely used — system is coping.',
                    None, None))
            else:
                findings.append(_finding('warning', 'memory', f'RAM usage high ({ram_pct:.0f}%)',
                    f'{ram_used_str} used of {ram_total_str}. Swap in use ({swap_ratio*100:.0f}%) — monitor closely.',
                    'fix_high_cpu', 'Show top memory processes'))
    elif swap_used_gb is not None and swap_total_gb is not None:
        # Fallback: we only have swap info, not RAM — report high swap as before
        if swap_total_gb > 0 and swap_used_gb / swap_total_gb > 0.5:
            findings.append(_finding('warning', 'memory', 'High swap usage',
                f'Swap {swap_used_gb:.1f}G used of {swap_total_gb:.1f}G. System may be memory-constrained.',
                None, None))

    # Disk usage per mount from system_info — skip header rows and short/invalid lines
    # Handles df output: "Filesystem  Size  Used  Avail  Use%  Mounted on"
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        # Skip header lines
        if re.match(r'^(?:Filesystem|Use%|tmpfs.*0%)', line, re.IGNORECASE):
            continue

        # Match lines that contain a percentage followed by a mount point
        # df format: "/dev/sda1  100G  80G  20G  80%  /"
        pct_m = re.search(r'\b(\d+)%\b', line)
        if not pct_m:
            continue
        pct = int(pct_m.group(1))
        if pct < 80:
            continue

        # Extract mount point — last field after the percentage
        after_pct = line[pct_m.end():].strip()
        mount = after_pct.split()[0] if after_pct.split() else ''
        if not mount or mount.startswith('('):
            # Fallback: first field
            parts = line.split()
            mount = parts[0] if parts else '?'

        # Skip noisy/virtual filesystems
        if any(skip in mount for skip in ['/snap/', '/proc', '/sys', '/dev', '/run']):
            continue

        # Extract available space for context (avail column in df is 4th field)
        avail_gb = 0
        df_parts = line.split()
        if len(df_parts) >= 4:
            avail_gb = _parse_size_gb(df_parts[3])

        _append_disk_finding(findings, pct, mount, avail_gb)

    # Uptime > 30 days (kernel updates need reboot)
    m = re.search(r'up\s+(\d+)\s+day', out, re.IGNORECASE)
    if m:
        days = int(m.group(1))
        if days > 30:
            findings.append(_finding('info', 'system', f'Uptime is {days} days',
                'Consider rebooting to apply kernel updates.',
                None, None))

    return findings


# ── Disk Audit ──

def _analyze_disk_audit(result):
    findings = []
    out = _out(result)

    # Large files count
    large_files = [l for l in out.split('\n') if re.match(r'^\s*[\d.]+[GMTP]', l)]
    if len(large_files) > 5:
        findings.append(_finding('info', 'disk', f'{len(large_files)} large files found (>100MB)',
            'Review large files — some may be unnecessary.',
            'show_large_files', 'Show large files'))

    # Disk mounts from disk_audit df output (catch what system_info may miss)
    # Handles both "df -h" style and custom script output
    for line in out.split('\n'):
        line = line.strip()
        if not line:
            continue
        if re.match(r'^(?:Filesystem|Use%)', line, re.IGNORECASE):
            continue

        pct_m = re.search(r'\b(\d+)%\b', line)
        if not pct_m:
            continue
        pct = int(pct_m.group(1))
        if pct < 80:
            continue

        after_pct = line[pct_m.end():].strip()
        mount = after_pct.split()[0] if after_pct.split() else ''
        if not mount or mount.startswith('('):
            parts = line.split()
            mount = parts[0] if parts else '?'

        if any(skip in mount for skip in ['/snap/', '/proc', '/sys', '/dev', '/run']):
            continue

        avail_gb = 0
        df_parts = line.split()
        if len(df_parts) >= 4:
            avail_gb = _parse_size_gb(df_parts[3])

        _append_disk_finding(findings, pct, mount, avail_gb)

    # Docker disk usage — improved: flag warning if reclaimable > 5GB
    if 'docker' in out.lower():
        docker_m = re.search(r'Reclaimable[:\s]+([0-9.]+\s*[GMKTgmkt][Bi]?)', out)
        if docker_m:
            reclaimable_str = docker_m.group(1).strip()
            reclaimable_gb = _parse_size_gb(reclaimable_str)
            if reclaimable_gb > 5:
                findings.append(_finding('warning', 'disk', f'Docker: {reclaimable_str} reclaimable',
                    f'Docker has not been pruned in a while. Run "docker system prune" to reclaim {reclaimable_str}.',
                    'fix_docker_prune', 'Docker system prune'))
            elif reclaimable_gb > 0:
                findings.append(_finding('info', 'disk', f'Docker reclaimable space: {reclaimable_str}',
                    'Unused Docker images and containers can be cleaned.',
                    'fix_docker_prune', 'Docker system prune'))

    # Snap disabled revisions — they waste disk and are common gotcha
    # "snap list --all" shows disabled revisions marked with "disabled"
    disabled_snaps = re.findall(r'^(\S+)\s+\S+\s+\d+\s+\S+\s+\S+\s+disabled', out, re.MULTILINE)
    if not disabled_snaps:
        # Alternative: count lines containing "disabled" in snap context
        snap_section = _extract_section(out, 'snap', end_markers=['---', 'Kernel', 'Old kernel'])
        if snap_section:
            disabled_snaps = re.findall(r'disabled', snap_section, re.IGNORECASE)
    if disabled_snaps:
        count = len(disabled_snaps)
        findings.append(_finding('info', 'disk', f'{count} disabled snap revision(s) wasting disk',
            'Old snap revisions are kept on disk but not used. Remove with: snap remove --revision.',
            'fix_snap_cleanup', 'Remove disabled snap revisions'))

    # Old kernels
    old_kernels = re.findall(
        r'linux-image-\d[\d.\-]+(?:-generic)?\s',
        out
    )
    # Also check for lines explicitly noting removable kernels
    kernel_remove_m = re.search(r'(\d+)\s+old\s+kernel[s]?\s+(?:can be|to)\s+remov', out, re.IGNORECASE)
    if kernel_remove_m:
        count = int(kernel_remove_m.group(1))
        findings.append(_finding('info', 'cleanup', f'{count} old kernel(s) can be removed',
            'Old kernels take space in /boot. Run: apt autoremove --purge',
            'fix_apt_autoremove', 'Run apt autoremove'))
    elif len(old_kernels) > 1:
        findings.append(_finding('info', 'cleanup', f'{len(old_kernels)} old kernel image(s) found',
            'Old kernels take space in /boot. Run: apt autoremove --purge',
            'fix_apt_autoremove', 'Run apt autoremove'))

    return findings


# ── Failed Services ──

def _analyze_failed_services(result):
    findings = []
    out = _out(result)

    if re.search(r'[Nn]o failed', out) or re.search(r'0 loaded units listed', out):
        findings.append(_finding('info', 'services', 'All services healthy',
            'No systemd units in failed state.', None, None))
        return findings

    # Collect failed unit lines — systemctl list-units --failed output variations:
    # "● nginx.service   loaded failed failed   ..."
    # "  nginx.service   loaded failed failed   ..."
    failed_lines = []
    for line in out.split('\n'):
        stripped = line.strip().lstrip('●').strip()
        if re.match(r'\S+\.service', stripped) and 'failed' in line.lower():
            failed_lines.append(stripped.split()[0])

    if not failed_lines:
        # Fallback: any line starting with a service name
        for line in out.split('\n'):
            if re.match(r'\s*[●\s]*\S+\.service', line):
                name = line.strip().lstrip('●').strip().split()[0]
                if name.endswith('.service'):
                    failed_lines.append(name)

    count = len(failed_lines) if failed_lines else 1
    services = ', '.join(failed_lines[:5])
    findings.append(_finding('critical', 'services',
        f'{count} failed service(s)',
        f'Failed: {services}' if services else 'Check systemd for failed units.',
        'show_failed_services', 'Show details'))

    return findings


# ── Journal ──

def _analyze_journal(result):
    findings = []
    out = _out(result)

    # Parse journal size — multiple output formats:
    # "Archived and active journals take up 2.3G."
    # "Journals take up: 2.3 GB"
    # "Journal size: 2.3G"
    size_str = None
    for pattern in [
        r'(?:Archived and active journals? take up|Journals? take up[:\s]+|Journal size[:\s]+)([\d.]+\s*[GMKgmk][Bi]?)',
        r'take up ([\d.]+\s*[GMKgmk][Bi]?)',
    ]:
        m = re.search(pattern, out, re.IGNORECASE)
        if m:
            size_str = m.group(1).strip()
            break

    if size_str:
        size_gb = _parse_size_gb(size_str)
        if size_gb > 2:
            findings.append(_finding('warning', 'disk', f'Journal logs using {size_str}',
                'Journal is large. Consider vacuuming to reclaim space.',
                'fix_journal_vacuum', 'Vacuum to 500MB'))
        elif size_gb > 1:
            findings.append(_finding('info', 'disk', f'Journal logs using {size_str}',
                'Moderate size. Vacuum if disk space is tight.',
                'fix_journal_vacuum', 'Vacuum to 500MB'))

    # /var/log total — "du -sh /var/log" output or "Log directory: 5.2G"
    for pattern in [
        r'([\d.]+\s*[GMKgmk][Bi]?)\s+/var/log',
        r'[Ll]og\s+(?:directory|total)[:\s]+([\d.]+\s*[GMKgmk][Bi]?)',
    ]:
        m = re.search(pattern, out)
        if m:
            log_size = m.group(1).strip()
            size_gb = _parse_size_gb(log_size)
            if size_gb > 5:
                findings.append(_finding('warning', 'disk', f'/var/log is {log_size}',
                    'Log directory is large. Check for runaway logs.',
                    None, None))
            break

    return findings


# ── Open Ports ──

def _analyze_ports(result):
    findings = []
    out = _out(result)

    # Count listening TCP ports — handles ss/netstat output with section markers
    tcp_lines = []
    in_tcp = False
    for line in out.split('\n'):
        if re.search(r'---\s*TCP\s*---', line, re.IGNORECASE):
            in_tcp = True
            continue
        if re.search(r'---\s*UDP\s*---', line, re.IGNORECASE):
            in_tcp = False
            continue
        if in_tcp and line.strip() and not re.match(r'^(?:State|Netid|Proto)', line):
            tcp_lines.append(line)

    if not tcp_lines:
        # Fallback: no section markers — count LISTEN lines directly
        tcp_lines = [l for l in out.split('\n')
                     if 'LISTEN' in l and not re.match(r'^(?:State|Netid|Proto)', l.strip())]

    if len(tcp_lines) > 10:
        findings.append(_finding('warning', 'security', f'{len(tcp_lines)} TCP ports listening',
            'High number of listening ports. Review for unnecessary services.',
            'show_open_ports', 'Show port details'))
    elif len(tcp_lines) > 0:
        findings.append(_finding('info', 'security', f'{len(tcp_lines)} TCP ports listening',
            'Port count is reasonable.',
            'show_open_ports', 'Show port details'))

    return findings


# ── Updates ──

def _analyze_updates(result):
    findings = []
    out = _out(result)

    # Package count — multiple formats:
    # "Upgradable: 12 packages", "12 packages can be upgraded", "12 upgradable"
    count = None
    for pattern in [
        r'Upgradable[:\s]+(\d+)\s*packages?',
        r'(\d+)\s+packages?\s+(?:can be|to be)\s+upgraded',
        r'(\d+)\s+upgradable',
        r'(\d+)\s+update[s]?\s+(?:available|to install)',
    ]:
        m = re.search(pattern, out, re.IGNORECASE)
        if m:
            count = int(m.group(1))
            break

    if count is not None:
        if count > 50:
            findings.append(_finding('critical', 'updates', f'{count} packages need updating',
                'System is significantly behind on updates.',
                'fix_apt_update', 'Run apt upgrade'))
        elif count > 20:
            findings.append(_finding('warning', 'updates', f'{count} packages need updating',
                'Schedule an update soon.',
                'fix_apt_update', 'Run apt upgrade'))
        elif count > 0:
            findings.append(_finding('info', 'updates', f'{count} packages can be updated',
                'Minor updates available.',
                'fix_apt_update', 'Run apt upgrade'))
        else:
            findings.append(_finding('info', 'updates', 'System is up to date',
                'All packages are current.', None, None))

    # Security updates specifically
    sec_m = re.search(r'(\d+)\s+security\s+update[s]?', out, re.IGNORECASE)
    if sec_m:
        sec_count = int(sec_m.group(1))
        if sec_count > 0:
            findings.append(_finding('warning', 'updates', f'{sec_count} security update(s) pending',
                'Security patches should be applied promptly.',
                'fix_apt_update', 'Run apt upgrade'))

    # Unattended-upgrades
    if re.search(r'not\s+installed', out, re.IGNORECASE) and 'unattended' in out.lower():
        findings.append(_finding('warning', 'updates', 'Unattended-upgrades not installed',
            'Security patches won\'t auto-apply.',
            'fix_install_unattended', 'Install unattended-upgrades'))

    return findings


# ── Orphan Packages ──

def _analyze_orphans(result):
    findings = []
    out = _out(result)

    # Find all "Count: N" occurrences in order
    counts = re.findall(r'[Cc]ount[:\s]+(\d+)', out)

    if len(counts) >= 1:
        count = int(counts[0])
        if count > 10:
            findings.append(_finding('warning', 'cleanup', f'{count} orphaned packages',
                'Unused dependencies taking disk space.',
                'fix_apt_autoremove', 'Run apt autoremove'))
        elif count > 0:
            findings.append(_finding('info', 'cleanup', f'{count} orphaned packages',
                'Minor cleanup available.',
                'fix_apt_autoremove', 'Run apt autoremove'))

    # Residual configs
    if len(counts) >= 2:
        rc_count = int(counts[1])
        if rc_count > 5:
            findings.append(_finding('info', 'cleanup', f'{rc_count} residual config files',
                'Leftover configs from removed packages.',
                'fix_purge_configs', 'Purge residual configs'))

    # APT cache — multiple size formats
    for pattern in [
        r'([\d.]+\s*[GMKgmk][Bi]?)\s+/var/cache/apt',
        r'[Aa][Pp][Tt]\s+cache[:\s]+([\d.]+\s*[GMKgmk][Bi]?)',
    ]:
        m = re.search(pattern, out)
        if m:
            size = m.group(1).strip()
            if _parse_size_gb(size) > 1:
                findings.append(_finding('info', 'cleanup', f'APT cache is {size}',
                    'Cached package files can be cleaned.',
                    'fix_apt_autoclean', 'Run apt autoclean'))
            break

    return findings


# ── Firewall ──

def _analyze_firewall(result):
    findings = []
    out = _out(result)
    out_lower = out.lower()

    # UFW
    if 'ufw' in out_lower:
        if re.search(r'\binactive\b', out_lower):
            findings.append(_finding('warning', 'security', 'Firewall (UFW) is inactive',
                'System has no active firewall. Consider enabling UFW.',
                'fix_enable_ufw', 'Enable UFW with defaults'))
        elif re.search(r'\bactive\b', out_lower):
            findings.append(_finding('info', 'security', 'Firewall is active',
                'UFW is running.', None, None))
    # nftables / iptables fallback
    elif re.search(r'not\s+installed|not\s+found|command\s+not\s+found', out_lower):
        findings.append(_finding('warning', 'security', 'No firewall detected',
            'Consider installing UFW.',
            'fix_install_ufw', 'Install UFW'))
    elif re.search(r'nf_tables|iptables', out_lower):
        findings.append(_finding('info', 'security', 'Firewall active (iptables/nftables)',
            'Non-UFW firewall is present.', None, None))

    return findings


# ── SSH ──

def _analyze_ssh(result):
    findings = []
    out = _out(result)

    # Count key fingerprints — multiple label formats
    key_count = len(re.findall(r'[Ff]ingerprint[:\s]', out))
    if key_count == 0:
        # Alternative: count "BEGIN ... PRIVATE KEY" or key file paths
        key_count = len(re.findall(r'-----BEGIN\s+\S+\s+PRIVATE KEY-----', out))
    if key_count == 0:
        key_count = len(re.findall(r'(?:id_rsa|id_ed25519|id_ecdsa|id_dsa)(?:\.pub)?', out))

    if key_count > 0:
        findings.append(_finding('info', 'security', f'{key_count} SSH key pair(s) found',
            'SSH keys are present.', None, None))
    else:
        findings.append(_finding('info', 'security', 'No SSH keys found',
            'No SSH keys detected. Generate one if needed: ssh-keygen -t ed25519',
            None, None))

    # Authorized keys
    m = re.search(r'(\d+)\s+authorized\s+key[s]?', out, re.IGNORECASE)
    if m:
        count = int(m.group(1))
        if count > 5:
            findings.append(_finding('warning', 'security', f'{count} authorized SSH keys',
                'High number of authorized keys. Audit for stale entries.',
                'show_ssh_keys', 'Show key details'))

    # Known hosts
    m = re.search(r'(\d+)\s+known\s+host[s]?', out, re.IGNORECASE)
    if m:
        count = int(m.group(1))
        if count > 100:
            findings.append(_finding('info', 'security', f'{count} known hosts entries',
                'Consider pruning stale known_hosts entries.',
                None, None))

    return findings


# ── Boot Analysis ──

def _analyze_boot(result):
    findings = []
    out = _out(result)

    # Detect whether this is a server or desktop — check for display server / graphical target
    is_desktop = bool(re.search(
        r'graphical\.target|display-manager|gdm|sddm|lightdm|x11|wayland|gnome|kde|xfce',
        out, re.IGNORECASE
    ))

    # Total boot time — systemd-analyze output:
    # "Startup finished in 3.141s (kernel) + 12.012s (userspace) = 15.153s"
    # "= 45.2s"
    m = re.search(r'=\s*([\d.]+)s', out)
    if not m:
        # "Total: 45.2s" or "Boot time: 45.2 seconds"
        m = re.search(r'(?:[Tt]otal|[Bb]oot\s+time)[:\s]+([\d.]+)\s*s', out)

    if m:
        total = float(m.group(1))
        if total > 60:
            findings.append(_finding('warning', 'performance', f'Boot time is {total:.0f}s',
                'Slow boot. Check for problematic services.',
                'show_boot_blame', 'Show slowest services'))
        elif total > 30:
            # Only warn on desktops — servers rarely reboot; 30s is fine
            if is_desktop:
                findings.append(_finding('warning', 'performance', f'Boot time is {total:.0f}s',
                    'Moderate boot time for a desktop. Check for slow services.',
                    'show_boot_blame', 'Show slowest services'))
            else:
                findings.append(_finding('info', 'performance', f'Boot time is {total:.0f}s',
                    'Acceptable boot time for a server.',
                    'show_boot_blame', 'Show slowest services'))

    return findings


# ── SMART ──

def _analyze_smart(result):
    findings = []
    out = _out(result)

    # Overall health — "SMART overall-health self-assessment test result: PASSED"
    if re.search(r'\bPASSED\b', out):
        findings.append(_finding('info', 'hardware', 'SMART health: PASSED',
            'Drive reports healthy.', None, None))
    elif re.search(r'\bFAILED\b', out):
        findings.append(_finding('critical', 'hardware', 'SMART health: FAILED',
            'Drive may be failing. Back up data immediately!',
            None, None))

    # Reallocated sectors — attribute 5
    m = re.search(r'Reallocated[_\s][Ss]ector[s]?.*?(\d+)\s*$', out, re.MULTILINE)
    if m and int(m.group(1)) > 0:
        findings.append(_finding('warning', 'hardware', 'Reallocated sectors detected',
            f'{m.group(1)} reallocated sectors. Monitor closely.',
            None, None))

    # Pending sectors — attribute 197
    m = re.search(r'Current_Pending_Sector.*?(\d+)\s*$', out, re.MULTILINE)
    if m and int(m.group(1)) > 0:
        findings.append(_finding('warning', 'hardware', 'Pending sectors detected',
            f'{m.group(1)} pending sectors — potential bad blocks.',
            None, None))

    if re.search(r'not\s+installed|not\s+found|command\s+not\s+found', out, re.IGNORECASE):
        findings.append(_finding('info', 'hardware', 'smartmontools not installed',
            'Install to monitor drive health.',
            'fix_install_smartmontools', 'Install smartmontools'))

    return findings


# ── Cron ──

def _analyze_cron(result):
    """Analyze cron_inventory output for useful findings."""
    findings = []
    out = _out(result)

    if not out.strip():
        return findings

    # Count total cron jobs across all users/locations
    # Typical script output lists jobs one per line or in sections
    job_lines = []
    for line in out.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # Cron job lines usually contain timing fields (5 fields before command)
        # e.g. "0 2 * * * /path/to/script.sh"
        # or labeled: "[root] 0 2 * * * /path/to/script.sh"
        m = re.search(
            r'(?:\S+\s+)?'           # optional user label
            r'([@\*\d/,\-]+\s+){4,5}'  # timing fields (at least 4)
            r'(.+)',                  # command
            line
        )
        if m:
            job_lines.append(line)

    # Check for cron jobs pointing to missing/non-existent scripts
    missing_scripts = []
    for line in job_lines:
        # Extract command — everything after timing fields
        cmd_m = re.search(
            r'(?:[@\*\d/,\-]+\s+){4,5}(.+)',
            line
        )
        if not cmd_m:
            continue
        command = cmd_m.group(1).strip()
        # Extract the first token of the command as the script path
        script = command.split()[0] if command.split() else ''
        # Only check absolute paths to scripts (skip built-ins, env, etc.)
        if script.startswith('/') and not os.path.exists(script):
            missing_scripts.append(script)

    if missing_scripts:
        unique_missing = list(dict.fromkeys(missing_scripts))  # deduplicate, preserve order
        count = len(unique_missing)
        sample = ', '.join(unique_missing[:3])
        findings.append(_finding('warning', 'cron', f'{count} cron job(s) point to missing scripts',
            f'Scripts not found: {sample}{"..." if count > 3 else ""}. Broken crons silently fail.',
            None, None))

    # Report total cron jobs as info
    total = len(job_lines)
    if total > 0:
        findings.append(_finding('info', 'cron', f'{total} cron job(s) scheduled',
            'Review periodically for stale or redundant jobs.',
            'show_cron', 'Show cron inventory'))
    else:
        # No jobs found — maybe output format not parsed, just note it
        if out.strip() and 'no cron' not in out.lower():
            findings.append(_finding('info', 'cron', 'Cron inventory available',
                'Could not parse individual jobs. Review output manually.',
                'show_cron', 'Show cron inventory'))

    return findings


# ── Shared helpers ──

def _append_disk_finding(findings: list, pct: int, mount: str, avail_gb: float = 0):
    """Add a disk finding, applying context-aware thresholds to reduce false positives.

    Context rules:
    - If >= 100 GB is still free, downgrade: 95%+ -> warning (not critical), 80%+ -> info
    - Critical only when disk is genuinely at risk (< ~10-20 GB free or > 95% on small disk)
    """
    # Absolute free space context
    lots_of_space = avail_gb >= 100  # 100 GB free is not urgent regardless of %

    if pct > 95:
        severity = 'warning' if lots_of_space else 'critical'
        detail = (f'{mount} is {pct}% full ({avail_gb:.0f}G free). '
                  + ('Large disk — no immediate action needed.' if lots_of_space
                     else 'Free space urgently.'))
        findings.append(_finding(severity, 'disk', f'Disk {mount} nearly full ({pct}%)',
            detail, 'fix_disk_cleanup', f'Run cleanup for {mount}'))
    elif pct > 80:
        severity = 'info' if lots_of_space else 'warning'
        detail = (f'{mount} is {pct}% full ({avail_gb:.0f}G free). '
                  + ('Plenty of absolute space remaining.' if lots_of_space
                     else 'Plan cleanup soon.'))
        findings.append(_finding(severity, 'disk', f'Disk {mount} getting full ({pct}%)',
            detail, 'fix_disk_cleanup', f'Run cleanup for {mount}'))


def _extract_section(text: str, keyword: str, end_markers: list[str] = None) -> str:
    """Extract a named section from script output text."""
    lines = text.split('\n')
    in_section = False
    section_lines = []
    for line in lines:
        if keyword.lower() in line.lower():
            in_section = True
        elif in_section:
            if end_markers and any(m in line for m in end_markers):
                break
            section_lines.append(line)
    return '\n'.join(section_lines)


def _finding(severity, category, title, detail, action_id=None, action_label=None):
    f = {
        'severity': severity,
        'category': category,
        'title': title,
        'detail': detail,
    }
    if action_id:
        f['action_id'] = action_id
        f['action_label'] = action_label
    return f


def _parse_size_gb(s):
    """Parse a human size string like '2.3G', '500M', '1.5 GB', '512 MiB' into GB."""
    if not s:
        return 0
    s = s.strip().upper()
    # Handle IEC units: GiB, MiB, KiB
    m = re.match(r'([\d.]+)\s*([GMKTP])(?:I?B)?', s)
    if not m:
        return 0
    val = float(m.group(1))
    unit = m.group(2)
    multipliers = {'T': 1024, 'G': 1, 'M': 1 / 1024, 'K': 1 / (1024 * 1024), 'P': 1024 * 1024}
    return val * multipliers.get(unit, 1)
