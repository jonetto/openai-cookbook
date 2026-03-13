#!/usr/bin/env python3
"""
HubSpot Analysis MCP Server
===========================
Exposes funnel, scoring, demand-gen, and visualization tools via Model Context Protocol
for use in Cursor, Claude Desktop, etc.

Tools (Funnel & Scoring — existing):
- run_smb_mql_funnel: SMB MQL funnel (MQL PYME → Deal Created → Won)
- run_accountant_mql_funnel: Accountant MQL funnel
- run_smb_accountant_involved_funnel: SMB funnel WITH vs WITHOUT accountant
- run_high_score_analysis: Score 40+ contactability and conversion
- run_mtd_scoring: Month-to-date scoring comparison (SQL/PQL by score range)
- run_visualization_report: HTML report from high_score CSV output

Tools (Demand Gen — evaluator quality, channel attribution, ROI):
- run_evaluator_quality: Evaluator quality by channel, ICP, persona (PQL/SQL/Won/MRR)
- run_pql_by_channel: Lightweight PQL rate by acquisition channel
- run_monthly_pql: Monthly PQL conversion rate trend
- run_deal_conversion_by_lead_source: Deal Created → Won conversion by lead source
- run_product_led_deals: Deals closed without sales activity (PLG/no-touch)
- run_icp_dashboard: ICP segmentation dashboard (revenue, churn by segment)
- run_business_age_conversion: Business age (CUIT/RNS) vs conversion validation
- run_deal_focused_pql: PQL effectiveness via deal attachment and win rate
- run_pql_sql_deal_relationship: Full PQL → SQL → Deal funnel with timing
- run_google_ads_report: Google Ads campaign performance (spend, clicks, conversions)
- run_google_ads_utm_linkage: Link HubSpot contact UTMs to Google Ads campaigns

Usage:
    python mcp_hubspot_analysis_server.py
    # Or: uv run mcp_hubspot_analysis_server.py

Cursor/Claude Desktop config (~/.cursor/mcp.json or claude_desktop_config.json):
    "hubspot-analysis": {
      "command": "python",
      "args": ["/path/to/openai-cookbook/tools/scripts/hubspot/mcp_hubspot_analysis_server.py"],
      "cwd": "/path/to/openai-cookbook"
    }
"""
import subprocess
import sys
from pathlib import Path
from calendar import monthrange

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

# Load .env for HUBSPOT_API_KEY
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(REPO_ROOT / "tools" / ".env")
except ImportError:
    pass


def _run_script(args: list[str], timeout: int = 600) -> tuple[int, str, str]:
    """Run a Python script from repo root. Returns (exit_code, stdout, stderr)."""
    cmd = [sys.executable] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout or "", result.stderr or ""
    except subprocess.TimeoutExpired as e:
        out = e.stdout if isinstance(e.stdout, str) else (e.stdout.decode(errors="replace") if e.stdout else "")
        err = e.stderr if isinstance(e.stderr, str) else (e.stderr.decode(errors="replace") if e.stderr else "")
        return -1, out, f"Process timed out after {timeout}s. {err}"
    except FileNotFoundError as e:
        return -1, "", f"Script not found: {e}"


def _format_output(exit_code: int, stdout: str, stderr: str) -> str:
    """Format subprocess output for MCP tool response."""
    parts = []
    if stdout:
        parts.append(stdout.strip())
    if stderr:
        parts.append(f"stderr:\n{stderr.strip()}")
    parts.append(f"\nExit code: {exit_code}")
    return "\n\n".join(parts)


def _months_to_args(months: str) -> list[str]:
    """Convert space-separated months (e.g. '2025-12 2026-01') to --months arg list."""
    return [m.strip() for m in months.split() if m.strip()]


# FastMCP must be imported after path setup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("hubspot-analysis")


