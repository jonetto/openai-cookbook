#!/usr/bin/env python3
"""
Export New Client MRR (Empresa vs Contador × Administración vs Sueldos) from Colppy DB
======================================================================================
Generates New Client MRR in the 4 Building Blocks REAL rows:
  New Product - Administración - ICP Pyme
  New Product - Administración - ICP Operador
  New Product - Sueldos - ICP Pyme
  New Product - Sueldos - ICP Operador

Logic (from BUILDING_BLOCKS_REAL_MAPPING.md):
- New Client MRR = first payments (pago.primerPago = 1)
- ICP Pyme (Empresa) = we invoice the SMB (facturacion.CUIT = empresa.CUIT)
- ICP Operador (Contador) = we invoice the accountant (facturacion.CUIT != empresa.CUIT)
- Product line: plan.nombre contains "Sueldos" (case-insensitive) → Sueldos; else → Administración

Uses colppy_export.db.

Usage:
  python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03
  python tools/scripts/colppy/export_new_client_mrr.py --month 2026-03 --csv
"""

import argparse
import calendar
import re
import sys
from datetime import date
from pathlib import Path

tools_dir = Path(__file__).resolve().parents[2]
REPO_ROOT = tools_dir.parent
sys.path.insert(0, str(tools_dir))

DEFAULT_COLPPY_DB = REPO_ROOT / "tools" / "data" / "colppy_export.db"


def _normalize_cuit(raw: str) -> str:
    """Normalize CUIT to 11 digits (strip, remove dashes)."""
    if not raw:
        return ""
    s = re.sub(r"\D", "", str(raw).strip())
    return s if len(s) == 11 else ""


def _product_line(plan_name: str) -> str:
    """
    Classify plan into product line for Building Blocks: Administración vs Sueldos.
    Rule: if plan.nombre contains 'Sueldos' (case-insensitive) → Sueldos (payroll);
    otherwise → Administración (Colppy accounting). Matches HubSpot product_family logic.
    """
    if not plan_name:
        return "Administración"
    return "Sueldos" if "sueldos" in (plan_name or "").lower() else "Administración"


def _print_detail_composition(rows: list[dict]) -> None:
    """Print each payment grouped by the 4 REAL buckets (Product × ICP)."""
    buckets = [
        ("New Product - Administración - ICP Pyme", "Administración", "Empresa"),
        ("New Product - Administración - ICP Operador", "Administración", "Contador"),
        ("New Product - Sueldos - ICP Pyme", "Sueldos", "Empresa"),
        ("New Product - Sueldos - ICP Operador", "Sueldos", "Contador"),
    ]
    for label, product_line, channel in buckets:
        subset = [r for r in rows if r["product_line"] == product_line and r["channel"] == channel]
        if not subset:
            print(f"\n--- {label} ---\n  (no payments)\n")
            continue
        total_importe = sum(r["importe"] for r in subset)
        print(f"\n--- {label} ---")
        print(f"  Total: ${total_importe:,.2f} ({len(subset)} payments)")
        print()
        print("  | #   | idPago  | idEmpresa | plan_name (trunc)     | fechaPago   | importe (ARS)  |")
        print("  |-----|---------|-----------|-----------------------|-------------|----------------|")
        for i, r in enumerate(subset, 1):
            plan = (r.get("plan_name") or "")[:22]
            print(f"  | {i:>3} | {r.get('idPago') or '':<7} | {r.get('idEmpresa') or '':<9} | {plan:<21} | {str(r.get('fechaPago') or '')[:10]:<11} | {r['importe']:>14,.2f} |")
        print()

    unknown = [r for r in rows if r["channel"] == "Unknown"]
    if unknown:
        total_unk = sum(r["importe"] for r in unknown)
        print("--- Unknown (no facturacion or CUIT) ---")
        print(f"  Total: ${total_unk:,.2f} ({len(unknown)} payments)")
        print()
        print("  | #   | idPago  | idEmpresa | plan_name (trunc)     | fechaPago   | importe (ARS)  |")
        print("  |-----|---------|-----------|-----------------------|-------------|----------------|")
        for i, r in enumerate(unknown, 1):
            plan = (r.get("plan_name") or "")[:22]
            print(f"  | {i:>3} | {r.get('idPago') or '':<7} | {r.get('idEmpresa') or '':<9} | {plan:<21} | {str(r.get('fechaPago') or '')[:10]:<11} | {r['importe']:>14,.2f} |")
        print()


