# Chief of Staff Agent — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chief of Staff agent with 5 commands for the colppy-ceo-assistant plugin — covering KPI snapshots, planning prep, meeting debriefs, action tracking, and calendar briefings.

**Architecture:** One orchestration agent (`chief-of-staff.md`) that handles open-ended requests, plus 5 focused command files (`cos-numbers`, `cos-pre-work`, `cos-debrief`, `cos-status`, `cos-agenda`). All files are markdown prompts with YAML frontmatter — no code files. A quarterly OKR data file (`q2-2026.md`) stores targets and actuals.

**Tech Stack:** Markdown prompts with YAML frontmatter, MCP tools (Fellow, Google Calendar, Slack, HubSpot), Bash curl for Google Sheets CSV export, `plugins/colppy-people-manager` profiles (read-only).

**Spec:** `docs/superpowers/specs/2026-03-12-chief-of-staff-design.md`

---

## File Structure

All files live under `plugins/colppy-ceo-assistant/`:

| # | Path | Responsibility | Action |
|---|------|---------------|--------|
| 1 | `agents/chief-of-staff.md` | Orchestration agent — routes open-ended CEO requests to the right command or handles directly | Create (new `agents/` dir) |
| 2 | `commands/cos-numbers.md` | KPI snapshot — fetches Building Blocks tabs, parses Plan vs Real, pulls HubSpot actuals, outputs gap analysis | Create |
| 3 | `commands/cos-pre-work.md` | Planning session prep — budget review, OKR status, people flags, Fellow action items | Create |
| 4 | `commands/cos-debrief.md` | Post-meeting extraction — Fellow transcript, decisions, action items, proposed OKR updates | Create |
| 5 | `commands/cos-status.md` | Action items & accountability — Fellow actions, OKR progress, people flags per leader | Create |
| 6 | `commands/cos-agenda.md` | Calendar briefing — upcoming meetings with people-manager context and Fellow history | Create |
| 7 | `data/okrs/q2-2026.md` | Q2 2026 OKR targets + actuals tracker | Create |
| 8 | `CLAUDE.md` | Plugin instructions — add Chief of Staff section | Modify |
| 9 | `.claude-plugin/plugin.json` | Plugin manifest — update description | Modify |

**No test files.** These are LLM prompt files, not code. Validation is manual invocation.

**Dependency order:** Task 1 (data file) → Tasks 2–6 (commands, parallelizable) → Task 7 (agent) → Task 8 (CLAUDE.md + plugin.json).

**Parallelization note:** Tasks 2–6 have **zero inter-dependencies** — they can all run in parallel. The Chunk 1/2 split is for readability only.

---

## Chunk 1: Foundation + First Two Commands

### Task 1: Create OKR data file

**Files:**
- Create: `plugins/colppy-ceo-assistant/data/okrs/q2-2026.md`

- [ ] **Step 1: Read OKR cache to extract company-level targets**

Read these cached CSVs to pull key annual targets:
- `data/okrs/cache/2026/okrs_colppy_company.csv` — company OKRs
- `data/okrs/cache/2026/okrs_ceo.csv` — CEO palancas
- `data/okrs/cache/2026/budget_aprobado_2026.csv` — budget KPIs

Extract: Total Customers (3,700), Net New (+783), New MRR ($398MM), NPS (+35), PQL (972), eNPS (>=20).

- [ ] **Step 2: Create the Q2 data file**

```markdown
# Q2 2026 OKRs

> Last updated: —
> Updated by: /cos-numbers

## Company Level

| KPI | Target Q2 | Apr Actual | May Actual | Jun Actual | Source |
|-----|-----------|------------|------------|------------|--------|
| Total Customers | 3,700 (year-end) | — | — | — | HubSpot |
| Net New Customers | +316 (Q2) | — | — | — | HubSpot |
| New MRR | per budget | — | — | — | Building Blocks |
| NPS | +35 | — | — | — | Manual |
| Churn MRR | per budget | — | — | — | Building Blocks |

## Revenue (Owner: Agustín Páez de Robles)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->

## Product/Engineering (Owner: Alejandro Soto)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->

## Customer (Owner: Agostina Bisso)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->

## People (Owner: Malén Baigorria)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->

## Sueldos (Owner: Yamila Sosa)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->

## Finance/Operations (Owner: TBD)
<!-- Populated after Q2 planning (March 18) via /cos-debrief -->
```

- [ ] **Step 3: Commit**

```bash
git add plugins/colppy-ceo-assistant/data/okrs/q2-2026.md
git commit -m "feat(cos): add Q2 2026 OKR tracking file"
```

---

### Task 2: Create `/cos-numbers` command

