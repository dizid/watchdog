# Strategic Brief: System Management Tool Commercialization

**Date:** 2026-03-30
**Status:** Research complete, decision needed

---

## The Opportunity

You built a tool to avoid sysadmin work. So does every other indie dev.

**The gap nobody owns:** AI-analyzed system health with plain-English findings and one-click fixes. Cockpit/Webmin give you panels and knobs. Netdata/Grafana give you graphs. Nobody gives you "here's what's wrong, here's the fix, click to run it."

**Target user:** Solo developer or small team (1-10) running Linux machines who says "I hate dealing with disk space and failed services" — not ops engineers.

### Competitor Landscape

| Tool | What it does | Price | What it lacks |
|------|-------------|-------|---------------|
| Cockpit | Full server admin GUI | Free | No AI, no "what should I fix" |
| Webmin | Everything-admin, legacy UI | Free | UI from 2003, overwhelming |
| Netdata | Real-time metrics | Free + $15/mo cloud | Metrics only, no fixes |
| Grafana | Observability platform | Free + cloud | Overkill for solo devs |
| btop/htop | Terminal TUI | Free | No web UI, no automation |
| **This tool** | AI findings + one-click fixes | ? | This position is unoccupied |

---

## Recommended Name: **Watchdog**

- Instantly communicates "it monitors so you don't have to"
- Resonates in dev culture (watchdog timer, watchdog process)
- Domain options: `usewatchdog.dev`, `watchdog.sh`, `getwatchdog.dev`
- Positioning: *"Watchdog runs your sysadmin checks and tells you exactly what to fix."*

---

## Product Tiers

### Free / Open Source (MIT license on GitHub)
- All bash scripts + Flask dashboard
- Overview page with AI analyzer
- One-click fixes with confirmation modal
- localStorage caching
- Self-hosted, runs on localhost

*Why free:* Builds trust, drives GitHub stars, removes adoption barriers. Cockpit/Webmin are free — you match the floor.

### Pro ($7/month or $59/year)
- Scheduled scans with email digest (weekly health report)
- Slack/Discord notifications on critical findings
- Historical data + trend graphs (disk over 30 days, etc.)
- Multi-machine support (lightweight agent per host)
- AI fix explanations (LLM-generated "why" for each finding)
- Custom fix scripts

### Team ($29/month, up to 5 seats)
- Everything in Pro
- Shared dashboard with role-based access
- Alert routing (disk alerts -> person A, security -> person B)
- Full audit log (who ran what, when)
- Webhook output

---

## Technical Architecture (Phased)

### Phase 1 — MVP (what we have + polish)
**Cost: $0 | Timeline: 1-2 weeks**
- Current Flask dashboard + scripts (already working)
- Convert to Vue 3 + Tailwind CSS 4 frontend (Dizid standard stack)
- Proper README + screenshots
- Publish to GitHub

### Phase 2 — Scheduled Scans + Notifications
**Cost: $0 | Timeline: 2 weeks**
- Cron-based scanner daemon (`scanner.py`)
- SQLite audit log (append-only)
- Auto-remediation for safe actions (apt autoremove, journal vacuum)
- Escalation via email for dangerous actions
- Risk classification config (`auto_approve` / `escalate` / `never_touch`)

### Phase 3 — Multi-Machine
**Cost: ~$5/mo | Timeline: 1 month**
- Pull-based agents (not SSH push — eliminates central key store risk)
- systemd service on each node, dedicated `sysmgt` user
- mTLS transport (certificate-based auth, revoke cert = decommission node)
- Central API (FastAPI) + Postgres (Neon free tier)
- Explicit sudoers whitelist per command — agent can't run arbitrary sudo

### Phase 4 — AI Layer
**Cost: ~$5-10/mo at moderate usage | Timeline: 1 month**
- Claude Sonnet for log analysis + root cause (structured output via tool_use)
- Claude Haiku for weekly pattern summaries (10x cheaper)
- Pattern learning: frequency table of approval history, not ML
- Remediation script generation (always escalated, never auto-executed)
- Estimated: ~$0.20/day at 10 nodes, 20 findings/day

### Security Model
- Generated scripts NEVER auto-execute — always human-approved
- Audit log is append-only (DB trigger prevents UPDATE/DELETE)
- Pull architecture eliminates central SSH key store
- Each node's sudoers whitelist is explicit per-command
- LLM output never directly executed — staged -> reviewed -> run

---

## Go-to-Market (90 days, <$50 total spend)

### Week 1-2: Polish + Publish
- Vue 3 + Tailwind 4 frontend rebuild
- Memorable README with screenshot/GIF
- GitHub publish under Watchdog brand

### Week 3: Launch
- **Show HN** post (Tuesday/Wednesday, 8-10am ET)
  - Framing: "I built an AI sysadmin because I kept forgetting to check my servers"
  - Respond to every comment within 30 min
  - Expected: 300-1,000 GitHub stars in 24 hours
- **Reddit**: r/selfhosted, r/linuxadmin, r/homelab
- **Dev.to**: Technical post with real code

### Week 4: Amplify
- **Product Hunt** launch (not same day as HN)
- **Twitter/X build-in-public** thread (weekly cadence)
  - The "solo dev + 18 AI agents building an AI sysadmin tool" meta-story is genuinely compelling

### Week 6: Monetize
- Pro waitlist on README + dashboard
- Email starred users: "Founding member price: $49/year (40% off forever)"
- **Target: 10 paying customers before building Pro infrastructure**
- Payment: Lemon Squeezy (handles EU VAT as merchant of record)

### Week 12+: Scale
- Pro backend live
- Content SEO starts compounding (target long-tail: "linux disk audit script", "automate apt upgrade safe way", "systemd journal too large")
- At $500 MRR, allocate $100/mo to Google Ads on long-tail terms

### Revenue Projections (conservative)
- Month 3: 10 paying users = ~$70/mo MRR
- Month 6: 50 paying users = ~$350/mo MRR
- Month 12: 150 paying users = ~$1,200 MRR ($14,400 ARR)
- Essentially passive income alongside Dizid client work

---

## Build-in-Public Angle

The meta-story sells itself: **"18 AI agents building an AI sysadmin tool, run by one person."**

Weekly cadence:
- Monday: Share a real Watchdog finding from your own machine
- Wednesday: Share a build update (which agent did what)
- Friday: Share a metric (stars, forks, signups, MRR)

This is 30 min/week and differentiates from every other indie hacker building SaaS.

---

## Decision Needed

**Option A: Keep it personal** — Continue as a local utility for your own machine. No brand, no launch. Just a useful tool.

**Option B: Open-source launch** — Rebrand, polish, GitHub publish, Show HN. See if it gets traction. Zero financial risk, just time. If it flops, you still have a useful tool.

**Option C: Full commercial path** — Open-source core + Pro tier. Aim for $1,200 MRR in 12 months. Requires: Vue frontend rebuild, branding, content writing, payment integration. Estimated effort: ~2 weeks for launch-ready, then ongoing 2-4 hours/week for content + support.

**Recommendation: Option B first, then C if traction appears.** Show HN is the litmus test. If 500+ stars in the first week, go commercial. If < 100, keep it as a portfolio piece and personal tool.
