# Onboarding Pulse — Pre-Change Baseline

**Period**: 2026-02-13 to 2026-03-13
**Model**: Old (pre-restructuring) — all leads could receive sales attention regardless of score
**Cutoff**: 2026-03-13 (sales restructuring → two-cohort model begins)

## Context

This baseline was captured BEFORE the two-cohort model existed. It reflects a world where any lead could get human attention. Use it as the "before" comparison for the no-touch PLG path that starts 2026-03-13.

## Table 1: Macro Funnel (HubSpot — 4,642 contacts)

| Stage | No-Touch (<40) | High-Touch (≥40) | Total |
| --- | --- | --- | --- |
| Registered | 4,522 (100%) | 120 (100%) | 4,642 (100%) |
| Wizard completed | 4,345 (96.1%) | 75 (62.5%) | 4,420 (95.2%) |
| PQL (`activo=true`) | 0 (0.0%) | 11 (9.2%) | 11 (0.2%) |
| Converted | 13 (0.3%) | 18 (15.0%) | 31 (0.7%) |

Note: the cohort classification here is retroactive (applied using current scoring rules to historical contacts). Under the old model, there was no formal split.

**PQL discrepancy**: Mixpanel shows 20 companies with ≥1 critical event, but HubSpot `activo=true` only shows 11. Either `activo` requires more than a single critical event to trigger, or there's a sync delay. PQL definition going forward = ≥1 critical event within 7 days (Mixpanel), not the `activo` flag alone.

## Table 2: Product Funnel (Mixpanel — 154 companies after zombie filter)

| Stage | Companies | % |
| --- | --- | --- |
| Appeared in Mixpanel (Login) | 154 | 100% |
| Did any critical event | 20 | 13.0% |
| Silent churners (login, 0 critical events) | 134 | 87.0% |

## Table 3: Critical Event Distribution

| Event | Count | Note |
| --- | --- | --- |
| Generó comprobante de compra | 193 | Most fired |
| Agregó un ítem | 122 | Most predictive (0.831 Opp Score) |
| Generó comprobante de venta | 92 | |
| Generó orden de pago | 71 | |
| Generó asiento contable | 65 | |
| Agregó una cuenta contable | 50 | |
| Generó recibo de cobro | 43 | |
| Descargó el diario general | 6 | |
| Descargó el balance | 3 | |
| Generó un ajuste de inventario | 1 | |
| Actualizó precios en pantalla masivo | 1 | |

## Table 4: Channel Mix (HubSpot)

| Channel | Registered | PQL | PQL% | No-Touch% |
| --- | --- | --- | --- | --- |
| Google Ads | 4,130 | 6 | 0.1% | 98.7% |
| Organic/Direct | 437 | 2 | 0.5% | 87.9% |
| Organic Search | 26 | 2 | 7.7% | 76.9% |
| Direct | 18 | 1 | 5.6% | 66.7% |
| Other | 23 | 0 | 0.0% | 95.7% |
| LinkedIn Ads | 7 | 0 | 0.0% | 85.7% |
| Colppy Portal | 1 | 0 | 0.0% | 100.0% |

## Key Gaps Identified

1. **HubSpot vs Mixpanel gap**: 4,642 registered → 154 companies in Mixpanel = ~96% never reach the product. Dominated by Google Ads PMax (4,130 registrations, 0.1% PQL rate).
2. **0 PQLs on no-touch path**: The `activo` flag is set directly by the product (not by sales or HubSpot). Zero PQLs means the product literally did not activate a single no-touch lead in 4 weeks. The 20 activations seen in Mixpanel critical events may correspond to sales-touched contacts, or there's a gap between "did a critical event" and "product set activo=true". Either way, this is the core PLG failure metric.
3. **87% silent churner rate**: Core PLG problem — 134 of 154 companies that logged in never performed a single critical event.
4. **Registro/Validó email tracking gap**: Only 5 and 4 companies respectively had these events in Mixpanel — pre-Login funnel cannot be measured from Mixpanel today.

## Data Sources

- HubSpot: `tools/scripts/hubspot/onboarding_pulse_baseline.py --weeks 4`
- Mixpanel: `tools/scripts/mixpanel/export_trial_events.py --from 2026-02-13 --to 2026-03-13 --level company --trial-window 7`
- Cache: `plugins/colppy-customer-success/skills/trial-data-model/cache/mixpanel_events_2026-02-13_2026-03-13_pendiente_pago_by-company_trial7d.json`
