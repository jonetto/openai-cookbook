# Chief of Staff Agent — Design Spec

**Date:** 2026-03-12
**Plugin:** colppy-ceo-assistant (extension)
**Author:** Juan Onetto + Claude
**Status:** Approved

---

## 1. Problem

Juan (CEO) needs a persistent assistant for:
- **Planning cadence**: preparing, running, and following up on quarterly/weekly planning sessions with his 8-person leadership team
- **Numbers**: staying current on budget vs actuals, OKR progress, and key gaps — on demand
- **Calendar**: briefings for upcoming meetings, conflict detection, context from people-manager and Fellow
- **Action tracking**: who owes what, what's overdue, what needs CEO attention

Currently these tasks are manual — pulling from Google Sheets, cross-referencing Fellow action items, checking people-manager profiles before 1:1s, and compiling pre-work for planning sessions.

## 2. Leadership Team

| Name | Role | Area |
|------|------|------|
| Juan Ignacio Onetto | CEO | — |
| Malén Baigorria | HRBP | People |
| Agostina Bisso | Head of Customer | Customer |
| Alejandro Soto | Head of Product Engineering | Product & Engineering |
| Jorge Ross | Tech Lead (reports to Alejandro) | Product & Engineering |
| Agustín Páez de Robles | Head of Revenue | Revenue |
| Yamila Sosa | PM — Liquidación de Sueldos | Product (Payroll) |
| Francisca Horton | RevOps Lead | Revenue Operations |

Source of truth for team data: `plugins/colppy-people-manager/data/*/profile.md`

## 3. Architecture

### Approach: Agent + 5 Commands

One orchestration agent (`chief-of-staff`) that handles open-ended requests, plus 5 focused commands for specific workflows. The agent delegates to commands' patterns when appropriate.

### Component Map

```
plugins/colppy-ceo-assistant/
├── agents/
│   ├── chief-of-staff.md          ← NEW
├── commands/
│   ├── portfolio-alert.md          (existing)
│   ├── cos-numbers.md              ← NEW
│   ├── cos-pre-work.md             ← NEW
│   ├── cos-debrief.md              ← NEW
│   ├── cos-status.md               ← NEW
│   └── cos-agenda.md               ← NEW
├── skills/
│   ├── galicia-investment-portfolio/  (existing)
│   └── schwab-investment-portfolio/   (existing)
├── data/
│   ├── portfolio-alert/            (existing)
│   ├── investments/                (existing)
│   └── okrs/                       ← NEW
│       └── q2-2026.md
```

No new skills needed — the agent reads from existing skills in other plugins.

### Tool Access

| MCP / Tool | Used For |
|------------|----------|
| Fellow | Meeting search, summaries, transcripts, action items |
| Google Calendar | Upcoming events, free time, prep briefs |
| Slack | Deliver summaries to Juan's DM (DE91378PM) only |
| HubSpot | Customer counts, deal pipeline for OKR actuals |
| Bash (curl) | Google Sheets budget data via Building Blocks registry |
| Read | People-manager profiles, OKR files, planning data |

### Cross-Plugin Dependencies (read-only)

| Source Plugin | What We Read | Purpose |
|---------------|-------------|---------|
| colppy-people-manager | `data/*/profile.md`, `data/*/summary.md` | Team context, coaching flags |
| colppy-revenue | `skills/building-blocks-budget/`, `skills/building-blocks-real/` | Budget fetching patterns |
| tools | `docs/GOOGLE_SHEETS_REGISTRY.json` | Google Sheets tab IDs |

## 4. Data File: OKRs

### `data/okrs/q2-2026.md`

The only new data file. Stores OKR targets (set manually at quarter start) and actuals (updated by the agent when `/cos-numbers` is run).

Structure:

```markdown
# Q2 2026 OKRs

## Company Level
| KPI | Target Q2 | Apr Actual | May Actual | Jun Actual | Source |
|-----|-----------|------------|------------|------------|--------|
| Total Customers | 3,700 (year-end) | — | — | — | HubSpot |
| Net New Customers | +316 (Q2) | — | — | — | HubSpot |
| New MRR | per budget | — | — | — | Building Blocks |
| NPS | +35 | — | — | — | Manual |
| Churn MRR | per budget | — | — | — | Building Blocks |

## Revenue (Owner: Agustín Páez de Robles)
| KPI | Target Q2 | Apr | May | Jun | Source |
(populated after Q2 planning March 18)

## Product/Engineering (Owner: Alejandro Soto)
## Customer (Owner: Agostina Bisso)
## People (Owner: Malén Baigorria)
## Finance/Operations (Owner: TBD)
```

Numeric targets come from the Q2 planning deck and Building Blocks budget. Area-level OKRs get populated after the March 18 planning session via `/cos-debrief`.

## 5. Commands

### `/cos-numbers` — KPI Snapshot

**Trigger:** "show me the numbers", "how are we doing", "budget status"

**Workflow:**
1. Fetch Building Blocks tabs via curl (colppy_budget, colppy_raw_actuals, colppy_budget_aprobado, churn_budget_real) using GOOGLE_SHEETS_REGISTRY.json
2. Parse Budget vs REAL for current month (reuse patterns from `refresh_budget_dashboard.py`)
3. Pull company OKR actuals from HubSpot (total customers, net new, deal pipeline)
4. Compare against `data/okrs/q2-2026.md` targets
5. Update actuals in the OKR file
6. Output: gap analysis — on track / behind / ahead, how material each gap is

