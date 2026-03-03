# Portfolio Alert Blueprint Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the Financial Analyst's portfolio-alert into a Stripe-style Blueprint with unattended Slack delivery, externalized state, and a document-based history/RAG layer.

**Architecture:** Separate the command file (pure workflow) from the state file (positions), add an append-only transaction ledger + weekly snapshots for history, and make Slack the mandatory terminal delivery node with no chat output path.

**Tech Stack:** Markdown files, Claude Cowork scheduled tasks, Slack MCP, Gmail MCP

**Root cause of Slack failure:** Step 4 says "Present findings in this format" — a chat output instruction. When run unattended there is no active conversation, the agent outputs to a void, considers the task done, and never reaches Step 5 (Slack). Fix: merge Steps 4+5 so Slack is the only output.

---

## File Paths

All files live under this BASE path (define as a variable when executing):

```
BASE=/Users/virulana/Library/Application\ Support/Claude/local-agent-mode-sessions/2de0c85a-a7ac-4c9e-91c1-bd8362c29e4f/edc3f46d-20a2-4e0f-91ea-29281346908f/local_2a66053c-635e-4708-ac3a-294fdcbd0904
```

Within the session (Cowork internal paths shown as reference):
- `$BASE/.claude/commands/portfolio-alert.md` → the Blueprint (rewrite)
- `$BASE/.claude/scheduled-tasks/portfolio-alert.md` → the trigger (fix cron)
- `$BASE/outputs/financial-advisor/references/portfolio-snapshot.md` → current state (update)
- `$BASE/outputs/financial-advisor/references/index.md` → CREATE NEW
- `$BASE/outputs/financial-advisor/history/transactions.md` → CREATE NEW
- `$BASE/outputs/financial-advisor/history/snapshots/2026-01-01.md` → CREATE NEW
- `$BASE/outputs/financial-advisor/alerts/` → CREATE DIRECTORY

---

## Task 1: Create directory structure

**Files:**
- Create dir: `$BASE/outputs/financial-advisor/history/`
- Create dir: `$BASE/outputs/financial-advisor/history/snapshots/`
- Create dir: `$BASE/outputs/financial-advisor/alerts/`

**Step 1: Create the directories**

```bash
BASE="/Users/virulana/Library/Application Support/Claude/local-agent-mode-sessions/2de0c85a-a7ac-4c9e-91c1-bd8362c29e4f/edc3f46d-20a2-4e0f-91ea-29281346908f/local_2a66053c-635e-4708-ac3a-294fdcbd0904"
mkdir -p "$BASE/outputs/financial-advisor/history/snapshots"
mkdir -p "$BASE/outputs/financial-advisor/alerts"
```

**Step 2: Verify**

```bash
ls "$BASE/outputs/financial-advisor/"
```

Expected output includes: `history/`, `alerts/`, `references/`

---

## Task 2: Archive the Jan 1 snapshot

Copy the existing `portfolio-snapshot.md` (Jan 1, 2026 data) into the history folder before it gets overwritten.

**Files:**
- Read: `$BASE/outputs/financial-advisor/references/portfolio-snapshot.md`
- Create: `$BASE/outputs/financial-advisor/history/snapshots/2026-01-01.md`

**Step 1: Read the existing snapshot**

Read the full file at:
`$BASE/outputs/financial-advisor/references/portfolio-snapshot.md`

**Step 2: Write it as the first history snapshot**

Write the exact same content to:
`$BASE/outputs/financial-advisor/history/snapshots/2026-01-01.md`

Add this header line at the very top if not already present:
```
> **Archived snapshot:** January 1, 2026 — end of tax year 2025. Source of truth for 2025 cost basis.
```

**Step 3: Verify**

```bash
head -5 "$BASE/outputs/financial-advisor/history/snapshots/2026-01-01.md"
```

Expected: shows the portfolio snapshot header with Jan 1 date.

---

## Task 3: Seed the transaction ledger

Create the append-only transaction history from the rebalancing log currently embedded in `$BASE/.claude/commands/portfolio-alert.md`.

**Files:**
- Read: `$BASE/.claude/commands/portfolio-alert.md` (source of Rebalancing Log)
- Create: `$BASE/outputs/financial-advisor/history/transactions.md`

**Step 1: Create transactions.md with seeded history**

