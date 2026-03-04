# Intercom Lexicon — Colppy

> Generated from live Intercom MCP data · 2026-03-03
> Workspace ID: `j7l53tgt`

---

## Overview

This lexicon maps all known contact attributes, conversation topics, and conversation tags in Colppy's Intercom workspace. It is the equivalent of the Mixpanel Lexicon and is intended to be the reference for:

- Building Intercom Segments natively (without external integrations)
- Filtering conversations in the AI analysis plugin
- Designing Intercom Series automations for lifecycle attribution

---

## 1. Contact Attributes

### 1.1 Identity & Registration (set at signup, synced from platform)

| Attribute | Type | Values | Source | Notes |
|-----------|------|--------|--------|-------|
| `Es Contador` | Boolean | `true` / `false` | PHP registration (`AltaDelegate.php`) | Core persona signal. Set from 3 signals: explicit param, utm_campaign="contador", or wizard role. |
| `Es administrador` | Boolean | `true` / `false` | PHP registration | Whether user is account admin |
| `Tipo Usuario` | String | `"Pyme"` / `"Contador"` | Registration | Derived from `Es Contador`. Not always present on older contacts. |
| `Estado usuario` | String | `"Habilitado"` | Platform | Account status |
| `¿Cuál es tu rol? wizard` | String | Free text (e.g., `"Soy dueño/ administrativo de una empresa"`) | Wizard Step 2 | Raw wizard role. **NULL when user skips Step 2** (Omitir button). |

**Known wizard role values:**

- `"Dueño de un estudio contable"` → maps to `Es Contador = true`
- `"Contador de un estudio"` → maps to `Es Contador = true`
- `"Soy dueño/ administrativo de una empresa"` → maps to `Es Contador = false`
- (null) → user clicked "Omitir" in wizard

---

### 1.2 Lifecycle Attributes (synced from Mixpanel → Zapier → Intercom)

> ⚠️ **BROKEN — DO NOT RELY ON THESE FOR SEGMENTATION**
> The Zapier→Intercom lifecycle sync has 3 structural issues that make these attributes unreliable:
>
> 1. **Naming inconsistencies**: `lifecycle_recurrentes_contabilidad` vs `lifecycle_recurrentes__liquidar_sueldos` (double underscore)
> 2. **Value inconsistencies**: some attributes write `"add"`, others write `"add_members"` for the same semantic state
> 3. **Typo**: `lifecycle_recurrentes_liquidar_sueldo` (singular) coexists with `lifecycle_recurrentes__liquidar_sueldos` (plural, double underscore)

**Full inventory of lifecycle attributes found:**

| Attribute Key | Values Seen | Behavioral Type |
|--------------|-------------|----------------|
| `lifecycle_evaluadores_admin` | `"remove_members"` / null | Admin (compras/ventas) |
| `lifecycle_evaluadores_conta` | `"remove_members"` / null | Contabilidad |
| `lifecycle_evaluadores_liquidar_sueldos` | null | Sueldos |
| `lifecycle_beginners_liquidar_sueldos` | `"remove_members"` / null | Sueldos |
| `lifecycle_recurrentes_contabilidad` | `"add"` | Contabilidad *(note: uses "contabilidad" not "conta")* |
| `lifecycle_recurrentes_liquidar_sueldo` | null | Sueldos *(singular — likely a legacy typo)* |
| `lifecycle_recurrentes__liquidar_sueldos` | `"add_members"` | Sueldos *(double underscore — likely correct version)* |
| `lifecycle_dormidos_admin` | null | Admin |
| `lifecycle_dormidos_liquidar_sueldos` | `"remove_members"` / null | Sueldos |

**Inferred (not yet observed but expected by the pattern):**

- `lifecycle_beginners_admin`
- `lifecycle_beginners_conta`
- `lifecycle_recurrentes_admin`
- `lifecycle_dormidos_conta`

**Recommended fix**: Replace all 12+ fragmented attributes with **3 clean custom attributes** written by Intercom Series automations, one per behavioral type:

- `lifecycle_admin` — state: `"evaluador"` / `"beginner"` / `"retenido"` / `"dormido"` / `"revivido"`
- `lifecycle_contabilidad` — same state machine
- `lifecycle_sueldos` — same state machine (⚠️ blocked until value event is added to eSueldos platform)

