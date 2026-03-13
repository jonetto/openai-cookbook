---
name: campaign-roi
description: Analyze campaign ROI by tracing acquisition spend to closed MRR. Compares paid channels vs connections, computes CAC, channel ROI, and budget vs actual performance. Uses Google Ads, HubSpot deals, and Building Blocks budget data.
---

# /campaign-roi

Analyze the return on investment of acquisition campaigns by tracing spend through to closed MRR.

## Usage

```
/colppy-revenue:campaign-roi 2026-02
/colppy-revenue:campaign-roi 2026-01 2026-02 2026-03   # multi-month trend
/colppy-revenue:campaign-roi --channel google-ads       # specific channel
```

---

## What I Need From You

- **Month(s)**: Which period to analyze (e.g., "2026-02", "Q1 2026")
- **Channel filter** (optional): google-ads, meta-ads, connections, all (default: all)

---

## Data Execution

### Preferred: hubspot-analysis MCP

When the **hubspot-analysis** MCP is available, use its tools as building blocks for this analysis:

| Step | MCP Tool | What it provides |
|------|----------|------------------|
| SMB funnel baseline (MQL → Deal → Won) | `run_smb_mql_funnel(months="2026-03")` | MQL count, deal creation, won deals, conversion rates by month |
| Accountant channel funnel | `run_accountant_mql_funnel(months="2026-03")` | Same funnel for accountant MQLs |
| Lead scoring performance | `run_high_score_analysis(month="2026-03")` | Score 40+ contactability, SQL/PQL rates |

These give you the **funnel conversion numbers** and deal-won counts. The channel attribution (Steps 2-4 below), spend data (Step 1), and ROI computation (Step 4) add the acquisition-cost dimension on top.

**Future**: `run_campaign_roi` tool will wrap the full analysis end-to-end (Python script: `tools/scripts/hubspot/analyze_campaign_roi.py`).

### Manual execution (when MCP not available)

If the hubspot-analysis MCP is not configured, execute the steps below using HubSpot MCP tools (`search_crm_objects`) and Google Ads MCP directly.

---

## Step-by-Step Execution

### Step 1: Pull Acquisition Spend

#### Google Ads

Use Google Ads MCP tools to fetch campaign-level data for the period:

- Campaign name, status
- Impressions, clicks, cost
- Conversions (if configured)

Group by campaign and sum spend.

#### Meta Ads

If Meta Ads data is available (scripts or API), fetch:

- Campaign name, spend, impressions, clicks

#### Connection Channel

Connections have **$0 acquisition cost**. This is structural — no ad spend required. Track volume only.

### Step 2: Pull New Customers Created in Period

From HubSpot, fetch deals closed-won in the target period:

- `closedate` in target period
- `hs_is_closed_won = true`
- Fetch: `dealname, amount, closedate, pipeline, hubspot_owner_id, createdate`

For each won deal:

- Get associated contacts via HubSpot associations
- For each contact, fetch: `lead_source, initial_utm_source, initial_utm_medium, initial_utm_campaign, hs_analytics_source, createdate, rol_wizard`
- Determine acquisition channel (same classification as evaluator-quality command)

### Step 3: Attribute MRR to Channels

For each won deal, attribute MRR to the acquisition channel of the FIRST contact associated:

| Attribution Rule | Logic |
|-----------------|-------|
| Contact has `initial_utm_*` data | Use `initial_utm_source`/`initial_utm_campaign` to map to channel (**primary — ~92% coverage**) |
| Contact has `utm_*` data | Fallback: use `utm_source`/`utm_campaign` (<1% coverage, pipeline broken) |
| Contact has `hs_analytics_source` | Use as fallback channel classification when no UTMs |
| Contact from connection | `lead_source` indicates connection origin |
| Multiple contacts | Use the earliest contact (first touch attribution) |

Sum MRR per channel.

### Step 4: Compute Channel Economics

For each channel, calculate:

```
CAC = Total Channel Spend / Number of Won Deals from Channel
Channel ROI = Total MRR from Channel / Total Channel Spend
MRR per Dollar = Total MRR / Total Spend (for paid channels)
Payback Period = CAC / Average MRR per Customer (months)
```

