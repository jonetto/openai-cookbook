# People Manager Agent — Design Doc

**Date:** 2026-03-08
**Status:** Approved
**Plugin:** `colppy-people-manager`

## Problem

The people-manager plugin today is skill-only. All three operating modes (session logging, evaluations, coaching queries) run inside the main conversation. This creates three problems:

1. **Context bloat** — transcript extraction + signal detection + file writes consume 15-20K tokens per person in the main chat
2. **No parallelism** — "log this week's 1:1s" processes each person sequentially while the user waits
3. **No coaching prep** — the user must manually read summaries before 1:1s instead of getting a pre-assembled brief

## Solution: Agent + Skill Split

Split the current monolithic skill into two components by interaction model:

| Component | Type | Handles | Why this execution model |
|-----------|------|---------|--------------------------|
| `session-processor` | **Agent** | Mode A (session logging) + Mode B (evaluations) | Heavy, write-intensive, can run in background |
| `one-on-one` | **Skill** (simplified) | Mode C (coaching queries) + coaching prep | Conversational, lightweight reads, benefits from back-and-forth |

## Architecture

```
plugins/colppy-people-manager/
├── .claude-plugin/plugin.json          # unchanged — agents auto-discovered
├── agents/
│   └── session-processor.md            # NEW: Mode A + Mode B
├── skills/
│   └── one-on-one/SKILL.md             # SIMPLIFIED: Mode C + coaching prep
├── data/                               # UNCHANGED
│   ├── _self/
│   ├── _template/
│   └── <person-slug>/
```

Data format, file structure, and folder layout remain identical. The agent writes the same files the skill wrote before.

## Agent: `session-processor`

### Trigger Patterns

| User says | Behavior |
|-----------|----------|
| "Log my 1:1 with Malén" | Single-person session logging |
| "Process this transcript" / "Add this doc from Martin" | Single-person from pasted/attached input |
| "Log this week's 1:1s" / "Process all my meetings" | Batch: fetch all meetings in range, process each |
| "Evaluate Malén" / "Feedforward for Ale" | Mode B: full evaluation with coaching arc rewrite |

### Mode A — Session Logging

**Steps:**

1. **Detect session type** — parse transcript for speaker count. 1 speaker = 1:1, 2+ = group call.
2. **Identify participants** — derive slugs (firstname-lastname, lowercase, no diacritics). If no folder exists, create from `_template/`.
3. **Hydrate context** — for each participant, read:
   - `data/<slug>/profile.md`
   - `data/<slug>/summary.md`
   - `data/_self/summary.md`
4. **Fetch transcript** — try Fellow MCP → Granola MCP → pasted/attached. Flag self-reported documents.
5. **Extract signals** — per person: leadership signals, execution signals, group dynamics (group calls), growth vs last session, coaching intervention, self-reflection.
6. **Write files:**
   - `data/<slug>/history/<YYYY-QN>/<YYYY-MM-DD>.md` — session file
   - `data/<slug>/summary.md` — rewritten (7 sections, <700 words)
   - `data/<slug>/action_items.md` — updated
   - `data/_self/history/<YYYY-QN>/<YYYY-MM-DD>.md` — CEO self-reflection
   - `data/_self/summary.md` — rewritten with new self-coaching themes
7. **Return summary** — "Logged 1:1 with Malén — 3 leadership signals, 2 new action items, 1 watch item updated"

### Mode B — Evaluation / Feedforward

**Steps:**

1. **Load full history** — all session files for the person in the target period + profile.md + coaching_arc.md + _self/profile.md
2. **Synthesize feedforward** — patterns across sessions, evidence-based observations, development recommendations
3. **Write files:**
   - `data/<slug>/history/evaluations/<YYYY-MM-DD>-feedforward.md`
   - `data/<slug>/coaching_arc.md` — rewritten with new quarter narrative (~1500 words)
   - `data/_self/history/<YYYY-QN>/<YYYY-MM-DD>.md` — coaching effectiveness self-reflection
