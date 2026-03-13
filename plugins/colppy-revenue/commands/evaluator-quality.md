---
name: evaluator-quality
description: Analyze evaluator quality by acquisition channel, ICP, and persona. Shows which channels produce evaluators that become beginners (PQL) and ultimately generate MRR. Traces the full attribution chain from signup to closed revenue.
---

# /evaluator-quality

Analyze the quality of evaluators entering the product flywheel — which channels, ICPs, and personas produce evaluators that activate and generate MRR.

## Usage

```
/colppy-revenue:evaluator-quality 2026-02
/colppy-revenue:evaluator-quality 2026-01 2026-02   # comparison
/colppy-revenue:evaluator-quality --icp contador     # filter by ICP
```

---

## What I Need From You

- **Month(s)**: Which period to analyze (e.g., "2026-02", "last 3 months")
- **Filter** (optional): Specific ICP (contador/pyme), channel (paid/connections), or campaign

---

## Data Execution

### Preferred: hubspot-analysis MCP

When the **hubspot-analysis** MCP is available, use its tools as building blocks for this analysis. These run battle-tested Python scripts and produce CSV audit trails in `tools/outputs/`:

| Step | MCP Tool | What it provides |
|------|----------|-----------------|
| Funnel baseline (MQL → Deal → Won) | `run_smb_mql_funnel(months="2026-03")` | MQL count, deal creation, won deals, conversion rates |
| Accountant channel funnel | `run_accountant_mql_funnel(months="2026-03")` | Same funnel for accountant MQLs |
| Lead scoring performance | `run_high_score_analysis(month="2026-03")` | Score 40+ contactability, owner performance, SQL/PQL rates |

These give you the **funnel conversion numbers**. The channel attribution overlay (Steps 2-6 below) adds the `initial_utm_*` dimension on top.

### Manual execution (when MCP not available)

If the hubspot-analysis MCP is not configured, execute the steps below using HubSpot MCP tools (`search_crm_objects`) directly.

---

## Step-by-Step Execution

### Step 1: Fetch Evaluators (MQLs) Created in Period

Search HubSpot contacts with these filters:

- `createdate` in target period
- `lead_source` HAS_PROPERTY (exclude nulls)
- `lead_source` NEQ `Usuario Invitado` (exclude team invitations)

**CRITICAL**: Always use HAS_PROPERTY + NEQ together for lead_source filtering.

Fetch these properties:

```
email, firstname, lastname, createdate, lead_source, rol_wizard,
hs_analytics_source, hs_analytics_source_data_1, hs_analytics_source_data_2,
initial_utm_source, initial_utm_medium, initial_utm_campaign,
utm_source, utm_medium, utm_campaign, utm_content, utm_term,
activo, fecha_activo, fit_score_contador,
hs_v2_date_entered_opportunity, hs_v2_date_entered_customer,
lifecyclestage, num_associated_deals, hubspot_owner_id
```

### Step 2: Classify by Channel

**CRITICAL UTM FIELD SELECTION**: HubSpot has three sets of UTM fields. Use this priority:

| Field Set | Coverage | Use When |
|-----------|----------|----------|
| `initial_utm_source`, `initial_utm_campaign`, `initial_utm_medium` | ~92% of contacts | **PRIMARY — always use these first** |
| `utm_source`, `utm_campaign`, `utm_medium` | <1% of contacts | Fallback only (pipeline broken) |
| `hs_analytics_source` | ~85% of contacts | Channel classification when no UTMs |

Group evaluators into acquisition channels:

| Channel | How to identify |
|---------|----------------|
| **Google Ads** | `initial_utm_source` = "google" AND `initial_utm_medium` = "ppc" |
| **Meta Ads** | `initial_utm_source` contains "facebook"/"instagram"/"meta" |
| **LinkedIn Ads** | `initial_utm_source` = "linkedin" AND `initial_utm_medium` = "linkedin" |
| **Organic Search** | No `initial_utm_source` AND `hs_analytics_source` = ORGANIC_SEARCH |
| **Direct** | No `initial_utm_source` AND `hs_analytics_source` = DIRECT_TRAFFIC |
| **Connections (Contador)** | `lead_source` indicates accountant connection or `rol_wizard` = contador-related values |
| **Connections (Peer)** | `lead_source` indicates peer/customer connection |
| **Colppy Portal** | `initial_utm_source` = "Colppy" AND `initial_utm_campaign` = "referral_portal_clientes" |
| **Other** | Everything else |

