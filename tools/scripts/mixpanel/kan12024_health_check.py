#!/usr/bin/env python3
"""
KAN-12024 Dual-Group Migration Health Check

Compares Mixpanel Login events BEFORE vs AFTER the dual-group change (~March 11, 2026).

Before: $groups.Company was typically idEmpresa (or missing)
After:  $groups.Company = CUITFacturacion (billing entity)
        $groups.product_id = idEmpresa (product subscription)

Uses Raw Export API (separate rate limit from JQL/Query API).

Validates against Colppy DB:
  - Does $groups.Company match facturacion.CUIT?
  - Does $groups.product_id match empresa.IdEmpresa?
  - Data completeness: % of events with groups populated
"""

import sys
import os
import json
import csv
import base64
import sqlite3
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime

from dotenv import load_dotenv
import requests

# Setup
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
load_dotenv(project_root / ".env")

MIXPANEL_USERNAME = os.getenv("MIXPANEL_USERNAME")
MIXPANEL_PASSWORD = os.getenv("MIXPANEL_PASSWORD")
MIXPANEL_PROJECT_ID = os.getenv("MIXPANEL_PROJECT_ID")

SQLITE_DB = project_root / "tools" / "data" / "colppy_export.db"
OUTPUT_DIR = project_root / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Periods: BEFORE and AFTER the dual-group change
BEFORE_FROM = "2026-03-09"
BEFORE_TO = "2026-03-10"
AFTER_FROM = "2026-03-11"
AFTER_TO = "2026-03-13"


def fetch_login_events(from_date: str, to_date: str) -> list:
    """Fetch Login events via Raw Export API."""
    auth_string = f"{MIXPANEL_USERNAME}:{MIXPANEL_PASSWORD}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Accept": "text/plain",
    }
    params = {
        "project_id": MIXPANEL_PROJECT_ID,
        "from_date": from_date,
        "to_date": to_date,
        "event": json.dumps(["Login"]),
    }
    url = "https://data.mixpanel.com/api/2.0/export"
    print(f"  Fetching Login events {from_date} → {to_date}...")

    response = requests.get(url, params=params, headers=headers, stream=True)
    if response.status_code != 200:
        print(f"  ERROR {response.status_code}: {response.text[:300]}")
        return []

    events = []
    for line in response.iter_lines(decode_unicode=True):
        if line and line.strip():
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"  → {len(events)} Login events")
    return events


def extract_group_info(event: dict) -> dict:
    """Extract grouping fields from a raw event."""
    props = event.get("properties", {})
    groups = props.get("$groups", {})

    return {
        "distinct_id": props.get("distinct_id", ""),
        "time": datetime.utcfromtimestamp(props.get("time", 0)).strftime("%Y-%m-%d %H:%M"),
        # Group keys
        "groups_company": str(groups.get("Company", "")) if groups.get("Company") else "",
        "groups_product_id": str(groups.get("product_id", "")) if groups.get("product_id") else "",
        # Legacy fields
        "idEmpresa": str(props.get("idEmpresa", "")),
        "company_id": str(props.get("company_id", "")),
        # Event-level properties
        "tipo_plan": props.get("Tipo Plan Empresa", ""),
        "nombre_empresa": props.get("Nombre de Empresa", ""),
        "email_admin": props.get("Email de Administrador", ""),
        "pais": props.get("Pais de Registro", ""),
    }


