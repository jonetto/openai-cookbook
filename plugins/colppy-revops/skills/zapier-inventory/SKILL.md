---
name: zapier-inventory
description: Query the Zapier automation inventory — active Zaps, app connections, data flow architecture, error status, and cleanup recommendations. Use when asked about Zapier integrations, what automations are running, which Zaps connect HubSpot/Mixpanel/Intercom/Slack, or when auditing the automation stack.
---

# Zapier Automation Inventory

Review and query the live inventory of Zapier automations powering Colppy's RevOps data pipelines.

---

## Data Sources

| File | Contents | Updated |
|------|----------|---------|
| `data/zapier/active_zaps_inventory.md` | 21 active (ON) Zaps with categories, owners, apps, data flow diagram | 2026-03-10 |
| `data/zapier/connections_audit.md` | 166 app connections, health status, cleanup recommendations | 2026-03-10 |
| `data/zapier/zapier-zaps-table.png` | Screenshot of full Zaps table (168 total) | 2026-03-10 |
| `data/zapier/zapier-connections.png` | Screenshot of connections page | 2026-03-10 |

All paths are relative to `plugins/colppy-revops/`.

## How to Answer Queries

### "What Zaps are running?" / "What automations do we have?"
Read `data/zapier/active_zaps_inventory.md` and present the summary table and category breakdown.

### "What connects HubSpot to Mixpanel?" / "How does data flow between X and Y?"
Read the inventory file and use the **Data Flow Architecture** diagram and the categorized Zap tables to trace the path. Key flows:
- **HubSpot → Mixpanel**: 7 Zaps via webhooks (lifecycle stage changes, lead events, qualifications)
- **Mixpanel → GSheet → HubSpot**: 5 scheduled cohort imports + 3 property updaters (with delay steps)
- **Intercom → Mixpanel**: 2 Zaps (series events, generic event tracking)
- **Intercom → HubSpot**: 1 Zap (multi-path routing based on Intercom flow)

### "Are there any errors?" / "What's broken?"
Check the **Errors Detected** section in the inventory. As of 2026-03-10:
- Zap 332991791 "Genera evento de nuevo lead desde WF Hubspot a Mixpanel Sueldos" — **Errored**

### "What connections need fixing?" / "Clean up Zapier"
Read `data/zapier/connections_audit.md` for:
- Broken connections needing reconnection
- Former employee connections safe to delete
- Connections with 0 Zaps (candidates for removal)

### "Who owns what?"
- **Juan Onetto**: 19 of 21 active Zaps
- **Daniel Sucre**: 1 active Zap (GMB → Slack notifications)
- **Pamela Viarengo**: 1 Zap (Track generico from Intercom — listed under Juan but Pamela visible in some views)

## Account Overview

| Metric | Value |
|--------|-------|
| Plan | Free (recently canceled Team plan) |
| Plan Tasks | 2.2k / 20k used |
| Total Zaps | 168 |
| Active (ON) | 21 |
| Off / Draft | 147 |
| App Connections | 166 |
| Broken Connections (page 1) | 15+ |
| MCP Servers | 2 (Claude, Claude Code) — no tools configured |

## Staleness Warning

This inventory is a **point-in-time snapshot** from 2026-03-10. If the user asks about current state and it's been more than 2 weeks, recommend re-running the Playwright scraper to refresh:

> "The Zapier inventory was last scraped on 2026-03-10. Would you like me to refresh it via the browser?"

To refresh: navigate Playwright to `zapier.com/app/assets/zaps?status=on`, extract the table, and update `data/zapier/active_zaps_inventory.md`.
