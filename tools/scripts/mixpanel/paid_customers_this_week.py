#!/usr/bin/env python3
"""
Analyze this week's paid customers who logged in.

Logic:
  1. Fetch all Login events for 2026-03-07..2026-03-13 via JQL
  2. Group by company_id + Tipo Plan Empresa → separate paid vs trial
  3. For paid companies, collect individual user profiles (email, role, company)
  4. Enrich paid company IDs with Engage API group profiles (name, industry, plan, dates)
  5. Output summary + detailed CSV

"Paid" = Tipo Plan Empresa != "pendiente_pago"
"""

import sys
import os
import json
import csv
import base64
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
import requests

# Load env
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
load_dotenv(project_root / ".env")

sys.path.insert(0, str(script_dir))
from mixpanel_api import MixpanelAPI

# Date range: this week (Mon Mar 7 – Thu Mar 13 2026)
FROM_DATE = "2026-03-07"
TO_DATE = "2026-03-13"

OUTPUT_DIR = project_root / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def step1_companies_by_plan(mp: MixpanelAPI) -> list:
    """Get all companies that had Login events, grouped by plan type."""
    print("\n═══ STEP 1: Login events by company + plan type ═══")
    script = f'''
    function main() {{
        return Events({{
            from_date: "{FROM_DATE}",
            to_date: "{TO_DATE}",
            event_selectors: [{{event: "Login"}}]
        }})
        .groupBy(
            [function(e) {{
                return e.properties["idEmpresa"] ||
                       e.properties["company_id"] ||
                       (e.properties["$groups"] ? e.properties["$groups"]["Company"] : null) ||
                       "unknown";
            }},
            "properties.Tipo Plan Empresa"],
            mixpanel.reducer.count()
        )
        .map(function(r) {{
            return {{
                company_id: r.key[0],
                plan_type: r.key[1],
                login_count: r.value
            }};
        }});
    }}
    '''
    results = mp.run_jql(script)
    print(f"  → {len(results)} company×plan combinations returned")
    return results


def step2_paid_users(mp: MixpanelAPI, paid_company_ids: set) -> list:
    """Get individual users who logged in from paid companies."""
    print("\n═══ STEP 2: Individual users from paid companies ═══")
    # JQL can't receive large arrays, so we filter post-query
    script = f'''
    function main() {{
        return Events({{
            from_date: "{FROM_DATE}",
            to_date: "{TO_DATE}",
            event_selectors: [{{event: "Login"}}]
        }})
        .filter(function(e) {{
            var plan = e.properties["Tipo Plan Empresa"];
            return plan && plan !== "pendiente_pago";
        }})
        .groupBy(
            [function(e) {{
                return e.properties["distinct_id"] ||
                       e.properties["$user_id"] ||
                       e.properties["Email"] ||
                       "unknown";
            }},
            function(e) {{
                return e.properties["idEmpresa"] ||
                       e.properties["company_id"] ||
                       (e.properties["$groups"] ? e.properties["$groups"]["Company"] : null) ||
                       "unknown";
            }},
            "properties.Tipo Plan Empresa",
            "properties.Rol",
            "properties.Nombre de Empresa",
            "properties.Email de Administrador"],
            mixpanel.reducer.count()
        )
        .map(function(r) {{
            return {{
                user_id: r.key[0],
                company_id: r.key[1],
                plan_type: r.key[2],
                role: r.key[3],
                company_name: r.key[4],
                admin_email: r.key[5],
                login_count: r.value
            }};
        }});
    }}
    '''
    results = mp.run_jql(script)
    print(f"  → {len(results)} user×company rows returned (all paid plans)")
    return results


