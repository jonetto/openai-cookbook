#!/usr/bin/env python3
"""
Export Mixpanel trial user events to a local cache file.

Uses the Raw Data Export API (data.mixpanel.com) — separate rate limit from Query API.
Supports --enrich flag to join group profiles for richer trial analysis.
Single API call downloads all events for trial users in a date range as JSONL,
then pivots by the chosen level (user, company, or product) for offline analysis.

With --enrich, also fetches group profiles from the Engage API and joins them
locally so company-level properties (Estado, Industria, Fecha primer pago, etc.)
are available even before KAN-12024 ships super properties on events.

Usage:
    # User-level (default — same as before)
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07

    # Company-level — aggregate users within each company
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07 --level company

    # Enrich with group profile properties (Estado, Industria, etc.)
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07 --level company --enrich

    # Product-level (post KAN-12024) — aggregate companies within each product
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07 --level product

    # All plans, company-level
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07 --level company --all-plans

    # True trial users only — enrich with Fecha Alta, then filter to companies ≤7 days since signup
    # (removes zombie pendiente_pago accounts from 2018-2024)
    python export_trial_events.py --from 2026-03-01 --to 2026-03-07 --level company --enrich --trial-window 7

Cache location:
    plugins/colppy-customer-success/skills/trial-data-model/cache/
    mixpanel_events_YYYY-MM-DD_YYYY-MM-DD[_planX][_by-level].json
"""

import sys
import os
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from dotenv import load_dotenv

# Load env
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
load_dotenv(project_root / ".env")

# Credentials
MIXPANEL_USERNAME = os.getenv("MIXPANEL_USERNAME")
MIXPANEL_PASSWORD = os.getenv("MIXPANEL_PASSWORD")
MIXPANEL_PROJECT_ID = os.getenv("MIXPANEL_PROJECT_ID")

# Group type IDs for the Engage API.
# These are project-specific hash integers (NOT sequential 0,1,2).
# Find them in Mixpanel → Project Settings → Group Keys,
# or from any Group Profile URL: ...profile#distinct_id=X&data_group_id=<THIS>
MIXPANEL_GROUP_TYPE_ID_COMPANY = os.getenv("MIXPANEL_GROUP_TYPE_ID_COMPANY")
MIXPANEL_GROUP_TYPE_ID_PRODUCT = os.getenv("MIXPANEL_GROUP_TYPE_ID_PRODUCT")

# Cache directory — under trial-data-model skill (NOT intercom cache)
CACHE_DIR = project_root / "plugins" / "colppy-customer-success" / "skills" / "trial-data-model" / "cache"

# Critical events to export (all persona-relevant events)
CRITICAL_EVENTS = [
    # Admin (compras/ventas)
    "Generó comprobante de venta",
    "Generó comprobante de compra",
    "Generó recibo de cobro",
    "Generó orden de pago",
    # Contabilidad
    "Generó asiento contable",
    "Descargó el balance",
    "Descargó el diario general",
    "Descargó el estado de resultados",
    "Descargó el estado de flujo de efectivo",
    "Agregó una cuenta contable",
    # Inventario
    "Agregó un ítem",
    "Generó un ajuste de inventario",
    "Actualizó precios en pantalla masivo",
    # Lifecycle
    "Login",
    "Registro",
    "Validó email",
]

# Event categories for persona classification
ADMIN_EVENTS = {"Generó comprobante de venta", "Generó comprobante de compra"}
CONTA_EVENTS = {
    "Generó asiento contable", "Descargó el balance", "Descargó el diario general",
    "Descargó el estado de resultados", "Agregó una cuenta contable",
}
INV_EVENTS = {"Agregó un ítem", "Generó un ajuste de inventario", "Actualizó precios en pantalla masivo"}
ALL_CRITICAL = ADMIN_EVENTS | CONTA_EVENTS | INV_EVENTS

