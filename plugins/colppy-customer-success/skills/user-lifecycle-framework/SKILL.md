---
name: user-lifecycle-framework
description: >
  Colppy's product lifecycle framework: behavioral personas, trial stages,
  activation thresholds, PQL definitions, and user lifecycle cuts (beginners,
  retained, resurrected, dormants). Source of truth for understanding how
  users move through the product. Apply when analyzing trial experience,
  activation, onboarding, retention, or behavioral segmentation.
---

# User Lifecycle Framework — Colppy

Encoded from Colppy's "Framework de Product Insights en Producto."
Source of truth for how users progress through the product lifecycle.

---

## Trial Window

| Parameter | Value |
|-----------|-------|
| Duration | 7 days free |
| Plan during trial | "Pendiente de Pago" (in Mixpanel events and Colppy DB) |
| Conversion signal | First payment (`primerPago=1` in Colppy) |
| Activation signal | `activo=true` + `fecha_activo` populated in HubSpot |

---

## Behavioral Personas

Determined by **product behavior** (Mixpanel events), NOT by wizard `rol_wizard` selection.
A user who selects "Contador" in the wizard but only does compra/venta is an **Operador**, not a true accountant.

| Persona | Critical Events (Mixpanel) | Description |
|---------|---------------------------|-------------|
| **Lleva la administración** | `Generó comprobante de compra`, `Generó comprobante de venta` | Core persona — invoicing, buying/selling. Most common. |
| **Lleva la contabilidad** | Accounting events (asientos contables, plan de cuentas) | True bookkeeping — journal entries, chart of accounts |
| **Lleva inventario** | Inventory events (stock movements, item management) | Inventory-focused usage |
| **Operador** | Same events as "Lleva la administración" BUT `contact_es_contador=true` AND operates across multiple client `id_empresa` values | Accountant behaving as administrator for their clients' companies |

### Wizard vs Reality Gap

The wizard captures *declared intent*. Mixpanel captures *actual behavior*. These frequently diverge:

| Wizard `rol_wizard` | Actual Behavior | Classification |
|---------------------|-----------------|----------------|
| Contador → operates client empresas | Admin events across multiple id_empresa | **Operador** (accountant-as-admin) |
| Contador → does contabilidad | Accounting events (asientos) | **Contador** (true accountant) |
| Pyme → does admin | Compra/venta events | **Pyme admin** (expected, aligned) |
| Pyme → barely uses product | Few/no critical events in 7-day trial | **At risk** — not activated |

---

## Trial Lifecycle Stages

| Stage | Signal | Source | Funnel Name |
|-------|--------|--------|-------------|
| **Evaluating** | Signed up + validated email | HubSpot `createdate` | MQL |
| **Activated** | Performed critical event during trial | Mixpanel + HubSpot `activo=true`, `fecha_activo` | PQL |
| **Converted** | First payment made | Colppy `primerPago=1` / HubSpot deal `hs_is_closed_won` | Customer |
| **Churned from trial** | 7 days passed, no payment | Absence of primerPago after trial window | — |

---

## Activation Threshold

**Default (from historical Mixpanel Signal report):** 4+ comprobantes de compra within 7 days correlates with week-2 retention.

**IMPORTANT:** This threshold needs periodic refresh. It can be validated by:
1. Mixpanel UI → Signal report (fast, manual)
2. API Method B: `run_retention_query` + `run_segmentation_query` to compute conversion rate at N=1,2,3,4,5,6+ events (automatable)

The threshold is a correlation, not causation. Use it as a health indicator, not a guarantee.

---

## User Lifecycle Cuts

From the lifecycle framework. These classify ALL active users, not just trial:

| Cut | Definition | Strategy |
|-----|-----------|----------|
| **Beginners (Nuevos)** | First time using the product in the period | First impression — critical window for activation |
| **Retained (Current)** | Consistent usage over time | Push toward power user; potential champions |
| **Resurrected (Revividos)** | Were active, went dormant, came back | Cheaper to reactivate than acquire new |
| **Dormants (Dormidos)** | Were active, now inactive | Understand pre-churn patterns |

---

## Health Metrics

| Metric | Formula | Source | Interpretation |
|--------|---------|--------|----------------|
| **Pulse** | (New + Resurrected) / Dormants | Mixpanel lifecycle | >1 = growing, <1 = shrinking |
| **Stickiness** | Days per month user performs critical event | Mixpanel | Higher = more engaged. Retained users typically 5-7pp above beginners |
| **PQL rate** | Activated / MQLs | HubSpot `activo` + `fecha_activo` | Target: >40% |
| **Trial conversion** | Converted / MQLs | HubSpot deals / Colppy primerPago | — |

---

## Mixpanel Custom Events Reference

| Custom Event | Component Events | Persona |
|-------------|-----------------|---------|
| Eventos clave del usuario que lleva la administración | Generó comprobante de compra + Generó comprobante de venta | Lleva la administración |
| (to be confirmed) | Accounting-specific events | Lleva la contabilidad |
| (to be confirmed) | Inventory-specific events | Lleva inventario |

**Note:** Exact Mixpanel event names for contabilidad and inventario personas need confirmation from the Mixpanel project. The administración events are confirmed.
