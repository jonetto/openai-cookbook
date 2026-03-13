#!/usr/bin/env python3
"""
PQL BY CHANNEL ANALYSIS
========================

Lightweight analysis of PQL (Product Qualified Lead) rates segmented by
acquisition channel. Uses initial_utm_* fields for channel attribution.

This is the core demand-gen quality metric: which channels produce evaluators
that actually activate in the product?

Faster than the full evaluator-quality analysis because it skips:
- ICP classification (no company lookups)
- MRR tracing (no deal lookups)
- Persona classification (just channel + PQL)

Usage:
  python analyze_pql_by_channel.py --month 2026-02
  python analyze_pql_by_channel.py --months 2026-01 2026-02 2026-03
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
from dotenv import load_dotenv
import argparse
import time

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

# Reuse channel classification from evaluator_quality
CONNECTION_CONTADOR_SOURCES = ['invitación estudio', 'invitacion estudio', 'estudio contable', 'contador']
CONNECTION_PEER_SOURCES = ['invitación empresa', 'invitacion empresa', 'recomendación', 'recomendacion']


def fetch_contacts_with_pql(start_date, end_date):
    """Fetch contacts created in period with PQL-relevant properties."""
    url = f"{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search"
    all_contacts = []
    after = None

    properties = [
        "email", "createdate", "lead_source", "rol_wizard",
        "hs_analytics_source",
        "initial_utm_source", "initial_utm_medium", "initial_utm_campaign",
        "activo", "fecha_activo",
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
                    time.sleep(int(response.headers.get('Retry-After', 2)))
                    continue
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == 2:
                    print(f"⚠️  Error fetching contacts: {e}")
                    return all_contacts
                time.sleep(2 ** attempt)

        data = response.json()
        all_contacts.extend(data.get('results', []))

        after = data.get('paging', {}).get('next', {}).get('after')
        if not after:
            break
        time.sleep(0.1)

    return all_contacts


def classify_channel(props):
    """Classify evaluator into acquisition channel (same logic as evaluator_quality)."""
    utm_source = (props.get('initial_utm_source') or '').lower().strip()
    utm_medium = (props.get('initial_utm_medium') or '').lower().strip()
    utm_campaign = (props.get('initial_utm_campaign') or '').lower().strip()
    analytics_source = (props.get('hs_analytics_source') or '').upper().strip()
    lead_source = (props.get('lead_source') or '').lower().strip()

    if utm_source == 'colppy' and utm_campaign == 'referral_portal_clientes':
        return 'Colppy Portal'
    if utm_source == 'google' and utm_medium in ('ppc', 'cpc'):
        return 'Google Ads'
    if any(x in utm_source for x in ['facebook', 'instagram', 'meta', 'fb', 'ig']):
        return 'Meta Ads'
    if utm_source == 'linkedin' and utm_medium == 'linkedin':
        return 'LinkedIn Ads'
    if any(x in lead_source for x in CONNECTION_CONTADOR_SOURCES):
        return 'Connections (Contador)'
    if any(x in lead_source for x in CONNECTION_PEER_SOURCES):
        return 'Connections (Peer)'
    if utm_source:
        return 'Other Paid'
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


def analyze_pql_by_channel(start_date, end_date):
    """Analyze PQL rate by channel for a single period."""

    print(f"\n{'='*80}")
    print(f"PQL BY CHANNEL ANALYSIS")
    print(f"Period: {start_date} to {end_date}")
    print(f"{'='*80}\n")

    # Fetch contacts
    print("📊 Fetching evaluators...")
    contacts = fetch_contacts_with_pql(start_date, end_date)
    print(f"   Found {len(contacts)} evaluators\n")

    if not contacts:
        print("❌ No evaluators found.")
        return None

    # Classify and compute PQL
    channel_data = {}
    campaign_data = {}

    for contact in contacts:
        props = contact.get('properties', {})
        channel = classify_channel(props)
        activo = str(props.get('activo', '')).lower() == 'true'
        fecha_activo = props.get('fecha_activo', '')
        is_pql = activo and bool(fecha_activo)
        utm_campaign = props.get('initial_utm_campaign', '') or '(none)'

        if channel not in channel_data:
            channel_data[channel] = {'evaluators': 0, 'pql': 0}
        channel_data[channel]['evaluators'] += 1
        if is_pql:
            channel_data[channel]['pql'] += 1

        # Campaign-level for paid channels
        if channel in ('Google Ads', 'Meta Ads', 'LinkedIn Ads'):
            key = f"{channel} | {utm_campaign}"
            if key not in campaign_data:
                campaign_data[key] = {'evaluators': 0, 'pql': 0}
            campaign_data[key]['evaluators'] += 1
            if is_pql:
                campaign_data[key]['pql'] += 1

    total = len(contacts)
    total_pql = sum(d['pql'] for d in channel_data.values())

    # Print results
    print("**PQL Rate by Channel**\n")
    print("| Channel | Evaluators | PQL | PQL Rate |")
    print("|---------|------------|-----|----------|")

    for ch, d in sorted(channel_data.items(), key=lambda x: -x[1]['evaluators']):
        pql_pct = d['pql'] / d['evaluators'] * 100 if d['evaluators'] else 0
        print(f"| {ch} | {d['evaluators']} | {d['pql']} | {pql_pct:.1f}% |")

    pql_pct_total = total_pql / total * 100 if total else 0
    print(f"| **TOTAL** | **{total}** | **{total_pql}** | **{pql_pct_total:.1f}%** |")
    print()

    # Campaign drill-down
    if campaign_data:
        print("**PQL Rate by Campaign (paid channels, top 20)**\n")
        print("| Channel / Campaign | Evaluators | PQL | PQL Rate |")
        print("|--------------------|------------|-----|----------|")
        for key, d in sorted(campaign_data.items(), key=lambda x: -x[1]['evaluators'])[:20]:
            pql_pct = d['pql'] / d['evaluators'] * 100 if d['evaluators'] else 0
            print(f"| {key[:60]} | {d['evaluators']} | {d['pql']} | {pql_pct:.1f}% |")
        print()

    # Save CSV
    output_dir = "tools/outputs"
    os.makedirs(output_dir, exist_ok=True)

    rows = []
    for ch, d in channel_data.items():
        rows.append({
            'Period': f"{start_date} to {end_date}",
            'Channel': ch,
            'Evaluators': d['evaluators'],
            'PQL': d['pql'],
            'PQL_Rate_%': round(d['pql'] / d['evaluators'] * 100, 2) if d['evaluators'] else 0,
        })
    df = pd.DataFrame(rows)
    start_clean = start_date.replace('-', '')
    end_clean = end_date.replace('-', '')
    output_file = f"{output_dir}/pql_by_channel_{start_clean}_{end_clean}.csv"
    df.to_csv(output_file, index=False)
    print(f"📄 Results saved: {output_file}")
    print()

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_evaluators': total,
        'total_pql': total_pql,
        'channel_data': channel_data,
    }


def main():
    parser = argparse.ArgumentParser(description='Analyze PQL Rate by Acquisition Channel')
    parser.add_argument('--month', type=str, help='Month in YYYY-MM format')
    parser.add_argument('--months', nargs='+', type=str, help='Multiple months')
    parser.add_argument('--start-date', type=str, help='Start date YYYY-MM-DD')
    parser.add_argument('--end-date', type=str, help='End date YYYY-MM-DD')
    args = parser.parse_args()

    if args.months:
        print("=" * 80)
        print("MULTI-MONTH PQL BY CHANNEL ANALYSIS")
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
            result = analyze_pql_by_channel(start_date, end_date)
            if result:
                result['month'] = month_str
                all_results.append(result)

        if len(all_results) > 1:
            print("=" * 80)
            print("PQL RATE TREND BY CHANNEL")
            print("=" * 80)
            print()
            # Collect all channels
            all_channels = set()
            for r in all_results:
                all_channels.update(r['channel_data'].keys())
            all_channels = sorted(all_channels)

            header = "| Channel |" + " | ".join(r['month'] for r in all_results) + " |"
            sep = "|---------|" + " | ".join("--------" for _ in all_results) + " |"
            print(header)
            print(sep)
            for ch in all_channels:
                cells = []
                for r in all_results:
                    d = r['channel_data'].get(ch, {'evaluators': 0, 'pql': 0})
                    pql_pct = d['pql'] / d['evaluators'] * 100 if d['evaluators'] else 0
                    cells.append(f"{d['pql']}/{d['evaluators']} ({pql_pct:.1f}%)")
                print(f"| {ch} | " + " | ".join(cells) + " |")
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

    analyze_pql_by_channel(start_date, end_date)


if __name__ == '__main__':
    main()
