# Trial Experience Analyst — Design Doc

> Agent + skills for understanding trial user experience at Colppy by connecting Intercom friction data, Mixpanel behavioral signals, and HubSpot conversion outcomes. Produces actionable reports for Marketing and Product teams.

**Date:** 2026-03-07
**Plugin:** `colppy-customer-success`
**Approach:** B (single multi-source agent + 2 new skills)

---

## Problem

During Colppy's 7-day free trial, three systems capture different facets of the user experience:

- **Intercom** — what users struggle with (support conversations in the "Primeros 90 días" inbox)
- **Mixpanel** — what users actually do (critical events, activation, behavioral persona)
- **HubSpot** — who users are and whether they convert (ICP, lifecycle stage, deals)

Today these signals live in silos. There is no automated way to answer: "SMB trial users who struggle with AFIP config have X% lower activation than those who don't contact support." Marketing and Product need this connection to prioritize fixes and refine targeting.

---

## Components

```
plugins/colppy-customer-success/
├── agents/
│   └── trial-experience-analyst.md       ← NEW — agent workflow
├── skills/
│   ├── user-lifecycle-framework/
│   │   └── SKILL.md                      ← NEW — Framework de Producto encoded
│   ├── trial-data-model/
│   │   └── SKILL.md                      ← NEW — cross-system identity & joins
│   ├── intercom-customer-research/       (exists)
│   ├── intercom-onboarding-setup/        (exists)
│   └── business-context/                 (exists)
```

### Component Roles

| Component | Type | Role |
|-----------|------|------|
| `trial-experience-analyst` | Agent | Workflow orchestration — steps to collect, analyze, and present |
| `user-lifecycle-framework` | Skill | Domain knowledge — lifecycle stages, behavioral personas, critical events, PQL/activation definitions |
| `trial-data-model` | Skill | Data knowledge — how to join users across Intercom, Mixpanel, HubSpot; which fields link which systems |

---

## Skill 1: User Lifecycle Framework

Encodes the "Framework de Product Insights en Producto" as machine-readable context.

### Behavioral Personas

Determined by **product behavior** (Mixpanel events), not by wizard selection:

| Persona | Critical Events (Mixpanel) | Description |
|---------|---------------------------|-------------|
| Lleva la administración | `Generó comprobante de compra`, `Generó comprobante de venta` | Core — invoicing and admin |
| Lleva la contabilidad | Accounting events (asientos, plan de cuentas) | Bookkeeping |
| Lleva inventario | Inventory events (stock, items) | Inventory management |
| Operador | Same events as admin, but `contact_es_contador=true` AND operates across multiple client empresas | Accountant behaving as administrator |

### Trial Lifecycle Stages (7-day window)

| Stage | Signal | Source |
|-------|--------|--------|
| Evaluating | Signed up, validated email → MQL | HubSpot `createdate` |
| Activated (PQL) | Performed critical event during trial | Mixpanel + HubSpot `activo=true`, `fecha_activo` |
| Converted | First payment | Colppy `primerPago=1` |
| Churned from trial | 7 days passed, no payment | No primerPago after trial window |

### Activation Threshold

Configurable. Default from historical Signal report: **4+ comprobantes de compra within 7 days** correlates with week-2 retention. The agent can self-validate this by running Method B (retention query + segmentation) on recent cohorts.

### Wizard vs Reality Gap

| Wizard `rol_wizard` | Actual Behavior | Classification |
|---------------------|-----------------|----------------|
| Contador → operates for clients | Admin events on client empresas | **Operador** (accountant-as-admin) |
| Contador → does contabilidad | Accounting events | **Contador** (true accountant) |
| Pyme → does admin | Compra/venta events | **Pyme admin** (expected) |
| Pyme → barely uses product | Few/no critical events | **At risk** — not activated |

### User Lifecycle Cuts (from Framework)

| Cut | Definition | Strategy |
|-----|-----------|----------|
| Beginners (Nuevos) | First time using the product in the period | First impression — critical for activation |
| Retained (Current) | Consistent usage over time | Push toward power user; potential champions |
| Resurrected (Revividos) | Were active, went dormant, came back | Cheaper to reactivate than acquire new |
| Dormants (Dormidos) | Were active, now inactive | Understand pre-churn patterns |

### Health Metrics

| Metric | Definition | Source |
|--------|-----------|--------|
| Pulse | (New + Resurrected) / Dormants. >1 = growing, <1 = shrinking | Mixpanel lifecycle |
| Stickiness | Days per month a user performs the critical event | Mixpanel (monthly) |
| PQL rate | % of MQLs that activate during trial | HubSpot `activo` + `fecha_activo` |