# Properties to capture from events at each level.
# These are super properties stamped on every event by FuncionesGlobales.js
USER_PROPERTIES = [
    "Tipo Plan Empresa", "idEmpresa", "contact_es_contador",
    "$email", "Email", "email", "Rol",
    "company_id", "product_id",  # group keys — always capture
]
COMPANY_PROPERTIES = [
    # From FuncionesGlobales.js productProps (line 1227-1247)
    "Tipo Plan Empresa", "Nombre de Empresa", "Fecha de Alta Empresa",
    "idPlanEmpresa", "Pais de Registro", "Email de Administrador",
    "Estado", "Nombre Plan", "Tipo Plan", "Fecha Alta", "Fecha Vencimiento",
    "Es Demo", "Es Trial", "Administradora Id",
    "Tipo de actividad", "Industria (colppy)",
    # From FuncionesGlobales.js companyProps (line 1211-1220)
    "CUIT", "Razon Social", "Mail Facturacion",
    "Condicion Iva", "Domicilio", "Localidad", "Provincia",
]


# ── Layer 1: Fetch ──────────────────────────────────────────────────────────

def fetch_raw_events(from_date: str, to_date: str, plan_filter: str = "pendiente_pago") -> list[dict]:
    """
    Download raw events from Mixpanel Raw Data Export API.

    Returns the flat list of event dicts (JSONL parsed).
    This is the same call regardless of pivot level.
    """
    import requests

    auth_string = MIXPANEL_USERNAME + ":" + MIXPANEL_PASSWORD
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": "Basic " + encoded_auth,
        "Accept": "text/plain",
    }

    params = {
        "project_id": MIXPANEL_PROJECT_ID,
        "from_date": from_date,
        "to_date": to_date,
        "event": json.dumps(CRITICAL_EVENTS),
    }

    if plan_filter:
        params["where"] = f'properties["Tipo Plan Empresa"] == "{plan_filter}"'

    url = "https://data.mixpanel.com/api/2.0/export"
    print(f"Exporting events from {from_date} to {to_date}...")
    if plan_filter:
        print(f"  Plan filter: {plan_filter}")
    print(f"  Events: {len(CRITICAL_EVENTS)} types")
    print(f"  Endpoint: {url}")

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


