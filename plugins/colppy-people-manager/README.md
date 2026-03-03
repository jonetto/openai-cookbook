# Colppy People Manager

CEO coaching toolkit that turns meeting transcripts into persistent leadership development records. It's a Claude plugin with three operating modes — session logging, feedforward evaluation, and coaching queries — all backed by plain markdown files organized by person and quarter.

Primary input comes from Fellow and Granola MCP integrations (meeting transcripts), but it also accepts pasted notes, PDFs, slides, or any document a direct report prepares.

---

## Why this exists

Four principles shape how this system works:

- **Evidence-based.** Every coaching observation requires a specific quote, moment, or behavior — not generalizations. "She improved her communication" is not acceptable; "In the Feb 14 session she pushed back on the timeline publicly for the first time, citing three specific risks" is.

- **Bilateral coaching.** The CEO reflects on their own coaching effectiveness alongside each person's growth. Every session produces a self-reflection entry connected to the CEO's 360 feedback and development themes. The coach develops too.

- **Transcript-first.** Fellow and Granola transcripts are the primary source of truth. This maximizes signal fidelity and eliminates the recall bias of manual notes taken hours later.

- **Quarterly rhythm.** Growth arcs are framed by quarters. Session files nest under quarter folders. Evaluations synthesize patterns across quarters. This matches the natural cadence of OKRs, calibrations, and performance cycles.

---

## How it works — three modes

| Mode | When to use | What happens |
|------|-------------|--------------|
| **A — Session** | After a 1:1 or group call | Processes transcript, writes session file per participant, updates summaries and action items, writes CEO self-reflection, surfaces coaching observations |
| **B — Evaluation** | Before a feedforward or review cycle | Synthesizes all sessions in a period into a feedforward document, rewrites the longitudinal coaching arc |
| **C — Query** | Ad-hoc coaching question | Reads relevant files, answers as a coaching partner, pushes back with questions when useful |

### Mode A — Session Logging

The core workflow. Takes a meeting transcript (from Fellow, Granola, pasted, or attached), detects whether it's a 1:1 or group call, extracts coaching signals per participant, and writes all files. Handles both 1:1 sessions and group calls with 3-8 participants.

Every session produces: one session file per participant, a CEO self-reflection entry, updated summaries, and updated action items. The full 10-step process is defined in `skills/one-on-one/SKILL.md`.

**Trigger phrases:** "Log my 1:1 with Ana", "Process this transcript", "Add this doc from Martin"

### Mode B — Evaluation / Feedforward

Generates a comprehensive feedforward evaluation by reading all session history for a person over a given period. Synthesizes leadership strengths, persistent gaps, growth trajectory, and coaching effectiveness into a single document. Also rewrites the person's `coaching_arc.md` with the latest longitudinal narrative.

Not gated to quarter boundaries — can be triggered anytime.

**Trigger phrases:** "Evaluate Ana", "Feedforward for Martin", "I need to review Pedro"

### Mode C — Query / Coaching

Answers coaching questions by selectively reading the right files. Can pull current state (summary), historical range (session files), long-term arc (coaching_arc), or team-wide patterns (all summaries). Responds as a coaching partner — surfaces patterns and asks questions back.

**Trigger phrases:** "Where is Ana this quarter?", "What patterns do I see?", "What was Martin like in Q4?"

---

## Data structure

All data lives in `plugins/colppy-people-manager/data/`.

```
data/
├── _template/                  # Blueprint — copy when adding a new person
│   ├── profile.md
│   ├── summary.md
│   ├── coaching_arc.md
│   └── action_items.md
│
├── _self/                      # CEO's own leadership development
│   ├── profile.md              # 360 survey, coaching program, development themes
│   ├── summary.md              # Current coaching snapshot (<700 words)
│   ├── coaching_arc.md         # Longitudinal development narrative
│   └── history/
│       └── YYYY-QN/
│           └── YYYY-MM-DD.md   # Self-reflection entries
│
└── <person-slug>/              # One folder per direct report
    ├── profile.md              # Background, role, evaluations, personality
    ├── summary.md              # Current state (<700 words, 7 required sections)
    ├── coaching_arc.md         # Quarter-by-quarter development narrative (~1500 words)
    ├── action_items.md         # Pending + completed with dates
    └── history/
        ├── YYYY-QN/
        │   └── YYYY-MM-DD.md   # Session notes (one file per session)
        └── evaluations/
            └── YYYY-MM-DD-feedforward.md
```

### Slug rules

Person folder names follow a strict format:
- Lowercase `firstname-lastname` with hyphens
- Remove diacritics: `á→a`, `é→e`, `í→i`, `ó→o`, `ú→u`, `ñ→n`, `ü→u`
- Only alphanumeric characters and hyphens
- Examples: Ana Gómez → `ana-gomez` | María José García López → `maria-jose-garcia-lopez`

### Quarter mapping

Quarters are determined by the **session date**, not the content discussed:

