#!/usr/bin/env python3
"""
EVALUATOR QUALITY ANALYSIS
===========================

Analyzes the quality of evaluators (MQLs) entering the product flywheel by
acquisition channel, ICP, and persona. Shows which channels produce evaluators
that activate (PQL), create deals (SQL), win deals, and generate MRR.

CHANNEL CLASSIFICATION (uses initial_utm_* fields — ~92% coverage):
- Google Ads: initial_utm_source="google" AND initial_utm_medium="ppc"
- Meta Ads: initial_utm_source contains "facebook"/"instagram"/"meta"
- LinkedIn Ads: initial_utm_source="linkedin" AND initial_utm_medium="linkedin"
- Organic Search: no initial_utm_source AND hs_analytics_source=ORGANIC_SEARCH
- Direct: no initial_utm_source AND hs_analytics_source=DIRECT_TRAFFIC
- Connections (Contador): lead_source indicates accountant connection
- Connections (Peer): lead_source indicates peer/customer connection
- Colppy Portal: initial_utm_source="Colppy" AND initial_utm_campaign="referral_portal_clientes"
- Other: everything else

ICP CLASSIFICATION (company-level):
- Cuenta Contador: company type in ['Cuenta Contador', 'Cuenta Contador y Reseller', 'Contador Robado']
- Cuenta Pyme: any other company type
- Unclassified: no associated company

PERSONA CLASSIFICATION (user-level):
- Accounting: rol_wizard in ['Contador', 'Estudio contable']
- Administrative: rol_wizard in ['Administrador', 'Dueño', 'Gerente']
- Unknown: other or missing

Usage:
  python analyze_evaluator_quality.py --month 2026-02
  python analyze_evaluator_quality.py --months 2026-01 2026-02
  python analyze_evaluator_quality.py --month 2026-02 --channel google-ads
"""

import os
import sys
import warnings
warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    pass
import requests
import pandas as pd
from datetime import datetime
from collections import defaultdict
from dotenv import load_dotenv
import argparse
import time
import json
import base64

_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.normpath(os.path.join(_script_dir, '..', '..', '..'))
load_dotenv(os.path.join(_project_root, '.env'))
load_dotenv()

HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
if not HUBSPOT_API_KEY:
    raise ValueError("HUBSPOT_API_KEY environment variable is required")

HUBSPOT_BASE_URL = 'https://api.hubapi.com'
HEADERS = {
    'Authorization': f'Bearer {HUBSPOT_API_KEY}',
    'Content-Type': 'application/json'
}
PORTAL_ID = "19877595"

ACCOUNTANT_COMPANY_TYPES = ['Cuenta Contador', 'Cuenta Contador y Reseller', 'Contador Robado']

# Mixpanel credentials (for behavioral persona classification)
MIXPANEL_USERNAME = os.getenv('MIXPANEL_USERNAME')
MIXPANEL_PASSWORD = os.getenv('MIXPANEL_PASSWORD')
MIXPANEL_PROJECT_ID = os.getenv('MIXPANEL_PROJECT_ID')

# Behavioral persona classification — from Mixpanel critical events
# Source of truth: plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md
PERSONA_ADMIN_EVENTS = {'Generó comprobante de venta', 'Generó comprobante de compra'}
PERSONA_CONTA_EVENTS = {
    'Generó asiento contable', 'Descargó el balance', 'Descargó el diario general',
    'Descargó el estado de resultados', 'Agregó una cuenta contable',
}
PERSONA_INV_EVENTS = {'Agregó un ítem', 'Generó un ajuste de inventario', 'Actualizó precios en pantalla masivo'}
PERSONA_SUELDOS_EVENTS = {'Liquidar sueldo'}
ALL_PERSONA_EVENTS = list(PERSONA_ADMIN_EVENTS | PERSONA_CONTA_EVENTS | PERSONA_INV_EVENTS | PERSONA_SUELDOS_EVENTS)