def step3_enrich_group_profiles(paid_company_ids: list) -> dict:
    """Fetch Engage API group profiles for paid companies."""
    print("\n═══ STEP 3: Enrich with company group profiles ═══")
    username = os.getenv("MIXPANEL_USERNAME")
    password = os.getenv("MIXPANEL_PASSWORD")
    project_id = os.getenv("MIXPANEL_PROJECT_ID")
    group_type_id = os.getenv("MIXPANEL_GROUP_TYPE_ID_COMPANY", "523052362160430142")

    auth = (username, password)
    url = "https://mixpanel.com/api/2.0/engage"

    # Fetch in batches of 100 (Engage API supports distinct_ids param)
    profiles = {}
    batch_size = 100
    for i in range(0, len(paid_company_ids), batch_size):
        batch = paid_company_ids[i:i + batch_size]
        payload = {
            "project_id": project_id,
            "data_group_id": group_type_id,
            "distinct_ids": json.dumps(batch),
            "page_size": max(100, len(batch)),
        }
        try:
            resp = requests.post(url, data=payload, auth=auth)
            resp.raise_for_status()
            data = resp.json()
            for result in data.get("results", []):
                cid = result.get("$distinct_id")
                props = result.get("$properties", {})
                profiles[str(cid)] = {
                    "Nombre de Empresa": props.get("Nombre de Empresa", ""),
                    "Razon Social": props.get("Razon Social", ""),
                    "Estado": props.get("Estado", ""),
                    "Industria": props.get("Industria (colppy)", props.get("Industria", "")),
                    "Nombre Plan": props.get("Nombre Plan", ""),
                    "Fecha Alta": props.get("Fecha Alta", ""),
                    "Fecha primer pago": props.get("Fecha primer pago", ""),
                    "Fecha Vencimiento": props.get("Fecha Vencimiento", ""),
                    "CUIT": props.get("CUIT", ""),
                    "Email Facturacion": props.get("Email Facturacion", ""),
                    "Es Demo": props.get("Es Demo", ""),
                    "Pais de Registro": props.get("Pais de Registro", ""),
                    "Condicion Iva": props.get("Condicion Iva", ""),
                }
            print(f"  → Batch {i//batch_size + 1}: fetched {len(data.get('results', []))} profiles")
        except Exception as e:
            print(f"  ⚠ Engage API error on batch {i//batch_size + 1}: {e}")

    print(f"  → Total enriched profiles: {len(profiles)}")
    return profiles


