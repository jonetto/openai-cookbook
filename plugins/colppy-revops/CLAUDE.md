# Colppy RevOps — Instructions

## Tool Usage Hierarchy

### Use bundled MCP tools — they are already high-level

This plugin bundles two MCP servers (`reconciliation` and `hubspot-analysis`) with pre-built analysis tools. These are the **correct level of abstraction** — use them directly.

| Task | Tool to use |
|------|-------------|
| Monthly Colppy ↔ HubSpot reconciliation | `run_full_refresh` (does refresh + reconciliation in one call) |
| Just run reconciliation (data already fresh) | `run_reconciliation` |
| SMB funnel analysis | `run_smb_mql_funnel` |
| Accountant funnel analysis | `run_accountant_mql_funnel` |
| Scoring / contactability analysis | `run_high_score_analysis` or `run_mtd_scoring` |
| CUIT enrichment (registration date, province, legal type) | `enrich_cuit` (local MCP) or remote API (see below) |
| Company name → CUIT lookup (1.24M+ RNS records) | `search_company_by_name` (local MCP) or remote API (see below) |

### RNS Remote API (works in Cowork / cloud sessions)

When the ARCA MCP server is not available (e.g., in Claude Cowork), use the remote HTTP API:

| Endpoint | URL |
|----------|-----|
| Enrich CUIT | `https://rns-cuit-enrichment.colppy-tools.workers.dev/enrich?cuit=30712461221` |
| Search by name | `https://rns-cuit-enrichment.colppy-tools.workers.dev/search?q=colppy&limit=10` |
| Health / info | `https://rns-cuit-enrichment.colppy-tools.workers.dev/` |

Use `WebFetch` to call these endpoints. The API returns JSON with the same fields as the local MCP tools. Search supports optional `&provincia=Buenos+Aires` filter.

### Do NOT bypass the reconciliation pipeline

- **Do NOT** query HubSpot deals API directly to build reconciliation reports — use `run_reconciliation` which handles the matching logic, CUIT normalization, and edge cases.
- **Do NOT** query the local SQLite DB (`tools/data/facturacion_hubspot.db`) directly with raw SQL — the reconciliation tools handle the correct joins, filters, and grouping.
- **Do NOT** call `refresh_colppy_db` without VPN access — it will fail. Check with the user first.

### Snapshot data for quick reference

Pre-computed JSON snapshots are available in `docs/` for quick reference without running the full pipeline:

- `colppy_hubspot_reconciliation_snapshot.json` — latest reconciliation results
- `colppy_cuit_snapshot.json` — CUIT-to-company mapping
- `colppy_first_payments_snapshot.json` — first payment dates
- `colppy_facturacion_snapshot.json` — facturacion data

Use snapshots for answering quick questions. Run the full pipeline only when the user needs fresh data or a new month's analysis.

## Data Pipeline Order

When running a full reconciliation for a new month:

1. `refresh_colppy_db` — sync from MySQL (requires VPN)
2. `refresh_hubspot_deals` — sync closed-won deals from HubSpot
3. `populate_deal_associations` — link deals to companies
4. `run_reconciliation` — match and produce report

Or simply: `run_full_refresh` which runs all 4 steps.

## Local DB Freshness Protocol

Before querying `tools/data/facturacion_hubspot.db` for analysis, check freshness and coverage:

### Step 1: Check refresh timestamps

```sql
-- Last deals/companies refresh
SELECT timestamp, period, source_metadata FROM hubspot_refresh_logs ORDER BY id DESC LIMIT 1;
-- Last associations refresh
SELECT timestamp FROM hubspot_deal_associations_refresh_logs ORDER BY id DESC LIMIT 1;
```

### Step 2: Decide refresh vs live API

| Condition | Action |
|-----------|--------|
| Query period ≤ last refresh date | Use local DB |
| Query period > last refresh date | Use HubSpot MCP tools directly |
| Associations refresh > 24h old and query needs Type 8 data | Run `populate_deal_associations` first, or use HubSpot MCP |

### Step 3: Coverage gaps — companies table

The `companies` table only contains CUIT-matched companies (imported via `build_facturacion_hubspot_mapping.py`). Accountant companies that are only associated to deals (never billed) may be missing.

When joining `deal_associations` to `companies`:

- Always use `LEFT JOIN`
- If any rows return NULL company name → fetch those company IDs from HubSpot MCP (`get_crm_objects`) in a single batch call
- Do NOT present results with missing names — resolve them first

## Zapier Automation Inventory

Pre-scraped inventory of the Zapier account powering Colppy's data pipelines:

- `data/zapier/active_zaps_inventory.md` — 21 active Zaps, categorized by function (event tracking, cohort imports, property updates)
- `data/zapier/connections_audit.md` — 166 app connections with health status and cleanup recommendations

Key facts: 168 total Zaps, 21 ON, plan at 2.2k/20k tasks. Most Zaps bridge HubSpot ↔ Mixpanel ↔ Intercom via webhooks and scheduled cohort exports. Use the `zapier-inventory` skill for queries.

## Sales Team Structure (from 2026-03-13)

The commercial team operates with 3 people in a pipeline model:

| Role | Focus | How it feeds the pipeline |
|------|-------|--------------------------|
| **1 Fidelización** (Customer team) | Accountant segmentation, relationship management | Generates qualified opportunities for closers |
| **2 Closers** | Score 40+ leads, commercial interventions | Close deals from scoring pipeline + Fidelización pipeline |

**RevOps monitoring responsibilities (Francisca):**

- Ensure score 40+ leads are being attended by closers (not left untouched)
- Track SQL cycle time and conversion rates for the sales-touched path
- Flag capacity gaps: if high-score leads accumulate without owner assignment

**Two-path split for all funnel reports:**

- **Sales-touched**: `fit_score_contador >= 40` AND `hubspot_owner_id` populated
- **No-touch (PLG)**: `fit_score_contador < 40` OR `hubspot_owner_id` empty → product must convert these

When running `run_high_score_analysis` or `run_mtd_scoring`, contextualize results against this structure — unengaged high-score contacts are now a direct capacity problem for just 2 closers.

## Supabase Publish Layer (shared read layer)

Pipeline results are published to Supabase for cross-agent access. Query these for quick answers instead of re-running full pipelines:

| Table | What it has | Query example |
|-------|-------------|---------------|
| `kpi_values` | Building Blocks (Budget/Forecast/Real × 7 tabs) | `?tab_id=eq.colppy_budget_first&section=eq.real` |
| `mtd_summary` | MTD billing from Colppy DB (new MRR by ICP × product, active clients, churn, payments) | `?month=eq.Mar-2026` |
| `reconciliation_summary` | Colppy ↔ HubSpot match results by category | `?year=eq.2026&month=eq.3` |
| `icp_dashboard` | Aggregated metrics by ICP type | `?month=eq.Mar-2026&icp_type=eq.Cuenta Pyme` |

**Access**: REST API with anon key (read-only). Credentials in `tools/.env`.

**Publishing**: After running reconciliation or billing analysis, publish results:

```bash
python3 tools/scripts/publish_to_supabase.py --mtd --month YYYY-MM
```

The `cos-numbers` command runs this automatically. Other agents can publish after their pipeline runs complete.

## Output Rules

- Present reconciliation results in the chat with markdown tables
- Always include match rates and unmatched items
- Group unmatched items by reason (missing CUIT, amount mismatch, etc.)