# Connection lead_source values (accountant connections)
CONNECTION_CONTADOR_SOURCES = [
    'invitación estudio',
    'invitacion estudio',
    'estudio contable',
    'contador',
]
CONNECTION_PEER_SOURCES = [
    'invitación empresa',
    'invitacion empresa',
    'recomendación',
    'recomendacion',
]


# ─────────────────────────────────────────────
# HubSpot API helpers (same pattern as SMB funnel)
# ─────────────────────────────────────────────

def fetch_evaluators(start_date, end_date):
    """
    Fetch contacts (evaluators/MQLs) created in period.
    Excludes lead_source='Usuario Invitado' using HAS_PROPERTY + NEQ pattern.
    Returns list of contact objects.
    """
    url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search"
    all_contacts = []
    after = None

    properties = [
        "email", "firstname", "lastname", "createdate", "lead_source", "rol_wizard",
        "hs_analytics_source", "hs_analytics_source_data_1", "hs_analytics_source_data_2",
        "initial_utm_source", "initial_utm_medium", "initial_utm_campaign",
        "activo", "fecha_activo", "fit_score_contador",
        "hs_v2_date_entered_opportunity", "hs_v2_date_entered_customer",
        "lifecyclestage", "num_associated_deals", "hubspot_owner_id",
    ]

    while True:
        filters = [
            {"propertyName": "createdate", "operator": "GTE", "value": f"{start_date}T00:00:00Z"},
            {"propertyName": "createdate", "operator": "LT", "value": f"{end_date}T00:00:00Z"},
            {"propertyName": "lead_source", "operator": "HAS_PROPERTY"},
            {"propertyName": "lead_source", "operator": "NEQ", "value": "Usuario Invitado"},
        ]
        payload = {
            "filterGroups": [{"filters": filters}],
            "properties": properties,
            "limit": 100,
        }
        if after:
            payload["after"] = after

        for attempt in range(3):
            try:
                response = requests.post(url, headers=HEADERS, json=payload, timeout=30)
                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', 2))
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    print(f"⚠️  Error fetching contacts: {e}")
                    return all_contacts
                time.sleep(2 ** attempt)

        data = response.json()
        results = data.get('results', [])
        all_contacts.extend(results)

        paging = data.get('paging', {})
        after = paging.get('next', {}).get('after')
        if not after:
            break
        time.sleep(0.1)

    return all_contacts


def batch_get_associations(from_type, to_type, object_ids, batch_size=100):
    """Get associations for multiple objects in batch. Returns {from_id: [to_ids]}"""
    url = f"{HUBSPOT_BASE_URL}/crm/v4/associations/{from_type}/{to_type}/batch/read"
    result_map = {}

    for i in range(0, len(object_ids), batch_size):
        batch = object_ids[i:i+batch_size]
        payload = {"inputs": [{"id": str(obj_id)} for obj_id in batch]}

        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                time.sleep(retry_after)
                response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
            if response.status_code in (200, 207):
                results = response.json().get('results', [])
                for item in results:
                    from_id = str(item.get('from', {}).get('id', ''))
                    to_ids = [str(t.get('toObjectId', '')) for t in item.get('to', [])]
                    result_map[from_id] = to_ids
        except Exception as e:
            print(f"⚠️  Batch association error: {e}")

        if i + batch_size < len(object_ids):
            time.sleep(0.1)

    return result_map


def batch_read_objects(object_type, object_ids, properties, batch_size=100):
    """Batch read objects from HubSpot. Returns {object_id: properties_dict}"""
    url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/{object_type}/batch/read"
    result_map = {}

    for i in range(0, len(object_ids), batch_size):
        batch = object_ids[i:i+batch_size]
        payload = {
            "properties": properties,
            "inputs": [{"id": str(obj_id)} for obj_id in batch],
        }

        try:
            response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 2))
                time.sleep(retry_after)
                response = requests.post(url, headers=HEADERS, json=payload, timeout=60)
            if response.status_code in (200, 207):
                results = response.json().get('results', [])
                for obj in results:
                    obj_id = str(obj.get('id', ''))
                    result_map[obj_id] = obj.get('properties', {})
        except Exception as e:
            print(f"⚠️  Batch read error: {e}")

        if i + batch_size < len(object_ids):
            time.sleep(0.1)

    return result_map