For paid channels, also fetch `initial_utm_campaign` for campaign-level drill-down.

### Step 3: Classify by ICP

For each evaluator, determine ICP via associated company:

- Fetch associated companies (if any) via HubSpot associations
- Check `type` field on PRIMARY company (association typeId 5)
- `type` in `['Cuenta Contador', 'Cuenta Contador y Reseller', 'Contador Robado']` → ICP Contador
- Any other → ICP Pyme
- No company → Unclassified (flag as data quality)

### Step 4: Classify by Persona

Use `rol_wizard` to approximate behavioral persona:

| rol_wizard value | Persona |
|-----------------|---------|
| Contador, Estudio contable | Accounting |
| Administrador, Dueño, Gerente | Administrative |
| Other/missing | Unknown |

### Step 5: Measure Evaluator → Beginner Conversion

For each evaluator, check:

- **PQL**: `activo = true` AND `fecha_activo` is populated
- **Time to PQL**: `fecha_activo` - `createdate` (in hours/days)
- **SQL**: `hs_v2_date_entered_opportunity` populated AND `num_associated_deals` > 0
- **Customer**: `hs_v2_date_entered_customer` populated or `lifecyclestage` = customer

### Step 6: Trace to MRR

For evaluators who became customers:

- Fetch associated deals (closed-won only)
- Sum `amount` for MRR attribution
- Group by acquisition channel

### Step 7: Present Results

#### Table 1: Channel Quality Summary

```
Channel          | Evaluators | PQL | PQL % | SQL | SQL % | Won | Won % | MRR (ARS)   | CAC*
─────────────────┼────────────┼─────┼───────┼─────┼───────┼─────┼───────┼─────────────┼──────
Google Ads       | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | ${x}
Meta Ads         | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | ${x}
Connections      | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | $0
Organic          | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | -
Direct           | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | -
─────────────────┼────────────┼─────┼───────┼─────┼───────┼─────┼───────┼─────────────┼──────
TOTAL            | {n}        | {n} | {x}%  | {n} | {x}%  | {n} | {x}%  | ${x}        | ${x}
```

*CAC = channel spend / won customers (only for paid channels with available spend data)

#### Table 2: ICP Quality Breakdown

```
ICP              | Evaluators | PQL % | Won % | MRR (ARS)   | Avg Time to PQL
─────────────────┼────────────┼───────┼───────┼─────────────┼─────────────────
Cuenta Contador  | {n}        | {x}%  | {x}%  | ${x}        | {x} days
Cuenta Pyme      | {n}        | {x}%  | {x}%  | ${x}        | {x} days
Unclassified     | {n}        | {x}%  | {x}%  | ${x}        | {x} days
```

#### Table 3: Persona Quality Breakdown

```
Persona          | Evaluators | PQL % | Won % | MRR (ARS)
─────────────────┼────────────┼───────┼───────┼─────────────
Accounting       | {n}        | {x}%  | {x}%  | ${x}
Administrative   | {n}        | {x}%  | {x}%  | ${x}
Unknown          | {n}        | {x}%  | {x}%  | ${x}
```

#### Table 4: Connection Share

```
Source           | Evaluators | % of Total | MRR (ARS)  | % of MRR
─────────────────┼────────────┼────────────┼────────────┼──────────
Paid channels    | {n}        | {x}%       | ${x}       | {x}%
Connections      | {n}        | {x}%       | ${x}       | {x}%
Organic/Direct   | {n}        | {x}%       | ${x}       | {x}%
```

### Step 8: Downstream Quality Signal (Optional)

If requested or if data is available, check retained status of beginners:

- Of PQLs from this cohort, how many are still performing critical events monthly?
- Flag channels with high PQL but low retention as potential false positives

---

## Important Notes

- **Terminology**: Never use "referral" — always "connection"
- **Attribution**: Trace full chain: channel → evaluator → PQL → deal won → MRR
- **Connection CAC**: Always $0 — this is key to the connection share analysis
- **Business age**: If CUIT enrichment data is available, include business age distribution by channel
- **Budget comparison**: If Building Blocks data is available, compare MRR actuals to budget
- **HubSpot portal**: 19877595 (for generating contact links)
- **Formatting**: Argentine number format ($1.234,56)
