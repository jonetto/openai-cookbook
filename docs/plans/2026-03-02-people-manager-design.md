# Design: colppy-people-manager — CEO Coaching Plugin

_Date: 2026-03-02_
_Phase: 1 — Claude Code, files-as-RAG, no MCP server_

---

## Problem

A CEO coaching a leadership team needs persistent, compounding context across sessions — spanning quarters — without losing the nuance of each person's development arc. Claude's context window resets every conversation. The solution is a files-as-RAG system: structured markdown files that Claude loads at conversation start, eliminating the need to re-explain context each time.

This also covers the CEO's own development: 360 feedback, notes from their own CEO, and self-reflections extracted from every coaching session they run.

---

## Scope (Phase 1)

- Claude Code only (CLI). No MCP server, no web interface.
- Transcript-first: primary input is Fellow / Granola MCP. Occasional documents prepared by the direct report (self-assessments, plans, decks, PDFs, slides).
- Minimal manual typing from the user — the system should work from transcripts alone.
- Shareable via git (team members clone repo, each runs their own copy).

---

## Plugin Structure

```
plugins/colppy-people-manager/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── one-on-one/
│       └── SKILL.md              ← Blueprint: orchestration + file formats
└── data/
    ├── _template/                ← Copy when adding a new person
    │   ├── profile.md
    │   ├── summary.md
    │   ├── coaching_arc.md
    │   └── action_items.md
    ├── _self/                    ← CEO's own development (mirrors same structure)
    │   ├── profile.md            ← 360 survey, CEO feedback notes, personal history
    │   ├── summary.md            ← Current development state as a leader
    │   ├── coaching_arc.md       ← Longitudinal growth arc
    │   └── history/
    │       └── 2026-Q1/
    │           └── 2026-03-02.md ← Self-reflection from each session run
    └── <person-slug>/            ← e.g. ana-gomez, martin-lopez
        ├── profile.md            ← Role, background, current quarter context
        ├── summary.md            ← Rolling current-state summary (~700 words)
        ├── coaching_arc.md       ← Longitudinal development arc (~1500 words)
        ├── action_items.md       ← Pending / completed (secondary, nice-to-have)
        └── history/
            ├── evaluations/
            │   └── 2026-03-02-feedforward.md
            └── 2026-Q1/
                └── 2026-03-02.md
```

---

## Three-Tier Memory Architecture

Solves the growing-history problem. Inspired by Stripe Minions' context hydration strategy: load selectively, not unconditionally.

| Tier | File | Target size | Loaded when |
|------|------|-------------|-------------|
| **Hot** | `summary.md` | ~700 words | Every session — always |
| **Warm** | `coaching_arc.md` | ~1500 words | Evaluations, deep dives, quarterly synthesis |
| **Cold** | `history/<Q>/<date>.md` | Unlimited | On-demand time travel ("what was Ana like in Q4 2025?") |

`summary.md` is **rewritten** (not appended) after every session — it always reflects current state.
`coaching_arc.md` is rewritten when an evaluation is generated or explicitly requested.
History files are written once and never modified — full fidelity, forever.

---

## Input Types

The system is transcript-first. Claude accepts any of these, alone or combined:

| Input | How provided |
|-------|-------------|
| Fellow transcript | MCP tool call (`granola_query_meetings` / Fellow MCP) |
| Granola transcript | MCP tool call |
| Pasted notes | User pastes text directly into chat |
| PDF | Attached — Claude reads natively |
| Slides / images | Attached — Claude reads natively (multimodal) |
| Document from direct report | Attached or pasted, flagged as "prepared by them" — self-reported signal |

When a document is prepared by the direct report (self-assessment, 30-60-90 plan, presentation), Claude weights it as **self-reported data** — the person's own voice and perception — not external observation. This distinction matters for coaching analysis.

---

## Two Operating Modes

### Mode A — Session Logging