# ─────────────────────────────────────────────
# Classification functions
# ─────────────────────────────────────────────

def classify_channel(props):
    """
    Classify evaluator into acquisition channel based on initial_utm_* fields (primary)
    and hs_analytics_source / lead_source (fallback).
    """
    utm_source = (props.get('initial_utm_source') or '').lower().strip()
    utm_medium = (props.get('initial_utm_medium') or '').lower().strip()
    utm_campaign = (props.get('initial_utm_campaign') or '').lower().strip()
    analytics_source = (props.get('hs_analytics_source') or '').upper().strip()
    lead_source = (props.get('lead_source') or '').lower().strip()

    # Colppy Portal (specific campaign)
    if utm_source == 'colppy' and utm_campaign == 'referral_portal_clientes':
        return 'Colppy Portal'

    # Google Ads
    if utm_source == 'google' and utm_medium in ('ppc', 'cpc'):
        return 'Google Ads'

    # Meta Ads
    if any(x in utm_source for x in ['facebook', 'instagram', 'meta', 'fb', 'ig']):
        return 'Meta Ads'

    # LinkedIn Ads
    if utm_source == 'linkedin' and utm_medium == 'linkedin':
        return 'LinkedIn Ads'

    # Connection (Contador)
    if any(x in lead_source for x in CONNECTION_CONTADOR_SOURCES):
        return 'Connections (Contador)'

    # Connection (Peer)
    if any(x in lead_source for x in CONNECTION_PEER_SOURCES):
        return 'Connections (Peer)'

    # If there are UTMs but didn't match above — classify as Other Paid
    if utm_source:
        return 'Other Paid'

    # No UTMs — fall back to analytics source
    if analytics_source == 'ORGANIC_SEARCH':
        return 'Organic Search'
    if analytics_source == 'DIRECT_TRAFFIC':
        return 'Direct'
    if analytics_source == 'SOCIAL_MEDIA':
        return 'Social (Organic)'
    if analytics_source == 'EMAIL_MARKETING':
        return 'Email'
    if analytics_source in ('REFERRALS', 'OTHER_CAMPAIGNS'):
        return 'Other'

    return 'Unclassified'


def fetch_mixpanel_personas(start_date, end_date):
    """
    Fetch behavioral personas from Mixpanel critical events.
    Uses the Raw Data Export API to get all persona-relevant events for the period,
    then classifies each user by their dominant event type.

    Returns {email_lower: persona_string}
    """
    if not MIXPANEL_USERNAME or not MIXPANEL_PASSWORD or not MIXPANEL_PROJECT_ID:
        print("   ⚠️  Mixpanel credentials not configured — falling back to 'Sin actividad'")
        return {}

    auth_string = f"{MIXPANEL_USERNAME}:{MIXPANEL_PASSWORD}"
    encoded_auth = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_auth}",
        "Accept": "text/plain",
    }

    params = {
        "project_id": MIXPANEL_PROJECT_ID,
        "from_date": start_date,
        "to_date": end_date,
        "event": json.dumps(ALL_PERSONA_EVENTS),
    }

    url = "https://data.mixpanel.com/api/2.0/export"
    try:
        response = requests.get(url, params=params, headers=headers, stream=True, timeout=120)
        if response.status_code != 200:
            print(f"   ⚠️  Mixpanel export error {response.status_code}: {response.text[:200]}")
            return {}
    except Exception as e:
        print(f"   ⚠️  Mixpanel export failed: {e}")
        return {}

    # Parse JSONL and build {email -> set of event names}
    user_events = defaultdict(set)
    event_count = 0
    for line in response.iter_lines(decode_unicode=True):
        if line and line.strip():
            try:
                evt = json.loads(line)
                event_name = evt.get('event', '')
                props = evt.get('properties', {})
                # Extract email from multiple possible fields
                email = (props.get('$email') or props.get('Email') or props.get('email') or
                         props.get('distinct_id', ''))
                if email and '@' in str(email):
                    user_events[str(email).lower().strip()].add(event_name)
                    event_count += 1
            except json.JSONDecodeError:
                continue

    print(f"   Mixpanel: {event_count} persona events from {len(user_events)} users")

    # Classify persona by dominant behavior
    persona_map = {}
    for email, events in user_events.items():
        has_conta = bool(events & PERSONA_CONTA_EVENTS)
        has_admin = bool(events & PERSONA_ADMIN_EVENTS)
        has_inv = bool(events & PERSONA_INV_EVENTS)
        has_sueldos = bool(events & PERSONA_SUELDOS_EVENTS)

        # Priority: Contabilidad > Sueldos > Inventario > Administración
        # (higher-complexity personas take priority when multiple match)
        if has_conta:
            persona_map[email] = 'Contabilidad'
        elif has_sueldos:
            persona_map[email] = 'Sueldos'
        elif has_inv:
            persona_map[email] = 'Inventario'
        elif has_admin:
            persona_map[email] = 'Administración'

    return persona_map


