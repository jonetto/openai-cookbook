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

## Output Rules

- Present reconciliation results in the chat with markdown tables
- Always include match rates and unmatched items
- Group unmatched items by reason (missing CUIT, amount mismatch, etc.)