**Files:**
- Create: `plugins/colppy-ceo-assistant/commands/cos-numbers.md`

This is the most complex command — it encodes the 4 parsing patterns for Building Blocks tabs.

- [ ] **Step 1: Create the command file**

**Frontmatter:**
```yaml
---
name: cos-numbers
description: "KPI snapshot — fetch Building Blocks budget data, parse Plan vs Real, pull HubSpot actuals, compare against OKR targets, and output a gap analysis. Use when the user asks 'show me the numbers', 'how are we doing', or 'budget status'."
---
```

**Body must include these sections in order:**

1. **Overview** — one paragraph: produces a Plan vs Real gap analysis for the current month
2. **Data sources table** — 6 Building Blocks tabs with registry IDs and what each provides
3. **Target month logic** — compute from current date. Three format variants:
   - `MMM-YYYY` (e.g. `Mar-2026`) — Pattern A, B
   - `MMM-YY` (e.g. `Mar-26`) — Pattern D
   - `MMM YY` (e.g. `Mar 26`, space) — Pattern C
4. **Step 1: Read registry** — `tools/docs/GOOGLE_SHEETS_REGISTRY.json`, extract file_id + gid for the 6 tabs
5. **Step 2: Fetch tabs** — curl template: `curl -sL "https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"`
6. **Step 3: Parse each tab** — per-pattern:
   - **Pattern A** (`colppy_budget`, `funnel_from_lead_product_icp`, `funnel_lead_product_icp`): Scan for row where first non-empty cell = "REAL". Top = Plan, bottom = Real. Find target month column in header. Extract values.
   - **Pattern B** (`churn_budget_real`): "Lost MRR Budget" header = plan. "Lost MRR Actual (Ending MRR)" header = actuals. Extract Early/Mid/Late % for month.
   - **Pattern C** (`colppy_raw_actuals`): All rows = actuals. Column format `MMM YY`. No plan here — plan from Pattern D.
   - **Pattern D** (`colppy_budget_aprobado`): All rows = plan. Column format `MMM-YY`. No actuals — actuals from Pattern C.
   - **Complementary pair:** For unit economics (ASP, CAC, Churn, LTV, NRR), compare D plan vs C actuals.
7. **Step 4: HubSpot actuals** — `search_crm_objects` for: total customers (`lifecyclestage = customer`), new this month (`createdate` filter), deal pipeline sum
8. **Step 5: Read OKR targets** — `${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md`
9. **Step 6: Gap analysis** — Plan vs Real per KPI, flag >10% deviations
10. **Step 7: Update OKR file** — write actuals into q2-2026.md, update timestamp
11. **Step 8: Output** — Revenue cards, Funnel cards, Unit economics, Customer count, OKR progress, 2-3 sentence narrative

**Key details for the prompt body:**
- Argentine number format: `.` for thousands, `,` for decimal
- `colppy_budget` has "Forecast Factor de Incremento en %" row at ~row 26 — part of Plan section, not separate
- Tab item names have typos ("Admnisitración") — match by substring
- Do NOT send to Slack. Output in chat. User decides when to forward.

- [ ] **Step 2: Read back and verify**

Verify: frontmatter has name/description, all 6 registry IDs referenced, all 4 patterns documented, 3 month formats covered, HubSpot filters specified, OKR path uses `${CLAUDE_PLUGIN_ROOT}`.

- [ ] **Step 3: Commit**

```bash
git add plugins/colppy-ceo-assistant/commands/cos-numbers.md
git commit -m "feat(cos): add /cos-numbers — KPI snapshot with 4-pattern Building Blocks parser"
```

---

### Task 3: Create `/cos-pre-work` command

**Files:**
- Create: `plugins/colppy-ceo-assistant/commands/cos-pre-work.md`

- [ ] **Step 1: Create the command file**

**Frontmatter:**
```yaml
---
name: cos-pre-work
description: "Prepare pre-work package for a quarterly planning session. Fetches budget actuals vs plan (full quarter), OKR status, people-manager coaching flags, and Fellow action items. Use when the user asks to 'prep the planning' or 'get ready for the planning session'."
---
```

**Body sections:**

1. **Overview** — structured pre-work package for leadership planning session
2. **Planning session structure** (from Malén 1:1):
   - Part 1 — Insights & Gaps: Financial/KPI gaps, OKR review, Guardrails
   - Part 2 — Q2 Planning: Guardrails revision, Palancas, OKRs, Team structure, Operating system
   - Roles: Time Keeper, Facilitator, Note Taker, Devil's Advocate