---

## Skill 2: Trial Data Model

### Cross-System Identity

Two granularity levels:

| Level | Key | Meaning |
|-------|-----|---------|
| **Person** | `email` | The human. Same across Intercom, HubSpot, Mixpanel (`distinct_id` = email) |
| **Subscription** | `id_empresa` | The company/plan the person operates in. One person can have events across multiple empresas (especially Operadors) |

### Identity Map

```
                    email (person)
    Intercom ◄──────────────────► HubSpot ◄──────► Mixpanel
  (conversations)                (contacts)      (distinct_id = email)
                                    │
                              id_empresa (subscription)
                                    │
                              Colppy DB ◄──────► Mixpanel
                            (billing, plans)   (id_empresa = super property
                                                = which subscription the
                                                event was performed in)
```

### What Each System Contributes

| Question | Source | Tool |
|----------|--------|------|
| What did the user struggle with? | Intercom | `scan_customer_feedback` / `scan_full_text` (team 2334166) |
| What topics are trending? | Intercom | `llm_classify.mjs` with topic config |
| Is the user accountant or SMB? | Intercom `contact_es_contador` / HubSpot company `type` | Cached in export; fallback HubSpot API |
| What did the user do in the product? | Mixpanel | `run_segmentation_query` on critical events |
| Did they activate (PQL)? | HubSpot | `activo=true` + `fecha_activo` |
| Did they convert to paid? | HubSpot / Colppy | Deal `hs_is_closed_won` or `primerPago=1` |
| What behavioral persona? | Mixpanel | Event distribution per user/empresa |

### Tools Available

| Tool | MCP Source | Purpose |
|------|-----------|---------|
| `scan_customer_feedback` | customer-success plugin | Fast Intercom topic scan (first message) |
| `scan_full_text` | customer-success plugin | Deep Intercom scan (all messages) |
| `get_conversation_feedback` | customer-success plugin | Deep-dive specific conversations |
| `analyze_onboarding_first_invoice` | customer-success plugin | Segmented onboarding classification |
| `run_segmentation_query` | Mixpanel MCP | Event counts by cohort/property |
| `run_funnels_query` | Mixpanel MCP | Conversion funnels |
| `run_retention_query` | Mixpanel MCP | Cohort retention curves |
| `search_crm_objects` | HubSpot MCP | Contact/deal search |
| `get_crm_objects` | HubSpot MCP | Fetch records by ID |

### Scripts Available

| Script | Purpose |
|--------|---------|
| `tools/scripts/intercom/export_cache_for_local_scan.mjs` | Export Intercom conversations with contact attributes |
| `tools/scripts/intercom/analyze_onboarding.py` | Segmented onboarding analysis (accountant vs SMB) |
| `plugins/colppy-customer-success/scripts/llm_classify.mjs` | LLM topic classification with few-shot learning |

---

## Agent Workflow

### Frontmatter

```yaml
name: trial-experience-analyst
description: >
  Analyze trial user experience by connecting Intercom support friction,
  Mixpanel product behavior, and HubSpot conversion data. Produces
  segmented reports for Marketing and Product teams.
model: inherit
color: green
```

### Trigger Examples

- "How is onboarding going this week?"
- "Trial experience report for February"
- "What are trial users struggling with?"
- "How are SMB trial users activating vs accountants?"
- "What's blocking conversion for the current cohort?"

### Step 1: Determine Cohort & Scope

- Parse request for: **time period** (default: last 7 days), **segment** (SMB, accountant, all), **topic filter** (optional)
- If user says "this month" or "February" → use calendar month boundaries

### Step 2: Intercom Friction Analysis

1. Check cached exports: `skills/intercom-developer-api-research/cache/conversations_*_team2334166.json`
2. If cache covers period → use it
3. If not → export fresh:
   ```bash
   cd tools/scripts/intercom
   node export_cache_for_local_scan.mjs --from YYYY-MM-DD --to YYYY-MM-DD --team 2334166
   ```
4. Classify by user type:
   ```bash
   python tools/scripts/intercom/analyze_onboarding.py \
     --cache <path> --user-type smb --llm
   python tools/scripts/intercom/analyze_onboarding.py \
     --cache <path> --user-type accountant --llm
   ```
5. Output: topic distribution by segment, top friction points

### Step 3: Mixpanel Behavioral Analysis

1. Query critical events for cohort using `run_segmentation_query`:
   - Event: critical events (comprobante compra/venta, contabilidad, inventario)
   - Filter: plan = "Pendiente de Pago" (trial users)
   - Breakdown: by `id_empresa` or user property
2. Query activation funnel using `run_funnels_query`:
   - Step 1: First login → Step 2: Critical event → Step 3: Payment