4. **Return summary** — "Feedforward complete for Malén — saved to evaluations/2026-03-08-feedforward.md, coaching arc updated"

### Batch Mode

When processing multiple meetings:

1. Query Fellow for all meetings in the date range
2. Filter to 1:1s and recurring team meetings (exclude large all-hands, external calls)
3. Process each **sequentially within the single agent** — not parallel agents

Sequential processing is intentional: `_self/summary.md` is rewritten after each session. Parallel agents would create write conflicts where the last writer wins and earlier self-reflections are lost. Sequential order also means each session's self-reflection builds on the previous one.

### MCP Tools Used

| MCP | Tool | Purpose |
|-----|------|---------|
| Fellow | `search_meetings` | Find meetings by name/date |
| Fellow | `get_meeting_transcript` | Retrieve full transcript |
| Granola | `query_granola_meetings` | Semantic meeting search (fallback) |
| Granola | `list_meetings` | List meetings in date range (fallback) |

## Skill: `one-on-one` (simplified)

### What's Removed

All of Mode A and Mode B — transcript fetching, signal extraction, file writing, evaluation synthesis. These move to the agent.

### What Stays

#### Mode C — Coaching Queries

| User says | What the skill does |
|-----------|---------------------|
| "Where is Malén this quarter?" | Reads summary.md, responds conversationally |
| "What patterns do I see across my team?" | Reads all summaries, synthesizes |
| "What was Ale like in Q4?" | Reads coaching_arc.md + relevant history |
| "Compare Fran and Agos on execution" | Reads both summaries, compares |

#### Coaching Prep (new, on-demand)

| User says | What the skill does |
|-----------|---------------------|
| "Prep my 1:1 with Malén" | Assembles a brief from 3 files |

**Brief format:**

```markdown
## 1:1 Prep — Malén Baigorria (YYYY-MM-DD)

### Open action items
- [ ] Item 1 — due date
- [ ] Item 2 — due date

### Active coaching themes
- Theme from summary.md section 3
- Theme 2

### Watch items
- Signal to probe from summary.md section 6

### Your own development note
- Relevant self-coaching theme from _self/summary.md

### Suggested opening
"Last time we talked about X. How did Y go?"
```

Stays as a skill (not agent) because:
- Lightweight — reads 3 files, formats output
- Interactive — user may adjust: "also add the budgeting conversation"
- Conversational — natural back-and-forth is the value

## Routing

The split is clean by trigger language:

| Signal words | Routes to |
|-------------|-----------|
| "log", "process", "transcript", "add this doc" | **Agent** (session-processor) |
| "evaluate", "feedforward", "review [person]" | **Agent** (session-processor) |
| "where is", "how is", "what patterns", "prep my 1:1", "compare" | **Skill** (one-on-one) |

The agent's YAML frontmatter description includes explicit `<example>` blocks (matching the pattern used by `trial-experience-analyst` and `facturacion-analyst`) to make routing reliable.

## What Does NOT Change

- **Data format** — all markdown files keep the same structure
- **Data directory** — `data/` stays where it is, same folder layout
- **Evidence-first principle** — agent must include quotes, timestamps, specific behavioral examples
- **Session file structure** — same 6 sections (leadership signals, execution signals, group dynamics, growth, coaching intervention, self-reflection)
- **Summary.md structure** — same 7 sections, <700 words
- **Cross-plugin isolation** — people-manager still doesn't read from other plugins

## Implementation Sequence

1. Create `agents/session-processor.md` — port Mode A + B logic from current SKILL.md
2. Simplify `skills/one-on-one/SKILL.md` — strip Mode A + B, keep Mode C, add coaching prep
3. Test: "Log my 1:1 with Malén" → verify agent triggers, writes correct files
4. Test: "Where is Malén?" → verify skill triggers, reads files correctly
5. Test: "Prep my 1:1 with Malén" → verify coaching prep format
6. Test: "Evaluate Malén" → verify Mode B runs as agent
