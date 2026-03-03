# Portfolio Alert Blueprint — Design Document

**Date:** 2026-03-02
**Status:** Approved
**Scope:** Restructure the Financial Analyst's `portfolio-alert` command as a Stripe-style Blueprint with unattended Slack delivery, externalized state, and a document-based history layer.

---

## Problem Statement

The current `portfolio-alert` scheduled task runs twice daily but never delivers to Slack unattendedly. Root cause: Step 4 says "Present findings in this format" — a chat-output instruction. When run unattended, the agent outputs to a void (no active conversation), considers the task done, and never reaches Step 5 (Slack). Additionally, portfolio positions are embedded inside the workflow file, making state updates require editing business logic.

Secondary issues:
- Cron mismatch between `commands/portfolio-alert.md` (`0 13,21`) and `scheduled-tasks/portfolio-alert.md` (`0 10,18`)
- No transaction history or historical snapshots — no way to answer cost-basis, performance, or timing questions
- Monday update only asks for Galicia screenshots; Schwab, Allaria, and Citi are not covered

---

## Architecture

Two files with clear separation of concerns, plus a history layer:

```
sessions/.../mnt/
  .claude/
    commands/
      portfolio-alert.md            ← Blueprint: workflow only (~40 lines)
    scheduled-tasks/
      portfolio-alert.md            ← Trigger: cron + pointer to command
  outputs/financial-advisor/
    references/
      portfolio-snapshot.md         ← Current state (updated every Monday)
      index.md                      ← Navigation guide (always small, always read first)
    history/
      transactions.md               ← Append-only full trade ledger
      snapshots/
        YYYY-MM-DD.md               ← Weekly point-in-time portfolio state
    alerts/
      YYYY-MM-DD-HH.md              ← Compiled alert archive (what was sent)
      FAILED-YYYY-MM-DD-HH.md       ← Failed delivery marker
```

**Invariants:**
- `portfolio-alert.md` (command) never contains position data
- `transactions.md` is append-only — past entries are never edited
- Slack DM is the ONLY output of every non-Monday run — nothing goes to chat canvas
- Every run produces a file in `alerts/` (success or FAILED-)

---

## Blueprint Node Map

```
[CRON: 10am + 6pm ART = 0 13,21 UTC, Mon–Fri]
         ↓
[DET] Read references/index.md                    ← understand what history exists
[DET] Read references/portfolio-snapshot.md       ← current positions into context
[DET] Is today Monday?
         ↓ YES                          ↓ NO (skip to data collection)
[AGT] Step 0: Ask for screenshots      |
       from all 4 accounts             |
       + any verbal trades             |
[DET] Read history/transactions.md     |
       → identify pending orders       |
[AGT] Compare screenshots → confirm    |
       fills, detect new trades        |
[DET] Append to transactions.md        |
[DET] Save history/snapshots/DATE.md   |
[DET] Update portfolio-snapshot.md     |
[DET] Update index.md                  |
         ↓                             ↓
[DET] Gmail search (6 queries)                    ← tool calls, no judgment
[AGT] Read emails, extract signals per source     ← LLM reads Tunguz/a16z/Ecofines,
       → structured signal objects                  maps insights to positions

[DET] Web search (6 fixed queries)                ← tool calls, no judgment
[AGT] Read results, scrape key articles           ← LLM interprets news vs thesis,
       → structured signal objects                  FX gap vs allocation

[DET] Earnings calendar (fixed ticker list)

[AGT] Cross-reference ALL signals:                ← main judgment node
       - Apply trigger conditions (±3%, earnings <7d, FX gap >5%)
       - Map newsletter insights to specific holdings
       - Score: ACTIONABLE / WATCH / CONTEXT

[AGT] Compile alert sections (🔴🟡🟢📅📧)         ← structure output in memory

[DET] CALL Slack send_message(
        channel=UE8BUUVME,
        text=compiled_alert                       ← THE terminal node
      )
         ↓ SUCCESS                    ↓ FAILURE
[DET] Write alerts/DATE-HH.md        [DET] Write alerts/FAILED-DATE-HH.md
[END] Task complete.                 [END] Task complete.
      NO chat output.                      NO chat output.
```

---

## File Specifications

### `commands/portfolio-alert.md` (workflow)

Structure after refactor:
- Frontmatter: `name`, `description`, `cron` (fixed to `0 13,21 * * 1-5`)
- Step 0: Monday screenshot request (all 4 accounts + verbal trades)
- Step 1: Gmail search queries (list only — no position data)
- Step 2: Web search queries (list only)
- Step 3: Earnings calendar tickers
- Step 4: Cross-reference + compile (with trigger condition rules)
- Step 5: **Mandatory Slack delivery** — explicit language: "The task is ONLY complete when the Slack DM is confirmed sent. Write audit log. Do not output to chat."

No portfolio positions, no rebalancing log, no price data.

### `references/portfolio-snapshot.md` (current state)

```markdown
# Portfolio Snapshot
**Last Updated:** YYYY-MM-DD (Monday update)
**Sources:** [list of screenshots/statements used]

## Positions by Account
[Galicia CEDEARs + FCI | Allaria | Schwab | Citi]

## Pending Orders
[orders placed but not yet confirmed as fills]

## Target Allocation
[asset class targets for rebalancing guidance]
```

### `references/index.md` (navigation guide)

```markdown
# Financial History Index
**Current snapshot:** YYYY-MM-DD
**Transactions:** N entries, DATE → present
**Snapshots available:** YYYY-MM-DD → present

## Key Events
[dated list of major rebalances, deployments, position changes]

## How to query history
- Cost basis → history/transactions.md (filter by asset)
- Past portfolio state → history/snapshots/YYYY-MM-DD.md
- Past alert signals → alerts/YYYY-MM-DD-HH.md
- Current positions → references/portfolio-snapshot.md
```

### `history/transactions.md` (append-only ledger)

```markdown
| Date | Account | Action | Asset | Qty | Local Price | USD Equiv | Notes |
```

Every trade ever. Append only. Never edited.

### `history/snapshots/YYYY-MM-DD.md` (weekly point-in-time)

Full portfolio state as of each Monday update. Same structure as `portfolio-snapshot.md`. Allows historical performance queries.

---

## Cron Fix

Both files must use identical cron: `0 13,21 * * 1-5` (UTC)

| Time UTC | Time ART | Run |
|----------|----------|-----|
| 13:00    | 10:00    | Pre-market |
| 21:00    | 18:00    | Post-close |

---

## Migration Steps

1. Create `references/index.md` from scratch
2. Move `references/portfolio-snapshot.md` from existing Jan 1 snapshot — update with current positions from `portfolio-alert.md` embedded data
3. Create `history/transactions.md` — seed with rebalancing log entries from `portfolio-alert.md`
4. Save `history/snapshots/2026-01-01.md` from the existing snapshot file
5. Rewrite `commands/portfolio-alert.md` — remove all position data, fix cron, restructure Steps 4+5
6. Fix `scheduled-tasks/portfolio-alert.md` — align cron to `0 13,21`
7. Test: run the command manually, verify Slack DM lands, verify alert file written