See Section 4c for full OR-event groups per attribute.

---

### 1.3 Commercial & Scoring (synced from HubSpot via native integration)

| Attribute | Type | Values | Notes |
|-----------|------|--------|-------|
| `Fit Score Pyme Comercial` | Number | 0–100 | ICP fit for Pyme persona |
| `Fit Score Contador Comercial` | Number | 0–100 | ICP fit for Contador persona |
| `Lifecycle Stage` | String | `"Lead"` | HubSpot Lifecycle Stage (native HubSpot↔Intercom sync) |
| `Lead Status` | String | `"Nuevo Lead (Pipeline de leads)"` | HubSpot Lead Status |
| `hubspot_tracking_cookie` | String | UUID | HubSpot tracking cookie — confirms HubSpot↔Intercom sync is active |

---

### 1.4 Product Signals (bot interactions & behavioral flags)

| Attribute | Type | Values | Notes |
|-----------|------|--------|-------|
| `Pedido de desactivación` | String | `"yes"` | User requested deactivation |
| `Click Inventario` | String | `"yes"` | User clicked into inventory module |
| `Vende productos` | String | `"yes"` | Bot-captured: sells physical products |
| `Vende servicios` | String | `"yes"` | Bot-captured: sells services |
| `NPS Implementación puntaje - Bot` | Number | 0–10 | NPS score from implementation bot |
| `Puntaje` | Number | 0–10 | NPS score (general) |
| `Comentarios` | String | Free text | NPS open text |
| `NPS reporte unificado comentarios - Bot` | String | Free text | NPS comments from report bot |
| `Bot - Calificación Colppy com` | String | Free text | Qualification answer from website bot |
| `Bot - Calificación Pymes` | String | Free text | Pyme qualification bot answer |
| `Bot Primeros 30 días` | String | Free text | Onboarding bot response |
| `Bot - NPS Conciliación` | String | Free text | Conciliation NPS bot |
| `Bot - NPS App Mobile` | String | Free text | Mobile app NPS bot |
| `Bot - NPS Implementación` | String | Free text | Implementation NPS bot |

---

### 1.5 Cross-System IDs

| Attribute | Type | Notes |
|-----------|------|-------|
| `mixpanel_id` | String | Usually equals email. Present on older contacts. |
| `salesforce_id` | String | Legacy SF Contact ID **OR** (on newer contacts) last support topic text like `"Error al emitir factura Electrónica"` — field was repurposed, treat with caution. |
| `Categor_a_de_la_cuenta_de_contador__c` | String | Legacy SF field: `Small` / `Big` / `Hunting` / null. Only present on SF-migrated contacts. |

---

### 1.6 Contact Info (legacy bot capture)

| Attribute | Type | Notes |
|-----------|------|-------|
| `Teléfono Adicional` | String | Formatted phone number |
| `Tu Nombre` | String | Legacy — captured by old bot flow |
| `Teléfono` | String | Legacy phone |
| `Código de área` | String | Legacy area code |
| `ult4tarjeta` | String | Last 4 digits of payment card |

---

## 2. Conversation Topics (Native Intercom AI — no integration needed)

Topics are assigned **automatically by Intercom's own AI** based on conversation content. No external integration. Already active.

| Topic | Description |
|-------|-------------|
| `Facturación Electrónica` | AFIP/ARCA electronic invoicing issues |
| `Venta` | Sales invoices, client billing |
| `Compras` | Purchase invoices, vendor bills |
| `Contabilidad` | Accounting entries, asientos, balance |
| `Sueldos` | Payroll, liquidaciones, recibos |
| `Importación y carga masiva` | Bulk import flows, CSV uploads, TXT import |
| `Inventario` | Stock management, products |
| `Tesorería` | Treasury, cash flow, orden de pago, cartera |
| `Reporte` | Reports, exports, analytics |
| `Integración` | External integrations (ARCA, AFIP, banks) |
| `Configuraciones y prueba` | Account setup, onboarding, configuration |

> **Key insight**: Topics are the most reliable native signal in Intercom. They map directly to the behavioral persona dimension from the Framework de Producto (contabilidad, administración, inventario) — and they're already there.

---

