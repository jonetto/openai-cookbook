#!/usr/bin/env python3
"""
Publish Pipeline Summaries to Supabase
=======================================
Publishes aggregated results from local SQLite pipelines to the Supabase
shared read layer. Raw data stays local; only "answers" are published.

Usage:
    python3 tools/scripts/publish_to_supabase.py --mtd                    # Publish MTD billing summary
    python3 tools/scripts/publish_to_supabase.py --mtd --month 2026-03    # Specific month
    python3 tools/scripts/publish_to_supabase.py --all                    # Publish all summaries

Requires: SUPABASE_URL and SUPABASE_SECRET_KEY in tools/.env
          colppy_export.db for MTD (refresh via export_colppy_to_sqlite.py first)
"""

import argparse
import calendar
import json
import os
import re
import sqlite3
import sys
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
ENV_PATH = REPO_ROOT / "tools" / ".env"
COLPPY_DB = REPO_ROOT / "tools" / "data" / "colppy_export.db"
HUBSPOT_DB = REPO_ROOT / "tools" / "data" / "facturacion_hubspot.db"


def load_env():
    env = {}
    with open(ENV_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"')
    return env


ENV = load_env()
SUPABASE_URL = ENV["SUPABASE_URL"]
SUPABASE_KEY = ENV["SUPABASE_SECRET_KEY"]

MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def supabase_request(method, table, data=None, params="", prefer=None):
    """Make a request to the Supabase REST API."""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    if params:
        url += f"?{params}"

    hdrs = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        hdrs["Prefer"] = prefer

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            text = resp.read().decode()
            return json.loads(text) if text.strip() else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode() if e.fp else ""
        print(f"  Supabase error {e.code}: {err_body}", file=sys.stderr)
        raise


def supabase_upsert(table, rows, on_conflict):
    """Upsert rows into a Supabase table."""
    if not rows:
        return
    supabase_request(
        "POST", table, data=rows,
        params=f"on_conflict={on_conflict}",
        prefer="resolution=merge-duplicates",
    )


def normalize_cuit(raw):
    if not raw:
        return ""
    s = re.sub(r"\D", "", str(raw).strip())
    return s if len(s) == 11 else ""


def get_db_freshness(db_path):
    """Get the last refresh timestamp from colppy_export.db."""
    if not db_path.exists():
        return None
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT timestamp FROM colppy_export_refresh_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row[0] if row else None
    except Exception:
        return None
    finally:
        conn.close()


# ── MTD Publisher ─────────────────────────────────────────────────────────────

def publish_mtd(year, month):
    """Publish MTD billing summary from colppy_export.db to Supabase."""
    if not COLPPY_DB.exists():
        print(f"ERROR: {COLPPY_DB} not found. Run export_colppy_to_sqlite.py first.")
        sys.exit(1)

    month_key = f"{MONTH_NAMES[month - 1]}-{year}"
    start_date = f"{year}-{month:02d}-01"
    last_day = calendar.monthrange(year, month)[1]
    end_date = f"{year}-{month:02d}-{last_day}"
    db_date = get_db_freshness(COLPPY_DB) or "unknown"
    now = datetime.now(timezone.utc).isoformat()

    print(f"Publishing MTD for {month_key}...")
    print(f"  colppy_export.db last refreshed: {db_date}")

    conn = sqlite3.connect(str(COLPPY_DB))
    conn.row_factory = sqlite3.Row

    rows_to_publish = []

    # ── New Product MRR (primerPago=1 by ICP × Product family) ─────────────
    # Definition: new product = pago.primerPago=1 in the month.
    # Do NOT use facturacion.fechaAlta (99.95% are 0000-00-00, never populated).
    # Each pago = one product (empresa × plan). Count = products, not empresas.
    first_payments = conn.execute("""
        SELECT
            p.idPago, p.idEmpresa, p.idPlan,
            pl.nombre AS plan_name, p.fechaPago, p.importe,
            e.CUIT AS product_cuit, f_dedup.CUIT AS customer_cuit
        FROM pago p
        LEFT JOIN plan pl ON pl.idPlan = p.idPlan
        LEFT JOIN (
            SELECT IdEmpresa, CUIT FROM empresa GROUP BY IdEmpresa
        ) e ON e.IdEmpresa = p.idEmpresa
        LEFT JOIN (
            SELECT IdEmpresa, CUIT, MIN(idFacturacion) as min_id
            FROM facturacion
            WHERE fechaBaja IS NULL OR fechaBaja = '' OR fechaBaja = '0000-00-00'
            GROUP BY IdEmpresa
        ) f_dedup ON f_dedup.IdEmpresa = p.idEmpresa
        WHERE p.primerPago = 1
          AND (p.estado = 1 OR (p.estado = 0 AND p.fechaTransferencia IS NOT NULL))
          AND p.fechaPago >= ? AND p.fechaPago <= ?
        ORDER BY p.fechaPago
    """, (start_date, end_date)).fetchall()

    # Classify each payment into ICP × Product family buckets.
    #
    # ICP (who pays):
    #   - Pyme:     facturacion.CUIT == empresa.CUIT  (self-billed)
    #   - Operador: facturacion.CUIT != empresa.CUIT  (accountant bills on behalf)
    #   - Unknown:  CUIT missing from either table
    #
    # Product family (what they bought):
    #   - Sueldos:        plan.nombre contains 'sueldos' (case-insensitive)
    #   - Administración: everything else
    buckets = {
        "new_mrr_adm_pyme": {"value": 0, "count": 0},
        "new_mrr_adm_operador": {"value": 0, "count": 0},
        "new_mrr_sueldos_pyme": {"value": 0, "count": 0},
        "new_mrr_sueldos_operador": {"value": 0, "count": 0},
        "new_mrr_unknown": {"value": 0, "count": 0},
    }

    for row in first_payments:
        importe = float(row["importe"] or 0)
        prod = normalize_cuit(row["product_cuit"])    # empresa.CUIT
        cust = normalize_cuit(row["customer_cuit"])    # facturacion.CUIT
        is_sueldos = "sueldos" in (row["plan_name"] or "").lower()

        if cust and prod:
            icp = "pyme" if cust == prod else "operador"
        else:
            icp = "unknown"

        product = "sueldos" if is_sueldos else "adm"

        if icp == "unknown":
            key = "new_mrr_unknown"
        else:
            key = f"new_mrr_{product}_{icp}"

        buckets[key]["value"] += importe
        buckets[key]["count"] += 1

    total_new = sum(b["value"] for b in buckets.values())
    total_new_count = sum(b["count"] for b in buckets.values())

    for metric, data in buckets.items():
        rows_to_publish.append({
            "month": month_key, "metric": metric,
            "value": round(data["value"], 2), "count": data["count"],
            "refreshed_at": now, "source_db_date": db_date,
        })

    rows_to_publish.append({
        "month": month_key, "metric": "new_mrr_total",
        "value": round(total_new, 2), "count": total_new_count,
        "refreshed_at": now, "source_db_date": db_date,
    })

    # ── Active billing products (non-cancelled facturacion rows) ───────────
    active = conn.execute("""
        SELECT COUNT(*) FROM facturacion
        WHERE fechaBaja IS NULL OR fechaBaja = '' OR fechaBaja = '0000-00-00'
    """).fetchone()[0]

    rows_to_publish.append({
        "month": month_key, "metric": "active_billing_products",
        "value": active, "count": active,
        "refreshed_at": now, "source_db_date": db_date,
    })

    # ── Churned products this month (fechaBaja in range) ─────────────────
    churned = conn.execute("""
        SELECT COUNT(*) FROM facturacion
        WHERE fechaBaja >= ? AND fechaBaja <= ?
    """, (start_date, end_date)).fetchone()[0]

    rows_to_publish.append({
        "month": month_key, "metric": "churned_products",
        "value": churned, "count": churned,
        "refreshed_at": now, "source_db_date": db_date,
    })

    # ── Payments collected MTD ────────────────────────────────────────────
    payments = conn.execute("""
        SELECT COUNT(*) as n, SUM(CAST(importe AS REAL)) as total
        FROM pago
        WHERE (estado = 1 OR (estado = 0 AND fechaTransferencia IS NOT NULL))
        AND fechaPago >= ? AND fechaPago <= ?
    """, (start_date, end_date)).fetchone()

    rows_to_publish.append({
        "month": month_key, "metric": "payments_collected",
        "value": round(float(payments[1] or 0), 2), "count": payments[0],
        "refreshed_at": now, "source_db_date": db_date,
    })

    # ── First payments (all, not just primerPago=1) ───────────────────────
    # Total payments = recurring billing health indicator
    all_payments = conn.execute("""
        SELECT COUNT(DISTINCT idEmpresa) as unique_empresas
        FROM pago
        WHERE (estado = 1 OR (estado = 0 AND fechaTransferencia IS NOT NULL))
        AND fechaPago >= ? AND fechaPago <= ?
    """, (start_date, end_date)).fetchone()

    rows_to_publish.append({
        "month": month_key, "metric": "paying_empresas_mtd",
        "value": all_payments[0], "count": all_payments[0],
        "refreshed_at": now, "source_db_date": db_date,
    })

    conn.close()

    # ── Upsert to Supabase ────────────────────────────────────────────────
    supabase_upsert("mtd_summary", rows_to_publish, "month,metric")

    print(f"  Published {len(rows_to_publish)} metrics to mtd_summary")
    print()
    print(f"  Summary for {month_key}:")
    for r in rows_to_publish:
        val = r["value"]
        cnt = r["count"]
        if val > 10000:
            print(f"    {r['metric']:30s}  ${val:>14,.0f}  ({cnt} items)")
        else:
            print(f"    {r['metric']:30s}  {val:>14,.2f}  ({cnt} items)")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    today = date.today()

    parser = argparse.ArgumentParser(
        description="Publish pipeline summaries to Supabase shared read layer"
    )
    parser.add_argument("--mtd", action="store_true", help="Publish MTD billing summary")
    parser.add_argument("--all", action="store_true", help="Publish all available summaries")
    parser.add_argument(
        "--month", metavar="YYYY-MM",
        help=f"Target month (default: {today.strftime('%Y-%m')})",
    )
    args = parser.parse_args()

    if args.month:
        parts = args.month.split("-")
        year, month = int(parts[0]), int(parts[1])
    else:
        year, month = today.year, today.month

    if not (args.mtd or args.all):
        parser.print_help()
        print("\nSpecify --mtd, or --all")
        sys.exit(1)

    if args.mtd or args.all:
        publish_mtd(year, month)

    print("\nDone.")


if __name__ == "__main__":
    main()
