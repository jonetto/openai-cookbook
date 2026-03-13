#!/usr/bin/env python3
"""
Onboarding Pulse Baseline — HubSpot Cohort Fetch

Pulls contacts created in the last N weeks with properties needed for
the CPO agent's Onboarding Pulse dashboard (Tables 1-4).

Classifies contacts into two paths:
- No-touch (PLG): fit_score_contador < 40 OR hubspot_owner_id empty
- Sales-touched: fit_score_contador >= 40 AND hubspot_owner_id populated

Outputs JSON with per-contact data + aggregate funnel metrics.
"""

import os
import sys
import json
import warnings
warnings.filterwarnings('ignore')
try:
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    pass
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse

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

PROPERTIES = [
    'email', 'createdate', 'activo', 'fecha_activo', 'fit_score_contador',
    'hubspot_owner_id', 'rol_wizard', 'lifecyclestage', 'lead_source',
    'initial_utm_source', 'initial_utm_campaign', 'initial_utm_medium',
    'num_associated_deals', 'hs_v2_date_entered_opportunity',
    'hs_analytics_source'
]


def search_contacts(from_date, to_date):
    """Fetch contacts created in date range, excluding 'Usuario Invitado'."""
    url = f'{HUBSPOT_BASE_URL}/crm/v3/objects/contacts/search'
    all_contacts = []
    after = None

    while True:
        body = {
            "filterGroups": [{
                "filters": [
                    {
                        "propertyName": "createdate",
                        "operator": "GTE",
                        "value": int(from_date.timestamp() * 1000)
                    },
                    {
                        "propertyName": "createdate",
                        "operator": "LTE",
                        "value": int(to_date.timestamp() * 1000)
                    },
                    {
                        "propertyName": "lead_source",
                        "operator": "HAS_PROPERTY"
                    },
                    {
                        "propertyName": "lead_source",
                        "operator": "NEQ",
                        "value": "Usuario Invitado"
                    }
                ]
            }],
            "properties": PROPERTIES,
            "limit": 100,
            "sorts": [{"propertyName": "createdate", "direction": "ASCENDING"}]
        }
        if after:
            body["after"] = after

        resp = requests.post(url, headers=HEADERS, json=body, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        results = data.get('results', [])
        all_contacts.extend(results)

        paging = data.get('paging', {}).get('next', {})
        after = paging.get('after')
        if not after:
            break

        # Rate limit courtesy
        import time
        time.sleep(0.15)

    return all_contacts


def classify_contact(props):
    """Classify contact into no-touch vs sales-touched path."""
    score = props.get('fit_score_contador')
    owner = props.get('hubspot_owner_id')

    try:
        score_val = float(score) if score else 0
    except (ValueError, TypeError):
        score_val = 0

    has_owner = bool(owner and str(owner).strip())

    if score_val >= 40 and has_owner:
        return 'sales_touched'
    return 'no_touch'


def classify_funnel_stage(props):
    """Determine the furthest funnel stage reached."""
    stages = []
    stages.append('registered')

    # Wizard completed proxy: rol_wizard is populated
    if props.get('rol_wizard') and str(props['rol_wizard']).strip():
        stages.append('wizard_completed')

    # PQL: activo = true
    activo = props.get('activo')
    if activo and str(activo).lower() in ('true', '1', 'yes'):
        stages.append('pql')

    # Converted: num_associated_deals > 0 (proxy — ideally check closed-won)
    deals = props.get('num_associated_deals')
    try:
        if deals and int(deals) > 0:
            stages.append('converted')
    except (ValueError, TypeError):
        pass

    return stages


def classify_channel(props):
    """Classify acquisition channel from UTM data."""
    source = (props.get('initial_utm_source') or '').lower()
    medium = (props.get('initial_utm_medium') or '').lower()
    campaign = (props.get('initial_utm_campaign') or '').lower()
    analytics = (props.get('hs_analytics_source') or '').lower()
    lead_source = (props.get('lead_source') or '')

    if source == 'google' and medium in ('cpc', 'ppc'):
        return 'Google Ads'
    if source in ('facebook', 'instagram', 'meta', 'fb', 'ig'):
        return 'Meta Ads'
    if source == 'linkedin':
        return 'LinkedIn Ads'
    if 'conexi' in lead_source.lower() or 'invit' in lead_source.lower():
        return 'Connections'
    if source == 'colppy' and 'referral' in campaign:
        return 'Colppy Portal'
    if not source and analytics == 'organic_search':
        return 'Organic Search'
    if not source and analytics == 'direct_traffic':
        return 'Direct'
    if not source:
        return 'Organic/Direct'
    return 'Other'


def main():
    parser = argparse.ArgumentParser(description='Onboarding Pulse Baseline')
    parser.add_argument('--weeks', type=int, default=4, help='Number of weeks to look back')
    parser.add_argument('--from-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--to-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--output', type=str, help='Output JSON path')
    args = parser.parse_args()

    if args.from_date and args.to_date:
        from_date = datetime.strptime(args.from_date, '%Y-%m-%d')
        to_date = datetime.strptime(args.to_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
    else:
        to_date = datetime.now()
        from_date = to_date - timedelta(weeks=args.weeks)

    print(f"Fetching HubSpot contacts: {from_date.strftime('%Y-%m-%d')} → {to_date.strftime('%Y-%m-%d')}")
    contacts = search_contacts(from_date, to_date)
    print(f"Found {len(contacts)} contacts")

    # Process each contact
    processed = []
    for c in contacts:
        props = c.get('properties', {})
        path = classify_contact(props)
        stages = classify_funnel_stage(props)
        channel = classify_channel(props)

        processed.append({
            'email': props.get('email'),
            'createdate': props.get('createdate'),
            'path': path,
            'stages': stages,
            'furthest_stage': stages[-1] if stages else 'registered',
            'channel': channel,
            'rol_wizard': props.get('rol_wizard'),
            'fit_score_contador': props.get('fit_score_contador'),
            'hubspot_owner_id': props.get('hubspot_owner_id'),
            'activo': props.get('activo'),
            'fecha_activo': props.get('fecha_activo'),
            'lead_source': props.get('lead_source'),
            'initial_utm_source': props.get('initial_utm_source'),
            'initial_utm_campaign': props.get('initial_utm_campaign'),
        })

    # Compute aggregates
    total = len(processed)
    no_touch = [c for c in processed if c['path'] == 'no_touch']
    sales_touched = [c for c in processed if c['path'] == 'sales_touched']

    def funnel_counts(contacts_list):
        return {
            'registered': len(contacts_list),
            'wizard_completed': sum(1 for c in contacts_list if 'wizard_completed' in c['stages']),
            'pql': sum(1 for c in contacts_list if 'pql' in c['stages']),
            'converted': sum(1 for c in contacts_list if 'converted' in c['stages']),
        }

    funnel = {
        'total': funnel_counts(processed),
        'no_touch': funnel_counts(no_touch),
        'sales_touched': funnel_counts(sales_touched),
    }

    # Channel breakdown
    channels = {}
    for c in processed:
        ch = c['channel']
        if ch not in channels:
            channels[ch] = {'registered': 0, 'pql': 0, 'no_touch': 0, 'sales_touched': 0}
        channels[ch]['registered'] += 1
        if 'pql' in c['stages']:
            channels[ch]['pql'] += 1
        channels[ch][c['path']] += 1

    # Wizard skip rate (no-touch only)
    nt_wizard_skip = sum(1 for c in no_touch if 'wizard_completed' not in c['stages'])
    nt_wizard_skip_rate = (nt_wizard_skip / len(no_touch) * 100) if no_touch else 0

    result = {
        'period': {
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'generated_at': datetime.now().isoformat(),
        },
        'funnel': funnel,
        'channels': channels,
        'activation_quality': {
            'wizard_skip_rate_no_touch': round(nt_wizard_skip_rate, 1),
            'total_no_touch': len(no_touch),
            'total_sales_touched': len(sales_touched),
        },
        'contacts': processed,
    }

    # Output
    output_path = args.output or os.path.join(
        _project_root, 'plugins', 'colppy-product', 'data',
        f'onboarding_pulse_baseline_{from_date.strftime("%Y%m%d")}_{to_date.strftime("%Y%m%d")}.json'
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print(f"ONBOARDING PULSE BASELINE — {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
    print(f"{'='*60}")
    print(f"\nTotal contacts: {total}")
    print(f"  No-touch (PLG): {len(no_touch)} ({len(no_touch)/total*100:.1f}%)")
    print(f"  Sales-touched:  {len(sales_touched)} ({len(sales_touched)/total*100:.1f}%)")

    print(f"\n{'─'*60}")
    print(f"{'Stage':<25} {'No-Touch':>10} {'Sales':>10} {'Total':>10}")
    print(f"{'─'*60}")
    for stage in ['registered', 'wizard_completed', 'pql', 'converted']:
        nt = funnel['no_touch'][stage]
        st = funnel['sales_touched'][stage]
        tot = funnel['total'][stage]
        nt_pct = f"({nt/funnel['no_touch']['registered']*100:.1f}%)" if funnel['no_touch']['registered'] else ""
        st_pct = f"({st/funnel['sales_touched']['registered']*100:.1f}%)" if funnel['sales_touched']['registered'] else ""
        tot_pct = f"({tot/funnel['total']['registered']*100:.1f}%)" if funnel['total']['registered'] else ""
        print(f"  {stage:<23} {nt:>4} {nt_pct:>5}  {st:>4} {st_pct:>5}  {tot:>4} {tot_pct:>5}")

    print(f"\n{'─'*60}")
    print(f"Wizard skip rate (no-touch): {nt_wizard_skip_rate:.1f}%")

    print(f"\n{'─'*60}")
    print(f"{'Channel':<20} {'Reg':>5} {'PQL':>5} {'PQL%':>6} {'NoTouch%':>9}")
    print(f"{'─'*60}")
    for ch, data in sorted(channels.items(), key=lambda x: -x[1]['registered']):
        pql_rate = (data['pql'] / data['registered'] * 100) if data['registered'] else 0
        nt_pct = (data['no_touch'] / data['registered'] * 100) if data['registered'] else 0
        print(f"  {ch:<18} {data['registered']:>5} {data['pql']:>5} {pql_rate:>5.1f}% {nt_pct:>8.1f}%")

    print(f"\nSaved to: {output_path}")
    return result


if __name__ == '__main__':
    main()