## 3. Conversation Tags (Manual — applied by agents)

Tags are manually applied by the support team. Current inventory:

### Incident / System Tags

| Tag | Meaning |
|-----|---------|
| `Caída ARCA` | ARCA outage affecting invoicing |
| `factura electrónica - caída arca` | FE failure specifically due to ARCA downtime |
| `Producto caída ARCA` | Product-level ARCA outage report |
| `Cs - eSueldos - Error de Ingreso/ Plataforma caída` | eSueldos platform down |

### Workflow / Process Tags

| Tag | Meaning |
|-----|---------|
| `Chat-Bot` | Conversation came via chatbot |
| `Respuestas a comunicaciones` | Reply to a proactive outbound communication |
| `Mod Cli-Factura X` | Client modification request — Factura X |
| `CS - Pedido de Factura Colppy` | Request for Colppy's own invoice |
| `Consultas-No responden` | User not responding to follow-up |
| `Correos Internos` | Internal email thread (noise) |
| `Spam` | Spam (HubSpot notifications, etc.) |

---

## 4. Recommended Native Intercom Segmentation Strategy

### Replace broken lifecycle attributes with Intercom-native approach

Instead of Mixpanel→Zapier→Intercom (which breaks), use **Intercom Series + 3 clean custom attributes**, one per behavioral type. Users can hold different stages simultaneously across products.

```text
Custom attributes to create (Type: String):
  lifecycle_admin        → "evaluador" | "beginner" | "retenido" | "dormido" | "revivido"
  lifecycle_contabilidad → same state machine
  lifecycle_sueldos      → same state machine  (⚠️ blocked — see Section 4c)
```

**State machine per attribute (negotiated native approximation):**

```text
EVENT TRIGGER (any qualifying event fires — see OR groups in Section 4c):
  ├─ Event count = 1 (first time ever)
  │    → set attribute = "beginner"
  ├─ Event count ≥ 2 AND first_event_at > 30 days ago AND last_event_at < 30 days ago
  │    → set attribute = "retenido"     [~75% fidelity vs Mixpanel "2 consecutive windows"]
  └─ attribute was "dormido" AND event fires
       → set attribute = "revivido"

SCHEDULED TRIGGER (Intercom filter, runs weekly):
  └─ attribute = "retenido" AND last qualifying event > 60 days ago
       → set attribute = "dormido"
```

> **Fidelity note**: "retenido" in Mixpanel = "event in 2 consecutive 30-day windows". The native approximation uses `event_count ≥ 2 + first > 30d ago + last < 30d ago`, which captures ~75% of true Retenidos with ~10% false positives. This is the negotiated definition for Intercom-native computation.

### Segment the 3-Layer Framework natively