def analyze_period(events: list, label: str) -> dict:
    """Analyze grouping quality for a set of events."""
    print(f"\n{'═'*60}")
    print(f"  {label}")
    print(f"{'═'*60}")

    total = len(events)
    if total == 0:
        print("  No events!")
        return {}

    infos = [extract_group_info(e) for e in events]

    # ── Group key population rates ──
    has_groups_company = sum(1 for i in infos if i["groups_company"])
    has_groups_product = sum(1 for i in infos if i["groups_product_id"])
    has_idempresa = sum(1 for i in infos if i["idEmpresa"])
    has_company_id = sum(1 for i in infos if i["company_id"])

    print(f"\n  Events: {total:,}")
    print(f"  Unique users: {len(set(i['distinct_id'] for i in infos)):,}")
    print(f"\n  Field population:")
    print(f"    $groups.Company:    {has_groups_company:>6,} ({has_groups_company*100/total:.1f}%)")
    print(f"    $groups.product_id: {has_groups_product:>6,} ({has_groups_product*100/total:.1f}%)")
    print(f"    idEmpresa:          {has_idempresa:>6,} ({has_idempresa*100/total:.1f}%)")
    print(f"    company_id:         {has_company_id:>6,} ({has_company_id*100/total:.1f}%)")

    # ── What does $groups.Company look like? ──
    company_values = [i["groups_company"] for i in infos if i["groups_company"]]
    looks_like_cuit = sum(1 for v in company_values if "-" in v or (v.isdigit() and len(v) == 11))
    looks_like_id = sum(1 for v in company_values if v.isdigit() and len(v) < 7)
    looks_like_other = len(company_values) - looks_like_cuit - looks_like_id

    print(f"\n  $groups.Company value patterns:")
    print(f"    Looks like CUIT (has dashes or 11 digits):  {looks_like_cuit:>6,} ({looks_like_cuit*100/max(1,len(company_values)):.1f}%)")
    print(f"    Looks like idEmpresa (short numeric):       {looks_like_id:>6,} ({looks_like_id*100/max(1,len(company_values)):.1f}%)")
    print(f"    Other format:                               {looks_like_other:>6,} ({looks_like_other*100/max(1,len(company_values)):.1f}%)")

    # Sample $groups.Company values
    sample_company = Counter(company_values)
    print(f"\n  Top 10 $groups.Company values (by frequency):")
    for val, count in sample_company.most_common(10):
        print(f"    {val:30s}  ({count:,} events)")

    # Sample $groups.product_id values
    product_values = [i["groups_product_id"] for i in infos if i["groups_product_id"]]
    if product_values:
        sample_product = Counter(product_values)
        print(f"\n  Top 10 $groups.product_id values:")
        for val, count in sample_product.most_common(10):
            print(f"    {val:30s}  ({count:,} events)")

    # ── Does $groups.Company == idEmpresa? (old behavior) ──
    both_present = [(i["groups_company"], i["idEmpresa"]) for i in infos
                    if i["groups_company"] and i["idEmpresa"]]
    if both_present:
        company_equals_id = sum(1 for gc, ie in both_present if gc == ie)
        print(f"\n  $groups.Company == idEmpresa? (old behavior indicator)")
        print(f"    Match: {company_equals_id:,} / {len(both_present):,} ({company_equals_id*100/len(both_present):.1f}%)")

    # ── Plan distribution ──
    plans = Counter(i["tipo_plan"] for i in infos if i["tipo_plan"])
    paid_events = sum(c for p, c in plans.items() if p != "pendiente_pago")
    trial_events = plans.get("pendiente_pago", 0)
    print(f"\n  Plan split: {paid_events:,} paid events, {trial_events:,} trial events")

    return {
        "total": total,
        "has_groups_company_pct": has_groups_company * 100 / total,
        "has_groups_product_pct": has_groups_product * 100 / total,
        "has_idempresa_pct": has_idempresa * 100 / total,
        "looks_like_cuit_pct": looks_like_cuit * 100 / max(1, len(company_values)),
        "looks_like_id_pct": looks_like_id * 100 / max(1, len(company_values)),
        "infos": infos,
    }


def validate_against_db(infos: list, label: str):
    """Cross-reference $groups values with Colppy DB."""
    print(f"\n{'─'*60}")
    print(f"  DB VALIDATION: {label}")
    print(f"{'─'*60}")

    db = sqlite3.connect(str(SQLITE_DB))
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    # Collect unique idEmpresa values
    empresa_ids = set()
    for i in infos:
        if i["idEmpresa"] and i["idEmpresa"].isdigit():
            empresa_ids.add(int(i["idEmpresa"]))

    if not empresa_ids:
        print("  No valid idEmpresa values to validate")
        db.close()
        return

    placeholders = ",".join("?" * len(empresa_ids))
    ids_list = list(empresa_ids)

    # Get empresa + facturacion data
    cur.execute(f"""
        SELECT
            e.IdEmpresa,
            e.CUIT as empresa_cuit,
            e.Nombre,
            f.CUIT as facturacion_cuit
        FROM empresa e
        LEFT JOIN facturacion f ON e.IdEmpresa = f.IdEmpresa AND f.fechaBaja IS NULL
        WHERE e.IdEmpresa IN ({placeholders})
    """, ids_list)

    db_lookup = {}
    for row in cur.fetchall():
        eid = str(row["IdEmpresa"])
        db_lookup[eid] = {
            "empresa_cuit": row["empresa_cuit"] or "",
            "facturacion_cuit": row["facturacion_cuit"] or "",
            "nombre": row["Nombre"] or "",
        }
    db.close()

    print(f"  Matched {len(db_lookup):,} / {len(empresa_ids):,} empresas in DB")

    # For events with $groups.Company, check if it matches facturacion CUIT
    def normalize_cuit(c: str) -> str:
        """Strip dashes for comparison."""
        return c.replace("-", "").strip() if c else ""

    matches_fact_cuit = 0
    matches_emp_cuit = 0
    matches_idempresa = 0
    matches_nothing = 0
    no_db_record = 0
    total_checked = 0

    mismatch_samples = []

    for info in infos:
        gc = info["groups_company"]
        ie = info["idEmpresa"]
        if not gc or not ie or not ie.isdigit():
            continue

        db_rec = db_lookup.get(ie)
        if not db_rec:
            no_db_record += 1
            continue

        total_checked += 1
        gc_norm = normalize_cuit(gc)
        fact_norm = normalize_cuit(db_rec["facturacion_cuit"])
        emp_norm = normalize_cuit(db_rec["empresa_cuit"])

        if fact_norm and gc_norm == fact_norm:
            matches_fact_cuit += 1
        elif emp_norm and gc_norm == emp_norm:
            matches_emp_cuit += 1
        elif gc == ie:
            matches_idempresa += 1
        else:
            matches_nothing += 1
            if len(mismatch_samples) < 10:
                mismatch_samples.append({
                    "idEmpresa": ie,
                    "groups_company": gc,
                    "facturacion_cuit": db_rec["facturacion_cuit"],
                    "empresa_cuit": db_rec["empresa_cuit"],
                    "nombre": db_rec["nombre"],
                })

    if total_checked > 0:
        print(f"\n  $groups.Company validation ({total_checked:,} events checked):")
        print(f"    = facturacion.CUIT:  {matches_fact_cuit:>6,} ({matches_fact_cuit*100/total_checked:.1f}%) ← CORRECT post-KAN-12024")
        print(f"    = empresa.CUIT:      {matches_emp_cuit:>6,} ({matches_emp_cuit*100/total_checked:.1f}%)")
        print(f"    = idEmpresa (old):   {matches_idempresa:>6,} ({matches_idempresa*100/total_checked:.1f}%) ← OLD behavior")
        print(f"    = nothing matched:   {matches_nothing:>6,} ({matches_nothing*100/total_checked:.1f}%)")

        if mismatch_samples:
            print(f"\n  Sample unmatched events:")
            for s in mismatch_samples[:5]:
                print(f"    idEmpresa={s['idEmpresa']}  $groups.Company={s['groups_company']}")
                print(f"      DB fact_cuit={s['facturacion_cuit']}  emp_cuit={s['empresa_cuit']}  ({s['nombre'][:30]})")

    # Validate $groups.product_id == idEmpresa (expected post-KAN-12024)
    product_checks = [(info["groups_product_id"], info["idEmpresa"])
                      for info in infos
                      if info["groups_product_id"] and info["idEmpresa"]]
    if product_checks:
        product_match = sum(1 for pid, ie in product_checks if pid == ie)
        print(f"\n  $groups.product_id == idEmpresa?")
        print(f"    Match: {product_match:,} / {len(product_checks):,} ({product_match*100/len(product_checks):.1f}%) ← should be ~100% post-KAN-12024")


