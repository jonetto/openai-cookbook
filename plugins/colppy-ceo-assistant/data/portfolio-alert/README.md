# Portfolio Alert — Cursor Cloud Agent

Daily portfolio intelligence scan: Gmail + web news + earnings → Slack DM to Juan.

## Quick Start

1. **Create the Cursor Automation** — follow [CURSOR_AUTOMATION_SETUP.md](./CURSOR_AUTOMATION_SETUP.md)
2. **Commit and push** — ensure `references/`, `history/`, and `blueprint.md` are in the repo
3. **Run** — automation triggers on schedule (default: 10am ART weekdays)

## Structure

| Path | Purpose |
|------|---------|
| `references/portfolio-snapshot.md` | Current positions, pending orders, allocation |
| `references/index.md` | Last snapshot date, key events |
| `history/transactions.md` | Append-only transaction ledger |
| `history/snapshots/` | Point-in-time snapshots (e.g. tax-year baseline) |
| `alerts/` | Audit logs of sent alerts (YYYY-MM-DD-HH.md) |
| `blueprint.md` | Full workflow for Cursor Cloud Agent |

## Legacy: Claude Cowork Runner

The script `tools/scripts/portfolio-alert-runner.sh` runs via Claude Code CLI + launchd. It is **deprecated** in favor of Cursor Automations. You can keep it as a fallback or remove it.