| Layer | Intercom Attribute | Already Available? |
|-------|-------------------|--------------------|
| WHO — Persona | `Es Contador = true/false` | ✅ Yes (via HubSpot↔Intercom) |
| WHERE — Lifecycle (Admin) | `lifecycle_admin` | ⚠️ Must create and populate via Series |
| WHERE — Lifecycle (Conta) | `lifecycle_contabilidad` | ⚠️ Must create and populate via Series |
| WHERE — Lifecycle (Sueldos) | `lifecycle_sueldos` | ❌ Blocked — missing value event |
| WHAT — Behavioral type | `Topics` (native AI classification) | ✅ Yes (Intercom's own AI) |
| WHAT — Problem tags | Conversation `Tags` | ⚠️ Partially — inconsistent, needs standardization |

### Segment examples (zero external integration)

```text
"Contadores in ARCA problems this week"
→ Es Contador = true
  AND Topic = "Facturación Electrónica"
  AND Tag contains "arca"

"Beginners in Admin who haven't done contabilidad yet"
→ lifecycle_admin = "beginner"
  AND lifecycle_contabilidad = "evaluador" (or null)

"Dormant Pymes with admin history + inventory interest"
→ Es Contador = false
  AND lifecycle_admin = "dormido"
  AND Click Inventario = "yes"

"Retenidos in contabilidad — high-value retention target"
→ lifecycle_contabilidad = "retenido"
```

---

## 4b. Events Tracked to Intercom (from Platform Codebase)

Events flow to Intercom via two mechanisms:

- **Server-side PHP**: `intercom_track_event($email, $eventName, $metadata)` in `functionsIntercom.php` — Intercom only
- **Client-side JS**: `colppyAnalytics(idEmpresa, type, eventName, properties, 'intercom')` → routes to BOTH `window.Intercom('trackEvent', ...)` AND `mixpanel.track(...)` — **dual-tracked**

> API: `GET /events?type=user&intercom_user_id={id}` — lists individual event records, **90-day limit** per official docs
> API: `GET /events/summaries` — returns all-time count, first_time, last_time per event (no 90-day limit)
> Segment UI filters use **summaries** (all-time), not the list endpoint. The 90-day limit affects only programmatic raw event listing.
> Submit: `POST /events` with `{ email, event_name, created_at, metadata }`

### Framework Critical Events — Confirmed Dual-Tracked (Mixpanel + Intercom)

These are the events defined as critical in the Framework de Producto that are confirmed to reach Intercom. These are the ONLY events that should be used to compute lifecycle state in Intercom Series:

| Event Name | Behavioral Type | Framework Role | Tracking Mechanism |
|---|---|---|---|
| `Generó comprobante de venta` | Admin (compras/ventas) | PRIMARY critical event | JS — colppyAnalytics (dual) |
| `Generó comprobante de compra` | Admin (compras/ventas) | PRIMARY critical event | JS — colppyAnalytics (dual) |
| `Generó asiento contable` | Contabilidad | PRIMARY critical event | JS — colppyAnalytics (dual) |
| `esueldos_autoregistro_exitoso` | Sueldos | Onboarding proxy only | Node.js — autoregistro-esueldos (dual) |
| *(missing)* | Sueldos | PRIMARY critical event — `Liquidó sueldos` | ❌ NOT YET TRACKED |

> All JS events via `colppyAnalytics(..., 'intercom')` are simultaneously sent to Mixpanel. PHP-only events (via `functionsIntercom.php` directly) are Intercom-only and may not have a Mixpanel counterpart.

---

### Registration & Session

| Event Name | Trigger | Metadata | Source |
|-----------|---------|----------|--------|
| `registro` | User completes main Colppy registration | None | PHP — AltaDelegate.php |
| `Registro` | User completes registration via MFE auth flow | — | mfe_authentication (JS) |
| `Validó email` | User validates their email address | — | mfe_authentication (JS) |
| `esueldos_autoregistro_exitoso` | User successfully auto-registers for eSueldos | `nombre`, `whatsapp`, `nombrePlan`, `origen: 'automatizacion_alta_sueldos'` | autoregistro-esueldos (Node.js) |
| `esueldos_autoregistro_fallido` | eSueldos auto-registration fails | Same as above | autoregistro-esueldos (Node.js) |
| `Visualizó inicio colppy` | User logs in / views dashboard | — | JS — colppyAnalytics |
| `Click en Empresa Demo` | User enters demo company | — | JS |
| `Modificó perfil` | User updates their profile | — | JS |

> **Note on `registro` vs `Registro`**: The lowercase `registro` is fired server-side from PHP on main platform signup. The capitalized `Registro` is fired client-side from the MFE authentication microfrontend — likely a duplicate signal for the same semantic event but from a different surface. Both should be treated as equivalent registration signals.

---

### Onboarding & Wizard (MFE)

| Event Name | Trigger | Metadata | Source |
|-----------|---------|----------|--------|
| `Finalizar Wizard` | Wizard Step 2 completed | — | mfe_onboarding |
| `Click en Atras Wizard` | User goes back in wizard | — | mfe_onboarding |
| `Click en completar datos` | User clicks to complete data | — | mfe_onboarding |
| `Agregó una empresa` | User adds a company | — | JS |
| `Invitó usuario` | User invites another user | — | JS |

---

### 🔑 Critical Events — Admin (compras/ventas) — LIFECYCLE SIGNAL

| Event Name | Trigger | Metadata | Source |
|-----------|---------|----------|--------|
| `Generó comprobante de venta` | Sales invoice generated | `amount`, `currency`, `tipo_factura`, `is_fe`, `type` | PHP (AltaDelegate + AfipProcesamiento) + JS |
| `Generó comprobante de compra` | Purchase invoice generated | — | JS — colppyAnalytics |
| `Imprimió comprobante de venta` | Invoice printed | — | JS |
| `Descargó el listado de comprobantes de venta` | Sales list exported | — | JS |
| `Descargó el listado de comprobantes de compra` | Purchase list exported | — | JS |
| `Descargó el libro iva ventas` | VAT sales book downloaded | — | JS |
| `Descargó el libro iva compras` | VAT purchase book downloaded | — | JS |
| `Generó recibo de cobro` | Payment receipt generated | — | JS |
| `Envió recibo de cobro` | Payment receipt sent | — | JS |
| `Generó un remito` | Delivery note generated | — | JS |
| `Imprimió orden de compra` | Purchase order printed | — | JS |

---

### 🔑 Critical Events — Contabilidad — LIFECYCLE SIGNAL

| Event Name | Trigger | Metadata | Source |
|-----------|---------|----------|--------|
| `Generó asiento contable` | Accounting entry created | `type`: "Asiento Diario" / "Asiento de Cierre y Apertura" / "Asiento de ajuste por inflación" / "Asiento de Refundición" | JS — colppyAnalytics |
| `Agregó una cuenta contable` | Chart of accounts updated | — | JS |
| `Descargó el diario general` | General journal downloaded | — | JS |
| `Descargó el balance` | Balance sheet downloaded | — | JS |
| `Descargó el estado de resultados` | Income statement downloaded | — | JS |
| `Descargó el estado de flujo de efectivo` | Cash flow downloaded | — | JS |
| `Descargó el resultado por centros de costo` | Cost center report downloaded | — | JS |
| `Descargó la posición impositiva mensual` | Tax position downloaded | — | JS |
| `Descargó el régimen de información de compras y ventas` | AFIP regime report | — | JS |
| `Seleccionó la opción asiento de refundición` | Refundición selected | — | JS |
| `Seleccionó la opción asiento de cierre y apertura` | Close/open entry selected | — | JS |
| `Seleccionó la opción asiento de ajuste por inflación` | Inflation adjustment selected | — | JS |

---

### ⚠️ Sueldos — LIFECYCLE GAP

| Event Name | Trigger | Notes |
| --- | --- | --- |
| `Click en sueldos` | Navigation click to sueldos module | ❌ Navigation only — NOT a value event |
| `esueldos_autoregistro_exitoso` | User activates eSueldos module | ✅ Onboarding — triggers `lifecycle_sueldos = "beginner"` (fires once) |
| `esueldos_autoregistro_fallido` | eSueldos activation fails | ⚠️ Failure signal — useful for support alerts, not lifecycle |

**Gap analysis**: The sueldos engine runs on `payroll.e-sueldos.com`. `esueldos_autoregistro_exitoso` can serve as the **beginner** trigger (user activated the module), but NO recurring value event exists to compute **retenido** or **dormido** states.

**Proposed fix** — add ONE call in the eSueldos platform at the liquidación completion step:

```javascript
// In the sueldos platform — after a payroll run completes
intercom_track_event(userEmail, 'Liquidó sueldos', {
  periodo: '2026-03',
  cantidad_empleados: 12
});
```

This single addition unblocks the entire `lifecycle_sueldos` state machine.

---

### Clients & Suppliers

| Event Name | Trigger |
|-----------|---------|
| `Agregó un cliente` | New client created |
| `Abrió el módulo clientes` | Client module opened |
| `Agregó un proveedor` | New supplier created |
| `Abrió el módulo proveedores` | Supplier module opened |

---

### Treasury & Payments

| Event Name | Trigger |
|-----------|---------|
| `Generó orden de pago` | Payment order generated |
| `Envió orden de pago` | Payment order sent |
| `Agregó medio de cobro` | Payment method added (receivable) |
| `Agregó medio de pago` | Payment method added (payable) |
| `Click en posición de cuenta de tesorería` | Treasury position viewed |
| `Descargó el reporte de seguimiento de cheques` | Check tracking report downloaded |

---

### Inventory

| Event Name | Trigger |
|-----------|---------|
| `Agregó un ítem` | Product/service item added |
| `Generó un ajuste de inventario` | Inventory adjustment made |
| `Activó impresión de remitos sin precios` | Remito setting toggled |
| `Agregó un talonario` | Invoice pad/book added |

---

### Upsell & Sales Signals

| Event Name | Metadata | Notes |
|-----------|----------|-------|
| `Visualizó ventana de upsell` | `from`: feature name | User saw upsell modal |
| `Click Upselling` | `from`: feature name | User clicked upsell CTA |
| `Quiero que me llamen` | — | Callback request |
| `Contactar a ventas plan contador` | — | Sales intent for Contador plan |

---

### Import / Bulk Load

| Event Name | Metadata |
|-----------|----------|
| `Subió archivo para importar` | `importer_type`: "Clientes" / "Facturas de Venta" / "Asientos" / "Precios" / "Items" / "Proveedores" / "Facturas de Compra" / "Extractos" |

---

### Vencimientos (separate MFE)

| Event Name | Trigger |
|-----------|---------|
| `Vencimientos - Página Vista` | Calendar page viewed |
| `Vencimientos - Exportar ICS` | Calendar exported to ICS |
| `Vencimientos - Importar a Google` | Calendar imported to Google |
| `Vencimientos - Item Seleccionado` | Due date item selected |
| `Vencimientos - Agregar Custom Click` | Custom item added |
| `Vencimientos - Suscripción Notificación` | Push notification enabled |
| `Vencimientos - Desuscripción Notificación` | Push notification disabled |
| `Vencimientos - Eliminar Custom` | Custom item deleted |
| `Notificaciones - Permiso Aceptado` | Browser notification permission granted |

---

### Dashboard First Steps (MFE)

| Event Name | Trigger |
|-----------|---------|
| `Click en comenzar primeros pasos` | User starts first steps guide |
| `Finalizó primeros pasos` | User completes all first steps |
| `Cerró primeros pasos` | User dismisses first steps |
| `Agregar factura de venta` | Empty state CTA clicked |
| `Agregar factura de compra` | Empty state CTA clicked |
| `Agregar Pago` | Empty state CTA clicked |
| `Conectar banco` | Empty state CTA clicked |
| `Agregar cliente` | Empty state CTA clicked |
| `Agregar producto/servicio` | Empty state CTA clicked |
| `Personalizar empresa` | Empty state CTA clicked |
| `Agregar asiento` | Empty state CTA clicked |
| `Conciliar cuentas` | Empty state CTA clicked |

---

### Mercado Pago (MFE)

| Event Name | Metadata | Trigger |
|-----------|----------|---------|
| `Click en generar facturas` | `from: 'Mercado pago'`, `total_rows_selected` | Invoice generation from MP |

---

### User Properties Updated via Intercom (not events)

These are `window.Intercom('update', {...})` calls that set user-level properties:

| Property | Values | Source |
|---------|--------|--------|
| `¿Cuándo querés implementar Colppy? wizard` | Free text from wizard | mfe_onboarding |
| `Tipo de actividad` | Activity selector value | mfe_onboarding |
| `Industria (colppy)` | Industry selector value | mfe_onboarding |
| `PRODUCT_TOUR_EXPERIMENT` | `'A'` / `'B'` | mfe_onboarding |

---

## 4c. Lifecycle Event Groups (OR Logic)

The lifecycle state machine for each attribute fires when **ANY** event in the group occurs — not just the single "critical" event. This makes the computation more inclusive and reduces false negatives.

Intercom Series trigger: `"User performs event"` → select all events from the group via OR conditions.

---

### lifecycle_admin — qualifying events (OR group)

Any of these events advances the `lifecycle_admin` state machine:

| Priority | Event Name | Signal Strength |
| --- | --- | --- |
| PRIMARY | `Generó comprobante de venta` | ★★★ Core admin value event |
| PRIMARY | `Generó comprobante de compra` | ★★★ Core admin value event |
| HIGH | `Generó recibo de cobro` | ★★ Accounts receivable management |
| HIGH | `Generó orden de pago` | ★★ Accounts payable management |
| HIGH | `Generó un remito` | ★★ Delivery / logistics activity |
| MEDIUM | `Descargó el libro iva ventas` | ★ VAT compliance activity |
| MEDIUM | `Descargó el libro iva compras` | ★ VAT compliance activity |
| MEDIUM | `Descargó el listado de comprobantes de venta` | ★ Active reporting on invoices |
| MEDIUM | `Descargó el listado de comprobantes de compra` | ★ Active reporting on purchases |

> Use all PRIMARY + HIGH events for the Series trigger. Add MEDIUM events if you want maximum recall.

---

### lifecycle_contabilidad — qualifying events (OR group)

Any of these events advances the `lifecycle_contabilidad` state machine:

| Priority | Event Name | Signal Strength |
| --- | --- | --- |
| PRIMARY | `Generó asiento contable` | ★★★ Core contabilidad value event |
| HIGH | `Descargó el balance` | ★★ Active use of accounting reports |
| HIGH | `Descargó el diario general` | ★★ Active use of accounting reports |
| HIGH | `Descargó el estado de resultados` | ★★ P&L analysis |
| HIGH | `Descargó la posición impositiva mensual` | ★★ Tax compliance activity |
| MEDIUM | `Descargó el estado de flujo de efectivo` | ★ Advanced accounting usage |
| MEDIUM | `Descargó el resultado por centros de costo` | ★ Advanced accounting usage |
| MEDIUM | `Descargó el régimen de información de compras y ventas` | ★ AFIP compliance |
| MEDIUM | `Agregó una cuenta contable` | ★ Chart of accounts management |

> Start with PRIMARY + HIGH for the Series trigger. The MEDIUM events can expand the group once the core pipeline is validated.

---

### lifecycle_sueldos — qualifying events (OR group)

| Priority | Event Name | Signal Strength | Status |
| --- | --- | --- | --- |
| ONBOARDING | `esueldos_autoregistro_exitoso` | ★ Module activation (fires once — use for `beginner` only) | ✅ Live |
| PRIMARY | `Liquidó sueldos` | ★★★ Core sueldos value event | ❌ Not yet tracked |

**Current capability**:

- `beginner`: fire on `esueldos_autoregistro_exitoso` (partial — module activation as proxy)
- `retenido` / `dormido` / `revivido`: **BLOCKED** until `Liquidó sueldos` is added

**Implementation path**: One `intercom_track_event()` call in the eSueldos platform at liquidación completion unblocks the full state machine. See Sueldos section above for the exact proposed call.

---

### Summary: Intercom Series needed

| Series Name | Trigger Events | Attribute Written | Status |
| --- | --- | --- | --- |
| Lifecycle Admin — Beginner | Any admin OR event (first time) | `lifecycle_admin = "beginner"` | ✅ Ready to build |
| Lifecycle Admin — Retenido | Any admin OR event (count ≥ 2, cadence met) | `lifecycle_admin = "retenido"` | ✅ Ready to build |
| Lifecycle Admin — Dormido | Scheduled: no admin event for 60d | `lifecycle_admin = "dormido"` | ✅ Ready to build |
| Lifecycle Admin — Revivido | Admin event after dormido state | `lifecycle_admin = "revivido"` | ✅ Ready to build |
| Lifecycle Conta — (same set) | Any contabilidad OR event | `lifecycle_contabilidad = *` | ✅ Ready to build |
| Lifecycle Sueldos — Beginner | `esueldos_autoregistro_exitoso` | `lifecycle_sueldos = "beginner"` | ✅ Partial |
| Lifecycle Sueldos — Retenido+ | `Liquidó sueldos` | `lifecycle_sueldos = "retenido"` | ❌ Blocked |

---

## 5. Data Quality Notes

| Issue | Impact | Recommendation |
| --- | --- | --- |
| `lifecycle_*` attributes — naming + value inconsistencies | Cannot segment by lifecycle reliably | Replace with 3 clean attributes via Series (see Section 4c) |
| `¿Cuál es tu rol? wizard` — null on ~40% of users | Can't derive behavioral type from wizard | Use Topics instead as behavioral proxy |
| `salesforce_id` — repurposed field | Unreliable for SF lookups | Don't use as SF reference |
| `Tipo Usuario` — missing on older contacts | Inconsistent persona attribute | Fall back to `Es Contador` which has better coverage |
| `mixpanel_id` — only on pre-2024 contacts | Can't join to Mixpanel for old contacts | Use email as join key instead |

---

Last updated: 2026-03-03 — generated from live MCP query of workspace j7l53tgt