def main():
    print("KAN-12024 DUAL-GROUP MIGRATION HEALTH CHECK")
    print("=" * 60)
    print(f"BEFORE period: {BEFORE_FROM} to {BEFORE_TO}")
    print(f"AFTER  period: {AFTER_FROM} to {AFTER_TO}")
    print(f"DB snapshot:   2026-03-06 (SQLite export)")

    # ── Fetch events ──
    print("\nFetching Login events via Raw Export API...")
    before_events = fetch_login_events(BEFORE_FROM, BEFORE_TO)
    after_events = fetch_login_events(AFTER_FROM, AFTER_TO)

    # ── Analyze both periods ──
    before_stats = analyze_period(before_events, f"BEFORE KAN-12024 ({BEFORE_FROM} to {BEFORE_TO})")
    after_stats = analyze_period(after_events, f"AFTER KAN-12024 ({AFTER_FROM} to {AFTER_TO})")

    # ── DB validation ──
    if before_stats.get("infos"):
        validate_against_db(before_stats["infos"], f"BEFORE ({BEFORE_FROM}–{BEFORE_TO})")
    if after_stats.get("infos"):
        validate_against_db(after_stats["infos"], f"AFTER ({AFTER_FROM}–{AFTER_TO})")

    # ── Side-by-side comparison ──
    if before_stats and after_stats:
        print(f"\n{'═'*60}")
        print(f"  BEFORE vs AFTER COMPARISON")
        print(f"{'═'*60}")
        metrics = [
            ("$groups.Company populated", "has_groups_company_pct"),
            ("$groups.product_id populated", "has_groups_product_pct"),
            ("idEmpresa populated", "has_idempresa_pct"),
            ("$groups.Company looks like CUIT", "looks_like_cuit_pct"),
            ("$groups.Company looks like idEmpresa", "looks_like_id_pct"),
        ]
        print(f"\n  {'Metric':45s} {'BEFORE':>10s} {'AFTER':>10s} {'Δ':>10s}")
        print(f"  {'─'*75}")
        for name, key in metrics:
            b = before_stats.get(key, 0)
            a = after_stats.get(key, 0)
            delta = a - b
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else "="
            print(f"  {name:45s} {b:>9.1f}% {a:>9.1f}% {arrow}{abs(delta):>8.1f}pp")

    # ── Save raw event samples to CSV for inspection ──
    for label, infos in [("before", before_stats.get("infos", [])),
                          ("after", after_stats.get("infos", []))]:
        if not infos:
            continue
        csv_path = OUTPUT_DIR / f"kan12024_login_sample_{label}.csv"
        fieldnames = list(infos[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in infos:
                writer.writerow(row)
        print(f"\n✅ {label.upper()} events CSV: {csv_path} ({len(infos)} rows)")


if __name__ == "__main__":
    main()
