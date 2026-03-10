#!/usr/bin/env python3
"""
Measure IVA Simple adoption from Mixpanel raw event data.

IVA Simple adds 'actividad' and 'operacion'/'operaciones' properties to
invoice events. Non-IVA-Simple users have these fields as undefined/empty.

Queries:
  - Generó comprobante de venta → check 'actividad' and 'operacion'
  - Generó comprobante de compra → check 'operaciones'

Date range: Dec 2025 (IVA Simple shipped) → now
"""

import sys
import os
import json
import base64
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from dotenv import load_dotenv

# Load env
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
load_dotenv(project_root / ".env")

MIXPANEL_USERNAME = os.getenv("MIXPANEL_USERNAME")
MIXPANEL_PASSWORD = os.getenv("MIXPANEL_PASSWORD")
MIXPANEL_PROJECT_ID = os.getenv("MIXPANEL_PROJECT_ID")

EVENTS = [
    "Generó comprobante de venta",
    "Generó comprobante de compra",
]

FROM_DATE = "2025-12-01"
TO_DATE = "2026-03-10"


def fetch_raw_events():
    import requests

    auth_string = MIXPANEL_USERNAME + ":" + MIXPANEL_PASSWORD
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": "Basic " + encoded_auth,
        "Accept": "text/plain",
    }
    params = {
        "project_id": MIXPANEL_PROJECT_ID,
        "from_date": FROM_DATE,
        "to_date": TO_DATE,
        "event": json.dumps(EVENTS),
    }

    url = "https://data.mixpanel.com/api/2.0/export"
    print(f"Fetching invoice events {FROM_DATE} → {TO_DATE}...")
    print(f"  Events: {EVENTS}")

    response = requests.get(url, params=params, headers=headers, stream=True)
    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text[:500]}")
        sys.exit(1)

    raw_events = []
    for line in response.iter_lines(decode_unicode=True):
        if line and line.strip():
            try:
                raw_events.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    print(f"  Downloaded {len(raw_events)} raw events")
    return raw_events


def is_real_value(val):
    """Check if a value is a real IVA Simple selection (not default/placeholder)."""
    if not val:
        return False
    s = str(val).strip().lower()
    return s not in ("", "0", "seleccionar", "null", "undefined", "none")


