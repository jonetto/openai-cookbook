---
name: trial-data-model
description: >
  Cross-system data model for trial user analysis: how to join Intercom
  conversations, Mixpanel product events, and HubSpot CRM data for the
  same user. Defines identity keys, what each system contributes, and
  available tools/scripts. Apply when analyzing trial users across
  multiple data sources.
---

# Trial Data Model — Cross-System Joins

How to connect a single user's experience across Intercom, Mixpanel, and HubSpot.

---

## Identity Levels

| Level | Key | Meaning | Example |
|-------|-----|---------|---------|
| **Person** | `email` | The human being | `maria@estudio.com` |
| **Subscription** | `id_empresa` | The company/plan they operate in | `500` (Maria's firm), `501` (her client) |

A single person (email) can have Mixpanel events across multiple `id_empresa` values — this is the **Operador** signal (accountant operating client companies).

---

## Identity Map

```
                    email (person)
    Intercom ◄──────────────────► HubSpot ◄──────► Mixpanel
  (conversations)                (contacts)      (distinct_id = email)
                                    │
                              id_empresa (subscription)
                                    │
                              Colppy DB ◄──────► Mixpanel
                            (billing, plans)   (id_empresa = super property
                                                on each event = which
                                                subscription the action
                                                was performed in)
```

---

## What Each System Contributes

| Question | Source | Tool / Method |
|----------|--------|---------------|
| What did the user struggle with? | **Intercom** | `scan_customer_feedback` or `scan_full_text` with `team_assignee_id: "2334166"` (Primeros 90 días) |
| What topics are trending? | **Intercom** | `analyze_onboarding.py --llm` or `llm_classify.mjs` with topic config |
| Is the user accountant or SMB? | **Intercom** `contact_es_contador` / **HubSpot** company `type` | Cached in Intercom export; fallback: HubSpot API by email |
| What did the user do in product? | **Mixpanel** | `run_segmentation_query` on critical events, filter by plan="Pendiente de Pago" |
| How far through the activation funnel? | **Mixpanel** | `run_funnels_query` (login → critical event → payment) |
| Did they activate (PQL)? | **HubSpot** | Contact: `activo=true` AND `fecha_activo` populated |
| Did they convert to paid? | **HubSpot** / **Colppy** | Deal `hs_is_closed_won=true` or Colppy `primerPago=1` |
| What behavioral persona? | **Mixpanel** | Event type distribution per distinct_id / id_empresa |
| What wizard role did they select? | **HubSpot** | Contact property `rol_wizard` |

---

## Tools Available

### Intercom (customer-success plugin MCP)

| Tool | Purpose | Speed |
|------|---------|-------|
| `scan_customer_feedback` | Scan first message by keywords + team inbox | Fast |
| `scan_full_text` | Scan all messages including agent replies | Slower — keep date ranges narrow (5-7 days) |
| `get_conversation_feedback` | Deep-dive specific conversation IDs | Per-conversation |
| `analyze_onboarding_first_invoice` | Segmented onboarding classification | Batch analysis |

### Mixpanel (Mixpanel MCP)

| Tool | Purpose |
|------|---------|
| `run_segmentation_query` | Event counts over time, breakdown by property |
| `run_funnels_query` | Multi-step conversion funnels |
| `run_retention_query` | Cohort retention (born_event → return_event) |

### HubSpot (HubSpot MCP)

| Tool | Purpose |
|------|---------|
| `search_crm_objects` | Search contacts/deals by filters |
| `get_crm_objects` | Fetch specific records by ID |

### Scripts (run via Bash)

| Script | Purpose |
|--------|---------|
| `tools/scripts/intercom/export_cache_for_local_scan.mjs` | Export Intercom conversations with contact attributes to local cache |
| `tools/scripts/intercom/analyze_onboarding.py` | Segmented onboarding analysis (--user-type smb/accountant --llm) |
| `plugins/colppy-customer-success/scripts/llm_classify.mjs` | LLM topic classification with few-shot learning |

---

## HubSpot Contact Properties for Trial Analysis

Always request these when querying trial contacts:

```
email, createdate, lifecyclestage, lead_source, rol_wizard,
activo, fecha_activo, hs_v2_date_entered_opportunity,
hs_v2_date_entered_customer, num_associated_deals
```

### Filtering Rules

- **Exclude invitations:** `lead_source HAS_PROPERTY` AND `lead_source NEQ "Usuario Invitado"` (both filters required — NEQ alone includes nulls)
- **Timezone:** HubSpot API returns UTC. Argentina is UTC-3. ~25 contacts at month boundaries may shift — acceptable.

---

## Intercom Cache Convention

Cached exports live in:
```
plugins/colppy-customer-success/skills/intercom-developer-api-research/cache/
  conversations_YYYY-MM-DD_YYYY-MM-DD_team2334166.json
```

Check for existing caches before making fresh API calls. If cache covers the requested period, use it.

---

## Segmentation Logic

| Segment | Signal | Source |
|---------|--------|--------|
| **SMB** | `contact_es_contador = false` or company type = "Cuenta Pyme" | Intercom export / HubSpot |
| **Accountant** | `contact_es_contador = true` or company type in ACCOUNTANT_COMPANY_TYPES | Intercom export / HubSpot |
| **Operador** (sub-segment of Accountant) | Accountant + admin events across multiple id_empresa | Mixpanel behavioral analysis |