@mcp.tool()
def run_smb_mql_funnel(months: str) -> str:
    """
    Run SMB MQL funnel analysis (MQL PYME → Deal Created → Won).
    months: Space-separated months in YYYY-MM format (e.g. "2025-12 2026-01 2026-02").
    Output: Markdown tables + CSV in tools/outputs/.
    """
    month_list = _months_to_args(months)
    if not month_list:
        return "Error: months must be non-empty (e.g. '2025-12 2026-01')"
    args = ["tools/scripts/hubspot/analyze_smb_mql_funnel.py", "--months"] + month_list
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_accountant_mql_funnel(months: str) -> str:
    """
    Run Accountant MQL funnel analysis (MQL Contador → Deal Created → Won).
    months: Space-separated months in YYYY-MM format (e.g. "2025-12 2026-01").
    Output: Markdown tables + CSV in tools/outputs/.
    """
    month_list = _months_to_args(months)
    if not month_list:
        return "Error: months must be non-empty (e.g. '2025-12 2026-01')"
    args = ["tools/scripts/hubspot/analyze_accountant_mql_funnel.py", "--months"] + month_list
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_smb_accountant_involved_funnel(
    months: str,
    minimal: bool = False,
    dual_criteria: bool = False,
) -> str:
    """
    Run SMB funnel WITH vs WITHOUT accountant involvement.
    months: Space-separated months in YYYY-MM format (e.g. "2025-12 2026-01").
    minimal: Skip contact filter and ICP coverage for faster run.
    dual_criteria: Also check association type 8 per deal (slower).
    Output: Markdown tables + CSV in tools/outputs/.
    """
    month_list = _months_to_args(months)
    if not month_list:
        return "Error: months must be non-empty (e.g. '2025-12 2026-01')"
    args = ["tools/scripts/hubspot/analyze_smb_accountant_involved_funnel.py", "--months"] + month_list
    if minimal:
        args.append("--minimal")
    if dual_criteria:
        args.append("--dual-criteria")
    code, out, err = _run_script(args, timeout=600)
    return _format_output(code, out, err)


@mcp.tool()
def run_high_score_analysis(
    month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    current_mtd: bool = False,
) -> str:
    """
    Run high-score (40+) sales handling analysis: contactability, owner performance, SQL/PQL conversion.
    Provide one of: month (YYYY-MM), start_date+end_date (YYYY-MM-DD), or current_mtd=True.
    Output: Markdown tables + CSV in tools/outputs/.
    """
    args = ["tools/scripts/hubspot/high_score_sales_handling_analysis.py"]
    if current_mtd:
        args.append("--current-mtd")
    elif month:
        args.extend(["--month", month])
    elif start_date and end_date:
        args.extend(["--start-date", start_date, "--end-date", end_date])
    else:
        args.append("--current-mtd")
    code, out, err = _run_script(args, timeout=120)
    return _format_output(code, out, err)


@mcp.tool()
def run_mtd_scoring(month1: str, month2: str) -> str:
    """
    Run month-to-date scoring comparison: SQL/PQL conversion by score range (40+, 30-39, etc.).
    month1: First period in YYYY-MM (e.g. "2026-01").
    month2: Second period in YYYY-MM (e.g. "2026-02").
    Output: Markdown tables + CSV in tools/outputs/.
    """
    args = [
        "tools/scripts/hubspot/mtd_scoring_full_pagination.py",
        "--month1", month1,
        "--month2", month2,
    ]
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_visualization_report(month: str) -> str:
    """
    Generate HTML visualization report from high_score analysis output.
    month: Month in YYYY-MM (e.g. "2026-02"). Expects high_score_contacts_* and high_score_owner_performance_* CSVs in tools/outputs/.
    Run run_high_score_analysis for that month first if files are missing.
    Output: tools/outputs/high_score_visualization_report_YYYY_MM.html
    """
    try:
        year, month_num = month.split("-")
        year_int = int(year)
        month_int = int(month_num)
        last_day = monthrange(year_int, month_int)[1]
        start_str = f"{year}-{month_num}-01"
        end_str = f"{year}-{month_num}-{last_day:02d}"
        period_suffix = start_str.replace("-", "_") + "_" + end_str.replace("-", "_")
    except (ValueError, IndexError):
        return f"Error: month must be YYYY-MM (e.g. '2026-02'), got '{month}'"

    output_dir = REPO_ROOT / "tools" / "outputs"
    contacts_file = output_dir / f"high_score_contacts_{period_suffix}.csv"
    owners_file = output_dir / f"high_score_owner_performance_{period_suffix}.csv"

    if not contacts_file.exists():
        return f"Error: {contacts_file} not found. Run run_high_score_analysis(month='{month}') first."
    if not owners_file.exists():
        return f"Error: {owners_file} not found. Run run_high_score_analysis(month='{month}') first."

    out_html = output_dir / f"high_score_visualization_report_{year}_{month_num}.html"
    args = [
        "tools/scripts/hubspot/generate_visualization_report.py",
        "--contacts-file", str(contacts_file),
        "--owners-file", str(owners_file),
        "--output", str(out_html),
    ]
    code, out, err = _run_script(args, timeout=60)
    result = _format_output(code, out, err)
    if code == 0:
        result = f"Report saved to: {out_html}\n\n" + result
    return result