def analyze(events):
    # Track IVA Simple usage — three tiers:
    #   - enabled: field present on form (non-null, includes "Seleccionar")
    #   - active:  user actually selected a real value
    venta_total = 0
    venta_enabled = 0   # field present (incl. "Seleccionar")
    venta_active = 0    # real value selected
    compra_total = 0
    compra_enabled = 0
    compra_active = 0

    companies_venta = defaultdict(lambda: {"total": 0, "enabled": 0, "active": 0, "actividades": set(), "operaciones": set()})
    companies_compra = defaultdict(lambda: {"total": 0, "enabled": 0, "active": 0, "operaciones": set()})

    monthly = defaultdict(lambda: {
        "venta_total": 0, "venta_enabled": 0, "venta_active": 0,
        "compra_total": 0, "compra_enabled": 0, "compra_active": 0,
    })

    # Distinct values seen (for understanding the data)
    all_actividad_values = defaultdict(int)
    all_operacion_values = defaultdict(int)
    all_operaciones_values = defaultdict(int)

    sample_active_venta = []
    sample_active_compra = []

    for ev in events:
        props = ev.get("properties", {})
        event_name = ev.get("event", "")
        company = props.get("company", props.get("company_id", "unknown"))
        if isinstance(company, list):
            company = company[0] if company else "unknown"
        company = str(company)

        ts = props.get("time", 0)
        month = datetime.fromtimestamp(ts).strftime("%Y-%m") if ts else "unknown"

        if event_name == "Generó comprobante de venta":
            venta_total += 1
            monthly[month]["venta_total"] += 1
            companies_venta[company]["total"] += 1

            actividad = props.get("actividad")
            operacion = props.get("operacion")

            # Track all distinct values
            if actividad is not None:
                all_actividad_values[str(actividad)] += 1
            if operacion is not None:
                all_operacion_values[str(operacion)] += 1

            # Enabled = field present at all (includes "Seleccionar")
            field_present = actividad is not None or operacion is not None
            if field_present:
                venta_enabled += 1
                monthly[month]["venta_enabled"] += 1
                companies_venta[company]["enabled"] += 1

            # Active = real value selected
            act_real = is_real_value(actividad)
            op_real = is_real_value(operacion)
            if act_real or op_real:
                venta_active += 1
                monthly[month]["venta_active"] += 1
                companies_venta[company]["active"] += 1
                if act_real:
                    companies_venta[company]["actividades"].add(str(actividad))
                if op_real:
                    companies_venta[company]["operaciones"].add(str(operacion))
                if len(sample_active_venta) < 10:
                    sample_active_venta.append({
                        "company": company, "actividad": actividad,
                        "operacion": operacion, "tipo_factura": props.get("tipo_factura"),
                        "amount": props.get("amount"), "month": month,
                    })

        elif event_name == "Generó comprobante de compra":
            compra_total += 1
            monthly[month]["compra_total"] += 1
            companies_compra[company]["total"] += 1

            operaciones = props.get("operaciones")
            if operaciones is not None:
                all_operaciones_values[str(operaciones)] += 1

            field_present = operaciones is not None
            if field_present:
                compra_enabled += 1
                monthly[month]["compra_enabled"] += 1
                companies_compra[company]["enabled"] += 1

            op_real = is_real_value(operaciones)
            if op_real:
                compra_active += 1
                monthly[month]["compra_active"] += 1
                companies_compra[company]["active"] += 1
                companies_compra[company]["operaciones"].add(str(operaciones))
                if len(sample_active_compra) < 10:
                    sample_active_compra.append({
                        "company": company, "operaciones": operaciones,
                        "tipo_factura": props.get("tipo_factura"),
                        "amount": props.get("amount"), "month": month,
                    })

    # Company sets
    enabled_companies_venta = {c for c, d in companies_venta.items() if d["enabled"] > 0}
    active_companies_venta = {c for c, d in companies_venta.items() if d["active"] > 0}
    enabled_companies_compra = {c for c, d in companies_compra.items() if d["enabled"] > 0}
    active_companies_compra = {c for c, d in companies_compra.items() if d["active"] > 0}
    all_enabled = enabled_companies_venta | enabled_companies_compra
    all_active = active_companies_venta | active_companies_compra

    print("\n" + "=" * 70)
    print("IVA SIMPLE ADOPTION REPORT (refined)")
    print(f"Period: {FROM_DATE} → {TO_DATE}")
    print("=" * 70)

    print(f"\n{'─'*70}")
    print(f" VENTAS (Generó comprobante de venta)")
    print(f"{'─'*70}")
    print(f"  Total invoices:                     {venta_total:>10,}")
    print(f"  IVA Simple ENABLED (field present):  {venta_enabled:>10,}  ({venta_enabled/venta_total*100:.1f}%)" if venta_total else "")
    print(f"  IVA Simple ACTIVE (real value):      {venta_active:>10,}  ({venta_active/venta_total*100:.1f}%)" if venta_total else "")
    print(f"  Companies total:                    {len(companies_venta):>10,}")
    print(f"  Companies ENABLED:                  {len(enabled_companies_venta):>10,}")
    print(f"  Companies ACTIVE:                   {len(active_companies_venta):>10,}")

    print(f"\n{'─'*70}")
    print(f" COMPRAS (Generó comprobante de compra)")
    print(f"{'─'*70}")
    print(f"  Total invoices:                     {compra_total:>10,}")
    print(f"  IVA Simple ENABLED (field present):  {compra_enabled:>10,}  ({compra_enabled/compra_total*100:.1f}%)" if compra_total else "")
    print(f"  IVA Simple ACTIVE (real value):      {compra_active:>10,}  ({compra_active/compra_total*100:.1f}%)" if compra_total else "")
    print(f"  Companies total:                    {len(companies_compra):>10,}")
    print(f"  Companies ENABLED:                  {len(enabled_companies_compra):>10,}")
    print(f"  Companies ACTIVE:                   {len(active_companies_compra):>10,}")

    print(f"\n{'─'*70}")
    print(f" COMBINED")
    print(f"{'─'*70}")
    print(f"  Companies with IVA Simple ENABLED:  {len(all_enabled):>10,}")
    print(f"  Companies with IVA Simple ACTIVE:   {len(all_active):>10,}")

    print(f"\n{'─'*70}")
    print(f" MONTHLY BREAKDOWN")
    print(f"{'─'*70}")
    for month in sorted(monthly.keys()):
        m = monthly[month]
        print(f"\n  {month}:")
        if m['venta_total']:
            er = f"{m['venta_enabled']/m['venta_total']*100:.1f}%"
            ar = f"{m['venta_active']/m['venta_total']*100:.1f}%"
            print(f"    Ventas:  {m['venta_total']:>8,} total | {m['venta_enabled']:>8,} enabled ({er}) | {m['venta_active']:>8,} active ({ar})")
        if m['compra_total']:
            er = f"{m['compra_enabled']/m['compra_total']*100:.1f}%"
            ar = f"{m['compra_active']/m['compra_total']*100:.1f}%"
            print(f"    Compras: {m['compra_total']:>8,} total | {m['compra_enabled']:>8,} enabled ({er}) | {m['compra_active']:>8,} active ({ar})")

    print(f"\n{'─'*70}")
    print(f" DISTINCT VALUES OBSERVED")
    print(f"{'─'*70}")
    print(f"\n  actividad (top 15):")
    for val, count in sorted(all_actividad_values.items(), key=lambda x: -x[1])[:15]:
        real = "✓" if is_real_value(val) else "✗"
        print(f"    {real} {val[:70]}: {count:,}")

    print(f"\n  operacion (top 15):")
    for val, count in sorted(all_operacion_values.items(), key=lambda x: -x[1])[:15]:
        real = "✓" if is_real_value(val) else "✗"
        print(f"    {real} {val[:70]}: {count:,}")

    print(f"\n  operaciones / compras (top 15):")
    for val, count in sorted(all_operaciones_values.items(), key=lambda x: -x[1])[:15]:
        real = "✓" if is_real_value(val) else "✗"
        print(f"    {real} {val[:70]}: {count:,}")

    if sample_active_venta:
        print(f"\n{'─'*70}")
        print(f" SAMPLE ACTIVE VENTA EVENTS (real values)")
        print(f"{'─'*70}")
        for s in sample_active_venta:
            print(f"  Company {s['company']}: actividad={s['actividad']}, "
                  f"operacion={s['operacion']}, tipo={s['tipo_factura']}, month={s['month']}")

    if sample_active_compra:
        print(f"\n{'─'*70}")
        print(f" SAMPLE ACTIVE COMPRA EVENTS (real values)")
        print(f"{'─'*70}")
        for s in sample_active_compra:
            print(f"  Company {s['company']}: operaciones={s['operaciones']}, "
                  f"tipo={s['tipo_factura']}, month={s['month']}")

    # Top ACTIVE companies
    top_active = sorted(
        [(c, d["active"], d["total"]) for c, d in companies_venta.items() if d["active"] > 0],
        key=lambda x: -x[1]
    )[:15]
    if top_active:
        print(f"\n{'─'*70}")
        print(f" TOP 15 ACTIVE IVA SIMPLE COMPANIES (ventas)")
        print(f"{'─'*70}")
        for c, active, total in top_active:
            acts = companies_venta[c]["actividades"]
            ops = companies_venta[c]["operaciones"]
            pct = f"{active/total*100:.0f}%"
            print(f"  Company {c}: {active}/{total} invoices ({pct})")
            if acts:
                print(f"    Actividades: {acts}")
            if ops:
                print(f"    Operaciones: {ops}")

    # Save full results
    output = {
        "period": {"from": FROM_DATE, "to": TO_DATE},
        "summary": {
            "venta_total": venta_total,
            "venta_enabled": venta_enabled,
            "venta_active": venta_active,
            "compra_total": compra_total,
            "compra_enabled": compra_enabled,
            "compra_active": compra_active,
            "unique_companies_enabled": len(all_enabled),
            "unique_companies_active": len(all_active),
            "total_companies_venta": len(companies_venta),
            "total_companies_compra": len(companies_compra),
        },
        "monthly": {m: dict(d) for m, d in sorted(monthly.items())},
        "distinct_values": {
            "actividad": dict(sorted(all_actividad_values.items(), key=lambda x: -x[1])),
            "operacion": dict(sorted(all_operacion_values.items(), key=lambda x: -x[1])),
            "operaciones": dict(sorted(all_operaciones_values.items(), key=lambda x: -x[1])),
        },
        "enabled_companies": sorted(all_enabled),
        "active_companies": sorted(all_active),
        "samples_active_venta": sample_active_venta,
        "samples_active_compra": sample_active_compra,
    }

    output_path = project_root / "output" / "iva_simple_adoption.json"
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nFull results saved to {output_path}")


if __name__ == "__main__":
    events = fetch_raw_events()
    analyze(events)