| Quarter | Date range |
|---------|------------|
| Q1 | Jan 1 – Mar 31 |
| Q2 | Apr 1 – Jun 30 |
| Q3 | Jul 1 – Sep 30 |
| Q4 | Oct 1 – Dec 31 |

A session on 2026-03-25 reviewing Q4 2025 performance goes under `2026-Q1/`.

---

## File schemas

### profile.md — Who they are

Comprehensive background document. No word limit — this is the richest file per person. Contains role metadata, current quarter context, background, key events timeline, personality and working style, development themes, evaluation results (SUMA matrix, feedforward), and materials on file.

Updated when new context arrives (evaluations, org changes, significant events) — not after every session.

### summary.md — Where they are now

Rolling snapshot of current coaching state. **Under 700 words.** Rewritten after every session (not appended). Seven required sections:

1. **Leadership Profile** — strengths and development areas as a leader
2. **Execution Profile** — how they deliver, accountability patterns
3. **Active Coaching Themes** — the 2-3 things being actively worked on
4. **Growth Arc (this quarter)** — what's moving (with evidence), what's stuck
5. **My Coaching Approach** — what's working, what to adjust
6. **Watch Items** — early signals, blind spots, questions for next session
7. **Materials on file** — PDFs/docs incorporated, with dates

### coaching_arc.md — How they've evolved

Longitudinal narrative (~1500 words) tracking development across quarters. Five sections:

1. **Development trajectory** — quarter-by-quarter headline
2. **Coaching approaches tried** — what worked, what didn't
3. **Breakthrough moments** — when something clicked and why
4. **Regression patterns** — behaviors that keep returning despite coaching
5. **Evolution of this coaching relationship** — how the approach changed over time

Rewritten during Mode B (evaluation), not after individual sessions.

### action_items.md — What's open

Pending and completed action items with owners and dates.

```markdown
## Pending
- [ ] Owner (YYYY-MM-DD): item description

## Completed
- [x] Owner (YYYY-MM-DD): item description ✓ YYYY-MM-DD
```

Updated after every session — items marked done when mentioned in transcript, new items added.

### Session files — What happened

One file per participant per session at `history/YYYY-QN/YYYY-MM-DD.md`. Six sections:

1. **Leadership signals** — specific observations with evidence
2. **Execution signals** — specific observations with evidence
3. **Group dynamics** — (group calls only) how they showed up with peers
4. **Growth vs last session** — progress and stuck points with evidence
5. **Coaching intervention** — what approach was tried (1:1s) or `—` (group calls)
6. **Self-reflection** — what the coach noticed about their own coaching

Every file includes a source header: `_Source: [Fellow | Granola | pasted | attached] | [1:1 | Group call — N participants]_`

---

## Adding a new person

1. Create the folder: `data/<slug>/` (e.g. `data/carolina-diaz/`)
2. Copy all 4 files from `data/_template/`
3. Replace `<Full Name>` in each file with their actual name
4. Populate `profile.md` with whatever context is available (role, background, evaluation data)
5. The `history/` folder will be created on first session

When triggered through the skill, say: *"Add Carolina Díaz"* — the system handles slug creation and file setup.

---

## Integrations

### Fellow MCP (primary)

Search for meetings and retrieve transcripts. Used for most 1:1s and recurring team meetings.

- `mcp__claude_ai_Fellow_ai__search_meetings` — find the meeting
- `mcp__claude_ai_Fellow_ai__get_meeting_transcript` — get the transcript

### Granola MCP (secondary)

Alternative transcript source, especially for ad-hoc meetings or calls not in Fellow.

- `mcp__claude_ai_Granola__query_granola_meetings`
- `mcp__claude_ai_Granola__list_meetings`

### Manual input

Pasted transcripts, attached PDFs, slides, or self-assessment documents prepared by the person. When a document comes from the person themselves (not external observation), the system flags it as self-reported to weigh appropriately.

---

## Current state

| Person | Slug | Role | Sessions | Notes |
|--------|------|------|----------|-------|
| Juan Onetto | `_self` | CEO | 1 | 360 survey (Oct 2025) + coaching program complete |
| Alejandro Soto | `alejandro-soto` | Head of Product Engineering | 1 | Full profile with SUMA Leadership Matrix (51 behaviors) |
| Malén Baigorria | `malen-baigorria` | HRBP | 1 | Full profile + coaching arc + 21 action items tracked |
| Agostina Bisso | `agostina-bisso` | Head of Customer | 0 | Full profile + coaching arc + SUMA Leadership Matrix (initial, no cycle closure) + 9 action items |

_Last updated: 2026-03-03_

---

## Key files

| File | Purpose |
|------|---------|
| `skills/one-on-one/SKILL.md` | Full operational blueprint — the 10-step session logging process, evaluation workflow, and query mode |
| `.claude-plugin/plugin.json` | Plugin metadata for Claude integration |
| `data/_template/` | Blueprint files for new people — copy and customize |
| `data/_self/profile.md` | CEO's 360 survey results and development themes |
