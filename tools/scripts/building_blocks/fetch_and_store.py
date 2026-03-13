#!/usr/bin/env python3
"""
Building Blocks — Fetch & Store (Supabase)
Fetches Building Blocks tabs from Google Sheets, parses them,
stores snapshots + parsed KPI values in Supabase, and detects changes.

Usage:
    python3 tools/scripts/building_blocks/fetch_and_store.py [--all] [--tab ID] [--dump] [--diff]

    --all       Fetch and store all 7 Building Blocks tabs
    --tab ID    Fetch a specific tab (default: colppy_budget_first)
    --dump      Print all current values after fetch
    --diff      Show changes vs previous snapshot

Requires: SUPABASE_URL and SUPABASE_SECRET_KEY in tools/.env
"""

import argparse
import csv
import io
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
ENV_PATH = os.path.join(REPO_ROOT, "tools", ".env")
REGISTRY_PATH = os.path.join(REPO_ROOT, "tools", "docs", "GOOGLE_SHEETS_REGISTRY.json")


def load_env():
    """Load key=value pairs from tools/.env"""
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

ALL_TABS = [
    "colppy_budget_first",
    "colppy_budget",
    "funnel_from_lead_product_icp",
    "funnel_lead_product_icp",
    "churn_budget_real",
    "colppy_raw_actuals",
    "colppy_budget_aprobado",
]


# ── Month column mappings ─────────────────────────────────────────────────
# Standard: shared by colppy_budget_first, colppy_budget, and funnel tabs
MONTH_COLS_STANDARD = {
    "Jan-2026": 31, "Feb-2026": 32, "Mar-2026": 33,
    "Apr-2026": 34, "May-2026": 35, "Jun-2026": 36,
    "Jul-2026": 37, "Aug-2026": 38, "Sep-2026": 39,
    "Oct-2026": 40, "Nov-2026": 41, "Dec-2026": 42,
}

MONTH_COLS_CHURN = {
    "Jan-2026": 5, "Feb-2026": 6, "Mar-2026": 7,
    "Apr-2026": 8, "May-2026": 9, "Jun-2026": 10,
    "Jul-2026": 11, "Aug-2026": 12, "Sep-2026": 13,
    "Oct-2026": 14, "Nov-2026": 15, "Dec-2026": 16,
}

MONTH_COLS_RAW_ACTUALS = {
    "Jan-2026": 13, "Feb-2026": 14,
}

MONTH_COLS_BUDGET_APROBADO = {
    "Jan-2026": 15, "Feb-2026": 16, "Mar-2026": 17,
    "Apr-2026": 18, "May-2026": 19, "Jun-2026": 20,
    "Jul-2026": 21, "Aug-2026": 22, "Sep-2026": 23,
    "Oct-2026": 24, "Nov-2026": 25, "Dec-2026": 26,
}


# ── Validated row map for colppy_budget_first (Pattern E) ─────────────────
# Source: memory/building_blocks_data_model.md (validated 2026-03-13)

ROW_MAP = {
    "budget": {
        "clients": {
            "bop": 2, "new_clients": 4, "subtotal_plus": 6,
            "lost_early": 8, "lost_mid": 9, "lost_late": 10,
            "subtotal_minus": 12, "eop": 14,
        },
        "mrr": {
            "bop": 18, "new_mrr": 20, "upsell": 21,
            "price_increase": 22, "expired_discounts": 23,
            "subtotal_plus": 25, "lost_mrr": 27, "downsell": 28,
            "retention_discounts": 29, "subtotal_minus": 31, "eop": 33,
        },
        "measures": {
            "new_asp": 37, "churn_asp": 38, "pct_churn": 40,
        },
    },
    "forecast": {
        "clients": {
            "bop": 47, "new_clients": 49, "subtotal_plus": 51,
            "lost_early": 53, "lost_mid": 54, "lost_late": 55,
            "subtotal_minus": 57, "eop": 59,
        },
        "mrr": {
            "bop": 63, "new_mrr": 65, "upsell": 66, "cross_sell": 67,
            "price_increase": 68, "expired_discounts": 69,
            "subtotal_plus": 71, "lost_mrr": 73, "downsell": 74,
            "retention_discounts": 75, "subtotal_minus": 77, "eop": 79,
        },
        "measures": {
            "new_asp": 83, "churn_asp": 84, "pct_churn": 86,
        },
    },
    "real": {
        "clients": {
            "bop": 91, "new_clients": 93, "subtotal_plus": 95,
            "lost_early": 97, "lost_mid": 98, "lost_late": 99,
            "subtotal_minus": 101, "eop": 103,
        },
        "mrr": {
            "bop": 107, "new_mrr": 109, "upsell": 110, "cross_sell": 111,
            "price_increase": 112, "expired_discounts": 113,
            "subtotal_plus": 115, "lost_mrr": 117, "downsell": 118,
            "retention_discounts": 119, "subtotal_minus": 121, "eop": 123,
        },
        "measures": {
            "new_asp": 127, "churn_asp": 128, "pct_churn": 130,
        },
    },
}