Write this file to `$BASE/outputs/financial-advisor/history/transactions.md`:

```markdown
# Transaction Ledger — Juan Ignacio Onetto

**Format:** Append-only. Never edit past entries. Add new rows at the bottom.
**CCL rates:** Used for ARS→USD conversion at time of trade.

| Date | Account | Action | Asset | Qty | Local Price | USD Equiv | Notes |
|------|---------|--------|-------|-----|-------------|-----------|-------|
| 2026-02-19 | Galicia Eminent | SELL | NVDA CEDEAR | 4,862 | ARS $11,230/unit | ~$7.67/unit | Trim: 48%→21% equity. Georgette 5% rule. Realized gain ~ARS $13.5M (~$9,185 USD), tax-exempt CEDEAR |
| 2026-02-19 | Galicia Eminent | BUY | V CEDEAR | 1,240 | ARS $25,860/unit | ~$17.65/unit | New Financials position. Proceeds from NVDA trim |
| 2026-02-27 | Schwab | BUY | SGOV | 1 | $100.38/share | $100.38/share | First SGOV share, filled |
| 2026-03-02 | Schwab | BUY | BRK/B | 16 | $480.77/share | $480.77/share | Part of $15K deployment. Market order placed post-market, fill expected Mar 3 |
| 2026-03-02 | Schwab | BUY | SGOV | 53 | $100.38/share | $100.38/share | Part of $15K deployment. Market order placed post-market, fill expected Mar 3 |
| 2026-03-02 | Schwab | BUY | SCHD | 62 | $31.87/share | $31.87/share | Part of $15K deployment. Market order placed post-market, fill expected Mar 3 |
```

**Step 2: Verify row count**

```bash
grep "^| 2026" "$BASE/outputs/financial-advisor/history/transactions.md" | wc -l
```

Expected: 6

---

## Task 4: Update portfolio-snapshot.md to current state

Replace the Jan 1 snapshot with the current state (Mar 2, 2026) from the data embedded in `portfolio-alert.md`. Add `Pending Orders` and `Target Allocation` sections.

**Files:**
- Read: `$BASE/.claude/commands/portfolio-alert.md` (source of current positions)
- Modify: `$BASE/outputs/financial-advisor/references/portfolio-snapshot.md`

**Step 1: Read the current positions from commands/portfolio-alert.md**

The command file contains tables for:
- "Galicia CEDEARs (as of Feb 28, 2026)"
- "Other Holdings" table (Allaria, FIMA, Schwab, Citi)
- "Portfolio Summary (Mar 2, 2026)"
- "Pending Rebalancing Actions"
- "Georgette 5% Rule Status"

**Step 2: Rewrite portfolio-snapshot.md with this structure**

```markdown
# Portfolio Snapshot — Juan Ignacio Onetto

**Last Updated:** 2026-03-02 (manual update from portfolio-alert data)
**Next Monday Update:** 2026-03-09
**Data Sources:** Galicia Online Banking (Feb 28 screenshot), Schwab interface (Mar 2 orders placed), Allaria statement, Citi balance

---

## Positions by Account

### Galicia Eminent — CEDEARs

[COPY the CEDEAR table from commands/portfolio-alert.md — the full ticker/qty/price/P&L table]

### Galicia Eminent — Mutual Funds (FCI)

| Fund | Balance (ARS) | Rate | Notes |
|------|--------------|------|-------|
| ARS FIMA Premium | ARS $106,116,691 | TNA 20.60% | Money market, as of Feb 28 |

### Allaria Securities (Offshore)

| Asset | Value (USD) | Notes |
|-------|------------|-------|
| Fixed income funds | ~$114,000 | Stable, no changes |

### Schwab

[COPY the Schwab rows from the "Other Holdings" table in commands/portfolio-alert.md]

### Citi Priority

| Account | Balance (USD) | Notes |
|---------|--------------|-------|
| Savings | ~$15,500 | Reduced after $15K wire to Schwab |

---

## Pending Orders

| Date Placed | Account | Asset | Qty | Order Type | Expected Fill | Status |
|-------------|---------|-------|-----|------------|---------------|--------|
| 2026-03-02 | Schwab | BRK/B | 16 | Market | 2026-03-03 open | PENDING |
| 2026-03-02 | Schwab | SGOV | 53 | Market | 2026-03-03 open | PENDING |
| 2026-03-02 | Schwab | SCHD | 62 | Market | 2026-03-03 open | PENDING |

_Update this section when Monday screenshots confirm fills._

---

## Portfolio Summary

[COPY the Portfolio Summary table from commands/portfolio-alert.md]

---

## Georgette 5% Rule

[COPY the Georgette 5% Rule Status section from commands/portfolio-alert.md]

---

## Target Allocation

| Category | Current % | Target % | Action if Breached |
|----------|-----------|----------|-------------------|
| Equities | ~22% | 20–30% | Trim if >30%, add if <15% |
| Fixed Income | ~22% | 20–30% | Rebalance annually |
| Cash (USD) | ~40% | 30–40% | Deploy when opportunities arise |
| ARS Money Market | ~14% | 10–20% | Reduce if ARS weakens sharply |
```

