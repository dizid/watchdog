# Watchdog

Lightweight system health dashboard for developers who don't want to be sysadmins. Runs checks, surfaces actionable findings, provides one-click fixes with human-in-the-loop confirmation.

## Stack

- **Backend**: Python 3 / Flask
- **Frontend**: Vanilla HTML/CSS/JS (dark glass morphism UI)
- **Scripts**: Bash (13 system check scripts)
- **Target OS**: Linux (Ubuntu 22.04/24.04)
- **No Node.js, no Docker, no cloud dependency**

## Architecture

```
dashboard/
├── server.py          # Flask API + routes (/, /checks, /api/*)
├── analyzer.py        # Parses script output into severity-rated findings
└── templates/
    ├── overview.html   # Landing page — health score, findings, one-click fixes
    └── index.html      # Individual check runner page
scripts/                # 13 bash check scripts (all hardened with graceful fallbacks)
install.sh              # One-command setup (venv + deps + optional systemd service)
start.sh                # Launch script
```

## Routes

- `/` — Overview (main product page, auto-scans on first visit)
- `/checks` — Individual check runner
- `/api/quick-stats` — Live CPU/RAM/disk/uptime
- `/api/tasks` — List all available checks
- `/api/run/<script>` — Run a single check
- `/api/analyze` — Run all checks + return analyzed findings
- `/api/fix/<action>` — Execute a whitelisted fix action
- `/api/fix-info/<action>` — Get fix details for confirmation modal

## Script Conventions

- Shebang: `#!/usr/bin/env bash`
- Use `set -uo pipefail` (not `-e` — optional checks should not kill the script)
- Check tools with `command -v` before use
- Use `timeout` on long-running commands (`find`, `du`)
- Handle empty results explicitly ("No X found")
- Sudo commands: try `sudo -n` first, print "needs sudo" if it fails
- Section headers: `=== SECTION NAME ===`

## Commercialization

Potential open-source + Pro SaaS product. Strategic brief at `docs/strategic-brief.md`.