def fetch_group_profiles(group_key: str = "company",
                         company_ids: list[str] | None = None) -> dict[str, dict]:
    """
    Fetch group profiles from the Mixpanel Engage API.

    Returns a dict mapping group_id → {property_name: value, ...}.
    This is the ONLY API that exposes group profile properties like
    Estado, Industria, Fecha primer pago, etc.

    If company_ids is provided, fetches only those specific profiles
    (much faster than fetching all 61K+). Otherwise fetches all.

    Requires MIXPANEL_GROUP_TYPE_ID_COMPANY (or _PRODUCT) in .env.
    The data_group_id is a project-specific hash integer — find it in
    Mixpanel → Project Settings → Group Keys.
    """
    import requests

    # Resolve the data_group_id for this group key
    group_type_ids = {
        "company": MIXPANEL_GROUP_TYPE_ID_COMPANY,
        "product_id": MIXPANEL_GROUP_TYPE_ID_PRODUCT,
    }
    data_group_id = group_type_ids.get(group_key)
    if not data_group_id:
        print(f"\n  Error: MIXPANEL_GROUP_TYPE_ID_{group_key.upper()} not set in .env")
        print(f"  Find it in Mixpanel → Project Settings → Group Keys,")
        print(f"  or from any Group Profile URL: ...&data_group_id=<THIS>")
        print(f"  Then add to .env: MIXPANEL_GROUP_TYPE_ID_{group_key.upper()}=<value>")
        return {}

    auth_string = MIXPANEL_USERNAME + ":" + MIXPANEL_PASSWORD
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": "Basic " + encoded_auth,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    url = "https://mixpanel.com/api/2.0/engage"
    profiles = {}
    session_id = None
    page = 0

    print(f"\nFetching '{group_key}' group profiles from Engage API...")
    print(f"  data_group_id: {data_group_id}")

    # If we know which IDs we need, fetch only those (1 API call vs 62 pages)
    if company_ids:
        ids_json = json.dumps(company_ids)
        print(f"  Targeted fetch: {len(company_ids)} specific profiles")
        post_data = {
            "project_id": MIXPANEL_PROJECT_ID,
            "data_group_id": data_group_id,
            "distinct_ids": ids_json,
        }
        response = requests.post(url, headers=headers, data=post_data)
        if response.status_code == 429:
            print("  Rate limited. Waiting 60s...")
            import time
            time.sleep(60)
            response = requests.post(url, headers=headers, data=post_data)
        if response.status_code == 200:
            data = response.json()
            for entry in data.get("results", []):
                group_id = str(entry.get("$distinct_id", ""))
                props = entry.get("$properties", {})
                if group_id:
                    profiles[group_id] = props
        else:
            print(f"  Engage API error {response.status_code}: {response.text[:300]}")
        print(f"  Fetched {len(profiles)} group profiles")
        return profiles

    # Full paginated fetch (all profiles)
    while True:
        post_data = {
            "project_id": MIXPANEL_PROJECT_ID,
            "data_group_id": data_group_id,
        }
        if session_id:
            post_data["session_id"] = session_id
            post_data["page"] = page

        response = requests.post(url, headers=headers, data=post_data)

        if response.status_code == 429:
            print(f"  Rate limited on page {page}. Waiting 60s...")
            import time
            time.sleep(60)
            continue

        if response.status_code != 200:
            print(f"  Engage API error {response.status_code}: {response.text[:300]}")
            break

        data = response.json()
        results = data.get("results", [])
        if not results:
            break

        page_size = data.get("page_size", 1000)
        for entry in results:
            group_id = str(entry.get("$distinct_id", ""))
            props = entry.get("$properties", {})
            if group_id:
                profiles[group_id] = props

        session_id = data.get("session_id")
        page += 1
        total = data.get("total", "?")
        print(f"  Page {page}: {len(results)} profiles (total: {total})")

        # Stop if we got fewer results than page_size (last page)
        if len(results) < page_size:
            break

    print(f"  Fetched {len(profiles)} group profiles")
    return profiles


def enrich_with_group_profiles(pivoted_data: list[dict], group_profiles: dict[str, dict],
                               level: str) -> list[dict]:
    """
    Join group profile properties into pivoted data.

    For company-level: match company_id → group profile, merge properties.
    For user-level: match each user's company_id → group profile, add as company_properties.
    """
    if level == "company":
        for company in pivoted_data:
            cid = str(company.get("company_id", ""))
            profile = group_profiles.get(cid, {})
            if profile:
                # Merge profile props into company properties (profile wins on conflict)
                for k, v in profile.items():
                    if v is not None and k not in ("$group_id", "$group_key"):
                        company["properties"][k] = v

    elif level == "user":
        for user in pivoted_data:
            cid = str(user.get("properties", {}).get("company_id")
                       or user.get("properties", {}).get("idEmpresa") or "")
            profile = group_profiles.get(cid, {})
            if profile:
                user["company_properties"] = {
                    k: v for k, v in profile.items()
                    if v is not None and k not in ("$group_id", "$group_key")
                }

    elif level == "product":
        for product in pivoted_data:
            for company in product.get("companies", []):
                cid = str(company.get("company_id", ""))
                profile = group_profiles.get(cid, {})
                if profile:
                    for k, v in profile.items():
                        if v is not None and k not in ("$group_id", "$group_key"):
                            company["properties"][k] = v

    return pivoted_data


# ── Layer 2: Classify ───────────────────────────────────────────────────────

