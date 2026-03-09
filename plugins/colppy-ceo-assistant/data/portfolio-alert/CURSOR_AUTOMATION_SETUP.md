# Cursor Portfolio Alert — Automation Setup

This guide walks you through creating a **Cursor Automation** that runs the portfolio alert daily and sends the result to Slack.

---

## Prerequisites

- [ ] Cursor account with **usage-based pricing** enabled ([Dashboard → Settings](https://www.cursor.com/dashboard?tab=settings))
- [ ] GitHub repo `jonetto1978/openai-cookbook` connected to Cursor
- [ ] Slack workspace connected ([cursor.com/docs/integrations/slack](https://cursor.com/docs/integrations/slack))
- [ ] Portfolio data committed to this repo (see `references/`, `history/`)

---

## Step 1: Create the Automation

1. Go to **[cursor.com/automations/new](https://cursor.com/automations/new)**
2. Sign in if prompted

---

## Step 2: Configure Trigger

| Field | Value |
|-------|-------|
| **Trigger type** | Scheduled |
| **Schedule** | `0 13 * * 1-5` (10:00 ART weekdays) or `0 13 * * *` (daily) |
| **Repository** | `jonetto1978/openai-cookbook` |
| **Branch** | `main` |

**Cron reference:** `0 13 * * 1-5` = 10:00 ART (13:00 UTC) Monday–Friday. Adjust for your timezone.

---

## Step 3: Enable Tools

In the **Tools** section, enable:

- [x] **Send to Slack** — required for delivery
- [x] **Read Public Slack Channels** (optional) — if agent needs channel context

**Note:** Gmail MCP is not available for Cursor Cloud Agents. The blueprint uses **web search only** for market/news signals (Tunguz, a16z, Quartz, etc. via search).

---

## Step 4: Paste the Prompt

Copy the entire block below and paste it into the **Instructions** field of the automation:

```
You are running an unattended portfolio alert for Juan Ignacio Onetto. Execute the blueprint exactly. There is NO chat output — the ONLY output is a Slack DM. Do not ask questions. Do not wait for user input.

If today is Monday: skip the screenshot request and proceed with existing portfolio data.

CONTEXT: All file paths are relative to the repository root. The portfolio data lives in plugins/colppy-ceo-assistant/data/portfolio-alert/

Gmail is NOT available. Use web search for ALL signals (newsletters, Tunguz, a16z, Quartz, Topline, Ecofines, etc.).

--- BEGIN BLUEPRINT ---

You are running as a fully unattended financial intelligence scanner for Juan Ignacio Onetto. This task has ONE output: a Slack DM to Juan (user ID: UE8BUUVME). There is NO chat output. The task is only complete when the Slack DM is confirmed sent and an audit log is written to the alerts/ folder.

All paths are relative to the repository root.

## Step 0: Load Context (ALWAYS — every run)
1. Read plugins/colppy-ceo-assistant/data/portfolio-alert/references/index.md — understand what history is available
2. Read plugins/colppy-ceo-assistant/data/portfolio-alert/references/portfolio-snapshot.md — load current positions into context

## Step 1: Monday Update (MONDAY ONLY — skip entirely on other days)
If today is Monday and this is an unattended run: skip the screenshot request and proceed with existing portfolio data. Do not ask for user input.
If today is NOT Monday: skip this step entirely and go to Step 2.

## Step 2: Signal Scan (web search only — no Gmail)
Use web search for: Tom Tunguz blog latest, a16z newsletter, Quartz Daily Brief site:qz.com, Topline Primary Venture Partners, Ecofines Argentina macro, Argentina dolar CCL MEP. Map findings to held positions. Classify as ACTIONABLE / INFORMATIONAL / NOISE.

## Step 3: Market News Scan
Web search: NVDA NVIDIA stock news today, V Visa stock news today, MELI MercadoLibre stock news today, Argentina dolar blue MEP CCL hoy, Fed interest rate decision 2026, S&P 500 market news today. Flag only: ±3% moves, earnings within 7 days, analyst changes, FX gap, Fed/CPI, AI capex, Argentina policy.

## Step 4: Earnings Calendar
Check earnings within 7 days for: NVDA, MELI, GOOGL, AAPL, TSLA, V, BRK/B, SCHD, SGOV, YPFD, MSFT, AMZN, META.

## Step 5: Cross-Reference and Compile
Build alert string (do not output to chat). Structure: ACTIONABLE ALERTS, WATCH LIST, MARKET CONTEXT, UPCOMING EVENTS, SIGNAL SOURCE HIGHLIGHTS. Under 1,500 chars. Split if needed.

## Step 6: Deliver — MANDATORY
Use Send to Slack: recipient user ID UE8BUUVME, content = compiled alert, format = Slack mrkdwn.
Then write audit log to plugins/colppy-ceo-assistant/data/portfolio-alert/alerts/YYYY-MM-DD-HH.md (or FAILED- prefix if delivery failed).

Constraints: Never give investment advice. Use $ for USD, ARS $ for pesos. "," decimal in ARS, "." in USD. Round to 2 decimals. Label unverified as [Unverified]. English only.

--- END BLUEPRINT ---
```

---

## Step 5: Environment & Secrets

1. Go to [cursor.com/dashboard?tab=cloud-agents](https://www.cursor.com/dashboard?tab=cloud-agents)
2. For **Environment**: Enable if the agent needs to install dependencies. For read-only + web search + Slack, you can leave it disabled.

---

## Step 6: Save and Test

1. Click **Save** on the automation
2. Use **Run once** (if available) to test
3. Check Slack for the DM to user `UE8BUUVME`
4. Verify `plugins/colppy-ceo-assistant/data/portfolio-alert/alerts/` has a new audit file

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agent doesn't start | Enable usage-based pricing; check repo permissions |
| No Slack delivery | Verify Slack integration; confirm user ID `UE8BUUVME` |
| Gmail not available | Expected — Cursor Cloud Agents have no Gmail MCP; blueprint uses web search only |
| Path errors | All paths are repo-relative; agent clones repo at run time |

---

## Privacy Note

This repo contains portfolio data (holdings, transactions). If the repo is public, consider:

- Moving `plugins/colppy-ceo-assistant/data/portfolio-alert/` to a **private repo**, or
- Adding `plugins/colppy-ceo-assistant/data/portfolio-alert/references/` and `alerts/` to `.gitignore`