For connections:

```
CAC = $0
Channel ROI = ∞ (flag as "zero-cost acquisition")
```

### Step 5: Pull Budget Targets

Fetch Building Blocks budget data from Google Sheets registry:

- Tab: `colppy_budget_first` (Budget & Forecast 2026) — New MRR targets
- Tab: `colppy_raw_actuals` (Raw Data Actuals) — MRR actuals

Compare:

- New MRR actual vs budget for the period
- New clients actual vs budget
- ASP actual vs budget

### Step 6: Campaign-Level Drill Down (Paid Channels)

For Google Ads, break down by individual campaign:

- Campaign name
- Spend
- Evaluators generated (contacts with matching utm_campaign)
- PQLs generated
- Deals won
- MRR attributed
- Cost per PQL
- Cost per deal won

### Step 7: Present Results

#### Table 1: Channel ROI Summary

```
Channel          | Spend (ARS)  | Won Deals | MRR (ARS)   | CAC (ARS)   | ROI    | Payback
─────────────────┼──────────────┼───────────┼─────────────┼─────────────┼────────┼────────
Google Ads       | ${x}         | {n}       | ${x}        | ${x}        | {x}x   | {x}mo
Meta Ads         | ${x}         | {n}       | ${x}        | ${x}        | {x}x   | {x}mo
Connections      | $0           | {n}       | ${x}        | $0          | ∞      | 0mo
Organic/Direct   | $0*          | {n}       | ${x}        | -           | -      | -
─────────────────┼──────────────┼───────────┼─────────────┼─────────────┼────────┼────────
TOTAL            | ${x}         | {n}       | ${x}        | ${x}        | {x}x   | {x}mo
```

*Organic has indirect costs (content, SEO) not tracked here

#### Table 2: Budget vs Actual

```
Metric               | Budget (ARS)  | Actual (ARS)  | % of Target | Delta
─────────────────────┼───────────────┼───────────────┼─────────────┼───────
New MRR              | ${x}          | ${x}          | {x}%        | ${x}
New Clients          | {n}           | {n}           | {x}%        | {n}
Net ASP              | ${x}          | ${x}          | {x}%        | ${x}
Acquisition Spend    | ${x}          | ${x}          | {x}%        | ${x}
```

#### Table 3: Google Ads Campaign Breakdown

```
Campaign                     | Spend    | Evaluators | PQLs | Won | MRR      | Cost/PQL | Cost/Won
─────────────────────────────┼──────────┼────────────┼──────┼─────┼──────────┼──────────┼─────────
{campaign_name}              | ${x}     | {n}        | {n}  | {n} | ${x}     | ${x}     | ${x}
{campaign_name}              | ${x}     | {n}        | {n}  | {n} | ${x}     | ${x}     | ${x}
...
```

#### Table 4: Connection Share Trend (if multi-month)

```
Month    | Paid MRR    | Connection MRR | Connection % | Total MRR
─────────┼─────────────┼────────────────┼──────────────┼───────────
{month}  | ${x}        | ${x}           | {x}%         | ${x}
{month}  | ${x}        | ${x}           | {x}%         | ${x}
```

### Step 8: Recommendations

Based on the data, provide at least one actionable recommendation:

- **Cut**: Campaigns with high spend and low MRR attribution
- **Invest**: Channels/campaigns with best ROI
- **Investigate**: Channels with high evaluator volume but low conversion
- **Connection opportunity**: If connection share is declining, flag it — the flywheel may be slowing

---

## Important Notes

- **Terminology**: Never use "referral" — always "connection"
- **Attribution**: First-touch attribution (earliest contact on the deal)
- **Connection economics**: Always $0 CAC — this is the structural advantage of the flywheel
- **Lag warning**: Deals won this month may have been evaluators from previous months. Note the cohort lag in the output
- **Currency**: Argentine number format ($1.234,56)
- **Budget source**: Building Blocks Google Sheets (see registry in `docs/GOOGLE_SHEETS_REGISTRY.json`)
- **HubSpot portal**: 19877595
