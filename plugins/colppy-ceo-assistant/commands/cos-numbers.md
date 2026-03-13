---
name: cos-numbers
description: "KPI snapshot — fetch Building Blocks data (Budget, Forecast, Real), pull HubSpot actuals, compare Real vs Forecast with Budget as baseline, and output a gap analysis. Use when the user asks 'show me the numbers', 'how are we doing', or 'budget status'."
---

# /cos-numbers — KPI Snapshot

Produce a **Budget vs Forecast vs Real gap analysis** for the quarter in progress. Refreshes KPI data from Google Sheets into Supabase, then queries the `kpi_values` table for all 7 Building Blocks tabs. For the current month (not yet closed in Building Blocks), pulls **Month-to-Date billing** from the Colppy production DB via `colppy_export.db`. Pulls customer counts from HubSpot, compares against OKR targets, and outputs a structured summary with gap flags.

**Key principle:** Compare Real vs Forecast (the latest expectation), show Budget as the original baseline reference.

---

## Data Sources (Supabase `kpi_values` table)

All data is pre-parsed and stored in Supabase. The `tab_id` column identifies the source:

| tab_id | What It Provides | Sections | Key block/line_name values |
|--------|------------------|----------|---------------------------|
| `colppy_budget_first` | Company-level MRR, Clients, Measures | budget, forecast, real | block: clients/mrr/measures; line_name: new_mrr, upsell, eop, etc. |
| `colppy_budget` | MRR by product line × ICP | forecast, real | line_name: "New Product - Administración - ICP Pyme", "Sub-total (+)", etc. |
| `funnel_from_lead_product_icp` | MQL/CQL/deal counts by ICP | forecast, real | line_name: "Lead - Administración - ICP Pyme", "Sub-total (+)", etc. |
| `funnel_lead_product_icp` | Conversion rates (%) | forecast, real | line_name: "Lead - Administración - Pyme según Wizard", etc. |
| `churn_budget_real` | Churn mix (Early/Mid/Late %) | forecast, real | block: churn_mix or pct_of_mrr; line_name: Early, Mid, Late, Total |
| `colppy_raw_actuals` | Gross/Net ASP, CAC, LTV, NRR | real only | line_name: "Gross ASP (New Clients)", "# New Clients", "ars/usd", etc. |
| `colppy_budget_aprobado` | Budget KPIs | budget only | block: kpis_ars, clients, reps, unit_economics_ars_k |

**Primary Revenue source:** `colppy_budget_first` — the only tab with all 3 layers (budget + forecast + real).

**Product drill-down:** `colppy_budget` — Forecast + Real by product line × ICP.

**Unit economics pair:** `colppy_budget_aprobado` (budget) + `colppy_raw_actuals` (real). No forecast available for unit economics yet.

---

## Target Month & Complete-Month Logic

Compute the target month from the current date:

```
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
current_month_index = current_date.month - 1  # 0-based
current_year = current_date.year
```

**Complete-month rule:** Only compare months where Real data exists. Query Supabase to check if the current month has non-null Real values:

```sql
SELECT COUNT(*) FROM kpi_values
WHERE tab_id = 'colppy_budget_first' AND section = 'real'
AND month = '{current_month}' AND value IS NOT NULL
AND snapshot_id = (SELECT MAX(id) FROM snapshots WHERE tab_id = 'colppy_budget_first')
```

If count = 0, the last complete month is `current_month - 1`. Sum only complete months for YTD comparisons. **Then run Step 2.5 to get MTD from Colppy DB for the current (incomplete) month.**

```
Quarter start months: Q1=Jan(0), Q2=Apr(3), Q3=Jul(6), Q4=Oct(9)
quarter_start = (current_month_index // 3) * 3
complete_months = months from quarter_start to last month with Real data
```

For example, on March 13 if March Real is empty: compare Jan+Feb Forecast vs Jan+Feb Real (2 of 3 months). Clearly label output as "2/3 months complete." The MTD section (Step 2.5) provides early visibility into March from actual billing data.

Month format in Supabase is always `MMM-YYYY` (e.g. `Jan-2026`). No format variants — the fetch script normalizes all tabs.

---

## Step 1: Refresh Supabase Data

Run the fetch script to update all 7 Building Blocks tabs:

```bash
python3 tools/scripts/building_blocks/fetch_and_store.py --all --diff
```

This will:
1. Fetch each tab's CSV from Google Sheets
2. Parse using the validated row map (colppy_budget_first) or label-based parser (all others)
3. Store a new snapshot + parsed values in Supabase
4. Detect and log any changes vs the previous snapshot

Review the `--diff` output. If values changed, flag them in the narrative.

---

## Step 2: Query KPI Data from Supabase

