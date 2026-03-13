#!/usr/bin/env python3
"""
Check wizard profile properties for today's new users.

Fetches Mixpanel user profiles via Engage API and checks which wizard
properties are set vs missing.

Usage:
    python3 tools/scripts/mixpanel/check_wizard_profiles.py

Requires: MIXPANEL_USERNAME, MIXPANEL_PASSWORD, MIXPANEL_PROJECT_ID in .env
Rate limit: Engage API shares the 60/hr Query API limit. Run when cool.
"""

import os
import json
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(project_root / ".env")

MIXPANEL_USERNAME = os.getenv("MIXPANEL_USERNAME")
MIXPANEL_PASSWORD = os.getenv("MIXPANEL_PASSWORD")
MIXPANEL_PROJECT_ID = os.getenv("MIXPANEL_PROJECT_ID")

auth_string = f"{MIXPANEL_USERNAME}:{MIXPANEL_PASSWORD}"
encoded_auth = base64.b64encode(auth_string.encode()).decode()


def fetch_profiles(distinct_ids):
    """Fetch user profiles via Engage API."""
    resp = requests.post(
        "https://mixpanel.com/api/2.0/engage",
        headers={"Authorization": f"Basic {encoded_auth}", "Accept": "application/json"},
        data={
            "project_id": MIXPANEL_PROJECT_ID,
            "distinct_ids": json.dumps(distinct_ids),
        },
    )
    data = resp.json()
    if "error" in data:
        print(f"ERROR: {data['error']}")
        return {}

    lookup = {}
    for r in data.get("results", []):
        props = r.get("$properties", {})
        did = props.get("$distinct_id", "")
        lookup[did] = props
    return lookup


def main():
    # Today's new users who completed the wizard (from Raw Export analysis)
    wizard_done = [
        "Rhooluduena@gmail.com",
        "gestion@reynaciclismo.com.ar",
        "qebymataxe@maildrop.cc",
        "fezuv@maildrop.cc",
        "wet.wren9743@maildrop.cc",
    ]
    wizard_not_done = [
        "aliciagolan@yahoo.com.ar",
        "celestinolozano52@gmail.com",
    ]
    all_ids = wizard_done + wizard_not_done

    WIZARD_PROPS = {
        "rol": "¿Cuál es tu rol? wizard",
        "cuando": "¿Cuándo querés implementar Colppy? wizard",
        "facturas": "¿Cuántas facturas emitís al mes?",
        "industria": "Industria (colppy)",
        "experiment": "PRODUCT_TOUR_EXPERIMENT",
    }

    print(f"Fetching {len(all_ids)} profiles...")
    profiles = fetch_profiles(all_ids)
    print(f"Got {len(profiles)} profiles\n")

    if not profiles:
        print("No profiles returned — likely rate limited. Try again later.")
        return

    print("=" * 100)
    print("NEW USERS TODAY — Wizard Profile Properties")
    print("=" * 100)

    for uid in all_ids:
        props = profiles.get(uid, {})
        ws = "WIZARD DONE" if uid in wizard_done else "WIZARD NOT DONE"
        if not props:
            print(f"\n  {uid} — {ws} — NO PROFILE")
            continue

        print(f"\n  {uid} — {ws}")
        print(f"    Wizard answers:")
        for label, prop_key in WIZARD_PROPS.items():
            val = props.get(prop_key, None)
            if val is None:
                print(f"      {label:15s}: — MISSING")
            else:
                print(f"      {label:15s}: {str(val)[:50]}")

        print(f"    Other profile:")
        for ep in [
            "Es Contador", "Es Administrador", "Estado Usuario",
            "Fecha de registro", "Verificó email", "company", "product_id",
        ]:
            val = props.get(ep, None)
            if val is not None:
                print(f"      {ep:25s}: {val}")

    # Summary
    print(f"\n{'=' * 90}")
    header = f"{'Group':20s} | {'#':3s} | {'Rol':4s} | {'Cuándo':8s} | {'Facturas':8s} | {'Industria':9s} | {'Experiment':10s}"
    print(header)
    print("-" * 90)
    for gname, gids in [("Wizard DONE", wizard_done), ("Wizard NOT DONE", wizard_not_done)]:
        n = len(gids)
        c = {}
        for label, pk in WIZARD_PROPS.items():
            c[label] = sum(
                1 for u in gids if profiles.get(u, {}).get(pk) not in (None, "")
            )
        print(
            f"{gname:20s} | {n:3d} | {c['rol']:4d} | {c['cuando']:8d} | "
            f"{c['facturas']:8d} | {c['industria']:9d} | {c['experiment']:10d}"
        )


if __name__ == "__main__":
    main()
