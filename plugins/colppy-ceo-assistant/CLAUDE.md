# Colppy CEO Assistant

CEO Assistant for Juan Ignacio Onetto — Chief of Staff agent for planning cadence and KPI tracking, plus daily portfolio alerts.

## Portfolio Alert

The `/portfolio-alert` command runs a fully unattended financial scan:
- Scans Gmail (colppy.com account) for macro/broker signals
- Web searches for market news on held positions
- Compiles an actionable alert and delivers via Slack DM to Juan (UE8BUUVME)
- Writes an audit log to `${CLAUDE_PLUGIN_ROOT}/data/portfolio-alert/alerts/`

**Run it:** `/colppy-ceo-assistant:portfolio-alert`

**Monday update (interactive only):** If you're in the session on Monday, provide Galicia + Schwab + Allaria + Citi screenshots when prompted. The blueprint updates the snapshot and logs any new trades.

## File Map

| File | Purpose |
|------|---------|
| `${CLAUDE_PLUGIN_ROOT}/data/portfolio-alert/references/portfolio-snapshot.md` | Current positions, allocation, Georgette 5% rule |
| `${CLAUDE_PLUGIN_ROOT}/data/portfolio-alert/references/index.md` | History index, key events, file navigation |
| `${CLAUDE_PLUGIN_ROOT}/data/portfolio-alert/history/transactions.md` | Append-only trade ledger |
| `${CLAUDE_PLUGIN_ROOT}/data/portfolio-alert/alerts/` | Audit logs of sent alerts |

## Updating After Monday Screenshots

After updating the snapshot interactively:
1. Run `publish.sh` in the repo at `plugins/colppy-ceo-assistant/`
2. Upload the new ZIP to Cowork to replace this plugin

---

## Chief of Staff

The `chief-of-staff` agent manages planning cadence, KPI tracking, calendar briefings, and leadership team coordination.

### Commands

| Command | What it does |
|---------|-------------|
| `/colppy-ceo-assistant:cos-numbers` | KPI snapshot — Plan vs Real gap analysis from Building Blocks + HubSpot |
| `/colppy-ceo-assistant:cos-pre-work` | Planning session prep — budget, OKRs, people flags, prior actions |
| `/colppy-ceo-assistant:cos-debrief` | Post-meeting extraction — decisions, actions, proposed OKR updates |
| `/colppy-ceo-assistant:cos-status` | Accountability check — per-person action items, OKR progress, flags |
| `/colppy-ceo-assistant:cos-agenda` | Calendar briefing — enriched with people-manager and Fellow context |

### Data Files

| File | Purpose |
|------|---------|
| `${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md` | Current quarter OKR targets + actuals |
| `${CLAUDE_PLUGIN_ROOT}/data/okrs/cache/2026/` | Cached OKR spreadsheet CSVs (14 files, static per quarter) |

### Cross-Plugin Dependencies (read-only)

- **colppy-people-manager:** Reads `data/*/profile.md` and `data/*/summary.md` for team context
- **tools:** Reads `tools/docs/GOOGLE_SHEETS_REGISTRY.json` for Google Sheets tab IDs

### Rules

- **Never write to people-manager** — coaching data is session-processor's domain
- **Never message team members on Slack** — only send to Juan's DM (`UE8BUUVME`)
- **Never auto-update OKRs from transcripts** — always get user confirmation first