Use `psycopg2` to query the latest snapshot for each tab. Connection details are in `tools/.env`.

```python
import psycopg2
conn = psycopg2.connect(
    host='aws-1-us-east-1.pooler.supabase.com', port=5432,
    dbname='postgres', user='postgres.zuqagibvwnjbpdprbptp',
    password=ENV['SUPABASE_PASSWORD'])
```

### Get latest snapshot IDs

```sql
SELECT DISTINCT ON (tab_id) tab_id, id as snapshot_id, fetched_at
FROM snapshots ORDER BY tab_id, id DESC
```

### Revenue data (colppy_budget_first)

```sql
SELECT section, block, line_name, month, value
FROM kpi_values
WHERE tab_id = 'colppy_budget_first'
AND snapshot_id = {latest_snapshot_id}
AND month IN ('Jan-2026', 'Feb-2026')  -- only complete months
ORDER BY section, block, line_name, month
```

Key line_name values for the MRR bridge:
- `new_mrr`, `upsell`, `cross_sell`, `price_increase`, `expired_discounts`
- `subtotal_plus` (total inflow, sin Cross Sell in Real), `lost_mrr`, `downsell`, `retention_discounts`
- `subtotal_minus` (total outflow), `eop` (ending MRR)
- `bop` (beginning of period)

### Product drill-down (colppy_budget)

```sql
SELECT section, line_name, month, value
FROM kpi_values
WHERE tab_id = 'colppy_budget'
AND snapshot_id = {latest_snapshot_id}
AND line_name LIKE 'New Product%%' OR line_name LIKE 'Sub-total%%'
AND month IN ('Jan-2026', 'Feb-2026')
```

### Funnel data

```sql
-- Counts
SELECT section, line_name, month, value FROM kpi_values
WHERE tab_id = 'funnel_from_lead_product_icp' AND snapshot_id = {id}
-- Conversion rates
SELECT section, line_name, month, value FROM kpi_values
WHERE tab_id = 'funnel_lead_product_icp' AND snapshot_id = {id}
```

### Churn detail

```sql
SELECT section, block, line_name, month, value FROM kpi_values
WHERE tab_id = 'churn_budget_real' AND snapshot_id = {id}
```

block = `churn_mix` (raw percentages) or `pct_of_mrr` (as share of total MRR).

### Unit economics (Budget vs Real)

```sql
-- Budget values
SELECT line_name, month, value FROM kpi_values
WHERE tab_id = 'colppy_budget_aprobado' AND snapshot_id = {id}
AND block = 'kpis_ars'
-- Real values
SELECT line_name, month, value FROM kpi_values
WHERE tab_id = 'colppy_raw_actuals' AND snapshot_id = {id}
```

Match by line_name between the two tabs:
- Budget `Net ASP New Client` ↔ Real `Net ASP (New Clients)` (in USD — multiply by `ars/usd`)
- Budget `New Clients (#)` ↔ Real `# New Clients`
- Budget `Net Churn %` ↔ Real `% Net Churn`
- Budget `LTV (DR 15%)` ↔ Real `LTV (r=15%)`

---

## Step 2.5: MTD from Colppy DB (current month only)

**When to run:** Only when the current month is NOT yet closed in Building Blocks (i.e., Step 2 shows no Real data for the current month). This provides Month-to-Date visibility from the actual billing system.

**Prerequisite:** VPN must be ON to refresh Colppy data. If VPN is off, skip this step and note "MTD unavailable (VPN off)."

### 2.5a: Refresh & Publish

Run the publish script which reads `colppy_export.db` and publishes aggregated MTD metrics to Supabase:

```bash
# If VPN is on and data needs refreshing:
python3 tools/scripts/colppy/export_colppy_to_sqlite.py --incremental

# Publish MTD to Supabase (always run this):
python3 tools/scripts/publish_to_supabase.py --mtd --month {YYYY-MM}
```

This calculates 10 metrics from `colppy_export.db` and upserts them into the `mtd_summary` Supabase table:
- `new_mrr_adm_pyme`, `new_mrr_adm_operador`, `new_mrr_sueldos_pyme`, `new_mrr_sueldos_operador`, `new_mrr_total`
- `active_billing_products`, `churned_products`, `payments_collected`, `paying_empresas_mtd`

**Definition of "new product":** A new product = `pago.primerPago=1` in that month. This flag is set by the Colppy backend on the first-ever approved payment for an empresa. Do NOT use `facturacion.fechaAlta` (99.95% are `0000-00-00` — legacy MySQL 5.6 column never populated by the app).

**Products vs Customers:** The MRR bridge tracks **products** (billing subscriptions), not customers (empresas). One empresa can have multiple products (e.g., Administración + Sueldos). Each `pago` row = one product. The `count` field in `mtd_summary` = number of products, not number of empresas.