# ── Supabase REST helpers ────────────────────────────────────────────────

def supabase_request(method: str, table: str, data=None, params: str = "",
                     headers_extra: dict = None, prefer: str = None) -> dict | list:
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
    if headers_extra:
        hdrs.update(headers_extra)

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text) if text else {}


def sb_insert(table: str, rows: list[dict], return_cols: str = "id") -> list[dict]:
    """Insert rows and return specified columns."""
    return supabase_request(
        "POST", table, data=rows,
        params=f"select={return_cols}",
        prefer="return=representation",
    )


def sb_select(table: str, params: str) -> list[dict]:
    """Select rows with query params."""
    return supabase_request("GET", table, params=params)


# ── Google Sheets / Registry ─────────────────────────────────────────────

def get_tab_info(tab_id: str) -> dict:
    with open(REGISTRY_PATH) as f:
        registry = json.load(f)
    for tab in registry["tabs"]:
        if tab["id"] == tab_id:
            return tab
    raise ValueError(f"Tab '{tab_id}' not found in registry")


def fetch_csv(file_id: str, gid: str) -> str:
    url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


# ── Value parsing ────────────────────────────────────────────────────────

def parse_value(raw: str) -> float | None:
    """Parse a cell value from the Building Blocks CSV."""
    if not raw or not raw.strip():
        return None
    s = raw.strip()
    # Dash = empty
    if s in ("-", "—", "–", "- ", " - ", "  -  ", "  - "):
        return None
    # Parentheses = negative
    is_negative = s.startswith("(") and s.endswith(")")
    if is_negative:
        s = s[1:-1].strip()
    s = s.lstrip("$").strip()
    # Percentage
    is_pct = s.endswith("%")
    if is_pct:
        s = s.rstrip("%").strip()
    # Ratio (e.g. "3.4x")
    is_ratio = s.endswith("x")
    if is_ratio:
        s = s.rstrip("x").strip()
    s = s.replace(",", "")
    try:
        val = float(s)
        if is_pct:
            val = val / 100.0
        if is_negative:
            val = -val
        return val
    except ValueError:
        return None


# ── Row-map parser for colppy_budget_first (validated) ───────────────────

def parse_rowmap(tab_id: str, rows: list[list[str]]) -> list[dict]:
    """Parse using the validated row map. Returns list of value dicts."""
    values = []
    for section, blocks in ROW_MAP.items():
        for block, lines in blocks.items():
            for line_name, row_idx in lines.items():
                if row_idx >= len(rows):
                    continue
                row = rows[row_idx]
                for month, col_idx in MONTH_COLS_STANDARD.items():
                    if col_idx >= len(row):
                        continue
                    raw_val = row[col_idx]
                    parsed = parse_value(raw_val)
                    values.append({
                        "tab_id": tab_id,
                        "section": section,
                        "block": block,
                        "line_name": line_name,
                        "month": month,
                        "value": parsed,
                        "raw_value": raw_val,
                        "row_index": row_idx,
                    })
    return values


# ── Label-based parser for non-validated tabs ────────────────────────────

# Section markers to detect in CSV cells
SECTION_MARKERS_MAP = {
    "FORECAST": "forecast",
    "FORECAST 2026": "forecast",
    "FORECAST 2026 DECEMBER": "forecast",
    "REAL": "real",
    "ACTUAL": "real",
    "ACTUAL 2026": "real",
}

# Labels to skip (headers, totals, meta rows)
SKIP_LABELS = {
    "", "Item", "Unit", "Product", "MRR", "KPIS (ARS)",
}

# Meta row prefixes to skip (Pattern A noise)
SKIP_PREFIXES = (
    "Forecast Factor", "Variaciones", "Price Increase Relate",
    "New Increase", "Upsell Increase", "Cross Increase",
    "Average Increase", "Monthly Revenues", "Price Increase Total",
    "Price Increase %", "PENDING",
)