**Step 3: Verify the file has the key sections**

```bash
grep "^## " "$BASE/outputs/financial-advisor/references/portfolio-snapshot.md"
```

Expected output:
```
## Positions by Account
## Pending Orders
## Portfolio Summary
## Georgette 5% Rule
## Target Allocation
```

---

## Task 5: Create index.md

**Files:**
- Create: `$BASE/outputs/financial-advisor/references/index.md`

**Step 1: Write index.md**

```markdown
# Financial History Index

**Last snapshot:** 2026-03-02
**Transactions:** 6 entries from 2026-02-19 → present
**Snapshots available:** 2026-01-01 → present (weekly from next Monday)

## Key Events
- 2026-02-19: NVDA trim 7,773→2,911 CEDEARs, opened V CEDEAR position (Georgette 5% rebalance)
- 2026-02-27: First SGOV share filled (Schwab)
- 2026-03-02: Schwab $15K deployment — BRK/B x16, SGOV x53, SCHD x62 (market orders, fills expected Mar 3)

## How to Query History

| Question | Where to look |
|----------|--------------|
| Current positions | `references/portfolio-snapshot.md` |
| Cost basis for a position | `history/transactions.md` — filter by asset |
| Portfolio state on a past date | `history/snapshots/YYYY-MM-DD.md` |
| What signals drove a past decision | `alerts/YYYY-MM-DD-HH.md` |
| Pending orders | `references/portfolio-snapshot.md` → Pending Orders section |

## File Map
- `references/portfolio-snapshot.md` — current state (updated every Monday)
- `references/index.md` — this file (updated every Monday)
- `history/transactions.md` — append-only ledger
- `history/snapshots/` — weekly point-in-time archives
- `alerts/` — compiled alert archive (what was sent to Slack)
```

**Step 2: Verify**

```bash
wc -l "$BASE/outputs/financial-advisor/references/index.md"
```

Expected: > 30 lines

---

## Task 6: Rewrite commands/portfolio-alert.md (the key fix)

This is the critical task. The new file is lean workflow only — no position data, Slack is the only terminal output.

**Files:**
- Overwrite: `$BASE/.claude/commands/portfolio-alert.md`

**Step 1: Back up the original**

```bash
cp "$BASE/.claude/commands/portfolio-alert.md" \
   "$BASE/.claude/commands/portfolio-alert.md.bak"
```

**Step 2: Write the new portfolio-alert.md**

Write this exact content to `$BASE/.claude/commands/portfolio-alert.md`:

