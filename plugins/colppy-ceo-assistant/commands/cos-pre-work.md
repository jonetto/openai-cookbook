---
name: cos-pre-work
description: "Prepare pre-work package for a quarterly planning session. Fetches budget actuals vs plan (full quarter), OKR status, people-manager coaching flags, and Fellow action items. Use when the user asks to 'prep the planning', 'pre-work for [date]', or 'get ready for the planning session'."
---

# /cos-pre-work — Planning Session Preparation

Compile a structured pre-work package for the leadership team's quarterly planning session. This gives Juan a complete picture before walking into the room: budget gaps, OKR progress, people flags, and outstanding actions.

---

## Planning Session Structure

From Malén's 1:1 (March 11, 2026):

**Part 1 — Insights & Gaps:**
- Financial/KPI gaps: how material are they?
- OKR review by area: what was achieved vs plan
- Guardrails: Q1 standards vs reality

**Part 2 — Q2 Planning:**
- Guardrails revision
- Palancas: initiatives, indicators, risks, tradeoffs, dependencies
- Company OKRs
- Area OKRs
- Team structure
- Operating system (meetings)

**Roles:** Time Keeper, Facilitator, Note Taker, Devil's Advocate

**Format:** Everything on slides, presencial dynamics defined per section

---

## Step 1: Identify Target Session

Check Google Calendar for the target planning session:

1. If the user specifies a date → use that date
2. Otherwise → search upcoming events for meetings with:
   - Title containing "Planning" or "Estratégica"
   - 4 or more attendees from the leadership team

**Leadership team names to match:**
Malén Baigorria, Agostina Bisso, Alejandro Soto, Jorge Ross, Agustín Páez de Robles, Yamila Sosa, Francisca Horton

Use Google Calendar MCP:
```
gcal_list_events(time_min=today, time_max=today+30d)
```

Filter results for planning sessions.

---

## Step 2: Fetch Full-Quarter Budget Data

Use the same approach as `/cos-numbers` but extract **all months in the quarter** (not just the current month).

1. Read `tools/docs/GOOGLE_SHEETS_REGISTRY.json` for tab IDs
2. Fetch the 6 Building Blocks tabs via curl:
   ```bash
   curl -sL "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
   ```
3. Parse using the 4 patterns (A/B/C/D) — see `/cos-numbers` for detailed pattern instructions
4. For each tab, extract Plan and Real values for **every month in the quarter being reviewed**

Compute quarter totals:
- Sum monthly Plan values → Quarter Plan
- Sum monthly Real values → Quarter Real
- Gap = Quarter Real − Quarter Plan
- Gap % = Gap / Quarter Plan

---

## Step 3: Read OKR Status

Read OKR files from `${CLAUDE_PLUGIN_ROOT}/data/okrs/`:

1. **Previous quarter file** (e.g. `q1-2026.md` when preparing for Q2): read area-level achievements — what was accomplished vs what was planned. This is the "what happened" view.

2. **Current quarter file** (e.g. `q2-2026.md`): read company-level targets. Area sections may be empty if this is the first planning for the new quarter — that's expected.

**Quarter file naming:** `q{1-4}-YYYY.md`

---

## Step 4: Read People-Manager Profiles

For each of the 6 leaders with people-manager profiles, read their context:

| Person | Directory |
|--------|-----------|
| Malén Baigorria | `plugins/colppy-people-manager/data/malen-baigorria/` |
| Agostina Bisso | `plugins/colppy-people-manager/data/agostina-bisso/` |
| Alejandro Soto | `plugins/colppy-people-manager/data/alejandro-soto/` |
| Agustín Páez de Robles | `plugins/colppy-people-manager/data/agustin-paez-de-robles/` |
| Francisca Horton | `plugins/colppy-people-manager/data/francisca-horton/` |
| Yamila Sosa | `plugins/colppy-people-manager/data/yamila-sosa/` |

For each person, read:
- `profile.md` — role, coaching themes, development areas
- `summary.md` — recent patterns, flags, key observations

Jorge Ross has no people-manager profile — his context is part of Alejandro's leadership.

**Extract for each leader:**
- Current coaching themes
- Any flags (exit signals, underperformance, morale concerns)
- Recent development milestones or blockers

---

## Step 5: Search Fellow for Outstanding Actions

Search Fellow for the most recent planning session:

1. Search meetings by title containing "Planning" or "Estratégica"
2. Filter to meetings with 4+ leadership team members (to distinguish from 1:1s or weekly check-ins)
3. Get the **most recent** match

From that meeting, extract:
- Summary
- AI-detected action items → categorize as completed, pending, overdue
- Key decisions that were made

Also search for action items assigned to each individual leader — these may come from 1:1s or other meetings, not just plannings.

---

## Step 6: Compile Pre-Work Package

Output a structured document with these sections:

### 📊 Budget: Quarter Plan vs Real

Table per area:

| Area | Quarter Plan | Quarter Real | Gap | Gap % | Status |
|------|-------------|-------------|-----|-------|--------|

Include: Revenue totals, MRR by product line, MQL/CQL/Deals by segment, Unit economics (ASP, CAC, Churn, LTV).

### 📈 OKR Review: What Was Achieved vs Plan

For each area (Revenue, Product, Customer, People, Sueldos):
- Key results from previous quarter
- What was achieved vs target
- What wasn't achieved and why (if context available from Fellow/profiles)

### 👥 People Flags

For each leader:
- **Name / Role**
- Coaching themes in focus
- Flags requiring attention (if any)
- Recent development milestones

### ✅ Outstanding Actions from Last Planning

Table:

| Owner | Action | Status | Due Date |
|-------|--------|--------|----------|

Highlight overdue items.

### 📋 Agenda Reminder

Reproduce the planning session structure (Part 1 + Part 2) with role assignments.

### 💡 Strategic Questions for Juan

2–3 questions for Juan to consider before the session. Base these on:
- The most material budget gaps
- Any people flags that might affect planning decisions
- Overdue actions that need to be addressed

**Do NOT send to Slack automatically.** Output in chat. Juan decides what to share and when.
