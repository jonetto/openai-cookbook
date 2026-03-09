# Colppy CEO Assistant

Daily financial intelligence for Juan Ignacio Onetto.

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