```markdown
---
name: portfolio-alert
description: "Scan markets, Gmail, and web for portfolio-moving news. Compile actionable alert and send via Slack DM to Juan. Runs twice daily on weekdays: pre-market (10 AM ART) and post-close (6 PM ART)."
cron: "0 13,21 * * 1-5"
---

# Portfolio Alert — Blueprint

You are running as a fully unattended financial intelligence scanner for Juan Ignacio Onetto. This task has ONE output: a Slack DM to Juan (user ID: `UE8BUUVME`). There is NO chat output. The task is only complete when the Slack DM is confirmed sent and an audit log is written to the alerts/ folder.

---

## Step 0: Load Context (ALWAYS — every run)

1. Read `outputs/financial-advisor/references/index.md` — understand what history is available
2. Read `outputs/financial-advisor/references/portfolio-snapshot.md` — load current positions into context

---

## Step 1: Monday Update (MONDAY ONLY — skip entirely on other days)

If today is Monday, ask Juan:

> "It's Monday — portfolio update time. Please share screenshots from all four accounts:
> 1. **Galicia Eminent** — Inversiones summary (pie chart page) + CEDEAR detail table
> 2. **Schwab** — Positions page (all holdings)
> 3. **Allaria** — Current holdings or latest statement
> 4. **Citi** — Savings balance (only if changed)
>
> Any trades this week not visible in the screenshots? Verbal description is fine.
> If no screenshots are provided, I'll proceed with existing data."

When screenshots are provided, execute in order:

a. Read `outputs/financial-advisor/history/transactions.md` — identify all PENDING entries
b. Extract position data from all screenshots provided
c. Compare with current `portfolio-snapshot.md` → confirm fills on pending orders, detect any new trades
d. Append confirmed fills and new trades to `outputs/financial-advisor/history/transactions.md` (append only — never edit past rows)
e. Update PENDING entries in `portfolio-snapshot.md` → Pending Orders section (mark filled orders as CONFIRMED, remove if no longer pending)
f. Save a full point-in-time snapshot to `outputs/financial-advisor/history/snapshots/YYYY-MM-DD.md` (today's date)
g. Update `outputs/financial-advisor/references/portfolio-snapshot.md` with all new data from screenshots
h. Update `outputs/financial-advisor/references/index.md`: new "Last snapshot" date, add any key events to the Key Events list

Then continue to Steps 2–6 using the freshly updated data.

---

## Step 2: Gmail Signal Scan

Search Gmail for new emails (last 24 hours) from these senders:

1. `from:wise-capital OR from:ecofines OR from:wmorales@wise.com.ar` — Argentine macro, FX, rates
2. `from:blog@tomtunguz.com` — SaaS/AI market intelligence
3. `from:a16z` — Tech/VC ecosystem signals
4. `from:schwab` — Account alerts, trade confirmations
5. `from:galicia OR from:allaria` — Broker notifications
6. `from:topline@mail.beehiiv.com` — SaaS GTM (Primary Venture Partners)

For Quartz Daily Brief (goes to jonetto@gmail.com — not scannable via MCP): use web search fallback: `site:qz.com` latest articles.

For each email or article found: read full content, extract key signal, map to specific held positions. Classify as: ACTIONABLE / INFORMATIONAL / NOISE.

---

## Step 3: Market News Scan

Run web searches for each query:

1. `NVDA NVIDIA stock news today`
2. `V Visa stock news today`
3. `MELI MercadoLibre stock news today`
4. `Argentina dolar blue MEP CCL hoy`
5. `Fed interest rate decision 2026`
6. `S&P 500 market news today`

For each result: read key articles, extract portfolio-relevant signals.

**Only flag findings that meet one or more trigger conditions:**
- Any held position moves ±3% or more in a single day
- Earnings date within 7 days for any held stock
- Analyst upgrade/downgrade on any held stock
- Argentine FX gap (CCL vs official) widens beyond 5% or narrows below 2%
- Fed rate decision or CPI/jobs data release
- AI capex news from any hyperscaler (Microsoft, Google, Amazon, Meta) — affects NVDA thesis
- New newsletter content from Tunguz, a16z, Ecofines, Quartz, or Topline with portfolio-relevant signals
- Any regulatory or policy change in Argentina affecting investments (BCRA, CNV, tax)

---

## Step 4: Earnings Calendar

Check earnings dates within the next 7 days for all held stocks plus hyperscalers:

**Held positions:** NVDA, MELI, GOOGL, AAPL, TSLA, V, BRK/B, SCHD, SGOV, YPFD

**Hyperscalers (capex guidance affects NVDA thesis):** MSFT, AMZN, META

---

## Step 5: Cross-Reference and Compile

Using ALL signals from Steps 2–4, compile the alert message. Do not output to chat — build this as a string in memory to hand off to Step 6.

Structure:

```
### 🔴 ACTIONABLE ALERTS
[only items requiring buy/sell/trim/add decision or immediate action — omit section if none]

### 🟡 WATCH LIST
[items approaching trigger thresholds — omit section if none]

### 🟢 MARKET CONTEXT
[broad conditions, FX rates, general sentiment — always include]

### 📅 UPCOMING EVENTS
[earnings, Fed meetings, Argentine policy dates within next 7 days — always include]