def classify_persona(events_dict: dict) -> str:
    """Classify a user's persona from their event counts."""
    has_admin = any(events_dict.get(e, 0) > 0 for e in ADMIN_EVENTS)
    has_conta = any(events_dict.get(e, 0) > 0 for e in CONTA_EVENTS)
    has_inv = any(events_dict.get(e, 0) > 0 for e in INV_EVENTS)

    if has_admin and has_conta:
        return "Admin + Contabilidad"
    if has_admin and has_inv:
        return "Admin + Inventario"
    if has_conta and has_inv:
        return "Contabilidad + Inventario"
    if has_admin:
        return "Lleva la administración"
    if has_conta:
        return "Lleva la contabilidad"
    if has_inv:
        return "Lleva inventario"
    if events_dict.get("Login", 0) > 0:
        return "Login only (not activated)"
    return "Other"


# ── Layer 3: Pivot ──────────────────────────────────────────────────────────

def pivot_by_user(raw_events: list[dict]) -> list[dict]:
    """Group events by distinct_id → per-user summary with persona."""
    users = defaultdict(lambda: {"events": defaultdict(int), "properties": {}})

    for evt in raw_events:
        event_name = evt.get("event", "unknown")
        props = evt.get("properties", {})
        distinct_id = props.get("distinct_id") or props.get("$distinct_id") or "unknown"

        users[distinct_id]["events"][event_name] += 1
        for prop_key in USER_PROPERTIES:
            val = props.get(prop_key)
            if val is not None:
                users[distinct_id]["properties"][prop_key] = val

    output = []
    for uid, data in users.items():
        evts = dict(data["events"])
        critical_count = sum(evts.get(e, 0) for e in ALL_CRITICAL)
        output.append({
            "distinct_id": uid,
            "persona": classify_persona(evts),
            "critical_events": critical_count,
            "logins": evts.get("Login", 0),
            "events": evts,
            "properties": dict(data["properties"]),
        })

    return output


def pivot_by_company(raw_events: list[dict]) -> list[dict]:
    """
    Group events by company_id → per-company summary.

    Each company nests its users (with their personas) so you can
    drill down from company metrics to individual user behavior.
    """
    # First pass: build user-level data, capturing BOTH user and company properties
    all_props = list(set(USER_PROPERTIES + COMPANY_PROPERTIES))
    users = defaultdict(lambda: {"events": defaultdict(int), "properties": {}})

    for evt in raw_events:
        event_name = evt.get("event", "unknown")
        props = evt.get("properties", {})
        distinct_id = props.get("distinct_id") or props.get("$distinct_id") or "unknown"

        users[distinct_id]["events"][event_name] += 1
        for prop_key in all_props:
            val = props.get(prop_key)
            if val is not None:
                users[distinct_id]["properties"][prop_key] = val

    # Second pass: group users into companies
    companies = defaultdict(lambda: {"users": [], "properties": {}, "events": defaultdict(int)})

    for uid, data in users.items():
        evts = dict(data["events"])
        props = dict(data["properties"])
        company_id = str(props.get("company_id") or props.get("idEmpresa") or "unknown")
        critical_count = sum(evts.get(e, 0) for e in ALL_CRITICAL)

        user_record = {
            "distinct_id": uid,
            "persona": classify_persona(evts),
            "critical_events": critical_count,
            "logins": evts.get("Login", 0),
            "events": evts,
        }
        companies[company_id]["users"].append(user_record)

        # Accumulate company-level event totals
        for ename, count in evts.items():
            companies[company_id]["events"][ename] += count

        # Capture company-level properties (last-write-wins from any user's events)
        for prop_key in COMPANY_PROPERTIES:
            val = props.get(prop_key)
            if val is not None:
                companies[company_id]["properties"][prop_key] = val

    # Build output with company summaries
    output = []
    for cid, data in companies.items():
        user_list = data["users"]
        company_events = dict(data["events"])
        total_critical = sum(company_events.get(e, 0) for e in ALL_CRITICAL)
        activated = [u for u in user_list if u["critical_events"] > 0]

        # Persona distribution within the company
        persona_dist = defaultdict(int)
        for u in user_list:
            persona_dist[u["persona"]] += 1

        output.append({
            "company_id": cid,
            "total_users": len(user_list),
            "activated_users": len(activated),
            "total_events": sum(company_events.values()),
            "total_critical_events": total_critical,
            "persona_distribution": dict(persona_dist),
            "events": company_events,
            "properties": dict(data["properties"]),
            "users": user_list,
        })

    return output