Triggered by: `"Log my 1:1 with Ana"` / `"Process this transcript"` / `"Add this document from Martin"`

```
[D] 1. Identify person — infer from transcript or ask if ambiguous
[D] 2. Hydrate context — read data/<person>/profile.md + summary.md
         also read data/_self/summary.md (CEO's current development state)
[D] 3. Accept input — Fellow/Granola MCP, pasted text, PDF, slides, or mixed
         if document is from the person, flag as self-reported
[A] 4. Extract coaching signals:
         - Leadership signals (how they lead: decisions, communication, team dynamics)
         - Execution signals (how they deliver: quality, accountability, ownership)
         - Growth vs last session (what moved, what's stuck)
         - Coaching intervention (what approach was used this session)
         - Self-reflection (what you noticed about your own leadership in this session)
[D] 5. Write session file → data/<person>/history/<YYYY-QN>/<YYYY-MM-DD>.md
[D] 6. Write self entry  → data/_self/history/<YYYY-QN>/<YYYY-MM-DD>.md
         tagged "Session with <person>" — same self-reflection content
[A] 7. Rewrite person's summary.md — current state, 7 sections, ~700 words
[A] 8. Update _self/summary.md — incorporate new self-reflection signal
[D] 9. Update action_items.md — mark done if mentioned, add new ones
[A] 10. Surface: 1-2 coaching observations to act on next session
```

### Mode B — Evaluation / Feedforward

Triggered by: `"Evaluate Ana"` / `"Generate a feedforward for Martin"` / `"I need to do a review of Pedro"`
Can happen anytime — not gated to quarter boundaries.

```
[D] 1. Identify person + period (default: all history)
[D] 2. Load full context:
         data/<person>/profile.md + summary.md + coaching_arc.md
         + all history files for the specified period
[A] 3. Synthesize — patterns across sessions in leadership, execution, growth, coaching effectiveness
[A] 4. Generate feedforward document — structured, evidence-based
[D] 5. Save → data/<person>/history/evaluations/<date>-feedforward.md
[A] 6. Rewrite coaching_arc.md — incorporate evaluation findings, update the arc
[A] 7. Surface: what this evaluation reveals about your own coaching of this person
```

### Mode C — Query / Coaching

Triggered by: `"Where is Ana this quarter?"` / `"What patterns do I see across my team?"` / `"What does Q4 say about Martin's leadership?"`

```
[D] 1. Identify person(s) and scope
[D] 2. Load relevant files only (summary for current state, history range for past, arc for long-term)
[A] 3. Answer / coach — synthesize, surface patterns, act as thinking partner
```

---

## File Formats

### `profile.md` (static — user maintains)

```markdown
# <Name> — Profile

| Field | Value |
|-------|-------|
| Role | |
| Team | |
| Tenure | |
| Direct reports | |
| Manager since | |

## Current Quarter Context
[OKRs, key projects, what they're being measured on]

## Background
[How they got here, relevant history, what shaped them as a leader]
```

**For `_self/profile.md`:**
Contains 360 survey results (summary + key verbatims), CEO feedback notes, personal leadership history. PDFs and docs can be pasted here as source material.

---

### `summary.md` (rewritten every session, ~700 words)

```markdown
# <Name> — Coaching Summary
_Last updated: YYYY-MM-DD_

## Leadership Profile
[Current strengths and development areas as a leader —
 how they lead people, make decisions, communicate, build team]

## Execution Profile
[How they deliver — quality, accountability, ownership patterns,
 decision-making under pressure]

## Active Coaching Themes
[The 2-3 specific things being actively worked on right now]

## Growth Arc (this quarter)
[What's moving with evidence, what's stuck despite coaching]

## My Coaching Approach
[What's working with this person, what I need to adjust as their leader]

## Watch Items
[Early signals, risks, blind spots, questions to probe next session]

## Materials on file
[PDFs, decks, docs incorporated — e.g. "Q1 self-assessment (2026-03-02)"]
```

