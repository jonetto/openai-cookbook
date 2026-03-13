---
name: mixpanel-analytics
description: Colppy's Mixpanel product analytics configuration including event tracking, user properties, PQL signals, and session recording analysis. Apply when discussing product usage, engagement metrics, PQL qualification, user behavior, or Mixpanel data.
---

# Mixpanel Analytics — Colppy

Colppy's product analytics setup in Mixpanel for tracking user behavior, engagement, and PQL signals.

---

## Key Concepts

- **PQL (Product Qualified Lead)**: Determined by product usage signals tracked in Mixpanel
- **Engagement Score**: Based on event frequency, feature adoption, session depth
- **Active Company**: Company with login events in the analysis period
- **id_empresa**: Links Mixpanel company data to HubSpot deals and Colppy database

---

## Dual-Group Data Model (KAN-12024, rolling out since 2026-03-11)

Colppy uses four Mixpanel assignment levels:

| Level | Key | What it identifies |
|-------|-----|-------------------|
| Device | `$device_id` | Pre-auth browser fingerprint |
| User | `distinct_id` (= email) | Individual user |
| Company | `company` group (= `CUITFacturacion`) | Billing entity (CUIT) |
| Product | `product_id` group (= `idEmpresa`) | Product subscription |

**The join key** between Mixpanel and the Colppy DB is `product_id` (or `company_id` in old events) = `empresa.IdEmpresa`.

### Old vs New Event Format

**Old events** (pre-KAN-12024, ~80% during rollout):
- `company_id` = idEmpresa, `company` = [idEmpresa]
- ~35 properties per Login event
- Company properties (CUIT, Estado, Plan) require `--enrich` via Engage API

**New events** (post-KAN-12024, ~20% as of Mar 12):
- `product_id` (array) = idEmpresa — the product subscription key
- `company_id` still = idEmpresa (unchanged as event property)
- **Super properties on events** (no Engage API needed):
  - `CUIT` (= `facturacion.CUIT`, billing entity — 95.3% validated)
  - `Razon Social`, `Nombre Plan`, `Plan` (idPlan), `Estado`, `Es Contador`
  - `Fecha Alta`, `Fecha Vencimiento`, `Condicion Iva`, `Es Demo`
  - `Rol`, `Mail Facturacion`, `Domicilio`
- ~98 properties per Login event

**Detect new events**: Check for `product_id` field presence.

**Validation script**: `tools/scripts/mixpanel/kan12024_health_check.py`

---

## Product Families

| Product | Description |
|---------|-------------|
| **Colppy** | Core SaaS accounting software |
| **Sueldos** | Payroll product (separate product family) |

---

## Integration Points

### HubSpot ↔ Mixpanel
- UTM fields synced via Mixpanel webhooks (uses existing HubSpot UTM fields, no custom fields)
- `id_empresa` links deals to Mixpanel company data
- PQL signals from Mixpanel feed into HubSpot scoring

### Key Mixpanel Scripts (tools/scripts/mixpanel/)
- 77 scripts covering events, properties, user analysis
- `mixpanel_api.py` — Core JQL API wrapper
- `get_company_stats.py` — Company event statistics
- `hubspot_mixpanel_integration.py` — Cross-platform analysis
- `export_active_companies_2025.py` — Active companies extraction

---

## MCP Tool Usage

### Segmentation Queries
Use `run_segmentation_query` for event analysis over time:
- unit: day, week, month
- where: filter expressions (e.g., `properties["country"] == "AR"`)
- on: property to group by

### Funnel Queries
Use `run_funnels_query` for conversion analysis:
- events: JSON array of funnel steps
- Supports per-step filters via `selector`
- count_type: "unique" (users) or "general" (events)

### Retention Queries
Use `run_retention_query` for cohort retention:
- born_event: initial event
- event: return event
- retention_type and unit

### Session Replays
Use `get_user_replays_data` for session analysis:
- By distinct_id with date range
- Or by specific replay_ids (up to 20)

---

## NPS to ICP Data Flow

- NPS surveys in Intercom link to Mixpanel user data
- `tipo_icp_contador` (Hibrido, Operador, Asesor) used for NPS segmentation
- This is separate from ICP Operador billing classification (which uses primary company type)