3. **Step 1: Identify target session** — Calendar search for meeting with 4+ leadership members, title "Planning" or "Estratégica". Or use user-specified date.
4. **Step 2: Fetch full-quarter budget** — same curl + Pattern A/B/C/D as `/cos-numbers` but ALL months in quarter. Compute quarter totals.
5. **Step 3: Read OKR status** — previous quarter file for area achievements, current quarter for company targets
6. **Step 4: Read people-manager profiles** — for 6 leaders: `plugins/colppy-people-manager/data/{person}/profile.md` and `summary.md`. Directories: `malen-baigorria`, `agostina-bisso`, `alejandro-soto`, `agustin-paez-de-robles`, `francisca-horton`, `yamila-sosa`. **Jorge Ross has NO profile** — read Alejandro's profile + Fellow history for Jorge's context instead.
7. **Step 5: Search Fellow** — meetings titled "Planning"/"Estratégica" with 4+ leaders. Get action items from most recent planning.
8. **Step 6: Compile** — Budget summary table, OKR review per area, People flags per leader, Outstanding actions, Agenda reminder, Strategic questions for Juan

- [ ] **Step 2: Commit**

```bash
git add plugins/colppy-ceo-assistant/commands/cos-pre-work.md
git commit -m "feat(cos): add /cos-pre-work — planning session preparation"
```

---

## Chunk 2: Remaining Commands + Agent + Plugin Updates

### Task 4: Create `/cos-debrief` command

**Files:**
- Create: `plugins/colppy-ceo-assistant/commands/cos-debrief.md`

- [ ] **Step 1: Create the command file**

**Frontmatter:**
```yaml
---
name: cos-debrief
description: "Extract decisions, action items, and OKR changes from a completed meeting. Searches Fellow for transcript + summary, proposes OKR updates for user confirmation. Use for 'debrief [meeting]' or 'process the planning'."
---
```

**Body sections:**

1. **Step 1: Find meeting** — Fellow search by date/title/participant. If ambiguous, list and ask.
2. **Step 2: Get data** — transcript + summary + AI action items from Fellow
3. **Step 3: Extract** — Decisions, OKRs discussed, Action items (who/what/when), Open questions
4. **Step 4: Propose OKR updates** — show diff "Current → Proposed" for `${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md`. **CRITICAL: wait for user confirmation before writing.**
5. **Step 5: Output** — structured debrief, clean and scannable
6. **Special case — post-planning:** also populate area-level OKR sections. Walk each area, propose KPIs/targets. Require confirmation.

- [ ] **Step 2: Commit**

```bash
git add plugins/colppy-ceo-assistant/commands/cos-debrief.md
git commit -m "feat(cos): add /cos-debrief — post-meeting extraction"
```

---

### Task 5: Create `/cos-status` command

**Files:**
- Create: `plugins/colppy-ceo-assistant/commands/cos-status.md`

- [ ] **Step 1: Create the command file**

**Frontmatter:**
```yaml
---
name: cos-status
description: "Action items and accountability. Pulls Fellow actions for leadership team, cross-references OKR progress, checks calendar deadlines, reads people-manager flags. Use for 'who owes what', 'status check', or 'what's overdue'."
---
```

**Body sections:**

1. **Leadership team** — 7 people with search names
2. **Step 1: Fellow action items** — per leader, categorize: completed, pending, overdue
3. **Step 2: OKR progress** — read `${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md`, check each area
4. **Step 3: Calendar** — next 2 weeks, deadlines, meetings per leader
5. **Step 4: People-manager flags** — read `summary.md` for 6 leaders. Look for: exit signals, underperformance, coaching items. **Jorge Ross: no profile** — read Alejandro's profile + Fellow history for Jorge's context instead.
6. **Step 5: Output** — per-person card: action items (pending/overdue count), OKR status, coaching flags, upcoming meetings. End with "CEO attention needed" top 3.

- [ ] **Step 2: Commit**

```bash
git add plugins/colppy-ceo-assistant/commands/cos-status.md
git commit -m "feat(cos): add /cos-status — action items and accountability"
```

---

### Task 6: Create `/cos-agenda` command

**Files:**
- Create: `plugins/colppy-ceo-assistant/commands/cos-agenda.md`

- [ ] **Step 1: Create the command file**

**Frontmatter:**
```yaml
---
name: cos-agenda
description: "Calendar briefing with context. Reads Google Calendar, enriches meetings with people-manager profiles and Fellow history, flags conflicts. Use for 'what's on my calendar', 'prep me for tomorrow', or 'brief me for today'."
---
```

**Body sections:**