# ─────────────────────────────────────────────
# Demand Gen tools — evaluator quality, channel attribution, ROI
# ─────────────────────────────────────────────


@mcp.tool()
def run_evaluator_quality(
    months: str,
    channel: str | None = None,
) -> str:
    """
    Analyze evaluator quality by acquisition channel, ICP, and persona.
    Shows which channels produce evaluators that activate (PQL), create deals (SQL),
    win deals, and generate MRR. Full attribution chain from signup to closed revenue.
    months: Space-separated months in YYYY-MM format (e.g. "2026-02" or "2026-01 2026-02").
    channel: Optional filter — e.g. "google-ads", "connections", "organic".
    Output: 5 markdown tables + 2 CSVs (contact-level detail + channel summary) in tools/outputs/.
    """
    month_list = _months_to_args(months)
    if not month_list:
        return "Error: months must be non-empty (e.g. '2026-02')"
    args = ["tools/scripts/hubspot/analyze_evaluator_quality.py", "--months"] + month_list
    if channel:
        args.extend(["--channel", channel])
    code, out, err = _run_script(args, timeout=600)
    return _format_output(code, out, err)


@mcp.tool()
def run_pql_by_channel(months: str) -> str:
    """
    Lightweight PQL rate analysis by acquisition channel.
    Uses initial_utm_* fields for channel attribution (~92% coverage).
    Faster than run_evaluator_quality — skips ICP/company lookups and MRR tracing.
    months: Space-separated months in YYYY-MM format (e.g. "2026-02" or "2026-01 2026-02 2026-03").
    Output: PQL rate by channel + campaign drill-down + CSV in tools/outputs/.
    """
    month_list = _months_to_args(months)
    if not month_list:
        return "Error: months must be non-empty (e.g. '2026-02')"
    args = ["tools/scripts/hubspot/analyze_pql_by_channel.py", "--months"] + month_list
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_monthly_pql(
    month: str | None = None,
    months: str | None = None,
) -> str:
    """
    Monthly PQL conversion rate (PQLs / All Contacts Created).
    Provides month-over-month PQL trend. Uses deal_focused_pql_analysis internally.
    month: Single month YYYY-MM. Or use months for multi-month comparison.
    months: Comma-separated months (e.g. "2025-11,2025-12,2026-01,2026-02").
    If neither provided, runs current month-to-date.
    Output: PQL rate, contact counts, JSON + CSV in tools/outputs/.
    """
    args = ["tools/scripts/hubspot/monthly_pql_analysis.py"]
    if months:
        args.extend(["--months", months])
    elif month:
        args.extend(["--month", month])
    # If neither, runs current MTD by default
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_deal_conversion_by_lead_source(
    month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Deal Created → Closed Won conversion rate by lead_source.
    Validates which acquisition channels convert deals best.
    Provide month (YYYY-MM) or start_date+end_date (YYYY-MM-DD).
    Output: Conversion table by lead_source with deal counts.
    """
    args = ["tools/scripts/hubspot/analyze_deal_conversion_by_lead_source.py"]
    if month:
        args.extend(["--month", month])
    elif start_date and end_date:
        args.extend(["--start-date", start_date, "--end-date", end_date])
    else:
        return "Error: provide month (YYYY-MM) or start_date+end_date"
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_product_led_deals(
    month: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Identify deals closed without sales activities (no-touch, product-led).
    Measures PLG effectiveness — deals won purely through product experience.
    Provide month (YYYY-MM) or start_date+end_date (YYYY-MM-DD).
    Output: No-touch vs touched deals, win rates, revenue comparison.
    """
    args = ["tools/scripts/hubspot/analyze_product_led_deals.py"]
    if month:
        args.extend(["--month", month])
    elif start_date and end_date:
        args.extend(["--start-date", start_date, "--end-date", end_date])
    else:
        return "Error: provide month (YYYY-MM) or start_date+end_date"
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_icp_dashboard(html: bool = False) -> str:
    """
    ICP segmentation dashboard: revenue, deal count, churn by ICP type.
    Uses local facturacion_hubspot.db for fast queries (no live API calls).
    Segments: ICP Operador (Cuenta Contador), ICP PYME, Híbrido, etc.
    html: If True, generates HTML dashboard file.
    Output: ICP breakdown tables. Optionally tools/outputs/ HTML dashboard.
    """
    args = ["tools/scripts/hubspot/analyze_icp_dashboard.py"]
    if html:
        args.extend(["--html", "tools/outputs/icp_dashboard.html"])
    code, out, err = _run_script(args, timeout=120)
    return _format_output(code, out, err)


@mcp.tool()
def run_business_age_conversion(reference_date: str | None = None) -> str:
    """
    Validate business age (from CUIT/RNS incorporation date) as a lead quality signal.
    Cross-references RNS dataset with HubSpot deal outcomes to measure conversion spread.
    reference_date: Optional YYYY-MM-DD for age calculation (default: today).
    Output: Conversion rates by business age bucket, spread analysis.
    """
    args = ["tools/scripts/analyze_business_age_conversion.py"]
    if reference_date:
        args.extend(["--reference-date", reference_date])
    code, out, err = _run_script(args, timeout=120)
    return _format_output(code, out, err)


@mcp.tool()
def run_deal_focused_pql(start_date: str, end_date: str) -> str:
    """
    PQL effectiveness analysis via deal attachment, win rate, revenue per contact.
    Answers: how well does PQL status predict deal creation and closure?
    start_date: Start date YYYY-MM-DD.
    end_date: End date YYYY-MM-DD.
    Output: PQL vs non-PQL deal rates, revenue per contact, conversion tables.
    """
    args = [
        "tools/scripts/hubspot/deal_focused_pql_analysis.py",
        "--start-date", start_date,
        "--end-date", end_date,
    ]
    code, out, err = _run_script(args, timeout=300)
    return _format_output(code, out, err)


@mcp.tool()
def run_pql_sql_deal_relationship(
    month: str | None = None,
    month_mtd: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> str:
    """
    Full PQL → SQL → Deal relationship analysis with timing.
    Answers: does PQL precede SQL? How does PQL status affect deal conversion?
    month: Full month analysis YYYY-MM.
    month_mtd: Month-to-date analysis YYYY-MM.
    Or start_date+end_date (YYYY-MM-DD).
    Output: PQL→SQL flow, timing analysis, conversion funnels + CSV in tools/outputs/.
    """
    args = ["tools/scripts/hubspot/pql_sql_deal_relationship_analysis.py"]
    if month:
        args.extend(["--month", month])
    elif month_mtd:
        args.extend(["--month-mtd", month_mtd])
    elif start_date and end_date:
        args.extend(["--start-date", start_date, "--end-date", end_date])
    else:
        return "Error: provide month, month_mtd, or start_date+end_date"
    code, out, err = _run_script(args, timeout=600)
    return _format_output(code, out, err)


@mcp.tool()
def run_google_ads_report(start_date: str, end_date: str) -> str:
    """
    Google Ads campaign performance report: spend, clicks, impressions, conversions.
    Requires GOOGLE_ADS_CUSTOMER_ID and GOOGLE_ADS_LOGIN_CUSTOMER_ID env vars.
    start_date: Start date YYYY-MM-DD.
    end_date: End date YYYY-MM-DD.
    Output: Campaign-level metrics table.
    """
    args = [
        "tools/scripts/google_ads_report.py",
        "--start_date", start_date,
        "--end_date", end_date,
    ]
    code, out, err = _run_script(args, timeout=120)
    return _format_output(code, out, err)


@mcp.tool()
def run_google_ads_utm_linkage(start_date: str, end_date: str) -> str:
    """
    Link HubSpot contact UTM campaigns to Google Ads campaigns.
    Cross-references initial_utm_campaign from HubSpot with Google Ads campaign names
    to enable spend-to-MRR attribution.
    start_date: Start date YYYY-MM-DD.
    end_date: End date YYYY-MM-DD.
    Output: Campaign linkage table with spend, contacts, and match rates.
    """
    args = [
        "tools/scripts/google_ads_hubspot_utm_linkage.py",
        "--start_date", start_date,
        "--end_date", end_date,
    ]
    code, out, err = _run_script(args, timeout=180)
    return _format_output(code, out, err)


if __name__ == "__main__":
    mcp.run(transport="stdio")