def query_new_client_mrr_local(
    db_path: Path, start_date: str, end_date: str
) -> list[dict]:
    """
    First payments in date range with Empresa vs Contador classification.
    Empresa = facturacion.CUIT = empresa.CUIT (we invoice the company)
    Contador = facturacion.CUIT != empresa.CUIT (we invoice the accountant)
    """
    import sqlite3
    with sqlite3.connect(str(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT
                p.idPago,
                p.idEmpresa,
                p.idPlan,
                pl.nombre AS plan_name,
                p.fechaPago,
                p.importe,
                e.CUIT AS product_cuit,
                f.CUIT AS customer_cuit
            FROM pago p
            LEFT JOIN plan pl ON pl.idPlan = p.idPlan
            LEFT JOIN empresa e ON e.IdEmpresa = p.idEmpresa
            LEFT JOIN facturacion f ON f.IdEmpresa = p.idEmpresa
              AND (f.fechaBaja IS NULL OR f.fechaBaja = '' OR f.fechaBaja = '0000-00-00')
            WHERE p.primerPago = 1
              AND (p.estado = 1 OR (p.estado = 0 AND p.fechaTransferencia IS NOT NULL))
              AND p.fechaPago >= ?
              AND p.fechaPago <= ?
            ORDER BY p.fechaPago, p.idPago
            """,
            (start_date, end_date),
        )
        rows = [dict(r) for r in cur.fetchall()]

    out = []
    for r in rows:
        prod = _normalize_cuit(r.get("product_cuit") or "")
        cust = _normalize_cuit(r.get("customer_cuit") or "")
        # Empresa = we invoice the company (customer_cuit = product_cuit)
        # Contador = we invoice someone else (accountant)
        if cust and prod:
            channel = "Empresa" if cust == prod else "Contador"
        else:
            channel = "Unknown"
        importe = float(r.get("importe") or 0)
        product_line = _product_line(r.get("plan_name") or "")
        out.append({
            "idPago": r.get("idPago"),
            "idEmpresa": r.get("idEmpresa"),
            "plan_name": r.get("plan_name"),
            "fechaPago": r.get("fechaPago"),
            "importe": importe,
            "channel": channel,
            "product_line": product_line,
        })
    return out


def main():
    today = date.today()
    start_default = today.replace(day=1).strftime("%Y-%m-%d")
    last_day = calendar.monthrange(today.year, today.month)[1]
    end_default = today.replace(day=last_day).strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(
        description="Export New Client MRR (Empresa vs Contador) for Building Blocks Raw Data"
    )
    parser.add_argument(
        "--month",
        metavar="YYYY-MM",
        help="Target month (e.g. 2026-03)",
    )
    parser.add_argument(
        "--start",
        default=start_default,
        help=f"Start date (YYYY-MM-DD). Default: {start_default}",
    )
    parser.add_argument(
        "--end",
        default=end_default,
        help=f"End date (YYYY-MM-DD). Default: {end_default}",
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_COLPPY_DB),
        help="Path to colppy_export.db (for --local)",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output as CSV",
    )
    parser.add_argument(
        "--detail",
        action="store_true",
        help="Print each payment with classification (composition for each bucket)",
    )
    args = parser.parse_args()

    if args.month:
        parts = args.month.split("-")
        if len(parts) != 2:
            print("ERROR: --month must be YYYY-MM", file=sys.stderr)
            sys.exit(1)
        year, month = int(parts[0]), int(parts[1])
        start_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day}"
    else:
        start_date = args.start
        end_date = args.end

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: DB not found: {db_path}", file=sys.stderr)
        print("Run export_colppy_to_sqlite.py first.", file=sys.stderr)
        sys.exit(1)
    rows = query_new_client_mrr_local(db_path, start_date, end_date)

    # Aggregate into 4 Building Blocks rows (Product × ICP)
    # ICP Pyme = Empresa, ICP Operador = Contador
    adm_pyme = sum(r["importe"] for r in rows if r["product_line"] == "Administración" and r["channel"] == "Empresa")
    adm_operador = sum(r["importe"] for r in rows if r["product_line"] == "Administración" and r["channel"] == "Contador")
    sueldos_pyme = sum(r["importe"] for r in rows if r["product_line"] == "Sueldos" and r["channel"] == "Empresa")
    sueldos_operador = sum(r["importe"] for r in rows if r["product_line"] == "Sueldos" and r["channel"] == "Contador")
    mrr_unknown = sum(r["importe"] for r in rows if r["channel"] == "Unknown")
    total = adm_pyme + adm_operador + sueldos_pyme + sueldos_operador + mrr_unknown

    n_adm_pyme = sum(1 for r in rows if r["product_line"] == "Administración" and r["channel"] == "Empresa")
    n_adm_operador = sum(1 for r in rows if r["product_line"] == "Administración" and r["channel"] == "Contador")
    n_sueldos_pyme = sum(1 for r in rows if r["product_line"] == "Sueldos" and r["channel"] == "Empresa")
    n_sueldos_operador = sum(1 for r in rows if r["product_line"] == "Sueldos" and r["channel"] == "Contador")
    n_unk = sum(1 for r in rows if r["channel"] == "Unknown")

    if args.csv:
        # One row per month: 4 columns for Building Blocks REAL sheet
        month_key = start_date[:7]
        print("month,new_product_administracion_icp_pyme,new_product_administracion_icp_operador,new_product_sueldos_icp_pyme,new_product_sueldos_icp_operador,new_client_mrr_unknown,total,count")
        print(f"{month_key},{adm_pyme:.2f},{adm_operador:.2f},{sueldos_pyme:.2f},{sueldos_operador:.2f},{mrr_unknown:.2f},{total:.2f},{len(rows)}")
        return

    # Human-readable: 4 rows matching Building Blocks REAL sheet
    print("=" * 72)
    print(f"New Client MRR — {start_date} to {end_date} (Building Blocks REAL)")
    print("=" * 72)
    print("Source: colppy_export.db (pago primerPago=1)")
    print("Product: plan.nombre contains 'Sueldos' → Sueldos; else → Administración")
    print("ICP: facturacion.CUIT = empresa.CUIT → ICP Pyme; else → ICP Operador")
    print()
    print(f"Records: {len(rows)} first payments")
    print()
    print("| Item (REAL sheet)                              | MRR (ARS)    | Count |")
    print("|------------------------------------------------|--------------|-------|")
    print(f"| New Product - Administración - ICP Pyme      | ${adm_pyme:>12,.2f} | {n_adm_pyme:>5} |")
    print(f"| New Product - Administración - ICP Operador  | ${adm_operador:>12,.2f} | {n_adm_operador:>5} |")
    print(f"| New Product - Sueldos - ICP Pyme             | ${sueldos_pyme:>12,.2f} | {n_sueldos_pyme:>5} |")
    print(f"| New Product - Sueldos - ICP Operador         | ${sueldos_operador:>12,.2f} | {n_sueldos_operador:>5} |")
    if n_unk:
        print(f"| Unknown (no facturacion/CUIT)                | ${mrr_unknown:>12,.2f} | {n_unk:>5} |")
    print(f"| Total                                        | ${total:>12,.2f} | {len(rows):>5} |")
    print()

    if args.detail:
        _print_detail_composition(rows)

    print()
    print("Use --csv to output CSV for Raw Data import. Use --detail to see payment-level composition.")


if __name__ == "__main__":
    main()
