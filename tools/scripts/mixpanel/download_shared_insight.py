#!/usr/bin/env python3
"""
Download a Mixpanel Insight report from a share link.

Resolves /s/TOKEN share links to bookmark IDs, then downloads the report data.

Usage:
    python download_shared_insight.py https://mixpanel.com/s/1giXfM
    python download_shared_insight.py https://mixpanel.com/s/1giXfM -o report.json
    python download_shared_insight.py --bookmark-id 12345
"""

import sys
import os
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv

# Load env
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
load_dotenv(project_root / ".env")

sys.path.insert(0, str(script_dir))
from mixpanel_api import MixpanelAPI

# Cache directory — under trial-data-model skill (NOT intercom cache)
CACHE_DIR = project_root / "plugins" / "colppy-customer-success" / "skills" / "trial-data-model" / "cache"


def resolve_share_link(share_url: str) -> dict:
    """
    Resolve a Mixpanel share link (/s/TOKEN) to get the bookmark_id.

    Share links redirect to the full Mixpanel report URL which contains
    the bookmark_id in the fragment: ...editor-card-id="report-BOOKMARK_ID"

    Returns: dict with bookmark_id and full_url
    """
    import requests

    print(f"Resolving share link: {share_url}")

    # Follow redirects to get the full URL
    r = requests.get(share_url, allow_redirects=True)

    full_url = r.url
    print(f"  Resolved to: {full_url[:120]}...")

    # Try to extract bookmark_id from URL fragment or page content
    # Pattern 1: URL contains report-BOOKMARK_ID
    match = re.search(r'report-(\d+)', full_url)
    if match:
        return {"bookmark_id": match.group(1), "full_url": full_url}

    # Pattern 2: Search page content for bookmark reference
    match = re.search(r'"bookmark_id"\s*:\s*(\d+)', r.text)
    if match:
        return {"bookmark_id": match.group(1), "full_url": full_url}

    # Pattern 3: Search for report ID in various formats
    match = re.search(r'"id"\s*:\s*(\d+).*?"type"\s*:\s*"report"', r.text)
    if match:
        return {"bookmark_id": match.group(1), "full_url": full_url}

    # Pattern 4: Extract from data attributes
    match = re.search(r'data-bookmark-id="(\d+)"', r.text)
    if match:
        return {"bookmark_id": match.group(1), "full_url": full_url}

    # If we can't find it, save the HTML for debugging
    debug_file = CACHE_DIR / "mixpanel_share_debug.html"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(debug_file, "w") as f:
        f.write(r.text)

    print(f"  Could not extract bookmark_id automatically.")
    print(f"  Debug HTML saved to: {debug_file}")
    print(f"  Full URL: {full_url}")
    print()
    print("  To get the bookmark_id manually:")
    print("  1. Open the share link in your browser")
    print("  2. Once the report loads, check the URL bar")
    print('  3. Look for: editor-card-id="report-BOOKMARK_ID"')
    print("  4. Run again with: --bookmark-id BOOKMARK_ID")

    return {"bookmark_id": None, "full_url": full_url}


def download_insight(bookmark_id: str, output_file: str = None) -> Path:
    """Download an Insight report by bookmark_id."""

    mixpanel = MixpanelAPI()

    if not mixpanel.auth[0]:
        print("Error: Set MIXPANEL_USERNAME and MIXPANEL_PASSWORD in .env")
        sys.exit(1)

    print(f"Downloading insight report (bookmark: {bookmark_id})...")

    try:
        result = mixpanel.export_insight_report(
            bookmark_id=bookmark_id,
            return_raw_json=True,
        )
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Save output
    if output_file is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d")
        output_file = str(CACHE_DIR / f"mixpanel_insight_{bookmark_id}_{ts}.json")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Saved to: {output_file}")

    # Print summary
    if isinstance(result, dict):
        series = result.get("series", {})
        if series:
            print(f"  Series keys: {list(series.keys())[:5]}")
        values = result.get("values", {})
        if values:
            print(f"  Value groups: {len(values)}")

    return Path(output_file)


def main():
    parser = argparse.ArgumentParser(description="Download Mixpanel Insight from share link")
    parser.add_argument("url", nargs="?", help="Share link (https://mixpanel.com/s/TOKEN)")
    parser.add_argument("--bookmark-id", "-b", help="Direct bookmark ID (skip share link resolution)")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--resolve-only", action="store_true",
                        help="Only resolve the share link, don't download")

    args = parser.parse_args()

    if not args.url and not args.bookmark_id:
        parser.print_help()
        sys.exit(1)

    bookmark_id = args.bookmark_id

    if args.url and not bookmark_id:
        resolved = resolve_share_link(args.url)
        bookmark_id = resolved["bookmark_id"]

        if not bookmark_id:
            sys.exit(1)

        if args.resolve_only:
            print(f"\nBookmark ID: {bookmark_id}")
            sys.exit(0)

    download_insight(bookmark_id, args.output)


if __name__ == "__main__":
    main()
