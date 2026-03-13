# Onboarding Pulse Baseline

**Established**: 2026-03-13
**Period measured**: 2026-03-01 to 2026-03-13 (March MTD)
**Primary data source**: Mixpanel (product behavior — source of truth for the product flywheel)
**Secondary data source**: HubSpot (acquisition volume, channel attribution)

---

## Table 1: Product Funnel (Mixpanel)

28 true trial companies (pendiente_pago, Fecha Alta within 7 days of period start).

| Stage | Companies | Rate |
|-------|-----------|------|
| Trial company created | 28 | 100% |
| Logged in | 28 | 100% |
| First critical event | 13 | 46.4% |
| Login → no critical event (silent churners) | 15 | 53.6% |

### Activation Event Breakdown

| Event | Companies | Persona |
|-------|-----------|---------|
| Agregó un ítem | 7 | Inventario |
| Generó comprobante de compra | 5 | Admin |
| Generó comprobante de venta | 5 | Admin |
| Generó orden de pago | 2 | Admin |
| Generó recibo de cobro | 2 | Admin |
| Descargó el diario general | 1 | Contabilidad |
| Generó asiento contable | 0 | Contabilidad |
| Descargó el balance | 0 | Contabilidad |
| Descargó el estado de resultados | 0 | Contabilidad |
| Generó un ajuste de inventario | 0 | Inventario |
| Actualizó precios en pantalla masivo | 0 | Inventario |
| Liquidar sueldo | 0 | Sueldos |

### Top Activated Companies (March MTD)

| Company ID | Critical Events | Name | Fecha Alta |
|-----------|----------------|------|------------|
| 117768 | 178 | BOSSFITNESS | 2026-03-03 |
| 117951 | 21 | SU ALIMENTACION CATERING S.A. | 2026-03-04 |
| 118212 | 21 | SURVEY S.R.L. | — |
| 118143 | 4 | — | — |
| 117953 | 4 | BRECTON CENTRAL BS AS S.A. | 2026-03-04 |
| 118123 | 3 | — | 2026-03-09 |
| 118159 | 2 | — | — |
| 118209 | 2 | — | — |
| 117834 | 1 | FUNDACION OBSERVATORIO PYME | 2026-03-03 |

---

## Table 2: Activation Quality

| Metric | Value |
|--------|-------|
| Activation rate | 46.4% (13 of 28) |
| Silent churner rate | 53.6% (15 of 28) |
| Top activation event | Agregó un ítem (7 companies, 25%) |
| Second activation event | Generó comprobante de venta/compra (5 each, 17.9%) |
| Median hours to first event | Not measured (requires raw event timestamps) |

---

## Table 3: Alerts

| Alert | Status | Detail |
|-------|--------|--------|
| Silent churner rate > 50% | **WARNING** | 53.6% — slightly above threshold. 15 of 28 companies logged in but did nothing. |
| Registro/Validó email tracking gap | **WARNING** | Only 2/1 companies fired these events. Pre-login funnel unmeasurable. |
| Small sample size | **INFO** | 28 companies in 13 days. Trends need 2+ weeks to be meaningful. |

---

## Table 4: Acquisition Context (HubSpot)

HubSpot registered 5,042 contacts in 4 weeks (Feb 12 - Mar 12). Mixpanel shows only 154 true trial companies in the same period. The 5,042 → 154 gap is an acquisition quality problem (primarily PMax junk traffic), not a product problem.

| Channel | Registrations | PQL Rate | Notes |
|---------|--------------|----------|-------|
| Google Ads | 4,493 (89%) | 0.2% | PMax dominates volume, near-zero quality |
| Organic/Direct | 466 (9%) | 0.4% | — |
| Organic Search | 30 (0.6%) | 6.7% | 33x better PQL rate than Google Ads |
| Other channels | 53 (1%) | 1.9% | — |

---

## Scope Separation

| Responsibility | Measured in | Owner |
|---------------|-------------|-------|
| Product flywheel (Login → activation → value) | Mixpanel | Growth PM |
| Acquisition quality (registration → reach product) | HubSpot vs Mixpanel gap | Marketing / RevOps |
| Sales conversion (score 40+ → deal) | HubSpot | Sales team (2 closers) |
| Accountant relationship (Fidelización → pipeline) | HubSpot | Customer team |

---

## Measurement Methodology

### Product funnel (Mixpanel)

```bash
python tools/scripts/mixpanel/export_trial_events.py \
    --from {start} --to {end} --level company --enrich --trial-window 7
```

- **Denominator**: Companies from Mixpanel group profiles with `Fecha Alta` in period and `Tipo Plan = pendiente_pago`
- **`--trial-window 7`**: Filters out zombie pendiente_pago accounts (companies created years ago that never converted but are still technically on the trial plan)
- **Activated**: ≥1 PRIMARY or HIGH critical event from the user lifecycle framework
- **Silent churner**: Login event fired, 0 critical events within trial window

### Known tracking gaps

- `Registro` event: Only fires for ~10-15% of companies. Cannot measure registration → email validation funnel.
- `Validó email` event: Even lower coverage (~5%). Until this is fixed, the funnel starts at `Login`.
- These are tracking instrumentation issues, not product issues. They should be filed as bugs.

### Acquisition context (HubSpot)

```bash
python tools/scripts/hubspot/onboarding_pulse_baseline.py \
    --from-date {start} --to-date {end}
```

- Used for channel breakdown (UTM attribution) and two-path classification (fit_score, owner)
- NOT used as funnel denominator — HubSpot contact count includes junk registrations that never reach the product

---

## Data Source Files

- Mixpanel March MTD: `plugins/colppy-customer-success/skills/trial-data-model/cache/mixpanel_events_2026-03-01_2026-03-13_pendiente_pago_by-company_trial7d.json`
- Mixpanel 4-week: `plugins/colppy-customer-success/skills/trial-data-model/cache/mixpanel_events_2026-02-12_2026-03-12_pendiente_pago_by-company_trial7d.json`
- HubSpot 4-week: `plugins/colppy-product/data/onboarding_pulse_baseline_20260212_20260312.json`

---

## Update Policy

- Update **weekly** when running the pulse
- Update baseline numbers **quarterly** or when a major product change ships
- Compare each weekly run against the March MTD baseline above
