---
name: cos-numbers
description: "KPI snapshot — fetch Building Blocks budget data, parse Plan vs Real, pull HubSpot actuals, compare against OKR targets, and output a gap analysis. Use when the user asks 'show me the numbers', 'how are we doing', or 'budget status'."
---

# /cos-numbers — KPI Snapshot

Produce a **Plan vs Real gap analysis** for the current month. Fetches live data from 6 Building Blocks tabs (Google Sheets), pulls customer counts from HubSpot, compares against OKR targets, and outputs a structured summary with gap flags.

---

## Data Sources

| Registry ID | Tab Name | What It Provides | Pattern |
|-------------|----------|------------------|---------|
| `colppy_budget` | Building Blocks Por Producto | MRR by product line (Administración, Sueldos, Upsell, Cross sell) | A |
| `funnel_from_lead_product_icp` | # Funnel_From_Lead_Product_All_ICP | MQL/CQL/deal counts by ICP segment | A |
| `funnel_lead_product_icp` | % Funnel_Lead_Product_All_ICP | Lead→CQL→Deal conversion rates (%) | A |
| `churn_budget_real` | Churn_Budget_Real | Lost MRR by lifecycle stage (Early/Mid/Late %) | B |
| `colppy_raw_actuals` | Raw Data -- Actuals | Gross/Net ASP, CAC, Churn %, LTV, NRR, New Clients | C |
| `colppy_budget_aprobado` | Budget Aprobado | KPIs: Net ASP, Gross Margin, CAC, LTV, NRR, New Clients (#) | D |

**Complementary pair:** For unit economics (ASP, CAC, Churn, LTV, NRR), compare Pattern D (plan) vs Pattern C (actuals). These two tabs form one logical unit.

---

## Target Month Logic

Compute the target month from the current date:

```
month_names = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
current_month = month_names[current_date.month - 1]
current_year = current_date.year
```

Three format variants are needed (different tabs use different formats):

| Format | Example | Used By |
|--------|---------|---------|
| `MMM-YYYY` | `Mar-2026` | Pattern A, B tabs |
| `MMM-YY` | `Mar-26` | Pattern D (`colppy_budget_aprobado`) |
| `MMM YY` | `Mar 26` (space, no dash) | Pattern C (`colppy_raw_actuals`) |

When searching for the target month column in a CSV header, try all three formats to find the match.

---

## Step 1: Read Registry

Read the canonical registry:

```bash
cat tools/docs/GOOGLE_SHEETS_REGISTRY.json
```

Extract `file_id` and `gid` for each of the 6 tabs listed above. Match by `id` field.

---

## Step 2: Fetch Tabs

For each tab, fetch as CSV:

```bash
curl -sL "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
```

Save each result for parsing. All 6 fetches are independent — run them all.

---

## Step 3: Parse Each Tab

### Pattern A — Plan + REAL split

**Tabs:** `colppy_budget`, `funnel_from_lead_product_icp`, `funnel_lead_product_icp`

1. Scan rows for one where the first non-empty cell equals `REAL` (case-sensitive)
2. Everything above that row = **Plan** section
3. Everything below = **Real** section
4. In the Plan section's header row (usually row 2), find the column index for the target month (`MMM-YYYY` format, e.g. `Mar-2026`)
5. In the Real section's header row (row after the REAL marker), find the same month column
6. Extract Plan and Real values for each item row in that column

**Notes:**
- The `colppy_budget` tab has a "Forecast Factor de Incremento en %" row at approximately row 26 — this is part of the Plan section, not a separate section. Ignore it for extraction; the item rows above it are the Plan values.
- Item names may have typos (e.g. "Admnisitración" instead of "Administración"). Match items between Plan and Real by substring or fuzzy match, not exact string.
- Numbers use Argentine format: `.` for thousands separator, `,` for decimal. Parse accordingly (strip dots, replace comma with period).

### Pattern B — Labeled Sections

**Tab:** `churn_budget_real`

1. Find row containing `Lost MRR Budget` → this starts the **Plan** section
2. Find row containing `Lost MRR Actual` → this starts the **Real** section
3. Find row containing `% of MRR` → this is a derived section (actuals as % of total MRR)
4. In each section, find the target month column (`MMM-YYYY` format)
5. Extract Early/Mid/Late percentages for Plan and Real

**Note:** This tab has a footer note saying "PENDING: Abrir como el resto de las solapas" — it will eventually be restructured to Pattern A. For now, use the labeled header approach.

### Pattern C — Actuals Only

**Tab:** `colppy_raw_actuals`

1. All rows are historical actuals — there is no Plan section in this tab
2. Column headers use `MMM YY` format (e.g. `Feb 26`) — note the **space** and **2-digit year**
3. Find the target month column using the `MMM YY` format
4. Extract values for: Gross ASP, Net ASP, Direct Cost, Gross Margin, % Gross Margin, CAC x Client, Total CAC, # New Clients, CAC Payback, % Net Churn, % Gross Churn, Customer Lifetime, LTV

**For gap analysis:** Pair these actuals with Pattern D's plan values.

### Pattern D — Plan Only

**Tab:** `colppy_budget_aprobado`

1. All rows are approved budget targets — there is no Real section in this tab
2. Column headers use `MMM-YY` format (e.g. `Mar-26`) — note the **dash** and **2-digit year**
3. Find the target month column using the `MMM-YY` format
4. Extract values for: Net ASP, Direct Cost, Gross Margin, % Gross Margin, CAC x Client, Total CAC, New Clients (#), CAC Payback, Net Churn %, Gross Churn %, Customer Lifetime, LTV, NRR
5. This tab also has a "Clients (#)" section with BoP, New, Lost, EoP — extract those too

**For gap analysis:** Pair these plan values with Pattern C's actuals.

---

## Step 4: HubSpot Actuals

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

## Step 5: Read OKR Targets

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

## Step 6: Gap Analysis

For each KPI, compute:

| Field | Description |
|-------|-------------|
| Plan | Value from the Plan section (or Pattern D for unit economics) |
| Real | Value from the Real section (or Pattern C for unit economics) |
| Gap | Real minus Plan (absolute) |
| Gap % | Gap as percentage of Plan |
| Status | ✅ On track (gap < 5%), ⚠️ Watch (5–10%), 🔴 Behind (>10% negative), 🟢 Ahead (>10% positive) |

Flag any KPI with >10% deviation as **material** — these need CEO attention.

---

## Step 7: Update OKR File

Write the current month's actuals into `${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md`:

1. Find the column for the current month (Apr/May/Jun)
2. Update each row's actual value
3. Update the "Last updated" timestamp to today's date
4. Update "Updated by" to `/cos-numbers`

---

## Step 8: Output

Present a structured gap analysis in chat:

### Header
```
📊 KPI Snapshot — {Month} {Year}
Generated: {today's date}
Data: Building Blocks + HubSpot
```

### Revenue (from `colppy_budget`)
Table: Product line | Plan MRR | Real MRR | Gap | Status

### Funnel (from `funnel_from_lead_product_icp`)
Table: Segment | Plan MQL | Real MQL | Gap | Status
Table: Segment | Plan CQL | Real CQL | Gap | Status
Table: Segment | Plan Deals | Real Deals | Gap | Status

### Unit Economics (from `colppy_budget_aprobado` + `colppy_raw_actuals`)
Table: KPI | Plan | Real | Gap | Status
(Include: Net ASP, CAC, Gross Margin %, Churn %, LTV, NRR, CAC Payback)

### Customers (from HubSpot)
- Total active customers: {count} (target: 3,700 year-end)
- New this month: {count}
- Open pipeline: ${amount}

### Churn (from `churn_budget_real`)
Table: Stage | Plan % | Real % | Gap

### OKR Progress
Table: KPI | Annual Target | YTD Actual | % Progress

### Narrative
2–3 sentences summarizing:
- What's going well (ahead of plan)
- What needs attention (behind plan)
- Most material gap and its impact

**Do NOT send to Slack automatically.** Output in chat only. Juan decides when and what to forward.
