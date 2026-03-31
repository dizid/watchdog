# Watchdog — Dev Notes

Lightweight system health dashboard for developers who don't want to be sysadmins.

## Current State

- 13 hardened bash scripts across 5 categories (monitoring, disk, security, cleanup, inventory)
- Flask backend with analyzer engine (severity-rated findings)
- Overview page with health score, one-click fixes, localStorage caching
- Individual checks page for raw script output
- Install script with optional systemd user service
- All scripts gracefully handle missing tools, timeouts, and empty results

## Project Structure

```
dashboard/server.py      — Flask API + routes
dashboard/analyzer.py    — Findings engine (parses script output → actionable findings)
dashboard/templates/     — overview.html (landing), index.html (checks)
scripts/                 — 13 bash check scripts
docs/                    — strategic brief, market analysis
install.sh               — one-command setup
start.sh                 — launch script
```

## Running

```bash
./start.sh               # starts on http://127.0.0.1:5111
```

## Roadmap

See `docs/strategic-brief.md` for full commercialization plan.

1. **Done** — Core dashboard, analyzer, hardened scripts, install script, README
2. **Next** — GitHub publish, Show HN launch
3. **If traction** — Pro tier (scheduled scans, notifications, multi-machine)
4. **Later** — AI layer (Claude-powered log analysis, pattern learning)
