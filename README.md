# Watchdog

Lightweight system health dashboard for developers who don't want to be sysadmins.

Watchdog runs 13 system checks, analyzes the results, and tells you exactly what needs fixing — with one-click actions to fix it. No metrics to configure, no dashboards to build, no agents to deploy. Just answers.

## Quick Start

```bash
git clone https://github.com/yourusername/watchdog.git
cd watchdog
./install.sh
./start.sh
```

Open **http://127.0.0.1:5111** — Watchdog auto-scans on first visit.

## What It Checks

| Category | Checks |
|----------|--------|
| **Monitoring** | System info, failed systemd services, boot time analysis |
| **Disk** | Usage audit, large/old files, journal log size, SMART health |
| **Security** | Open ports, SSH key inventory, firewall status, available updates |
| **Cleanup** | Orphaned packages, old kernels, snap revisions, APT cache |
| **Inventory** | Package list export, cron job inventory |

## How It Works

1. **Scan** — Runs all checks (~30-60 seconds)
2. **Analyze** — Parses output into findings with severity levels (critical / warning / info)
3. **Act** — Each finding with a fix shows an action button. Click it, see the exact command, confirm, done.
4. **Cache** — Results are cached locally. Reopen the page and your last scan is right there.

### Human-in-the-Loop

Every fix action shows a confirmation modal with the exact command before running. Destructive operations are dry-run only — they show what would be cleaned but don't delete anything.

## Pages

- **/** — Overview with analyzed findings, health score, and one-click fixes
- **/checks** — Raw output from each individual check script

## Requirements

- Python 3.8+
- Linux (tested on Ubuntu 22.04/24.04)
- No Node.js, no Docker, no cloud account

Some checks may need `sudo` for full results (SMART, firewall). They degrade gracefully without it.

## Configuration

| Env var | Default | Description |
|---------|---------|-------------|
| `WATCHDOG_PORT` | `5111` | Dashboard port |
| `WATCHDOG_DOCS_DIR` | `./docs` | Where package lists get exported |

## Project Structure

```
watchdog/
├── dashboard/
│   ├── server.py          # Flask API + routes
│   ├── analyzer.py        # Findings engine
│   └── templates/
│       ├── overview.html   # Main overview page
│       └── index.html      # Individual checks page
├── scripts/                # 13 bash check scripts
├── install.sh              # One-command installer
├── start.sh                # Launch script
└── requirements.txt        # Flask
```

## Adding Custom Checks

Drop a `.sh` script in `scripts/`, add an entry to the `TASKS` dict in `dashboard/server.py`, and restart. The script should:

- Start with `#!/usr/bin/env bash` and `set -uo pipefail`
- Use `=== SECTION ===` headers for output
- Check for required tools with `command -v`
- Handle missing tools gracefully

## License

MIT