**Classification rules (applied to each pago with primerPago=1):**

| Dimension | How to determine | Source |
|-----------|-----------------|--------|
| **ICP Pyme** | `facturacion.CUIT == empresa.CUIT` for the same IdEmpresa (self-billed) | empresa + facturacion tables |
| **ICP Operador** | `facturacion.CUIT != empresa.CUIT` (accountant bills on client's behalf) | empresa + facturacion tables |
| **Administración** | `plan.nombre` does NOT contain 'sueldos' (case-insensitive) | plan table |
| **Sueldos** | `plan.nombre` contains 'sueldos' (case-insensitive) — includes "Enterprise + Sueldos", "Pack de sueldos", "Colppy Plus Sueldos", etc. | plan table |

This produces 4 buckets: `new_mrr_adm_pyme`, `new_mrr_adm_operador`, `new_mrr_sueldos_pyme`, `new_mrr_sueldos_operador` (plus `new_mrr_unknown` when CUIT data is missing).

### 2.5b: Query MTD from Supabase

All MTD data is now in Supabase — query it the same way as Building Blocks:

```sql
SELECT metric, value, count, refreshed_at, source_db_date
FROM mtd_summary
WHERE month = '{MMM-YYYY}'
ORDER BY metric
```

Or via REST API (works from any agent, including Cowork):
```
GET /rest/v1/mtd_summary?month=eq.Mar-2026&order=metric
Header: apikey: {SUPABASE_ANON_KEY}
```

Key metrics for the output:

| metric | What it means |
|--------|---------------|
| `new_mrr_adm_pyme` | New MRR from Administración × ICP Pyme (primerPago=1) |
| `new_mrr_adm_operador` | New MRR from Administración × ICP Operador (accountant-billed) |
| `new_mrr_sueldos_pyme` | New MRR from Sueldos × ICP Pyme |
| `new_mrr_sueldos_operador` | New MRR from Sueldos × ICP Operador |
| `new_mrr_total` | Sum of all new product MRR |
| `active_billing_products` | Non-cancelled billing relationships (facturacion rows) |
| `churned_products` | Products with `fechaBaja` in the current month |
| `payments_collected` | Total ARS collected (all payments, not just first) |
| `paying_empresas_mtd` | Unique empresas that paid this month |

### 2.5c: Integrate into output

Present MTD as a separate section after the closed-month gap analysis.

Compare MTD New MRR against the monthly Forecast for context (e.g., "New MRR at ${X} = {N}% of monthly forecast with {days_remaining} days left").

---

## Step 3: HubSpot Actuals

Pull live customer data from HubSpot:

1. **Total active customers:** Search companies with `lifecyclestage = customer`
   ```
   search_crm_objects(object_type="companies", filter_groups=[{"filters":[{"propertyName":"lifecyclestage","operator":"EQ","value":"customer"}]}], properties=["name"])
   ```
   Count total results (paginate through all pages).

2. **New customers this month:** Search companies with `lifecyclestage = customer` AND `createdate >= first day of current month`
   ```
   search_crm_objects(object_type="companies", filter_groups=[{"filters":[{"propertyName":"lifecyclestage","operator":"EQ","value":"customer"},{"propertyName":"createdate","operator":"GTE","value":"YYYY-MM-01T00:00:00Z"}]}], properties=["name","createdate"])
   ```

3. **Deal pipeline value:** Search open deals, sum `amount` property
   ```
   search_crm_objects(object_type="deals", filter_groups=[{"filters":[{"propertyName":"dealstage","operator":"NOT_IN","values":["closedwon","closedlost"]}]}], properties=["amount","dealname","dealstage"])
   ```

---

## Step 4: Read OKR Targets

Read the current quarter's OKR file:

```
${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md
```

Extract the Company Level targets. For area-level targets (if populated), extract those too.

**Quarter file logic:** Determine current quarter from date:
- Jan–Mar → `q1-YYYY.md`
- Apr–Jun → `q2-YYYY.md`
- Jul–Sep → `q3-YYYY.md`
- Oct–Dec → `q4-YYYY.md`

---

## Step 5: Gap Analysis

**Primary comparison:** Real vs Forecast (are we meeting our latest projection?).

**Baseline reference:** Budget (are we still aligned with the original approved plan?).

For each KPI with complete-month data:

| Field | Description |
|-------|-------------|
| Budget | Value from the Budget section (Pattern E or D) — summed over complete months |
| Forecast | Value from the Forecast section (Pattern E or A) — summed over complete months |
| Real | Value from the Real section — summed over complete months |
| Gap | Real minus Forecast (absolute) |
| Gap % | Gap as percentage of Forecast |
| Status | ✅ On track (gap < 5%), ⚠️ Watch (5–10%), 🔴 Behind (>10% negative), 🟢 Ahead (>10% positive) |
| Budget Δ | Real minus Budget (to show drift from original plan) |

Flag any KPI with >10% deviation from Forecast as **material** — these need CEO attention.

**For unit economics (Pattern C+D):** Only Budget vs Real is available (no Forecast). Show 2-column comparison.

---

## Step 6: Update OKR File

Write the current month's actuals into the quarter's OKR file:

1. Find the column for the current month
2. Update each row's actual value
3. Update the "Last updated" timestamp to today's date
4. Update "Updated by" to `/cos-numbers`

---

## Step 7: Output

Present a structured gap analysis in chat:

### Header
```
📊 KPI Snapshot — Q{N} {Year} ({X}/{Y} months complete)
Generated: {today's date}
Data: Building Blocks + HubSpot + Colppy DB (MTD)
Last complete month: {month name}
MTD source: Colppy billing DB (refreshed {timestamp}) — or "MTD unavailable (VPN off)"
```

### Revenue (from `colppy_budget_first`)
```
MRR Summary — {complete months listed}
Line          | Budget    | Forecast  | Real      | Gap (R-F)  | Status
─────────────────────────────────────────────────────────────────────────
New MRR       | $X        | $X        | $X        | +/-$X (N%) | ✅/⚠️/🔴
Upsell        | ...       | ...       | ...       | ...        | ...
Cross Sell    | ...       | ...       | ...       | ...        | ...
Price Incr.   | ...       | ...       | ...       | ...        | ...
Exp. Disc.    | ...       | ...       | ...       | ...        | ...
─────────────────────────────────────────────────────────────────────────
Total In (+)  | $X        | $X        | $X        | +/-$X (N%) | ...
Churn         | $X        | $X        | $X        | +/-$X (N%) | ...
Downsell      | $X        | $X        | $X        | +/-$X (N%) | ...
Ret. Disc.    | $X        | $X        | $X        | +/-$X (N%) | ...
─────────────────────────────────────────────────────────────────────────
Total Out (-) | $X        | $X        | $X        | +/-$X (N%) | ...
─────────────────────────────────────────────────────────────────────────
EoP MRR       | $X        | $X        | $X        | +/-$X (N%) | ...

Products:  Budget {N} | Forecast {N} | Real {N} new, {N} lost → EoP {N}
```

### Product Drill-Down (from `colppy_budget`, optional)
Table: Product line | Forecast MRR | Real MRR | Gap | Status
(Show only if a Revenue line is flagged 🔴 — drill down to find which product/ICP is causing the gap)

### Funnel (from `funnel_from_lead_product_icp`)
Table: Segment | Forecast MQL | Real MQL | Gap | Status
Table: Segment | Forecast CQL | Real CQL | Gap | Status
Table: Segment | Forecast Deals | Real Deals | Gap | Status

### Conversion Rates (from `funnel_lead_product_icp`)
Table: Stage | Forecast % | Real % | Gap

### Unit Economics (from `colppy_budget_aprobado` + `colppy_raw_actuals`)
Table: KPI | Budget | Real | Gap | Status
(Include: Net ASP, CAC, Gross Margin %, Churn %, LTV, NRR, CAC Payback)
Note: No Forecast available for unit economics — showing Budget vs Real only.

### Customers (from HubSpot)
- Total active customers: {count} (target: 3,700 year-end)
- New this month: {count}
- Open pipeline: ${amount}

### Churn Detail (from `churn_budget_real`)
Table: Stage | Forecast % | Real % | Gap

### MTD — Current Month (from Colppy DB, Step 2.5)

Only shown when current month is not yet closed in Building Blocks.

```text
📊 MTD — {Month} {Year} (as of {today}, {days_elapsed}/{days_in_month} days)
Source: Colppy billing DB

New Client MRR:
  Adm. Pyme:      ${X}  ({N} products)
  Adm. Operador:  ${X}  ({N} products)
  Sueldos Pyme:   ${X}  ({N} products)
  Sueldos Oper.:  ${X}  ({N} products)
  Total New MRR:  ${X}  ({N} products)  → {pct}% of monthly Forecast

Active Billing: {N} products
Lost this month: {N} products (${X})
```

### OKR Progress
Table: KPI | Annual Target | YTD Actual | % Progress

### Narrative
2–3 sentences summarizing:
- What's going well (Real ahead of Forecast)
- What needs attention (Real behind Forecast)
- Budget drift: where Forecast itself has moved significantly from Budget
- Most material gap and its impact

**Do NOT send to Slack automatically.** Output in chat only. Juan decides when and what to forward.