def get_tab_config(tab_id: str) -> dict:
    """Return parsing config for a given tab."""
    if tab_id in ("colppy_budget", "funnel_from_lead_product_icp", "funnel_lead_product_icp"):
        return {
            "label_col": 4,
            "month_cols": MONTH_COLS_STANDARD,
            "section_col": 4,
            "default_section": "forecast",
            "default_block": "default",
        }
    elif tab_id == "churn_budget_real":
        return {
            "label_col": 0,
            "month_cols": MONTH_COLS_CHURN,
            "section_col": 0,
            "default_section": "forecast",
            "default_block": "churn_mix",
        }
    elif tab_id == "colppy_raw_actuals":
        return {
            "label_col": 1,
            "month_cols": MONTH_COLS_RAW_ACTUALS,
            "section_col": None,
            "default_section": "real",
            "default_block": "actuals",
        }
    elif tab_id == "colppy_budget_aprobado":
        return {
            "label_col": 2,
            "month_cols": MONTH_COLS_BUDGET_APROBADO,
            "section_col": None,
            "default_section": "budget",
            "default_block": "kpis_ars",
        }
    raise ValueError(f"No config for tab: {tab_id}")


def parse_labeled(tab_id: str, rows: list[list[str]]) -> list[dict]:
    """Parse a tab using label-based auto-discovery. Returns list of value dicts."""
    cfg = get_tab_config(tab_id)
    label_col = cfg["label_col"]
    month_cols = cfg["month_cols"]
    section_col = cfg["section_col"]
    current_section = cfg["default_section"]
    current_block = cfg["default_block"]
    values = []

    for row_idx, row in enumerate(rows):
        # Check for section markers
        if section_col is not None and len(row) > section_col:
            cell = row[section_col].strip()
            cell_upper = cell.upper()
            if cell_upper in SECTION_MARKERS_MAP:
                current_section = SECTION_MARKERS_MAP[cell_upper]
                continue
            # Churn tab: "Lost MRR Actual (Ending MRR)" precedes REAL
            if "Lost MRR Actual" in cell:
                continue

        # Budget aprobado: detect sub-section headers
        if tab_id == "colppy_budget_aprobado" and len(row) > 2:
            cell = row[2].strip()
            if cell == "Clients (#)":
                current_block = "clients"
                continue
            elif cell == "Reps Performance":
                current_block = "reps"
                continue
            elif cell == "Units Economics (ARS k)":
                current_block = "unit_economics_ars_k"
                continue

        # Churn tab: "% of MRR" sub-section
        if tab_id == "churn_budget_real" and len(row) > 0:
            if "% of MRR" in row[0]:
                current_block = "pct_of_mrr"
                continue

        # Get label
        if len(row) <= label_col:
            continue
        label = row[label_col].strip()

        # Skip non-data rows
        if label in SKIP_LABELS:
            continue
        if any(label.startswith(p) for p in SKIP_PREFIXES):
            continue
        # Skip section markers that might appear in label column
        if label.upper() in SECTION_MARKERS_MAP:
            continue
        if label.startswith("Lost MRR"):
            continue

        # Extract values for each month
        for month, col_idx in month_cols.items():
            if col_idx >= len(row):
                continue
            raw_val = row[col_idx].strip()
            parsed = parse_value(raw_val)
            # Only store if there's actual data
            if parsed is not None or (raw_val and raw_val.strip()):
                values.append({
                    "tab_id": tab_id,
                    "section": current_section,
                    "block": current_block,
                    "line_name": label,
                    "month": month,
                    "value": parsed,
                    "raw_value": raw_val,
                    "row_index": row_idx,
                })

    return values


# ── Unified parse + store ────────────────────────────────────────────────

def parse_and_store(tab_id: str, raw_csv: str) -> int:
    """Parse CSV and store snapshot + values in Supabase. Returns snapshot_id."""
    rows = list(csv.reader(io.StringIO(raw_csv)))
    now = datetime.now(timezone.utc).isoformat()

    # Insert snapshot
    result = sb_insert("snapshots", [{
        "fetched_at": now,
        "tab_id": tab_id,
        "row_count": len(rows),
    }])
    snapshot_id = result[0]["id"]

    # Parse using appropriate strategy
    if tab_id == "colppy_budget_first":
        values = parse_rowmap(tab_id, rows)
    else:
        values = parse_labeled(tab_id, rows)

    # Attach snapshot_id
    for v in values:
        v["snapshot_id"] = snapshot_id

    # Batch insert
    BATCH = 500
    for i in range(0, len(values), BATCH):
        sb_insert("kpi_values", values[i:i + BATCH])

    print(f"  Stored snapshot #{snapshot_id}: {len(values)} values from {len(rows)} rows")
    return snapshot_id