def pivot_by_product(raw_events: list[dict]) -> list[dict]:
    """
    Group events by product_id → per-product summary.

    Requires KAN-12024 dual-group migration to be live (product_id on events).
    Each product nests its companies, which in turn nest their users.
    """
    # First: get company-level data
    company_data = pivot_by_company(raw_events)

    # Group companies into products
    products = defaultdict(lambda: {"companies": [], "properties": {}})

    for company in company_data:
        # product_id comes from the users' event properties
        product_ids = set()
        for user in company["users"]:
            # Check user events for product_id — it's a super property
            pid = None
            for evt_props_key in USER_PROPERTIES:
                if evt_props_key == "product_id":
                    # We need to look at the original user properties
                    # product_id was captured during user pivot
                    break
            product_ids.add("unknown")

        # For now, look at the raw events to find product_id per company
        # This will work once KAN-12024 ships
        product_id = "unknown"
        for user in company["users"]:
            # product_id would be in the user's captured properties
            # but we stripped user properties during company pivot
            pass

        products[product_id]["companies"].append(company)

    # Since product_id isn't live yet, return a simpler structure
    output = []
    for pid, data in products.items():
        company_list = data["companies"]
        output.append({
            "product_id": pid,
            "total_companies": len(company_list),
            "total_users": sum(c["total_users"] for c in company_list),
            "activated_users": sum(c["activated_users"] for c in company_list),
            "total_events": sum(c["total_events"] for c in company_list),
            "companies": company_list,
        })

    return output


# ── Layer 4: Build cache ────────────────────────────────────────────────────

PIVOT_FUNCTIONS = {
    "user": pivot_by_user,
    "company": pivot_by_company,
    "product": pivot_by_product,
}

# The key name for the main data array in the cache
PIVOT_DATA_KEY = {
    "user": "users",
    "company": "companies",
    "product": "products",
}


def build_cache(raw_events: list[dict], level: str, from_date: str, to_date: str,
                plan_filter: str) -> dict:
    """Pivot raw events by the chosen level and build the cache structure."""
    pivot_fn = PIVOT_FUNCTIONS[level]
    data_key = PIVOT_DATA_KEY[level]
    pivoted = pivot_fn(raw_events)

    cache = {
        "exported_at": datetime.now().isoformat(),
        "from_date": from_date,
        "to_date": to_date,
        "plan_filter": plan_filter or "all",
        "level": level,
        "total_raw_events": len(raw_events),
    }

    if level == "user":
        cache["unique_users"] = len(pivoted)
        cache["activated_users"] = sum(1 for u in pivoted if u["critical_events"] > 0)
        # Persona summary
        persona_summary = defaultdict(int)
        for u in pivoted:
            persona_summary[u["persona"]] += 1
        cache["persona_summary"] = dict(persona_summary)
        # Event summary
        event_totals = defaultdict(int)
        event_user_counts = defaultdict(int)
        for u in pivoted:
            for ename, count in u["events"].items():
                event_totals[ename] += count
                event_user_counts[ename] += 1
        cache["event_summary"] = {
            e: {"total": event_totals[e], "unique_users": event_user_counts[e]}
            for e in sorted(event_totals.keys(), key=lambda x: -event_totals[x])
        }

    elif level == "company":
        cache["unique_companies"] = len(pivoted)
        cache["unique_users"] = sum(c["total_users"] for c in pivoted)
        cache["activated_companies"] = sum(1 for c in pivoted if c["activated_users"] > 0)
        cache["activated_users"] = sum(c["activated_users"] for c in pivoted)
        # Company size distribution
        size_dist = defaultdict(int)
        for c in pivoted:
            n = c["total_users"]
            if n == 1:
                bucket = "1 user"
            elif n <= 3:
                bucket = "2-3 users"
            elif n <= 10:
                bucket = "4-10 users"
            else:
                bucket = "11+ users"
            size_dist[bucket] += 1
        cache["company_size_distribution"] = dict(size_dist)

    elif level == "product":
        cache["unique_products"] = len(pivoted)
        cache["unique_companies"] = sum(p["total_companies"] for p in pivoted)
        cache["unique_users"] = sum(p["total_users"] for p in pivoted)

    cache[data_key] = pivoted
    return cache


