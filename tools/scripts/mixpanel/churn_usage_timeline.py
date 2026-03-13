#!/usr/bin/env python3
"""
Churn investigation: per-company monthly usage timeline.

Given a company_id or user email, produces a monthly breakdown of key metrics
(logins, invoices, feature diversity) to identify usage decline patterns.

Usage:
    # By company ID
    python churn_usage_timeline.py --company 20486 --months 6

    # By user email (finds companies first, then analyzes each)
    python churn_usage_timeline.py --email gbreier@emporioaroma.com.ar --months 6

    # Custom date range
    python churn_usage_timeline.py --company 20486 --from 2025-09-01 --to 2026-03-10

    # JSON output (for agent consumption)
    python churn_usage_timeline.py --company 20486 --months 6 --json

Output: Monthly timeline with login count, invoice count (compra+venta),
feature diversity, and trend indicators.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from mixpanel_api import MixpanelAPI

from dotenv import load_dotenv
project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")

# Critical events grouped by category
EVENT_CATEGORIES = {
    "login": ["Login"],
    "invoice_venta": ["Generó comprobante de venta"],
    "invoice_compra": ["Generó comprobante de compra"],
    "cobro": ["Generó recibo de cobro"],
    "pago": ["Generó orden de pago"],
    "contabilidad": ["Generó asiento contable", "Descargó el balance", "Descargó el diario general"],
    "inventario": ["Movimiento de stock"],
    "sueldos": ["Liquidación de sueldos"],
    "config": ["Configuración empresa", "Alta de usuario"],
}

ALL_EVENTS = [e for events in EVENT_CATEGORIES.values() for e in events]


def get_monthly_company_events(mixpanel: MixpanelAPI, company_id: str, from_date: str, to_date: str) -> list:
    """Get monthly event counts for a company, grouped by event name and month."""
    script = f'''
    function main() {{
        return Events({{
            from_date: "{from_date}",
            to_date: "{to_date}"
        }})
        .filter(function(event) {{
            return (
                (event.properties["$groups"] &&
                 event.properties["$groups"]["Company"] === "{company_id}") ||
                event.properties["idEmpresa"] === "{company_id}" ||
                event.properties["company_id"] === "{company_id}" ||
                (event.properties["company"] &&
                 (event.properties["company"] === "{company_id}" ||
                  (Array.isArray(event.properties["company"]) &&
                   event.properties["company"].indexOf("{company_id}") >= 0)))
            );
        }})
        .groupBy(
            [function(event) {{
                var d = new Date(event.time);
                return d.getFullYear() + "-" + ("0" + (d.getMonth()+1)).slice(-2);
            }}, "name"],
            mixpanel.reducer.count()
        )
        .map(function(result) {{
            return {{
                month: result.key[0],
                event_name: result.key[1],
                count: result.value
            }};
        }});
    }}
    '''
    return mixpanel.run_jql(script)


def get_monthly_user_events(mixpanel: MixpanelAPI, email: str, from_date: str, to_date: str) -> list:
    """Get monthly event counts for a user by email."""
    script = f'''
    function main() {{
        return Events({{
            from_date: "{from_date}",
            to_date: "{to_date}"
        }})
        .filter(function(event) {{
            return (
                event.properties["$email"] === "{email}" ||
                event.properties["Email"] === "{email}" ||
                event.properties["distinct_id"] === "{email}" ||
                (typeof event.properties["$user_id"] === "string" &&
                 event.properties["$user_id"].toLowerCase() === "{email}".toLowerCase())
            );
        }})
        .groupBy(
            [function(event) {{
                var d = new Date(event.time);
                return d.getFullYear() + "-" + ("0" + (d.getMonth()+1)).slice(-2);
            }}, "name"],
            mixpanel.reducer.count()
        )
        .map(function(result) {{
            return {{
                month: result.key[0],
                event_name: result.key[1],
                count: result.value
            }};
        }});
    }}
    '''
    return mixpanel.run_jql(script)


def categorize_event(event_name: str) -> str:
    """Map an event name to its category."""
    for category, events in EVENT_CATEGORIES.items():
        if event_name in events:
            return category
    return "other"


def build_timeline(raw_events: list) -> dict:
    """Build a structured monthly timeline from raw event data."""
    # Group by month
    months = defaultdict(lambda: defaultdict(int))
    all_months = set()

    for event in raw_events:
        month = event["month"]
        event_name = event["event_name"]
        count = event["count"]
        all_months.add(month)

        category = categorize_event(event_name)
        months[month][category] += count
        months[month]["_total"] += count
        months[month][f"_raw_{event_name}"] = count

    # Sort months chronologically
    sorted_months = sorted(all_months)

    # Build timeline
    timeline = []
    for month in sorted_months:
        data = months[month]

        # Count distinct event types (feature diversity)
        raw_events_in_month = [k for k in data.keys() if k.startswith("_raw_") and data[k] > 0]
        feature_diversity = len(raw_events_in_month)

        entry = {
            "month": month,
            "logins": data.get("login", 0),
            "invoices_venta": data.get("invoice_venta", 0),
            "invoices_compra": data.get("invoice_compra", 0),
            "cobros": data.get("cobro", 0),
            "pagos": data.get("pago", 0),
            "contabilidad": data.get("contabilidad", 0),
            "inventario": data.get("inventario", 0),
            "sueldos": data.get("sueldos", 0),
            "other": data.get("other", 0),
            "total_events": data["_total"],
            "feature_diversity": feature_diversity,
        }
        timeline.append(entry)

    return {
        "months": timeline,
        "summary": compute_summary(timeline),
    }


def compute_summary(timeline: list) -> dict:
    """Compute trend summary from timeline data."""
    if len(timeline) < 2:
        return {"trend": "insufficient_data", "months_analyzed": len(timeline)}

    # Split into halves for comparison
    mid = len(timeline) // 2
    first_half = timeline[:mid]
    second_half = timeline[mid:]

    def avg(entries, key):
        vals = [e[key] for e in entries]
        return sum(vals) / len(vals) if vals else 0

    metrics = {}
    for key in ["logins", "invoices_venta", "invoices_compra", "total_events", "feature_diversity"]:
        first_avg = avg(first_half, key)
        second_avg = avg(second_half, key)

        if first_avg > 0:
            change_pct = ((second_avg - first_avg) / first_avg) * 100
        elif second_avg > 0:
            change_pct = 100.0
        else:
            change_pct = 0.0

        metrics[key] = {
            "first_half_avg": round(first_avg, 1),
            "second_half_avg": round(second_avg, 1),
            "change_pct": round(change_pct, 1),
        }

    # Determine overall trend
    total_change = metrics["total_events"]["change_pct"]
    if total_change <= -50:
        trend = "cliff_drop"
    elif total_change <= -25:
        trend = "significant_decline"
    elif total_change <= -10:
        trend = "moderate_decline"
    elif total_change <= 10:
        trend = "stable"
    elif total_change <= 25:
        trend = "moderate_growth"
    else:
        trend = "strong_growth"

    # Find peak month
    if timeline:
        peak = max(timeline, key=lambda x: x["total_events"])
        last = timeline[-1]
        peak_info = {"month": peak["month"], "total_events": peak["total_events"]}
        last_info = {"month": last["month"], "total_events": last["total_events"]}
    else:
        peak_info = None
        last_info = None

    return {
        "trend": trend,
        "months_analyzed": len(timeline),
        "metrics": metrics,
        "peak_month": peak_info,
        "last_month": last_info,
    }


def print_timeline_table(result: dict, identifier: str):
    """Pretty-print the timeline as a table."""
    timeline = result["months"]
    summary = result["summary"]

    print(f"\n{'='*80}")
    print(f"  USAGE TIMELINE: {identifier}")
    print(f"  Trend: {summary['trend'].upper().replace('_', ' ')}")
    print(f"{'='*80}")

    # Header
    print(f"\n{'Month':<10} {'Logins':>8} {'FC Vta':>8} {'FC Cmp':>8} {'Cobros':>8} {'Pagos':>8} {'Contab':>8} {'Total':>8} {'Divers':>8}")
    print(f"{'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")

    for entry in timeline:
        print(f"{entry['month']:<10} {entry['logins']:>8} {entry['invoices_venta']:>8} {entry['invoices_compra']:>8} "
              f"{entry['cobros']:>8} {entry['pagos']:>8} {entry['contabilidad']:>8} "
              f"{entry['total_events']:>8} {entry['feature_diversity']:>8}")

    # Summary
    print(f"\n{'─'*80}")
    print(f"  SUMMARY (first half vs second half)")
    print(f"{'─'*80}")

    for key, data in summary.get("metrics", {}).items():
        arrow = "↓" if data["change_pct"] < -5 else "↑" if data["change_pct"] > 5 else "→"
        label = key.replace("_", " ").title()
        print(f"  {label:<25} {data['first_half_avg']:>8.1f} → {data['second_half_avg']:>8.1f}  ({arrow} {data['change_pct']:+.1f}%)")

    if summary.get("peak_month"):
        print(f"\n  Peak: {summary['peak_month']['month']} ({summary['peak_month']['total_events']} events)")
        print(f"  Last: {summary['last_month']['month']} ({summary['last_month']['total_events']} events)")


def main():
    parser = argparse.ArgumentParser(description="Churn investigation: per-company monthly usage timeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--company", help="Company ID (id_empresa) to analyze")
    group.add_argument("--email", help="User email (finds companies first, then analyzes)")

    parser.add_argument("--months", type=int, default=6, help="Number of months to look back (default: 6)")
    parser.add_argument("--from", dest="from_date", help="Start date (YYYY-MM-DD), overrides --months")
    parser.add_argument("--to", dest="to_date", help="End date (YYYY-MM-DD), default: today")
    parser.add_argument("--json", action="store_true", help="Output as JSON (for agent consumption)")

    args = parser.parse_args()

    # Calculate date range
    to_date = args.to_date or datetime.now().strftime("%Y-%m-%d")
    if args.from_date:
        from_date = args.from_date
    else:
        from_dt = datetime.now() - timedelta(days=args.months * 30)
        from_date = from_dt.strftime("%Y-%m-%d")

    # Initialize API
    mixpanel = MixpanelAPI()

    if args.email:
        # Step 1: Find companies for this user
        print(f"Finding companies for {args.email}...")
        companies = mixpanel.get_user_companies(args.email, from_date, to_date)

        if not companies:
            # Fallback: get events directly by email
            print(f"No companies found via group lookup. Fetching user events directly...")
            raw_events = get_monthly_user_events(mixpanel, args.email, from_date, to_date)

            if not raw_events:
                print(f"No events found for {args.email} in {from_date} to {to_date}")
                sys.exit(0)

            result = build_timeline(raw_events)

            if args.json:
                print(json.dumps({"email": args.email, "company_id": None, **result}, indent=2, ensure_ascii=False))
            else:
                print_timeline_table(result, args.email)
            return

        print(f"Found {len(companies)} companies: {[c['company_id'] for c in companies]}")

        # Analyze each company
        all_results = {}
        for company in companies:
            cid = str(company["company_id"])
            print(f"\nAnalyzing company {cid}...")
            raw_events = get_monthly_company_events(mixpanel, cid, from_date, to_date)

            if raw_events:
                result = build_timeline(raw_events)
                all_results[cid] = result

                if not args.json:
                    print_timeline_table(result, f"Company {cid} (via {args.email})")
            else:
                print(f"  No events found for company {cid}")

        if args.json:
            print(json.dumps({"email": args.email, "companies": all_results}, indent=2, ensure_ascii=False))

    else:
        # Direct company analysis
        company_id = args.company
        print(f"Analyzing company {company_id} from {from_date} to {to_date}...")

        raw_events = get_monthly_company_events(mixpanel, company_id, from_date, to_date)

        if not raw_events:
            print(f"No events found for company {company_id}")
            sys.exit(0)

        result = build_timeline(raw_events)

        if args.json:
            print(json.dumps({"company_id": company_id, **result}, indent=2, ensure_ascii=False))
        else:
            print_timeline_table(result, f"Company {company_id}")


if __name__ == "__main__":
    main()