# ── Change detection ─────────────────────────────────────────────────────

def detect_changes(tab_id: str, new_snapshot_id: int) -> list[dict]:
    """Compare new snapshot against the previous one for the same tab."""
    prev = sb_select("snapshots",
        f"tab_id=eq.{tab_id}&id=lt.{new_snapshot_id}&order=id.desc&limit=1&select=id")

    if not prev:
        return []

    prev_id = prev[0]["id"]
    now = datetime.now(timezone.utc).isoformat()

    def get_values(snap_id):
        rows = sb_select("kpi_values",
            f"snapshot_id=eq.{snap_id}&select=section,block,line_name,month,value")
        return {(r["section"], r["block"], r["line_name"], r["month"]): r["value"] for r in rows}

    old_vals = get_values(prev_id)
    new_vals = get_values(new_snapshot_id)

    changes = []
    all_keys = set(old_vals.keys()) | set(new_vals.keys())
    change_inserts = []
    for key in sorted(all_keys):
        old_v = old_vals.get(key)
        new_v = new_vals.get(key)
        if old_v != new_v and not (old_v is None and new_v is None):
            section, block, line_name, month = key
            changes.append({
                "section": section, "block": block,
                "line_name": line_name, "month": month,
                "old": old_v, "new": new_v,
            })
            change_inserts.append({
                "detected_at": now, "tab_id": tab_id,
                "section": section, "block": block,
                "line_name": line_name, "month": month,
                "old_value": old_v, "new_value": new_v,
                "old_snapshot": prev_id, "new_snapshot": new_snapshot_id,
            })

    if change_inserts:
        for i in range(0, len(change_inserts), 500):
            sb_insert("change_log", change_inserts[i:i + 500])

    return changes


# ── Display ──────────────────────────────────────────────────────────────

def dump_current(snapshot_id: int):
    """Print all values from the latest snapshot."""
    rows = sb_select("kpi_values",
        f"snapshot_id=eq.{snapshot_id}&order=section,block,line_name,month&select=section,block,line_name,month,value,raw_value")

    current_section = None
    current_block = None
    for r in rows:
        if r["section"] != current_section:
            print(f"\n{'='*60}")
            print(f"  {r['section'].upper()}")
            print(f"{'='*60}")
            current_section = r["section"]
            current_block = None
        if r["block"] != current_block:
            print(f"\n  [{r['block']}]")
            current_block = r["block"]
        val = r["value"]
        val_str = f"{val:>15,.2f}" if val is not None else f"{'—':>15s}"
        print(f"    {r['line_name']:<55s} {r['month']:<12s} {val_str}  (raw: {r['raw_value']})")


def print_changes(changes: list[dict]):
    if not changes:
        print("  No changes vs previous snapshot.")
        return
    print(f"\n  {'!'*60}")
    print(f"  {len(changes)} VALUE(S) CHANGED vs previous snapshot")
    print(f"  {'!'*60}")
    for c in changes:
        old_s = f"{c['old']:,.2f}" if c['old'] is not None else "—"
        new_s = f"{c['new']:,.2f}" if c['new'] is not None else "—"
        print(f"  {c['section']:8s} {c['block']:20s} {c['line_name']:<40s} {c['month']:<12s} {old_s} → {new_s}")


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Fetch & store Building Blocks data in Supabase")
    parser.add_argument("--all", action="store_true", help="Fetch all 7 Building Blocks tabs")
    parser.add_argument("--tab", default="colppy_budget_first", help="Tab ID to fetch (default: colppy_budget_first)")
    parser.add_argument("--dump", action="store_true", help="Print all current values after fetch")
    parser.add_argument("--diff", action="store_true", help="Show changes vs previous snapshot")
    args = parser.parse_args()

    tabs_to_fetch = ALL_TABS if args.all else [args.tab]
    total_values = 0

    for tab_id in tabs_to_fetch:
        tab = get_tab_info(tab_id)
        print(f"\nFetching {tab['tab_name']}...")
        raw_csv = fetch_csv(tab["file_id"], tab["gid"])
        print(f"  Fetched {len(raw_csv)} bytes")

        snapshot_id = parse_and_store(tab_id, raw_csv)

        if args.diff:
            changes = detect_changes(tab_id, snapshot_id)
            print_changes(changes)

        if args.dump:
            dump_current(snapshot_id)

    print(f"\nDone. {len(tabs_to_fetch)} tab(s) stored in Supabase.")


if __name__ == "__main__":
    main()