def classify_icp(company_type):
    """Classify ICP from company type field."""
    if not company_type:
        return 'Unclassified'
    if company_type in ACCOUNTANT_COMPANY_TYPES:
        return 'Cuenta Contador'
    return 'Cuenta Pyme'


# ─────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────

def analyze_evaluator_quality(start_date, end_date, channel_filter=None):
    """
    Analyze evaluator quality for a single period.
    Returns dict with results for CSV output.
    """
    start_dt = datetime.fromisoformat(f"{start_date}T00:00:00+00:00")
    end_dt = datetime.fromisoformat(f"{end_date}T00:00:00+00:00")

    print(f"\n{'='*80}")
    print(f"EVALUATOR QUALITY ANALYSIS")
    print(f"Period: {start_date} to {end_date}")
    if channel_filter:
        print(f"Channel filter: {channel_filter}")
    print(f"{'='*80}\n")

    # ── Stage 1: Fetch evaluators ──
    print("📊 Stage 1: Fetching evaluators (MQLs)...")
    contacts = fetch_evaluators(start_date, end_date)
    print(f"   Found {len(contacts)} evaluators\n")

    if not contacts:
        print("❌ No evaluators found for this period.")
        return None

    # ── Stage 2: Classify each evaluator ──
    print("📊 Stage 2: Classifying evaluators by channel...")

    # Fetch behavioral personas from Mixpanel (actual product behavior > wizard declaration)
    print("📊 Stage 2b: Fetching behavioral personas from Mixpanel...")
    mixpanel_personas = fetch_mixpanel_personas(start_date, end_date)

    evaluators = []
    persona_matched = 0
    for contact in contacts:
        props = contact.get('properties', {})
        contact_id = contact.get('id')

        channel = classify_channel(props)

        # Persona from Mixpanel behavior; fallback to 'Sin actividad'
        email = (props.get('email') or '').lower().strip()
        persona = mixpanel_personas.get(email, 'Sin actividad')
        if persona != 'Sin actividad':
            persona_matched += 1

        # PQL check
        activo = str(props.get('activo', '')).lower() == 'true'
        fecha_activo = props.get('fecha_activo', '')
        is_pql = activo and bool(fecha_activo)

        # SQL check
        sql_date = props.get('hs_v2_date_entered_opportunity', '')
        num_deals = int(props.get('num_associated_deals') or 0)
        is_sql = bool(sql_date) and num_deals > 0

        # Customer check
        customer_date = props.get('hs_v2_date_entered_customer', '')
        lifecycle = (props.get('lifecyclestage') or '').lower()
        is_customer = bool(customer_date) or lifecycle == 'customer'

        # Time to PQL (days)
        time_to_pql = None
        if is_pql and fecha_activo:
            try:
                create_dt = datetime.fromisoformat(props.get('createdate', '').replace('Z', '+00:00'))
                activo_dt = datetime.fromisoformat(fecha_activo.replace('Z', '+00:00'))
                time_to_pql = (activo_dt - create_dt).total_seconds() / 86400
            except (ValueError, TypeError):
                pass

        evaluators.append({
            'contact_id': contact_id,
            'email': email,
            'channel': channel,
            'persona': persona,
            'declared_persona': props.get('rol_wizard', ''),  # wizard declaration for comparison
            'icp': None,  # filled in Stage 3
            'is_pql': is_pql,
            'is_sql': is_sql,
            'is_customer': is_customer,
            'time_to_pql_days': time_to_pql,
            'utm_campaign': props.get('initial_utm_campaign', ''),
            'fit_score': props.get('fit_score_contador', ''),
        })

    print(f"   Persona from behavior: {persona_matched}/{len(evaluators)} ({persona_matched/len(evaluators)*100:.1f}%)")
    print(f"   Sin actividad: {len(evaluators) - persona_matched}\n")

    # Apply channel filter if specified
    if channel_filter:
        filter_lower = channel_filter.lower().replace('-', ' ').replace('_', ' ')
        evaluators = [e for e in evaluators if filter_lower in e['channel'].lower().replace('-', ' ')]
        print(f"   After filter: {len(evaluators)} evaluators in '{channel_filter}'\n")
    else:
        # Channel distribution preview
        channel_counts = {}
        for e in evaluators:
            channel_counts[e['channel']] = channel_counts.get(e['channel'], 0) + 1
        for ch, cnt in sorted(channel_counts.items(), key=lambda x: -x[1]):
            print(f"   {ch}: {cnt}")
        print()

    # ── Stage 3: Resolve ICP via company associations ──
    print("📊 Stage 3: Resolving ICP (company type)...")
    contact_ids = [e['contact_id'] for e in evaluators]
    contact_company_map = batch_get_associations('contacts', 'companies', contact_ids)

    # Collect all unique company IDs to batch-read
    all_company_ids = set()
    for company_ids in contact_company_map.values():
        all_company_ids.update(company_ids)

    company_types = {}
    if all_company_ids:
        company_props = batch_read_objects('companies', list(all_company_ids), ['type', 'name'])
        for comp_id, props in company_props.items():
            company_types[comp_id] = props.get('type', '')

    # Assign ICP to each evaluator
    classified_count = 0
    for ev in evaluators:
        company_ids = contact_company_map.get(str(ev['contact_id']), [])
        if company_ids:
            # Use first (primary) company
            comp_type = company_types.get(company_ids[0], '')
            ev['icp'] = classify_icp(comp_type)
            classified_count += 1
        else:
            ev['icp'] = 'Unclassified'

    print(f"   ICP classified: {classified_count}/{len(evaluators)} ({classified_count/len(evaluators)*100:.0f}%)\n")

    # ── Stage 4: Trace customers to deals for MRR ──
    print("📊 Stage 4: Tracing customers to deals for MRR attribution...")
    customer_evaluators = [e for e in evaluators if e['is_customer']]
    customer_mrr = {}  # contact_id -> mrr amount

    if customer_evaluators:
        customer_ids = [e['contact_id'] for e in customer_evaluators]
        customer_deal_map = batch_get_associations('contacts', 'deals', customer_ids)

        # Collect all deal IDs
        all_deal_ids = set()
        for deal_ids in customer_deal_map.values():
            all_deal_ids.update(deal_ids)

        if all_deal_ids:
            deal_props = batch_read_objects('deals', list(all_deal_ids),
                                            ['amount', 'dealstage', 'closedate', 'dealname'])
            for contact_id_str, deal_ids in customer_deal_map.items():
                total_mrr = 0
                for deal_id in deal_ids:
                    d = deal_props.get(deal_id, {})
                    if d.get('dealstage') in ('closedwon', '34692158'):
                        try:
                            total_mrr += float(d.get('amount', 0) or 0)
                        except (ValueError, TypeError):
                            pass
                customer_mrr[contact_id_str] = total_mrr

    # Assign MRR to evaluators
    for ev in evaluators:
        ev['mrr'] = customer_mrr.get(str(ev['contact_id']), 0)

    total_mrr = sum(ev['mrr'] for ev in evaluators)
    print(f"   Customers: {len(customer_evaluators)}, Total MRR: ${total_mrr:,.0f}\n")

    # ── Stage 5: Build summary tables ──
    print(f"{'='*80}")
    print("RESULTS")
    print(f"{'='*80}\n")

    total = len(evaluators)
    total_pql = sum(1 for e in evaluators if e['is_pql'])
    total_sql = sum(1 for e in evaluators if e['is_sql'])
    total_won = sum(1 for e in evaluators if e['is_customer'])

    # Table 1: Channel Quality Summary
    print("**Table 1: Channel Quality Summary**\n")
    print("| Channel | Evaluators | PQL | PQL % | SQL | SQL % | Won | Won % | MRR (ARS) |")
    print("|---------|------------|-----|-------|-----|-------|-----|-------|-----------|")

    channel_data = {}
    for ev in evaluators:
        ch = ev['channel']
        if ch not in channel_data:
            channel_data[ch] = {'count': 0, 'pql': 0, 'sql': 0, 'won': 0, 'mrr': 0}
        channel_data[ch]['count'] += 1
        if ev['is_pql']:
            channel_data[ch]['pql'] += 1
        if ev['is_sql']:
            channel_data[ch]['sql'] += 1
        if ev['is_customer']:
            channel_data[ch]['won'] += 1
        channel_data[ch]['mrr'] += ev['mrr']

    for ch, d in sorted(channel_data.items(), key=lambda x: -x[1]['count']):
        pql_pct = d['pql'] / d['count'] * 100 if d['count'] else 0
        sql_pct = d['sql'] / d['count'] * 100 if d['count'] else 0
        won_pct = d['won'] / d['count'] * 100 if d['count'] else 0
        print(f"| {ch} | {d['count']} | {d['pql']} | {pql_pct:.1f}% | {d['sql']} | {sql_pct:.1f}% | {d['won']} | {won_pct:.1f}% | ${d['mrr']:,.0f} |")

    print(f"| **TOTAL** | **{total}** | **{total_pql}** | **{total_pql/total*100:.1f}%** | **{total_sql}** | **{total_sql/total*100:.1f}%** | **{total_won}** | **{total_won/total*100:.1f}%** | **${total_mrr:,.0f}** |")
    print()

    # Table 2: ICP Quality Breakdown
    print("**Table 2: ICP Quality Breakdown**\n")
    print("| ICP | Evaluators | PQL % | Won % | MRR (ARS) | Avg Time to PQL |")
    print("|-----|------------|-------|-------|-----------|-----------------|")

    icp_data = {}
    for ev in evaluators:
        icp = ev['icp']
        if icp not in icp_data:
            icp_data[icp] = {'count': 0, 'pql': 0, 'won': 0, 'mrr': 0, 'pql_times': []}
        icp_data[icp]['count'] += 1
        if ev['is_pql']:
            icp_data[icp]['pql'] += 1
        if ev['is_customer']:
            icp_data[icp]['won'] += 1
        icp_data[icp]['mrr'] += ev['mrr']
        if ev['time_to_pql_days'] is not None:
            icp_data[icp]['pql_times'].append(ev['time_to_pql_days'])

    for icp, d in sorted(icp_data.items(), key=lambda x: -x[1]['count']):
        pql_pct = d['pql'] / d['count'] * 100 if d['count'] else 0
        won_pct = d['won'] / d['count'] * 100 if d['count'] else 0
        avg_time = f"{sum(d['pql_times'])/len(d['pql_times']):.1f} days" if d['pql_times'] else "N/A"
        print(f"| {icp} | {d['count']} | {pql_pct:.1f}% | {won_pct:.1f}% | ${d['mrr']:,.0f} | {avg_time} |")
    print()

    # Table 3: Persona Quality Breakdown
    print("**Table 3: Persona Quality Breakdown**\n")
    print("| Persona | Evaluators | PQL % | Won % | MRR (ARS) |")
    print("|---------|------------|-------|-------|-----------|")

    persona_data = {}
    for ev in evaluators:
        p = ev['persona']
        if p not in persona_data:
            persona_data[p] = {'count': 0, 'pql': 0, 'won': 0, 'mrr': 0}
        persona_data[p]['count'] += 1
        if ev['is_pql']:
            persona_data[p]['pql'] += 1
        if ev['is_customer']:
            persona_data[p]['won'] += 1
        persona_data[p]['mrr'] += ev['mrr']

    for p, d in sorted(persona_data.items(), key=lambda x: -x[1]['count']):
        pql_pct = d['pql'] / d['count'] * 100 if d['count'] else 0
        won_pct = d['won'] / d['count'] * 100 if d['count'] else 0
        print(f"| {p} | {d['count']} | {pql_pct:.1f}% | {won_pct:.1f}% | ${d['mrr']:,.0f} |")
    print()

    # Table 4: Connection Share
    print("**Table 4: Connection Share**\n")
    print("| Source | Evaluators | % of Total | MRR (ARS) | % of MRR |")
    print("|--------|------------|------------|-----------|----------|")

    paid_channels = ['Google Ads', 'Meta Ads', 'LinkedIn Ads', 'Other Paid']
    connection_channels = ['Connections (Contador)', 'Connections (Peer)', 'Colppy Portal']

    groups = {
        'Paid channels': paid_channels,
        'Connections': connection_channels,
        'Organic/Direct': ['Organic Search', 'Direct', 'Social (Organic)', 'Email', 'Other', 'Unclassified'],
    }
    for group_name, channels in groups.items():
        g_count = sum(channel_data.get(ch, {}).get('count', 0) for ch in channels)
        g_mrr = sum(channel_data.get(ch, {}).get('mrr', 0) for ch in channels)
        pct_total = g_count / total * 100 if total else 0
        pct_mrr = g_mrr / total_mrr * 100 if total_mrr else 0
        print(f"| {group_name} | {g_count} | {pct_total:.1f}% | ${g_mrr:,.0f} | {pct_mrr:.1f}% |")
    print()

    # ── Stage 6: Campaign drill-down for top paid channel ──
    google_ads_evaluators = [e for e in evaluators if e['channel'] == 'Google Ads']
    if google_ads_evaluators:
        print("**Table 5: Google Ads Campaign Breakdown (top 15)**\n")
        print("| Campaign | Evaluators | PQL | PQL % | Won | MRR (ARS) |")
        print("|----------|------------|-----|-------|-----|-----------|")

        campaign_data = {}
        for ev in google_ads_evaluators:
            camp = ev['utm_campaign'] or '(none)'
            if camp not in campaign_data:
                campaign_data[camp] = {'count': 0, 'pql': 0, 'won': 0, 'mrr': 0}
            campaign_data[camp]['count'] += 1
            if ev['is_pql']:
                campaign_data[camp]['pql'] += 1
            if ev['is_customer']:
                campaign_data[camp]['won'] += 1
            campaign_data[camp]['mrr'] += ev['mrr']

        for camp, d in sorted(campaign_data.items(), key=lambda x: -x[1]['count'])[:15]:
            pql_pct = d['pql'] / d['count'] * 100 if d['count'] else 0
            print(f"| {camp[:50]} | {d['count']} | {d['pql']} | {pql_pct:.1f}% | {d['won']} | ${d['mrr']:,.0f} |")
        print()

    # ── Save results ──
    results = {
        'start_date': start_date,
        'end_date': end_date,
        'total_evaluators': total,
        'total_pql': total_pql,
        'total_sql': total_sql,
        'total_won': total_won,
        'total_mrr': total_mrr,
        'channel_data': channel_data,
        'icp_data': {k: {kk: vv for kk, vv in v.items() if kk != 'pql_times'} for k, v in icp_data.items()},
        'persona_data': persona_data,
    }

    # Save detailed CSV
    output_dir = "tools/outputs"
    os.makedirs(output_dir, exist_ok=True)

    # Contact-level CSV (audit trail)
    df = pd.DataFrame(evaluators)
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    detail_file = f"{output_dir}/evaluator_quality_contacts_{start_clean}_{end_clean}.csv"
    df.to_csv(detail_file, index=False)
    print(f"📄 Contact-level detail saved: {detail_file}")

    # Summary CSV (channel x metrics)
    summary_rows = []
    for ch, d in channel_data.items():
        summary_rows.append({
            'Period': f"{start_date} to {end_date}",
            'Channel': ch,
            'Evaluators': d['count'],
            'PQL': d['pql'],
            'PQL_Rate_%': round(d['pql'] / d['count'] * 100, 2) if d['count'] else 0,
            'SQL': d['sql'],
            'SQL_Rate_%': round(d['sql'] / d['count'] * 100, 2) if d['count'] else 0,
            'Won': d['won'],
            'Won_Rate_%': round(d['won'] / d['count'] * 100, 2) if d['count'] else 0,
            'MRR': round(d['mrr'], 2),
        })
    df_summary = pd.DataFrame(summary_rows)
    summary_file = f"{output_dir}/evaluator_quality_summary_{start_clean}_{end_clean}.csv"
    df_summary.to_csv(summary_file, index=False)
    print(f"📄 Channel summary saved: {summary_file}")
    print()

    return results


