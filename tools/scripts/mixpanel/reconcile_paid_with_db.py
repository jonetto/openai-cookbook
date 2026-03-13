#!/usr/bin/env python3
"""
Reconcile Mixpanel paid customers with Colppy DB.

Join key: idEmpresa (Mixpanel) = IdEmpresa (empresa table)

Checks:
  1. Plan match: Mixpanel Tipo Plan Empresa vs DB plan.tipo
  2. Active status: empresa.activa (0=active, 2=payment_fail, 3=deactivated)
  3. CUIT consistency: empresa.CUIT vs facturacion.CUIT
  4. Billing status: facturacion.fechaBaja (NULL=active billing)
  5. Trial flag: empresa.istrial vs plan.tipo

SQLite export last synced: 2026-03-06
Mixpanel data: 2026-03-07 to 2026-03-13
"""

import csv
import sqlite3
import json
from pathlib import Path
from collections import defaultdict, Counter

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MIXPANEL_CSV = PROJECT_ROOT / "output" / "paid_companies_summary_2026-03-07_2026-03-13.csv"
SQLITE_DB = PROJECT_ROOT / "tools" / "data" / "colppy_export.db"
OUTPUT_DIR = PROJECT_ROOT / "output"


def load_mixpanel_companies():
    """Load paid companies from Mixpanel CSV."""
    companies = {}
    with open(MIXPANEL_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["company_id"]
            if cid in ("unknown", "undefined", "null", ""):
                continue
            companies[cid] = {
                "mx_plan": row["plan_type"],
                "mx_logins": int(row["total_logins"]),
                "mx_users": int(row["unique_users"]),
            }
    return companies


def reconcile(mx_companies: dict):
    """Join Mixpanel companies with Colppy DB and compare."""
    db = sqlite3.connect(str(SQLITE_DB))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Build lookup: empresa + plan
    empresa_ids = [int(cid) for cid in mx_companies.keys() if cid.isdigit()]
    placeholders = ",".join("?" * len(empresa_ids))

    cur.execute(f"""
        SELECT
            e.IdEmpresa,
            e.Nombre,
            e.razonSocial,
            e.CUIT as empresa_cuit,
            e.activa,
            e.idPlan,
            e.istrial,
            e.FechaAlta,
            e.fechaVencimiento,
            e.UltimoLogin,
            e.esEmpresaDemo,
            e.email,
            e.pais,
            p.nombre as plan_nombre,
            p.tipo as plan_tipo,
            p.precio,
            p.precio_siniva,
            p.meses as billing_period
        FROM empresa e
        LEFT JOIN plan p ON e.idPlan = p.idPlan
        WHERE e.IdEmpresa IN ({placeholders})
    """, empresa_ids)

    db_empresas = {}
    for row in cur.fetchall():
        db_empresas[str(row["IdEmpresa"])] = dict(row)

    # Facturacion lookup (active billing records)
    cur.execute(f"""
        SELECT
            IdEmpresa,
            CUIT as facturacion_cuit,
            razonSocial as facturacion_razon,
            fechaAlta as facturacion_desde,
            fechaBaja as facturacion_hasta
        FROM facturacion
        WHERE IdEmpresa IN ({placeholders})
        AND fechaBaja IS NULL
    """, empresa_ids)

    facturacion = {}
    for row in cur.fetchall():
        eid = str(row["IdEmpresa"])
        facturacion[eid] = dict(row)

    db.close()

    # ── Reconciliation ──
    results = []
    stats = {
        "total_mx": len(mx_companies),
        "found_in_db": 0,
        "not_in_db": 0,
        "plan_match": 0,
        "plan_mismatch": 0,
        "active_in_db": 0,
        "inactive_in_db": 0,
        "has_billing": 0,
        "no_billing": 0,
        "cuit_match": 0,
        "cuit_mismatch": 0,
        "demo_flagged": 0,
        "trial_flag_mismatch": 0,
    }

    plan_mismatches = []
    cuit_mismatches = []
    inactive_but_logging_in = []

    for cid, mx in mx_companies.items():
        row = {
            "idEmpresa": cid,
            "mx_plan": mx["mx_plan"],
            "mx_logins": mx["mx_logins"],
            "mx_users": mx["mx_users"],
        }

        db_emp = db_empresas.get(cid)
        if not db_emp:
            row["reconcile_status"] = "NOT_IN_DB"
            stats["not_in_db"] += 1
            results.append(row)
            continue

        stats["found_in_db"] += 1
        row["db_nombre"] = db_emp["Nombre"]
        row["db_razon_social"] = db_emp["razonSocial"]
        row["db_cuit"] = db_emp["empresa_cuit"]
        row["db_plan_nombre"] = db_emp["plan_nombre"]
        row["db_plan_tipo"] = db_emp["plan_tipo"]
        row["db_precio"] = db_emp["precio"]
        row["db_precio_siniva"] = db_emp["precio_siniva"]
        row["db_billing_period"] = db_emp["billing_period"]
        row["db_activa"] = db_emp["activa"]
        row["db_istrial"] = db_emp["istrial"]
        row["db_fecha_alta"] = db_emp["FechaAlta"]
        row["db_fecha_vencimiento"] = db_emp["fechaVencimiento"]
        row["db_ultimo_login"] = db_emp["UltimoLogin"]
        row["db_es_demo"] = db_emp["esEmpresaDemo"]
        row["db_pais"] = db_emp["pais"]

        # Check 1: Plan match
        if mx["mx_plan"] == db_emp["plan_tipo"]:
            row["plan_status"] = "MATCH"
            stats["plan_match"] += 1
        else:
            row["plan_status"] = "MISMATCH"
            stats["plan_mismatch"] += 1
            plan_mismatches.append({
                "idEmpresa": cid,
                "nombre": db_emp["Nombre"],
                "mx_plan": mx["mx_plan"],
                "db_plan_tipo": db_emp["plan_tipo"],
                "db_plan_nombre": db_emp["plan_nombre"],
                "logins": mx["mx_logins"],
            })

        # Check 2: Active status
        if db_emp["activa"] == 0:
            row["active_status"] = "ACTIVE"
            stats["active_in_db"] += 1
        else:
            status_map = {2: "PAYMENT_FAIL", 3: "USER_DEACTIVATED"}
            row["active_status"] = status_map.get(db_emp["activa"], f"STATUS_{db_emp['activa']}")
            stats["inactive_in_db"] += 1
            inactive_but_logging_in.append({
                "idEmpresa": cid,
                "nombre": db_emp["Nombre"],
                "activa": db_emp["activa"],
                "status": row["active_status"],
                "logins": mx["mx_logins"],
                "users": mx["mx_users"],
            })

        # Check 3: Demo flag
        if db_emp["esEmpresaDemo"] == 1:
            row["demo_flag"] = "IS_DEMO"
            stats["demo_flagged"] += 1

        # Check 4: Trial flag inconsistency
        if db_emp["istrial"] == 1 and mx["mx_plan"] != "pendiente_pago":
            row["trial_flag_status"] = "MISMATCH_TRIAL_BUT_PAID_PLAN"
            stats["trial_flag_mismatch"] += 1

        # Check 5: Billing / CUIT
        fact = facturacion.get(cid)
        if fact:
            row["has_active_billing"] = "YES"
            row["facturacion_cuit"] = fact["facturacion_cuit"]
            row["facturacion_razon"] = fact["facturacion_razon"]
            row["facturacion_desde"] = fact["facturacion_desde"]
            stats["has_billing"] += 1

            # CUIT match
            if db_emp["empresa_cuit"] and fact["facturacion_cuit"]:
                if db_emp["empresa_cuit"].strip() == fact["facturacion_cuit"].strip():
                    row["cuit_status"] = "MATCH"
                    stats["cuit_match"] += 1
                else:
                    row["cuit_status"] = "MISMATCH"
                    stats["cuit_mismatch"] += 1
                    cuit_mismatches.append({
                        "idEmpresa": cid,
                        "nombre": db_emp["Nombre"],
                        "empresa_cuit": db_emp["empresa_cuit"],
                        "facturacion_cuit": fact["facturacion_cuit"],
                    })
        else:
            row["has_active_billing"] = "NO"
            stats["no_billing"] += 1

        results.append(row)

    return results, stats, plan_mismatches, cuit_mismatches, inactive_but_logging_in


def main():
    print("Loading Mixpanel paid companies...")
    mx_companies = load_mixpanel_companies()
    print(f"  → {len(mx_companies)} companies with valid idEmpresa")

    print("\nReconciling with Colppy DB (SQLite export)...")
    results, stats, plan_mm, cuit_mm, inactive = reconcile(mx_companies)

    # ── Summary ──
    print(f"\n{'═'*60}")
    print(f"RECONCILIATION SUMMARY")
    print(f"{'═'*60}")
    print(f"  Mixpanel paid companies:     {stats['total_mx']:,}")
    print(f"  Found in Colppy DB:          {stats['found_in_db']:,} ({stats['found_in_db']*100/stats['total_mx']:.1f}%)")
    print(f"  NOT in Colppy DB:            {stats['not_in_db']:,}")
    print()
    print(f"  Plan type MATCH:             {stats['plan_match']:,} ({stats['plan_match']*100/max(1,stats['found_in_db']):.1f}%)")
    print(f"  Plan type MISMATCH:          {stats['plan_mismatch']:,}")
    print()
    print(f"  Active in DB (activa=0):     {stats['active_in_db']:,}")
    print(f"  Inactive but logging in:     {stats['inactive_in_db']:,}")
    print()
    print(f"  Has active billing record:   {stats['has_billing']:,}")
    print(f"  No billing record:           {stats['no_billing']:,}")
    print(f"  CUIT match (emp=fact):       {stats['cuit_match']:,}")
    print(f"  CUIT mismatch:               {stats['cuit_mismatch']:,}")
    print()
    print(f"  Demo empresas:               {stats['demo_flagged']:,}")
    print(f"  Trial flag mismatch:         {stats['trial_flag_mismatch']:,}")

    # ── Plan mismatches ──
    if plan_mm:
        print(f"\n{'─'*60}")
        print(f"PLAN MISMATCHES (Mixpanel vs DB) — {len(plan_mm)} companies")
        print(f"{'─'*60}")
        # Group by mismatch pattern
        patterns = Counter()
        for m in plan_mm:
            patterns[(m["mx_plan"], m["db_plan_tipo"])] += 1
        print(f"\n  Pattern distribution (mx_plan → db_plan_tipo):")
        for (mx, db), count in patterns.most_common(20):
            print(f"    {mx:35s} → {db:35s}  ({count} companies)")

        print(f"\n  Top 10 by login volume:")
        for m in sorted(plan_mm, key=lambda x: -x["logins"])[:10]:
            print(f"    [{m['idEmpresa']}] {m['nombre'][:35]:35s}  mx={m['mx_plan']:30s} db={m['db_plan_tipo']}")

    # ── Inactive but logging in ──
    if inactive:
        print(f"\n{'─'*60}")
        print(f"INACTIVE IN DB BUT LOGGED IN THIS WEEK — {len(inactive)} companies")
        print(f"{'─'*60}")
        status_counts = Counter(i["status"] for i in inactive)
        for s, c in status_counts.most_common():
            print(f"  {s}: {c} companies")
        print(f"\n  Top 10 by login volume:")
        for i in sorted(inactive, key=lambda x: -x["logins"])[:10]:
            print(f"    [{i['idEmpresa']}] {i['nombre'][:35]:35s}  status={i['status']:20s}  logins={i['logins']}  users={i['users']}")

    # ── CUIT mismatches ──
    if cuit_mm:
        print(f"\n{'─'*60}")
        print(f"CUIT MISMATCHES (empresa vs facturacion) — {len(cuit_mm)} companies")
        print(f"{'─'*60}")
        for m in cuit_mm[:15]:
            print(f"    [{m['idEmpresa']}] {m['nombre'][:30]:30s}  empresa={m['empresa_cuit']:15s}  facturacion={m['facturacion_cuit']}")

    # ── Write full CSV ──
    csv_path = OUTPUT_DIR / "reconciled_paid_companies_2026-03-07_2026-03-13.csv"
    if results:
        fieldnames = sorted(set().union(*(r.keys() for r in results)))
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in sorted(results, key=lambda x: -x.get("mx_logins", 0)):
                writer.writerow(r)
        print(f"\n✅ Full reconciliation CSV: {csv_path}")
        print(f"   Rows: {len(results)}")


if __name__ == "__main__":
    main()