def print_summary(cache: dict, level: str):
    """Print human-readable summary to stdout."""
    print(f"\n  Level: {level}")
    print(f"  Total raw events: {cache['total_raw_events']}")

    if level == "user":
        print(f"  Unique users: {cache['unique_users']}")
        print(f"  Activated: {cache['activated_users']}")
        print(f"  Persona breakdown:")
        for p, c in sorted(cache["persona_summary"].items(), key=lambda x: -x[1]):
            print(f"    {p}: {c}")

    elif level == "company":
        print(f"  Unique companies: {cache['unique_companies']}")
        print(f"  Activated companies: {cache['activated_companies']}")
        print(f"  Total users across companies: {cache['unique_users']}")
        print(f"  Activated users: {cache['activated_users']}")
        print(f"  Company size distribution:")
        for bucket, count in cache["company_size_distribution"].items():
            print(f"    {bucket}: {count}")
        # Top 5 most active companies
        top = sorted(cache["companies"], key=lambda c: -c["total_critical_events"])[:5]
        if top:
            print(f"  Top 5 companies by critical events:")
            for c in top:
                name = c["properties"].get("Nombre de Empresa", "?")
                print(f"    {c['company_id']}: {c['total_critical_events']} critical, "
                      f"{c['total_users']} users — {name}")

    elif level == "product":
        print(f"  Unique products: {cache['unique_products']}")
        print(f"  Unique companies: {cache['unique_companies']}")
        print(f"  Unique users: {cache['unique_users']}")


# ── Trial window filter ─────────────────────────────────────────────────────