def main():
    parser = argparse.ArgumentParser(description='Analyze Evaluator Quality by Channel, ICP, and Persona')
    parser.add_argument('--month', type=str, help='Month in YYYY-MM format (e.g., 2026-02)')
    parser.add_argument('--months', nargs='+', type=str, help='Multiple months (e.g., --months 2026-01 2026-02)')
    parser.add_argument('--start-date', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='End date YYYY-MM-DD')
    parser.add_argument('--channel', type=str, help='Filter by channel (e.g., google-ads, connections, organic)')
    args = parser.parse_args()

    if args.months:
        print("=" * 80)
        print("MULTI-MONTH EVALUATOR QUALITY ANALYSIS")
        print("=" * 80)
        print(f"\nAnalyzing {len(args.months)} month(s): {', '.join(args.months)}\n")

        all_results = []
        for month_str in args.months:
            year, month = month_str.split('-')
            start_date = f"{year}-{month}-01"
            if month == '12':
                end_date = f"{int(year)+1}-01-01"
            else:
                end_date = f"{year}-{int(month)+1:02d}-01"

            result = analyze_evaluator_quality(start_date, end_date, args.channel)
            if result:
                result['month'] = month_str
                all_results.append(result)

        # Comparative summary across months
        if len(all_results) > 1:
            print("=" * 80)
            print("COMPARATIVE SUMMARY")
            print("=" * 80)
            print()
            print("| Month | Evaluators | PQL | PQL % | SQL | Won | Won % | MRR (ARS) |")
            print("|-------|------------|-----|-------|-----|-----|-------|-----------|")
            for r in all_results:
                pql_pct = r['total_pql'] / r['total_evaluators'] * 100 if r['total_evaluators'] else 0
                won_pct = r['total_won'] / r['total_evaluators'] * 100 if r['total_evaluators'] else 0
                print(f"| {r['month']} | {r['total_evaluators']} | {r['total_pql']} | {pql_pct:.1f}% | {r['total_sql']} | {r['total_won']} | {won_pct:.1f}% | ${r['total_mrr']:,.0f} |")
            print()
        return

    if args.month:
        year, month = args.month.split('-')
        start_date = f"{year}-{month}-01"
        if month == '12':
            end_date = f"{int(year)+1}-01-01"
        else:
            end_date = f"{year}-{int(month)+1:02d}-01"
    elif args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        parser.print_help()
        return

    analyze_evaluator_quality(start_date, end_date, args.channel)


if __name__ == '__main__':
    main()
