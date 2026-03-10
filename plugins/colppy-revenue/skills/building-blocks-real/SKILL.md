---
name: building-blocks-real
description: Monthly export of Building Blocks REAL metrics from Colppy DB — New Client MRR (Empresa vs Contador), script usage, classification rules, and Raw Data feed. Core workflow run every month. Trigger when the user asks about New Client MRR, Raw Data actuals, Empresa vs Contador, exporting for Building Blocks, or monthly REAL refresh.
---

# Building Blocks REAL — New Client MRR & Raw Data Export

## Trigger

User asks about:
- New Client MRR
- Raw Data actuals / Building Blocks REAL
- Empresa vs Contador export
- Monthly export for Building Blocks
- Feeding Raw Data tab
- New Client MRR Empresa / Contador

**This workflow is run every month.** Use this skill to run the export, explain classification, or troubleshoot.

---

## Full Mapping Doc

**Read:** `docs/BUILDING_BLOCKS_REAL_MAPPING.md` — where every REAL number comes from (Budget Aprobado, Raw Data -- Actuals), data flow, and all metric definitions.

---

## New Client MRR — Two-way classification

Output matches the **4 Building Blocks REAL rows** (Product × ICP):

| Item (REAL sheet) | Product line | ICP | Rule |
|-------------------|--------------|-----|------|
| New Product - Administración - ICP Pyme | Administración | Pyme | plan.nombre does **not** contain "Sueldos" AND facturacion.CUIT = empresa.CUIT |
| New Product - Administración - ICP Operador | Administración | Operador | plan.nombre does **not** contain "Sueldos" AND facturacion.CUIT ≠ empresa.CUIT |
| New Product - Sueldos - ICP Pyme | Sueldos | Pyme | plan.nombre contains "Sueldos" AND facturacion.CUIT = empresa.CUIT |
| New Product - Sueldos - ICP Operador | Sueldos | Operador | plan.nombre contains "Sueldos" AND facturacion.CUIT ≠ empresa.CUIT |

### How product line is determined

- **Sueldos:** `plan.nombre` contains `"Sueldos"` (case-insensitive). Colppy payroll product; matches HubSpot product_family "Sueldos (Payroll Processing)".
- **Administración:** Any other plan → Colppy accounting (Administración). Matches HubSpot "Colppy (Financial Management)".

### How ICP is determined (who we invoice)

- **ICP Pyme (Empresa):** `facturacion.CUIT = empresa.CUIT` — we invoice the SMB.
- **ICP Operador (Contador):** `facturacion.CUIT ≠ empresa.CUIT` — we invoice the accountant.

- **Source:** First payments only → `pago.primerPago = 1`
- **CUIT:** Normalized to 11 digits (no dashes) for comparison
- **Unknown:** No facturacion row or missing CUIT; included in total, reported separately

---

## Script — Export New Client MRR

**Path:** `tools/scripts/colppy/export_new_client_mrr.py` (workspace root = openai-cookbook)

### Prerequisite

**Refresh Colppy export DB** (if not already done for the target month):

```bash
python tools/scripts/colppy/export_colppy_to_sqlite.py --year YYYY --month M
```

Output: `tools/data/colppy_export.db`

### Monthly run

```bash
# Human-readable (default: current month)
python tools/scripts/colppy/export_new_client_mrr.py --month YYYY-MM

# Example: March 2026
python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03

# CSV for Raw Data import
python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03 --csv

# Custom date range
python tools/scripts/colppy/export_new_client_mrr.py --start 2026-03-01 --end 2026-03-31
```

### Output

- **Console:** Table with 4 rows (Administración/Sueldos × ICP Pyme/Operador), MRR (ARS), Count; optional Unknown row; Total.
- **CSV:** One row per month — `month, new_product_administracion_icp_pyme, new_product_administracion_icp_operador, new_product_sueldos_icp_pyme, new_product_sueldos_icp_operador, new_client_mrr_unknown, total, count`

---

## Raw Data Tab (Building Blocks)

- **Tab:** Raw Data -- Actuals (gid 947718476)
- **New Product MRR rows (REAL):** 4 rows — New Product Administración ICP Pyme, Administración ICP Operador, Sueldos ICP Pyme, Sueldos ICP Operador (columns = months).
- **Data flow:** Export CSV → paste or IMPORTRANGE into Raw Data → Budget Aprobado pulls via IMPORTRANGE

---

## Output Formatting

- Currency: `$` prefix, comma as decimal separator (Argentina)
- When showing results, include date range and record count

---

## Related

- **building-blocks-budget** — Budget vs Real dashboard, fetch tabs, deviation analysis
- **icp-classification** — HubSpot ICP Operador vs PYME (primary company type); Colppy Empresa/Contador is the DB equivalent for billing
- **docs-reference** — Points to BUILDING_BLOCKS_REAL_MAPPING.md for full REAL mapping