1. **Step 1: Read Calendar** — Google Calendar MCP, default: today + tomorrow. Accept range arg.
2. **Step 2: Identify leadership meetings** — match attendees against team list
3. **Step 3: Enrich** — for each leadership meeting:
   - Read `plugins/colppy-people-manager/data/{person}/profile.md` + `summary.md`
   - Fellow: last 2-3 meetings with that person, open action items
   - Jorge Ross: Fellow only, no profile
4. **Step 4: Flag issues** — back-to-back, conflicts, missing agendas, overdue items
5. **Step 5: Output** — chronological. Leadership meetings get enriched context cards. Others get basic info. Flags section at end. Readable in 2 minutes.

- [ ] **Step 2: Commit**

```bash
git add plugins/colppy-ceo-assistant/commands/cos-agenda.md
git commit -m "feat(cos): add /cos-agenda — contextual calendar briefing"
```

---

### Task 7: Create `chief-of-staff` agent

**Files:**
- Create: `plugins/colppy-ceo-assistant/agents/chief-of-staff.md`

- [ ] **Step 1: Create agents directory**

```bash
mkdir -p plugins/colppy-ceo-assistant/agents
```

- [ ] **Step 2: Create the agent file**

**Frontmatter** must include: `name: chief-of-staff`, `description` with 5 examples (one per command), each in `<example>` tags matching the pattern from `session-processor.md`.

**Body sections:**

1. **Identity** — "You are the CEO's Chief of Staff. You help Juan stay on top of his leadership team, company numbers, and planning cadence."
2. **Command delegation table:**
   - Numbers/KPIs/budget → `/cos-numbers` (always delegate)
   - Planning prep → `/cos-pre-work` (always delegate)
   - Meeting debrief → `/cos-debrief` (always delegate)
   - Who owes what → `/cos-status` (always delegate)
   - Calendar/tomorrow/today → `/cos-agenda` (always delegate)
   - Open-ended questions → handle directly: combine calendar + OKR status + overdue items
   - People questions about a leader → read profile + Fellow directly
3. **Key behaviors:**
   - Calendar-grounded: check today/this week before open-ended responses
   - Reads people-manager, never writes
   - Updates OKR actuals only via `/cos-numbers`
   - Slack to Juan only (`UE8BUUVME`, `DE91378PM`)
   - No investment advice (portfolio-alert's domain)
4. **Boundary with other agents** — include this table:
   | Domain | Owner | Chief of Staff's role |
   | Coaching & 1:1s | session-processor (people-manager) | Reads profiles, doesn't write |
   | Product strategy | cpo-agent (product) | Not involved |
   | Demand generation | demand-generation (revenue) | Reads numbers, doesn't analyze channels |
   | Portfolio/investments | portfolio-alert (ceo-assistant) | Separate domain, no overlap |
   | Architecture review | architecture-researcher | Not involved |
5. **Leadership team reference** — names, roles, profile paths
6. **Data files reference** — OKR tracker, OKR cache, registry, people-manager
7. **Quarter rotation** — create new file at quarter start, determine current from date

- [ ] **Step 3: Commit**

```bash
git add plugins/colppy-ceo-assistant/agents/chief-of-staff.md
git commit -m "feat(cos): add chief-of-staff orchestration agent"
```

---

### Task 8: Update CLAUDE.md and plugin.json

**Files:**
- Modify: `plugins/colppy-ceo-assistant/CLAUDE.md`
- Modify: `plugins/colppy-ceo-assistant/.claude-plugin/plugin.json`

- [ ] **Step 1: Add Chief of Staff section to CLAUDE.md**

After existing "Portfolio Alert" section, add:
- **Chief of Staff** header
- Commands table (5 commands with `/colppy-ceo-assistant:cos-*` invocation syntax)
- Data files table (OKR tracker + cache)
- Cross-plugin dependencies (people-manager, tools registry)
- Rules: never write to people-manager, never Slack team members, never auto-update OKRs

- [ ] **Step 2: Update plugin.json**

Bump version to `1.1.0`. Update description to mention Chief of Staff + planning cadence + KPI tracking.

- [ ] **Step 3: Commit**

```bash
git add plugins/colppy-ceo-assistant/CLAUDE.md plugins/colppy-ceo-assistant/.claude-plugin/plugin.json
git commit -m "docs(cos): update CLAUDE.md and plugin.json with Chief of Staff"
```

---

## Validation

After all tasks complete, validate interactively:

1. **`/colppy-ceo-assistant:cos-numbers`** — verify it fetches tabs, parses Plan vs Real, outputs gap analysis
2. **`/colppy-ceo-assistant:cos-agenda`** — verify it reads Calendar and enriches with people-manager
3. **Open-ended to agent** — "what should I focus on this week?" — verify it combines calendar + OKRs + actions