### 📧 SIGNAL SOURCE HIGHLIGHTS
[new content from Tunguz, a16z, Ecofines, Quartz, Topline — mapped to positions — omit if no new content]

Sources: [URLs]
```

Keep total message under ~1,500 chars. If over limit, split into two messages: send ACTIONABLE + WATCH first, then CONTEXT + EVENTS + SOURCES as a follow-up.

---

## Step 6: Deliver — THE ONLY OUTPUT

**MANDATORY. Do not skip. Do not ask for confirmation. Do not output to chat.**

Call the Slack send_message tool:
- **Recipient:** user ID `UE8BUUVME`
- **Content:** the compiled alert from Step 5
- **Format:** Slack mrkdwn

After the Slack tool call completes:

**If delivery succeeded:**
Write the full alert text to: `outputs/financial-advisor/alerts/YYYY-MM-DD-HH.md`
(use current date and hour — e.g., `2026-03-03-10h.md`)

**If delivery failed:**
Write the full alert text to: `outputs/financial-advisor/alerts/FAILED-YYYY-MM-DD-HH.md`

Task is complete when the audit log file is written. No other action needed.

---

## Constraints

- Never provide investment advice — present data, let Juan decide
- Use $ for USD, ARS $ for Argentine pesos
- Use "," as decimal separator in ARS figures; "." in USD figures
- Round to 2 decimal places max
- Label unverified data as [Unverified]
- If markets are closed (weekends, US/Argentine holidays), note this and report only upcoming events
- Answer in English
```

**Step 3: Verify the cron and no embedded position data**

```bash
grep "cron:" "$BASE/.claude/commands/portfolio-alert.md"
grep -c "GOOGL\|NVDA\|ARS \$" "$BASE/.claude/commands/portfolio-alert.md"
```

Expected:
- cron line shows: `"0 13,21 * * 1-5"`
- match count: 0 (no position data or ARS values embedded)

---

## Task 7: Fix scheduled-tasks/portfolio-alert.md cron

The scheduled-tasks file currently has `"0 10,18 * * 1-5"` (wrong — fires at 7am + 3pm ART). Align it with the command file.

**Files:**
- Modify: `$BASE/.claude/scheduled-tasks/portfolio-alert.md`

**Step 1: Read the current scheduled-tasks file**

Read `$BASE/.claude/scheduled-tasks/portfolio-alert.md` and verify the cron line.

**Step 2: Fix the cron**

Edit the frontmatter cron value from `"0 10,18 * * 1-5"` to `"0 13,21 * * 1-5"`.

Also update the description if it still says "10 AM and 6 PM" — that's correct ART, just expressed in UTC now.

**Step 3: Verify**

```bash
grep "cron:" "$BASE/.claude/scheduled-tasks/portfolio-alert.md"
```

Expected: `cron: "0 13,21 * * 1-5"`

---

## Task 8: Manual test run

Verify the entire Blueprint works end-to-end before relying on the cron.

**Step 1: In Claude Cowork, run the command manually**

In the Financial Analyst Cowork session, type:
```
/portfolio-alert
```

Or trigger it from the commands panel.

**Step 2: Watch the Progress panel**

Expected progress nodes in order:
- Read index.md ✓
- Read portfolio-snapshot.md ✓
- (Monday only: screenshot request)
- Gmail search ✓
- Read/classify emails ✓
- Web searches ✓
- Read/interpret results ✓
- Earnings calendar ✓
- Cross-reference and compile ✓
- Send Slack DM ✓  ← this must appear
- Write audit log ✓

**Step 3: Verify Slack delivery**

Check Slack — DM from Financial Analyst should appear in Juan's DMs within ~2 minutes of task start.

**Step 4: Verify audit log**

```bash
ls "$BASE/outputs/financial-advisor/alerts/"
```

Expected: a file named `YYYY-MM-DD-HH.md` (no FAILED- prefix = success).

**Step 5: If FAILED- file appears instead**

Read it — the compiled alert text will be there. Check Slack connector status in Cowork settings. The file proves the Blueprint ran correctly; only the Slack delivery step failed.

---

## Rollback

If something goes wrong, the original command file is at:
`$BASE/.claude/commands/portfolio-alert.md.bak`

```bash
cp "$BASE/.claude/commands/portfolio-alert.md.bak" \
   "$BASE/.claude/commands/portfolio-alert.md"
```