---

### Session file `history/<YYYY-QN>/<YYYY-MM-DD>.md` (written once, never modified)

```markdown
# YYYY-MM-DD — <Name>
_Source: Fellow transcript | Q1 review deck (PDF, self-prepared)_

## Leadership signals
- [Observation with evidence from transcript]

## Execution signals
- [Observation with evidence from transcript]

## Growth vs last session
- Progress: [what moved]
- Stuck: [what didn't, despite prior coaching]

## Coaching intervention this session
[What frame or approach was used — e.g. "explored the fear behind the avoidance pattern"]

## Self-reflection (me as their coach)
[What I noticed about my own leadership in this session]
```

**For `_self/history/` entries:**
```markdown
# YYYY-MM-DD — Self-reflection
_Session with: <Name>_

## What I noticed about my own leadership
[Patterns, tendencies, things I did well or need to adjust]

## Connection to my development areas
[How this session relates to my 360 feedback or CEO coaching]
```

---

### Feedforward document `history/evaluations/<date>-feedforward.md`

```markdown
# <Name> — Feedforward
_Generated: YYYY-MM-DD | Period: YYYY-QN → YYYY-QN_

## Leadership assessment
[Pattern across sessions — how they lead, evidence-based]

## Execution assessment
[How they deliver, consistency, ownership depth]

## Growth: what moved
[Concrete evidence of development across the period]

## Growth: what's stuck
[Persistent patterns despite coaching — with examples]

## Coaching plan going forward
[Specific focus areas, approaches to try, what to stop doing]

## My own contribution as their coach
[Where my coaching helped, where I need to adjust]
```

---

### `coaching_arc.md` (rewritten at evaluation time, ~1500 words)

Captures the **longitudinal story** — not the current state (that's `summary.md`) but how the person has evolved since you started working together:

- Quarter-by-quarter headline (e.g. Q3-25: "defensive, reactive" → Q1-26: "leading through others")
- Coaching approaches tried and their outcomes
- Breakthrough moments and regression patterns
- How your own coaching of this person has evolved

---

## Example Prompts

```
"Log my 1:1 with Ana from today"
→ Mode A — fetches Fellow transcript, writes all files

"Add this self-assessment from Martin" [attach PDF]
→ Mode A — uses document as session input, flags as self-reported

"Evaluate Ana — give me a feedforward for her"
→ Mode B — reads full history, generates feedforward document

"What patterns do I see across my full team this quarter?"
→ Mode C — reads all summary.md files, synthesizes team-level patterns

"Where was Pedro in Q4 2025?"
→ Mode C — reads history/2025-Q4/ for Pedro, synthesizes

"What does my 360 say I should be working on, and how is it showing up in my sessions?"
→ Mode C — reads _self/profile.md + recent _self/history/, connects themes

"Add Ana Gómez as a new direct report"
→ Creates data/ana-gomez/ from _template, fills in profile.md
```

---

## Phase 2 (future — not in scope now)

When sharing with coworkers or moving to Claude.ai / Cowork:

- Thin Node.js MCP server wrapping the `data/` folder
- Tools: `read_person_summary`, `write_session`, `list_people`, `generate_feedforward`
- Same file structure — no migration needed
- Each user's `data/` stays local; only the server interface changes

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Rewrite summary, not append | Keeps context compact and current; history files hold full fidelity |
| `_self/` mirrors same structure | Symmetric: you coach your team the same way you track yourself |
| Evaluation is anytime, not quarterly-gated | Feedforwards happen when needed, not on a calendar |
| Transcript-first, minimal typing | Removes friction; system gets used because input is effortless |
| Document-from-person flagged as self-reported | Coaching distinction: their voice vs your observation |
| Three-tier memory | Solves growing history: hot/warm/cold loaded selectively |
| Inspired by Stripe Minions blueprints | Deterministic nodes guarantee files are always written; agentic nodes do the interpretation |
