# Building Blocks — REAL / Actuals Mapping

**Purpose:** Document where each REAL (actual) number comes from and how it is calculated. Use when onboarding, debugging discrepancies, or automating data refresh.

**Spreadsheet:** [Building Blocks Colppy Budget Q4-2025 + FY2026](https://docs.google.com/spreadsheets/d/1vouNcGMeNbpWW6znS8SZZdjUvG6ZzUIq_rh0zr4mJlY/edit)

**Last Updated:** 2026-03-08

---

## 1. Tab Overview

| Tab | Registry ID | GID | Role |
|-----|-------------|-----|------|
| Budget Aprobado | colppy_budget_aprobado | 1060880412 | Consolidated KPIs, Units Economics, P&L (actuals) |
| Raw Data -- Actuals | colppy_raw_actuals | 947718476 | Source of truth for MRR components (New, Upsell, Cross Sell, Churn, Discounts) |

**Data flow:** Both Raw Data and Budget Aprobado use **IMPORTRANGE** from their upstream sources. When the source is updated, downstream tabs refresh automatically.

---

## 2. Budget Aprobado (gid 1060880412)

**URL:** `.../edit?gid=1060880412`

### 2.1 Sections

| Section | Rows (approx) | Content | Source |
|---------|---------------|---------|--------|
| New Per Budget Aprobado | 1 | Title | — |
| KPIs (ARS) | 2–16 | Net ASP, Direct Cost, Gross Margin, CAC, Churn %, LTV, NRR | IMPORTRANGE from Raw Data |
| Clients (#) | 18–24 | BoP, New, Churn, EoP, Net New Clients | IMPORTRANGE from Raw Data |
| Reps Performance | 26–32 | Total Sales Reps, Ramping, Ramped, AVG PPR | IMPORTRANGE from Raw Data |
| Units Economics (ARS k) | 34–54 | BoP MRR, New, New Clients, Upsells, Cross-selling, Price Movements, Expired Discounts, Churn, EoP MRR, Net New, Growth %, EBITDA | IMPORTRANGE from Raw Data |
| P&L (ARS k) | 56–85 | Revenues, Direct Costs, Platform, Support, Gross Margin, OpEx, EBITDA | IMPORTRANGE from Raw Data |

### 2.2 Units Economics — Metric Mapping

| Metric | Definition | Source | Calculation |
|--------|------------|--------|-------------|
| BoP MRR | Beginning of Period MRR | IMPORTRANGE from Raw Data | Raw Data |
| New | New MRR (total from new clients) | IMPORTRANGE from Raw Data | Raw Data "New Total" |
| New Clients | MRR from new clients only | IMPORTRANGE from Raw Data | Raw Data "New Clients" |
| Upsells | Upsell MRR | IMPORTRANGE from Raw Data | Raw Data "Upsell" |
| Cross-selling | Cross-sell MRR | IMPORTRANGE from Raw Data | Raw Data "Cross Sell" |
| Price Movements | Price increase impact | IMPORTRANGE from Raw Data | Raw Data "Price Increase" |
| Expired Discounts | MRR recovered when discounts expire | IMPORTRANGE from Raw Data | Raw Data (manual input; backoffice exists) |
| Churn | Lost MRR (churned customers) | IMPORTRANGE from Raw Data | Raw Data "Churn Total" (from facturacion.fechaBaja) |
| EoP MRR | End of Period MRR | IMPORTRANGE from Raw Data | BoP + New − Churn + adjustments |
| Net New | Net new MRR (New − Churn + adjustments) | IMPORTRANGE from Raw Data | Raw Data |
| Growth (MRR) | Month-over-month MRR growth % | Formula | (EoP − BoP) / BoP × 100 |
| % EBITDA | EBITDA margin | Formula | EBITDA / Revenues × 100 |

### 2.3 KPIs — Metric Mapping

| Metric | Definition | Source | Calculation |
|--------|------------|--------|-------------|
| Net ASP New Client | Average ticket (net) for new clients | IMPORTRANGE from Raw Data | Raw Data "Net ASP (New Clients)" |
| Direct Cost Client | Cost per client | IMPORTRANGE from Raw Data | Raw Data |
| Gross Margin | Gross margin per client | IMPORTRANGE from Raw Data | Raw Data |
| CAC x Client | Customer acquisition cost per client | IMPORTRANGE from Raw Data | Total CAC / New Clients |
| Total CAC | Total acquisition spend | IMPORTRANGE from Raw Data | Raw Data |
| New Clients (#) | Count of new clients | IMPORTRANGE from Raw Data | Raw Data "# New Clients" |
| Net Churn % | Net churn rate | IMPORTRANGE from Raw Data | Raw Data |
| Gross Churn % | Gross churn rate | IMPORTRANGE from Raw Data | Raw Data |
| Customer Lifetime | Months | IMPORTRANGE from Raw Data | 1 / Net Churn % |
| LTV (DR 15%) | Lifetime value (discount rate 15%) | Formula | IMPORTRANGE from Raw Data |
| NRR | Net Revenue Retention | Formula | IMPORTRANGE from Raw Data |

---

## 3. Raw Data -- Actuals (gid 947718476)

**URL:** `.../edit?gid=947718476`

### 3.1 Sections

| Section | Rows (approx) | Content | Source |
|---------|---------------|---------|--------|
| Top KPIs | 2–19 | Gross/Net ASP, Direct Cost, CAC, # New Clients, Churn %, LTV, rCAC | Colppy DB / IMPORTRANGE |
| New Client MRR | 24–26 | New Client MRR Empresa, New Client MRR Contador, Total | Colppy DB (pago primerPago=1); scripts exist in plugins |
| Costs / CAC | 30–36 | Direct Costs, CAC (ARS, USD), New Clients, Total Clients | Colppy DB / IMPORTRANGE |
| Churn & Upsell | 39–51 | Total Churn, Upsell, Upsell MRR Empresa/Contador, Cross Sell, Net Churn | Colppy DB (churn: facturacion.fechaBaja; upsell: month-over-month amount delta for same id_empresa) |
| BoP / EoP | 48–50, 77–85 | BoP MRR, New from New Clients, Upsell, EoP | Colppy facturacion |
| Expired Discounts | 54–56 | Expired MRR Contador, Expired MRR Empresa, Total | **Manual** (backoffice exists; no access) |
| Discounts | 58–70 | New Client Discounts, Upsell Discounts, Others (Contador, Empresa) | Colppy / manual |
| En ARS (Nominal) | 76–85 | BoP, New Total, New Clients, Upsell, Price Increase, Expired Discounts, Churn Total, EoP | Formulas from above |
| En ARS (DI) | 93–100 | Same metrics, inflation-adjusted (Factor DI) | Formula | Nominal × Factor DI (Factor DI updated automatically) |

### 3.2 Metric Definitions (Raw Data)

| Metric | Definition | Source | Calculation |
|--------|------------|--------|--------------|
| New Client MRR Empresa | MRR from new SMB (PyME) clients | Colppy DB (pago) | First payment (`primerPago = 1`), facturacion.CUIT = empresa.CUIT (we invoice the company) |
| New Client MRR Contador | MRR from new accountant clients | Colppy DB (pago) | First payment (`primerPago = 1`), facturacion.CUIT ≠ empresa.CUIT (we invoice the accountant) |
| Total New Client MRR | Sum of Empresa + Contador | Formula | Empresa + Contador |

**Building Blocks REAL uses 4 rows (Product × ICP):** New Product Administración ICP Pyme, Administración ICP Operador, Sueldos ICP Pyme, Sueldos ICP Operador. Product line: `plan.nombre` contains "Sueldos" → Sueldos; else → Administración. Script: `export_new_client_mrr.py` outputs all 4.
| Upsell MRR Empresa | Upsell MRR from SMB clients | Colppy facturacion | **Month-over-month delta:** same `id_empresa`, compare `amount` between months; positive delta = upsell |
| Upsell MRR Contador | Upsell MRR from accountant clients | Colppy facturacion | Same logic: amount delta for same id_empresa |
| Cross Sell MRR | Cross-sell MRR (add-on products) | Colppy facturacion | Same id_empresa, new product line |
| BoP MRR | Beginning of Period MRR | Colppy facturacion | Sum(amount) at start of month |
| EoP MRR | End of Period MRR | Colppy facturacion | Sum(amount) at end of month |
| Total Churn | Gross churn (lost MRR) | Colppy facturacion | `fechaBaja` in period; sum(amount) of churned id_empresa |
| Net Churn | Net churn | Colppy facturacion | *[TBD: formula]* |
| Expired Discounts | MRR from expired discount promotions | **Manual** | Backoffice exists; user has no access. Entered manually in Raw Data. |
| Discounts (New/Upsell/Others) | Discounts applied | Colppy / manual | *[TBD]* |
| Factor DI | Inflation adjustment factor | **Automatic** | Updated automatically; all up to date |

### 3.3 Colppy Data Sources

| Colppy Source | Tables / Fields | Use For |
|---------------|-----------------|---------|
| facturacion | IdEmpresa, CUIT, amount, fechaAlta, fechaBaja | Active MRR, BoP, EoP, **Churn** (fechaBaja) |
| pago | primerPago, id_empresa, amount | **New Client MRR** (first payment; primerPago = 1) |
| plan | nombre, precio | Plan changes, upsell detection |
| empresa | CUIT, idPlan | Product line, ICP (Empresa vs Contador) |

**Upsell detection:** Compare `amount` for same `id_empresa` month-over-month; positive delta = upsell.

**Scripts:** `export_colppy_to_sqlite.py`, `reconcile_facturacion_colppy.py`, **`export_new_client_mrr.py`**. See [FIRST_PAYMENT_ENTRY_POINTS.md](../../tools/docs/FIRST_PAYMENT_ENTRY_POINTS.md).

**New Client MRR export:**
```bash
# Refresh colppy_export.db first (if needed)
python tools/scripts/colppy/export_colppy_to_sqlite.py --year 2026 --month 3

# Export New Client MRR for a month
python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03

# CSV output for Raw Data import
python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03 --csv
```

---

## 4. Data Flow Diagram

```
┌─────────────────────┐
│ Colppy MySQL        │
│ (facturacion, pago, │
│  empresa, plan)     │
└──────────┬──────────┘
           │ Export / Script (New Client MRR scripts in plugins)
           ▼
┌─────────────────────┐
│ Raw Data --         │
│ Actuals (gid        │
│ 947718476)          │
│                     │
│ • New Client MRR    │  ← pago (primerPago=1); scripts exist
│ • Upsell            │  ← month-over-month amount delta, same id_empresa
│ • Churn             │  ← facturacion.fechaBaja
│ • Expired Discounts │  ← Manual (backoffice)
│ • Factor DI         │  ← Automatic
└──────────┬──────────┘
           │ IMPORTRANGE (auto-updates when source changes)
           ▼
┌─────────────────────┐     ┌─────────────────────┐
│ Budget Aprobado     │     │ Building Blocks Por  │
│ (gid 1060880412)    │     │ Producto (colppy_   │
│ IMPORTRANGE from    │     │ budget)             │
│ Raw Data            │     │ • REAL section      │
└─────────────────────┘     └─────────────────────┘
           │                            │
           └────────────┬───────────────┘
                        │
                        ▼
              ┌─────────────────────┐
              │ Budget Dashboard    │
              │ (refresh_budget_     │
              │  dashboard.py)      │
              │ Uses: colppy_budget,│
              │ asp_forecast_2026   │
              └─────────────────────┘
```

---

## 5. Resolved Questions

| # | Question | Answer |
|---|----------|--------|
| 1 | How is Raw Data populated? | **IMPORTRANGE** from upstream source. Auto-updates when source changes. |
| 2 | Does Budget Aprobado pull from Raw Data? | **IMPORTRANGE**. All up to date. |
| 3 | New Client MRR source? | Colppy DB (`pago` with `primerPago = 1`). **Scripts exist in plugins** to generate from DB. |
| 4 | Upsell detection? | **Month-over-month delta:** same `id_empresa`, compare `amount`; positive delta = upsell. |
| 5 | Churn source? | **facturacion.fechaBaja** |
| 6 | Expired Discounts? | **Manual.** Backoffice exists; user has no access. |
| 7 | Factor DI (inflation)? | **Automatic.** All updated. |

---

## 6. Related Docs

- [BUILDING_BLOCKS_BUDGET_GUIDE.md](./BUILDING_BLOCKS_BUDGET_GUIDE.md) — Fetch, parse, dashboard
- [GOOGLE_SHEETS_REGISTRY.json](../../tools/docs/GOOGLE_SHEETS_REGISTRY.json) — Tab IDs, gids
- [FIRST_PAYMENT_ENTRY_POINTS.md](../../tools/docs/FIRST_PAYMENT_ENTRY_POINTS.md) — Colppy payment flow
- [FACTURACION_COLPPY_RECONCILIATION.md](../../tools/docs/FACTURACION_COLPPY_RECONCILIATION.md) — Billing reconciliation
