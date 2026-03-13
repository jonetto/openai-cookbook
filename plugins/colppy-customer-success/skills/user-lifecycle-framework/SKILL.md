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
| **Lleva la contabilidad** | `Generó asiento contable` (primary), `Descargó el balance`, `Descargó el diario general`, `Agregó una cuenta contable` | True bookkeeping — journal entries, chart of accounts, financial reports |
| **Lleva inventario** | `Agregó un ítem` (primary), `Generó un ajuste de inventario`, `Actualizó precios en pantalla masivo` | Inventory-focused — item catalog, stock adjustments, price management |
| **Liquida sueldos** | `Liquidar sueldo` | Payroll processing — demonstrates real usage of the payroll module |
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

## Mixpanel Critical Events Reference

### Per-Persona Event Hierarchy

**Lleva la administración** — Lifecycle: `lifecycle_admin_comprasventa`

| Priority | Event Name | Signal |
|----------|-----------|--------|
| PRIMARY | `Generó comprobante de venta` | Core invoicing value event |
| PRIMARY | `Generó comprobante de compra` | Core purchasing value event |
| HIGH | `Generó recibo de cobro` | Payment receipt — active collections |
| HIGH | `Generó orden de pago` | Payment order — active payments |
| MEDIUM | `Descargó el libro iva ventas` | VAT compliance |
| MEDIUM | `Descargó el libro iva compras` | VAT compliance |

**Lleva la contabilidad** — Lifecycle: `lifecycle_contabilidad`

| Priority | Event Name | Signal |
|----------|-----------|--------|
| PRIMARY | `Generó asiento contable` | Core accounting entry (types: Diario, Cierre y Apertura, Ajuste por inflación, Refundición) |
| HIGH | `Descargó el balance` | Balance sheet — active reporting |
| HIGH | `Descargó el diario general` | General journal — active reporting |
| HIGH | `Descargó el estado de resultados` | P&L analysis |
| MEDIUM | `Descargó el estado de flujo de efectivo` | Advanced accounting |
| MEDIUM | `Agregó una cuenta contable` | Chart of accounts management |

**Lleva inventario** — Lifecycle: not yet implemented in Intercom

| Priority | Event Name | Signal |
|----------|-----------|--------|
| PRIMARY | `Agregó un ítem` | Item catalog management |
| PRIMARY | `Generó un ajuste de inventario` | Stock adjustment |
| HIGH | `Actualizó precios en pantalla masivo` | Bulk price update |

### Mixpanel Custom Composite Events

| Custom Event | Component Events | Persona |
|-------------|-----------------|---------|
| Eventos clave del usuario que lleva la administración | `Generó comprobante de compra` + `Generó comprobante de venta` | Lleva la administración |

> The contabilidad and inventario personas do not have pre-built Mixpanel custom composite events. Query their component events individually using `run_segmentation_query`.