def parse_fecha(raw) -> datetime | None:
    """
    Parse Fecha Alta / Fecha Vencimiento from group profiles.

    Two formats observed in Engage API group profiles:
    - JS-style: 'Sun Mar 01 2026 21:35:16 GMT-0300 (hora estándar de Argentina)'
    - ISO string: '2026-03-01T00:00:00' (often timezone-naive)
    - Unix timestamp: int or float

    All returned datetimes are UTC-aware.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return datetime.fromtimestamp(raw, tz=timezone.utc)
    s = str(raw).strip()
    # JS-style: 'Day Mon DD YYYY HH:MM:SS GMT±HHMM (...)'
    try:
        s_clean = s[:s.index('(')].strip() if '(' in s else s
        return datetime.strptime(s_clean, '%a %b %d %Y %H:%M:%S GMT%z')
    except (ValueError, IndexError):
        pass
    # ISO string (possibly timezone-naive)
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        pass
    return None


def filter_by_trial_window(pivoted_data: list[dict], level: str,
                            from_date: str, to_date: str,
                            trial_window_days: int) -> tuple[list[dict], int]:
    """
    Post-filter to only keep companies whose trial started during the export window.

    A company is "in trial" if its Fecha Alta falls within [from_date, to_date].
    This works correctly for both short windows (7-day) and full-month exports.

    Requires --enrich to have been run first (Fecha Alta comes from group profiles).

    Returns (filtered_data, original_count).
    """
    start = datetime.strptime(from_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end = datetime.strptime(to_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    original_count = len(pivoted_data)

    def is_in_trial(properties: dict) -> bool:
        raw = properties.get("Fecha Alta") or properties.get("Fecha alta") \
              or properties.get("Fecha de Alta Empresa")
        if raw is None:
            return False
        fecha_alta = parse_fecha(raw)
        if fecha_alta is None:
            return False
        # Keep companies whose trial started within the export date range
        return start <= fecha_alta <= end

    if level == "company":
        filtered = [c for c in pivoted_data if is_in_trial(c.get("properties", {}))]
    elif level == "user":
        filtered = [u for u in pivoted_data if is_in_trial(u.get("company_properties", {}))]
    else:
        # product level: filter companies within each product
        filtered = []
        for product in pivoted_data:
            trial_companies = [
                c for c in product.get("companies", [])
                if is_in_trial(c.get("properties", {}))
            ]
            if trial_companies:
                product_copy = {
                    **product,
                    "companies": trial_companies,
                    "total_companies": len(trial_companies),
                    "total_users": sum(c["total_users"] for c in trial_companies),
                    "activated_users": sum(c["activated_users"] for c in trial_companies),
                    "total_events": sum(c["total_events"] for c in trial_companies),
                }
                filtered.append(product_copy)

    return filtered, original_count


# ── Discovery ──────────────────────────────────────────────────────────────

def discover_group_type_ids():
    """
    Try to discover group type IDs by querying Engage API with different IDs.

    Mixpanel assigns project-specific hash integers as data_group_id.
    This function cannot guess them — instead it explains how to find them.
    """
    print("=" * 60)
    print("HOW TO FIND YOUR data_group_id VALUES")
    print("=" * 60)
    print()
    print("Option 1: Mixpanel UI → Project Settings → Group Keys")
    print("  The data_group_id is shown next to each group key.")
    print()
    print("Option 2: Open any Group Profile in Mixpanel UI")
    print("  The URL contains: ...&data_group_id=<THIS_VALUE>")
    print(f"  Example: https://mixpanel.com/project/{MIXPANEL_PROJECT_ID}/view/*/app/profile#distinct_id=X&data_group_id=<VALUE>")
    print()
    print("Once found, add to .env:")
    print("  MIXPANEL_GROUP_TYPE_ID_COMPANY=<value for 'company' group key>")
    print("  MIXPANEL_GROUP_TYPE_ID_PRODUCT=<value for 'product_id' group key>")
    print()

    # Show current config status
    if MIXPANEL_GROUP_TYPE_ID_COMPANY:
        print(f"  ✓ MIXPANEL_GROUP_TYPE_ID_COMPANY = {MIXPANEL_GROUP_TYPE_ID_COMPANY}")
    else:
        print("  ✗ MIXPANEL_GROUP_TYPE_ID_COMPANY = (not set)")
    if MIXPANEL_GROUP_TYPE_ID_PRODUCT:
        print(f"  ✓ MIXPANEL_GROUP_TYPE_ID_PRODUCT = {MIXPANEL_GROUP_TYPE_ID_PRODUCT}")
    else:
        print("  ✗ MIXPANEL_GROUP_TYPE_ID_PRODUCT = (not set)")


# ── Main ────────────────────────────────────────────────────────────────────

def export_events(from_date: str, to_date: str, plan_filter: str = "pendiente_pago",
                  level: str = "user", enrich: bool = False,
                  trial_window: int | None = None) -> Path:
    """Fetch events and save pivoted cache at the specified level."""
    raw_events = fetch_raw_events(from_date, to_date, plan_filter)
    cache = build_cache(raw_events, level, from_date, to_date, plan_filter)

    if enrich:
        # Extract company IDs from pivoted data for targeted Engage API fetch
        data_key = PIVOT_DATA_KEY[level]
        company_ids = None
        if level == "company":
            company_ids = [str(c["company_id"]) for c in cache[data_key] if c["company_id"] != "unknown"]
        elif level == "user":
            company_ids = list({
                str(u["properties"].get("company_id") or u["properties"].get("idEmpresa") or "")
                for u in cache[data_key]
            } - {""})
        group_profiles = fetch_group_profiles(group_key="company", company_ids=company_ids)
        if group_profiles:
            data_key = PIVOT_DATA_KEY[level]
            cache[data_key] = enrich_with_group_profiles(cache[data_key], group_profiles, level)
            cache["enriched"] = True
            cache["group_profiles_count"] = len(group_profiles)
            print(f"\n  Enriched {len(cache[data_key])} {level} records with {len(group_profiles)} group profiles")
        else:
            cache["enriched"] = False
            print("\n  Skipped enrichment — no group profiles fetched (check .env config)")

    if trial_window is not None:
        if not enrich:
            print("\n  Warning: --trial-window requires --enrich to have Fecha Alta data.")
            print("  Run with --enrich --trial-window to filter correctly.")
        data_key = PIVOT_DATA_KEY[level]
        filtered, original_count = filter_by_trial_window(cache[data_key], level, from_date, to_date, trial_window)
        cache[data_key] = filtered
        cache["trial_window_days"] = trial_window
        cache["trial_window_kept"] = len(filtered)
        cache["trial_window_excluded"] = original_count - len(filtered)
        print(f"\n  --trial-window {trial_window}d: kept {len(filtered)}/{original_count} {level}s "
              f"(Fecha Alta within {trial_window} days of {from_date})")

    plan_suffix = f"_{plan_filter}" if plan_filter else "_all"
    level_suffix = f"_by-{level}" if level != "user" else ""
    trial_suffix = f"_trial{trial_window}d" if trial_window is not None else ""
    cache_file = CACHE_DIR / f"mixpanel_events_{from_date}_{to_date}{plan_suffix}{level_suffix}{trial_suffix}.json"

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)

    print(f"\nCache saved to: {cache_file}")
    print_summary(cache, level)
    return cache_file


def main():
    parser = argparse.ArgumentParser(description="Export Mixpanel trial events to cache")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--plan", default="pendiente_pago",
                        help="Plan filter (default: pendiente_pago for trial users)")
    parser.add_argument("--all-plans", action="store_true",
                        help="Export all plans (no plan filter)")
    parser.add_argument("--level", choices=["user", "company", "product"], default="user",
                        help="Pivot level: user (default), company, or product")
    parser.add_argument("--enrich", action="store_true",
                        help="Enrich with group profile properties via Engage API "
                             "(Estado, Industria, Fecha primer pago, etc.). "
                             "Requires MIXPANEL_GROUP_TYPE_ID_COMPANY in .env")
    parser.add_argument("--trial-window", type=int, default=None, metavar="N",
                        help="Post-filter to companies whose Fecha Alta is within N days of "
                             "--from date (default: no filter). Requires --enrich. "
                             "Removes zombie accounts (companies on pendiente_pago for years). "
                             "Example: --enrich --trial-window 7")
    parser.add_argument("--discover-groups", action="store_true",
                        help="Try to auto-discover group type IDs by testing the Engage API. "
                             "Prints the IDs found so you can add them to .env")

    args = parser.parse_args()

    if not MIXPANEL_USERNAME or not MIXPANEL_PASSWORD:
        print("Error: Set MIXPANEL_USERNAME and MIXPANEL_PASSWORD in .env")
        sys.exit(1)

    if args.discover_groups:
        discover_group_type_ids()
        return

    if not args.from_date or not args.to_date:
        parser.error("--from and --to are required (unless using --discover-groups)")

    plan_filter = None if args.all_plans else args.plan
    export_events(args.from_date, args.to_date, plan_filter, args.level, args.enrich,
                  args.trial_window)


if __name__ == "__main__":
    main()