def main():
    mp = MixpanelAPI()

    # ── Step 1: Companies by plan ──
    company_plan_data = step1_companies_by_plan(mp)

    # Separate paid vs trial
    paid_companies = {}
    trial_companies = {}
    unknown_companies = {}

    for row in company_plan_data:
        cid = str(row.get("company_id", "unknown"))
        plan = row.get("plan_type", "")
        logins = row.get("login_count", 0)

        if plan == "pendiente_pago":
            trial_companies[cid] = {"plan": plan, "logins": logins}
        elif plan and plan != "undefined":
            paid_companies[cid] = {"plan": plan, "logins": logins}
        else:
            unknown_companies[cid] = {"plan": plan or "(empty)", "logins": logins}

    print(f"\n{'─'*50}")
    print(f"SUMMARY — Login activity {FROM_DATE} to {TO_DATE}")
    print(f"{'─'*50}")
    print(f"  Paid companies:    {len(paid_companies)}")
    print(f"  Trial companies:   {len(trial_companies)}")
    print(f"  Unknown/empty:     {len(unknown_companies)}")
    print(f"  Total companies:   {len(paid_companies) + len(trial_companies) + len(unknown_companies)}")

    # Plan type breakdown for paid
    plan_counts = defaultdict(int)
    for info in paid_companies.values():
        plan_counts[info["plan"]] += 1
    print(f"\n  Paid plan breakdown:")
    for plan, count in sorted(plan_counts.items(), key=lambda x: -x[1]):
        print(f"    {plan}: {count} companies")

    # ── Step 2: Individual paid users ──
    paid_users = step2_paid_users(mp, set(paid_companies.keys()))

    print(f"\n  Unique paid users who logged in: {len(set(u['user_id'] for u in paid_users))}")

    # ── Step 3: Enrich company profiles ──
    paid_ids = list(paid_companies.keys())
    # Filter out "unknown" and non-numeric if needed
    valid_ids = [cid for cid in paid_ids if cid not in ("unknown", "undefined", "null", "")]
    group_profiles = step3_enrich_group_profiles(valid_ids)

    # ── Output: Detailed CSV ──
    csv_path = OUTPUT_DIR / f"paid_customers_logins_{FROM_DATE}_{TO_DATE}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "user_id", "company_id", "plan_type", "role", "company_name_event",
            "admin_email", "login_count",
            # Enriched from group profile
            "gp_nombre_empresa", "gp_razon_social", "gp_estado", "gp_industria",
            "gp_nombre_plan", "gp_fecha_alta", "gp_fecha_primer_pago",
            "gp_fecha_vencimiento", "gp_cuit", "gp_email_facturacion",
            "gp_es_demo", "gp_pais", "gp_condicion_iva"
        ])
        for u in sorted(paid_users, key=lambda x: (-x["login_count"], x["company_id"])):
            cid = str(u.get("company_id", ""))
            gp = group_profiles.get(cid, {})
            writer.writerow([
                u.get("user_id", ""),
                cid,
                u.get("plan_type", ""),
                u.get("role", ""),
                u.get("company_name", ""),
                u.get("admin_email", ""),
                u.get("login_count", 0),
                gp.get("Nombre de Empresa", ""),
                gp.get("Razon Social", ""),
                gp.get("Estado", ""),
                gp.get("Industria", ""),
                gp.get("Nombre Plan", ""),
                gp.get("Fecha Alta", ""),
                gp.get("Fecha primer pago", ""),
                gp.get("Fecha Vencimiento", ""),
                gp.get("CUIT", ""),
                gp.get("Email Facturacion", ""),
                gp.get("Es Demo", ""),
                gp.get("Pais", ""),
                gp.get("Condicion Iva", ""),
            ])

    print(f"\n✅ Detailed CSV saved: {csv_path}")
    print(f"   Rows: {len(paid_users)}")

    # ── Output: Company summary CSV ──
    summary_path = OUTPUT_DIR / f"paid_companies_summary_{FROM_DATE}_{TO_DATE}.csv"
    with open(summary_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "company_id", "plan_type", "total_logins", "unique_users",
            "gp_nombre_empresa", "gp_razon_social", "gp_estado", "gp_industria",
            "gp_nombre_plan", "gp_fecha_alta", "gp_fecha_primer_pago",
            "gp_cuit", "gp_pais"
        ])

        # Aggregate users per company
        company_users = defaultdict(lambda: {"logins": 0, "users": set(), "plan": ""})
        for u in paid_users:
            cid = str(u.get("company_id", ""))
            company_users[cid]["logins"] += u.get("login_count", 0)
            company_users[cid]["users"].add(u.get("user_id", ""))
            company_users[cid]["plan"] = u.get("plan_type", "")

        for cid, info in sorted(company_users.items(), key=lambda x: -x[1]["logins"]):
            gp = group_profiles.get(cid, {})
            writer.writerow([
                cid,
                info["plan"],
                info["logins"],
                len(info["users"]),
                gp.get("Nombre de Empresa", ""),
                gp.get("Razon Social", ""),
                gp.get("Estado", ""),
                gp.get("Industria", ""),
                gp.get("Nombre Plan", ""),
                gp.get("Fecha Alta", ""),
                gp.get("Fecha primer pago", ""),
                gp.get("CUIT", ""),
                gp.get("Pais", ""),
            ])

    print(f"✅ Company summary CSV saved: {summary_path}")
    print(f"   Companies: {len(company_users)}")

    # ── Print top 20 companies by login volume ──
    print(f"\n{'═'*70}")
    print(f"TOP 20 PAID COMPANIES BY LOGIN VOLUME ({FROM_DATE} to {TO_DATE})")
    print(f"{'═'*70}")
    sorted_companies = sorted(company_users.items(), key=lambda x: -x[1]["logins"])
    for i, (cid, info) in enumerate(sorted_companies[:20], 1):
        gp = group_profiles.get(cid, {})
        name = gp.get("Nombre de Empresa") or gp.get("Razon Social") or "(no name)"
        plan = gp.get("Nombre Plan") or info["plan"]
        print(f"  {i:2d}. [{cid}] {name}")
        print(f"      Plan: {plan} | Logins: {info['logins']} | Users: {len(info['users'])}")


if __name__ == "__main__":
    main()