**Output format:** Summary cards (like the existing budget dashboard) + narrative of key gaps.

### `/cos-pre-work` — Planning Session Preparation

**Trigger:** "prep the planning", "pre-work for [date]", "get ready for the planning session"

**Workflow:**
1. Identify the target planning session (from Calendar or argument)
2. Fetch Q1 budget actuals vs forecast (Building Blocks — full quarter)
3. Read each area's OKR status from `data/okrs/`
4. Read people-manager profiles for each leader (coaching context, flags)
5. Search Fellow for outstanding action items from the previous planning
6. Check what pre-work has been sent/completed (Fellow notes, Slack if available)
7. Output: structured pre-work package with:
   - Budget: Q1 actual vs forecast vs budget (per area)
   - OKRs: what was achieved vs plan, what wasn't
   - People flags: who needs attention, open coaching items
   - Outstanding actions from last session
   - Agenda reminder with roles

**Planning session structure** (from Malén 1:1, March 11):
- Part 1 — Insights & Gaps: Financial/KPI gaps (how material?), OKR review by area, Guardrails Q1 standards vs reality
- Part 2 — Q2 Planning: Guardrails revision, Palancas (initiatives, indicators, risks, tradeoffs, dependencies), Company OKRs, Area OKRs, Team structure, Operating system (meetings)
- Roles: Time Keeper, Facilitator, Note Taker, Devil's Advocate
- Format: Everything on slides, presencial dynamics defined per section

### `/cos-debrief` — Post-Meeting Extraction

**Trigger:** "debrief [meeting]", "process the planning", "what came out of yesterday's meeting"

**Workflow:**
1. Search Fellow for the target meeting (by date, title, or participant)
2. Get transcript + summary + AI-detected action items
3. Extract: decisions made, OKRs agreed, action items with owners and dates
4. Update `data/okrs/` with any new targets or actuals discussed
5. Output: structured debrief with decisions, actions (who/what/when), and OKR changes

### `/cos-status` — Action Items & Accountability

**Trigger:** "who owes what", "status check", "what's overdue"

**Workflow:**
1. Pull Fellow action items for the leadership team (search by participant names)
2. Cross-reference with `data/okrs/` progress
3. Check Calendar for upcoming deadlines
4. Read people-manager summaries for flagged situations (exits, underperformance, critical coaching)
5. Output: per-person status — pending items, overdue items, coaching flags, upcoming commitments

### `/cos-agenda` — Calendar Briefing

**Trigger:** "what's on my calendar", "prep me for tomorrow", "brief me for today"

**Workflow:**
1. Read Google Calendar for the specified range (default: today + tomorrow)
2. For each meeting with a leadership team member:
   - Pull their people-manager profile (role, coaching themes, recent flags)
   - Search Fellow for recent meeting notes with that person
   - Check for open action items between Juan and that person
3. Flag: conflicts, back-to-back meetings, missing prep time
4. Output: per-meeting briefing — context, what to focus on, open items with that person

## 6. Agent: `chief-of-staff`

### Identity

```yaml
name: chief-of-staff
description: >
  CEO's Chief of Staff agent. Manages planning cadence, KPI tracking,
  calendar briefings, and leadership team coordination. Use when the user
  asks about upcoming meetings, team status, company numbers, or planning
  preparation. Delegates to cos-* commands for structured workflows.
```

### Key Behaviors

1. **Calendar-grounded**: always checks what's happening today/this week before responding
2. **Reads people-manager, never writes**: coaching data is session-processor's domain
3. **Updates OKR actuals**: when fetching numbers, keeps `data/okrs/q2-2026.md` current
4. **Slack to Juan only**: messages go to DM DE91378PM, never directly to team members
5. **Delegates to revenue tools**: for MRR/churn/funnel, uses existing colppy-revenue skills — doesn't recalculate
6. **No investment advice**: portfolio is portfolio-alert's domain

### Boundary with Other Agents

| Domain | Owner | Chief of Staff's role |
|--------|-------|-----------------------|
| Coaching & 1:1s | session-processor (people-manager) | Reads profiles, doesn't write |
| Product strategy | cpo-agent (product) | Not involved |
| Demand generation | demand-generation (revenue) | Reads numbers, doesn't analyze channels |
| Portfolio/investments | portfolio-alert (ceo-assistant) | Separate domain, no overlap |
| Architecture review | architecture-researcher | Not involved |

## 7. Delivery

- **On-demand only** — no cron, no scheduled pushes
- All commands invocable as `/cos-*` slash commands
- Agent invocable for open-ended requests ("what should I focus on this week?")

## 8. Files Created

| # | File | Type |
|---|------|------|
| 1 | `agents/chief-of-staff.md` | Agent |
| 2 | `commands/cos-numbers.md` | Command |
| 3 | `commands/cos-pre-work.md` | Command |
| 4 | `commands/cos-debrief.md` | Command |
| 5 | `commands/cos-status.md` | Command |
| 6 | `commands/cos-agenda.md` | Command |
| 7 | `data/okrs/q2-2026.md` | Data |

**Modified:** `CLAUDE.md` (add Chief of Staff section)

**Total:** 7 new files, 1 modified, 0 new dependencies.