3. Output: activation rate, avg events per user, behavioral persona distribution

### Step 4: HubSpot Conversion Cross-Reference

1. Query contacts created in period using `search_crm_objects`:
   - Properties: `email, createdate, activo, fecha_activo, lead_source, rol_wizard, num_associated_deals, lifecyclestage`
   - Exclude: `lead_source = Usuario Invitado` (use HAS_PROPERTY + NEQ filter)
2. PQL rate: count `activo=true` AND `fecha_activo` in period
3. Conversion rate: count `lifecyclestage = customer` or closed-won deal
4. Segment all counts by ICP

### Step 5: Present Full Results

**Always output ALL tables — never abbreviate.**

**5a — Cohort Summary Table**

| Metric | SMB | Accountant | Total |
|--------|-----|------------|-------|
| Trial signups (MQL) | X | X | X |
| Activated (PQL) | X | X | X |
| PQL rate | X% | X% | X% |
| Converted (paid) | X | X | X |
| Conversion rate | X% | X% | X% |
| Intercom conversations | X | X | X |
| Avg critical events in trial | X | X | X |

**5b — Friction Report (Intercom)**

| Topic | SMB | Accountant | Severity | Example |
|-------|-----|------------|----------|---------|
| factura_electronica_config | X | X | High | "No puedo configurar..." |

With clickable Intercom URLs for each referenced conversation.

**5c — Behavioral Persona Distribution**

| Persona | Count | % of Cohort | Activation Rate | Avg Events |
|---------|-------|-------------|-----------------|------------|
| Lleva administración | X | X% | X% | X |
| Lleva contabilidad | X | X% | X% | X |
| Operador | X | X% | X% | X |
| Not activated | X | X% | 0% | <1 |

**5d — Wizard vs Reality Matrix**

| Wizard Role | Actual Behavior | Count | Conversion Rate |
|-------------|-----------------|-------|-----------------|
| Contador → Contabilidad | Aligned | X | X% |
| Contador → Administración | Operador | X | X% |
| Pyme → Administración | Aligned | X | X% |
| Pyme → No activity | At risk | X | X% |

### Step 6: Interpret & Recommend

1. **TL;DR** — 3 bullets: biggest friction point, activation gap, conversion blocker

2. **For Marketing:**
   - Which UTM sources produce trial users that activate vs churn?
   - Wizard role mismatch rate — attracting wrong persona?
   - Recommended messaging changes based on actual behavior

3. **For Product:**
   - Top friction points blocking activation (ranked by frequency x severity)
   - Feature gaps: what are users trying to do but failing?
   - Stickiness signal: hitting activation threshold?

4. **Health Score:**
   - PQL rate > 40% + top friction < 15% of conversations → "Healthy trial"
   - PQL rate 25-40% or top friction 15-30% → "Needs attention"
   - PQL rate < 25% or top friction > 30% → "Trial experience at risk"

### Constraints

- **Read-only** — never modify Intercom, HubSpot, or Mixpanel data
- **Never invent data** — if a source is unavailable, state it and present partial results
- **Never skip tables** — full output every time
- **Always show data sources** — state which cache files, date ranges, and filters were used
- **Always segment by ICP** — never present unsegmented totals without the breakdown
- **Currency in Argentine format** — `$1.234` (dot for thousands)

---

## Future: Activation Threshold Self-Refresh (Method B)

Not in scope for v1 but designed for:

1. Use `run_retention_query` (born_event = first login with plan Pendiente de Pago, return_event = critical event)
2. Use `run_segmentation_query` to get per-user event counts in first 7 days
3. For N = 1, 2, 3, 4, 5, 6+: compute conversion rate and week-2 retention
4. Find inflection point → update activation threshold in `user-lifecycle-framework` skill

---

## Open Questions

1. **Activation threshold**: Currently 4 comprobantes in 7 days (from historical Signal report). Needs refresh — defer to Method B or manual Mixpanel Signal report.
2. ~~**Mixpanel event names**~~: **RESOLVED** — Confirmed from codebase (`intercom-lexicon.md`, `MIXPANEL_LEXICON_CONFIG.md`, JS source). Admin: `Generó comprobante de compra/venta`. Contabilidad: `Generó asiento contable`. Inventario: `Agregó un ítem`, `Generó un ajuste de inventario`. Updated in `user-lifecycle-framework/SKILL.md`.
3. **Intercom → Mixpanel deep join**: v1 reports Intercom and Mixpanel side by side (same cohort, segmented). A future v2 could join at the email level to say "users who contacted support about X had Y% lower activation."

---

*Generated: 2026-03-07*
