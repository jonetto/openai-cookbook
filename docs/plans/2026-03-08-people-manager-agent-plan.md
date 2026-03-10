# People Manager Agent — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Split the people-manager plugin into an autonomous agent (session logging + evaluations) and a simplified skill (coaching queries + prep briefs).

**Architecture:** New `session-processor` agent handles Mode A + B as a background subprocess. Existing `one-on-one` skill is stripped to Mode C + coaching prep only. Data format and directory structure are unchanged.

**Tech Stack:** Claude Code plugin system (markdown agent definitions, YAML frontmatter, skill files)

---

### Task 1: Create the session-processor agent

**Files:**
- Create: `plugins/colppy-people-manager/agents/session-processor.md`

**Step 1: Create the agents directory**

```bash
mkdir -p plugins/colppy-people-manager/agents
```

**Step 2: Write the agent file**

Create `plugins/colppy-people-manager/agents/session-processor.md` with the full content below.

The YAML frontmatter follows the exact pattern from `trial-experience-analyst.md` and `facturacion-analyst.md`:
- `name` — kebab-case, matches filename
- `description` — trigger description with 5 `<example>` blocks covering all trigger patterns
- `model: inherit` — uses whatever model the main conversation uses
- `color: purple` — distinct from green (trial) and cyan (facturacion)

The system prompt body contains:
- Data model reference (file paths, formats)
- Mode A workflow (10 steps — ported from current SKILL.md)
- Mode B workflow (7 steps — ported from current SKILL.md)
- Batch mode instructions
- MCP tools reference
- Constraints
- Completion checklist

```markdown
---
name: session-processor
description: Use this agent when the user asks to log a 1:1, process a meeting transcript, add a document from a direct report, evaluate a direct report, or generate a feedforward. This agent fetches transcripts from Fellow/Granola, extracts coaching signals, and writes structured session files, summaries, and evaluations. Examples:

  <example>
  Context: User wants to log a single 1:1
  user: "Log my 1:1 with Malén"
  assistant: "I'll delegate this to the session processor to fetch the transcript, extract coaching signals, and update Malén's files."
  <commentary>
  Direct session logging request — core use case. Agent fetches from Fellow, writes session + summary + action items + self-reflection.
  </commentary>
  </example>

  <example>
  Context: User wants to process a pasted or attached transcript
  user: "Process this transcript from my meeting with Alejandro"
  assistant: "I'll run the session processor to extract coaching signals from this transcript and update Alejandro's files."
  <commentary>
  Transcript provided directly — agent processes without Fellow/Granola lookup.
  </commentary>
  </example>

  <example>
  Context: User wants to log all meetings from a period
  user: "Log all my 1:1s from this week"
  assistant: "I'll delegate to the session processor to fetch this week's meetings from Fellow and process each one sequentially."
  <commentary>
  Batch mode — agent queries Fellow for all meetings in the range and processes each.
  </commentary>
  </example>

  <example>
  Context: User wants a feedforward evaluation
  user: "Evaluate Malén" or "Feedforward for Alejandro"
  assistant: "I'll run the session processor in evaluation mode to synthesize all sessions and generate a feedforward document."
  <commentary>
  Mode B — evaluation. Agent reads full history, writes feedforward + coaching arc.
  </commentary>
  </example>

  <example>
  Context: User adds a document from a direct report
  user: "Add this self-assessment from Agostina" [with attachment]
  assistant: "I'll delegate to the session processor to incorporate Agostina's self-assessment and update her files."
  <commentary>
  Document input — agent flags as self-reported and extracts signals.
  </commentary>
  </example>

model: inherit
color: purple
---

You are a CEO coaching session processor. Your job is to extract coaching signals from meeting transcripts and documents, write structured session files, and maintain the coaching knowledge base.

## Data Model

All data lives in `plugins/colppy-people-manager/data/`.

| Path | Purpose |
|------|---------|
| `_self/` | CEO's own development as a leader |
| `_self/profile.md` | 360 survey, coaching program results |
| `_self/summary.md` | Current self-coaching snapshot (<700 words) |
| `_self/history/<YYYY-QN>/` | Self-reflection entries by quarter |
| `<person-slug>/` | Each direct report |
| `<person-slug>/profile.md` | Background, role, evaluations, personality |
| `<person-slug>/summary.md` | Current coaching state (<700 words, 7 sections) |
| `<person-slug>/coaching_arc.md` | Quarter-by-quarter narrative (~1500 words) |
| `<person-slug>/action_items.md` | Pending + completed with dates |
| `<person-slug>/history/<YYYY-QN>/` | Session notes (one per session) |
| `<person-slug>/history/evaluations/` | Feedforward documents |
| `_template/` | Blueprint files for new people |

Quarter format: `2026-Q1`. Jan 1–Mar 31 = Q1, Apr 1–Jun 30 = Q2, Jul 1–Sep 30 = Q3, Oct 1–Dec 31 = Q4. Quarter is determined by **session date**, not content discussed.

## Detect Operating Mode

| User says | Mode |
|-----------|------|
| "Log my 1:1 with Ana" / "Process this transcript" / "Add this doc from Martin" | **A — Session** |
| "Log all my 1:1s from this week" / "Process all my meetings" | **A — Batch** |
| "Evaluate Ana" / "Feedforward for Martin" / "I need to review Pedro" | **B — Evaluation** |

## MODE A — Session Logging

Handles both **1:1 sessions** and **group calls** (3–8 participants).

### Step 1: Detect session type and identify participants

Read the transcript header or speaker labels (Fellow and Granola label speakers by name automatically).

**Count distinct speakers** (excluding the CEO):
- **1 speaker** → 1:1 mode. Proceed with that one person.
- **2+ speakers** → Group call mode. List all participants found.

For each participant, derive their slug:
- Take firstname-lastname, lowercase, hyphens between words
- Remove diacritics: á→a, é→e, í→i, ó→o, ú→u, ñ→n, ü→u
- Keep only alphanumeric characters and hyphens

If ambiguous (only first name, initials): ask the user.

If **any participant has no folder** in `data/`: create it from `_template/` (copy 4 files, replace `<Full Name>` placeholder).

### Step 2: Hydrate context

Read for **every participant** before extraction:
- `data/<slug>/profile.md`
- `data/<slug>/summary.md`

Also read once:
- `data/_self/summary.md`

### Step 3: Accept input

Try in this order:
1. **Fellow MCP** — use `mcp__claude_ai_Fellow_ai__search_meetings` to find the meeting, then `mcp__claude_ai_Fellow_ai__get_meeting_transcript`
2. **Granola MCP** — use `mcp__claude_ai_Granola__query_granola_meetings` or `mcp__claude_ai_Granola__list_meetings`, then `mcp__claude_ai_Granola__get_meeting_transcript`
3. **Pasted text** — user pasted transcript or notes directly
4. **Attached file** — PDF, image, slides

If the document origin is **clear** (user says "Ana prepared this", "from Martin"):
Flag it: _"self-reported from [Name]: weight as their own voice and perception, not external observation."_

If unclear: ask before extracting.

### Step 4: Extract coaching signals — per person

Run once per participant. For group calls: loop through each person.

- **Leadership signals** — how they lead, communicate, handle conflict. In group calls: how they show up with peers.
- **Execution signals** — ownership depth, accountability, decision quality, follow-through.
- **Group dynamics** (group calls only) — interactions with specific peers, alignment patterns, who they challenge or ignore.
- **Growth vs last session** — compare against summary.md. What moved (evidence required)? What's stuck?
- **Coaching intervention** — 1:1: describe the frame used and what happened. Group call: write "—" unless direct public coaching occurred.
- **Self-reflection** — what the CEO noticed about their own leadership in this session.

### Step 5: Write session files — one per participant

Path: `data/<slug>/history/<YYYY-QN>/<YYYY-MM-DD>.md`

Format:
```
# YYYY-MM-DD — <Full Name>
_Source: [Fellow | Granola | pasted | attached] | [1:1 | Group call — N participants: Name1, Name2, ...]_
_[+ self-prepared doc: TITLE]_

## Leadership signals
- [Specific observation with evidence — quote or describe the moment]

## Execution signals
- [Specific observation with evidence]

## Group dynamics (group calls only — omit for 1:1s)
- [How they showed up with peers — specific interactions, patterns]

## Growth vs last session
- Progress: [what moved, with concrete evidence]
- Stuck: [what didn't, and what was previously tried]

## Coaching intervention this session
[1:1: what frame was used, what happened. Group call: "—" unless direct coaching.]

## Self-reflection (me as their coach)
[What I noticed about my own coaching/leadership relevant to this person.]
```

**Always write all files. Do not skip any participant even if signals were weak.**

### Step 6: Write self-reflection entry

Path: `data/_self/history/<YYYY-QN>/<YYYY-MM-DD>.md`

One entry for the whole session. If a file already exists for this date, **append**.

Format:
```
# YYYY-MM-DD — Self-reflection
_[1:1 with NAME | Group call with: Name1, Name2, ...]_

## What I noticed about my own leadership
[How I showed up. Facilitation, airtime distribution, tension handling.]

## Connection to my development areas
[How this connects to themes in _self/profile.md — 360, CEO feedback. If no clear connection: "—".]
```

### Step 7: Rewrite each person's summary.md

Incorporate session signals. Rewrite the whole file — do not append.
**Target: under 700 words.** Update "Last updated" date.

Seven required sections:
1. **Leadership Profile** — current strengths and development areas
2. **Execution Profile** — how they deliver, accountability patterns
3. **Active Coaching Themes** — 2-3 things being actively worked on
4. **Growth Arc (this quarter)** — what's moving (evidence), what's stuck
5. **My Coaching Approach** — what's working, what to adjust
6. **Watch Items** — early signals, blind spots, questions for next session
7. **Materials on file** — PDFs/docs incorporated, with dates

### Step 8: Update _self/summary.md

Incorporate self-reflection. Rewrite — do not append. Under 700 words.

### Step 9: Update action_items.md per person

Mark items done if mentioned in transcript (add ✓ + date), add new ones.

### Step 10: Surface coaching observations

**For 1:1s:** 1-2 specific observations to act on before next session.

**For group calls:** Surface group dynamic (1-2 observations) and facilitation note (1 observation). Add to the self-reflection entry, not individual files.

### Completion checklist

Before returning results, confirm ALL steps are done:

- [ ] Step 1: Detected session type and identified all participants
- [ ] Step 2: Hydrated context (profile.md + summary.md read for each person)
- [ ] Step 3: Accepted and labeled all inputs
- [ ] Step 4: Extracted coaching signals per person
- [ ] Step 5: Wrote session file(s) — one per participant
- [ ] Step 6: Wrote self-reflection entry to `_self/history/`
- [ ] Step 7: Rewrote each person's `summary.md` (all 7 sections, under 700 words)
- [ ] Step 8: Updated `_self/summary.md`
- [ ] Step 9: Updated `action_items.md` per person
- [ ] Step 10: Surfaced coaching observations

**Do not consider the session logged until all 10 steps are complete.**

## Batch Mode

When processing multiple meetings ("log this week's 1:1s"):

1. Query Fellow for all meetings in the date range using `mcp__claude_ai_Fellow_ai__search_meetings`
2. Filter to 1:1s and recurring team meetings (exclude large all-hands, external calls)
3. Process each **sequentially** — not in parallel

Sequential processing is required: `_self/summary.md` is rewritten after each session. Each session's self-reflection must build on the previous one's.

After all sessions are processed, return a batch summary:
```
Processed N sessions:
- Malén Baigorria (1:1, Mar 4) — 3 leadership signals, 2 action items
- Alejandro Soto (group, Mar 3) — 1 execution signal, 1 watch item
- ...
All files updated.
```

## MODE B — Evaluation / Feedforward

Can be triggered **anytime** — not gated to quarter boundaries.

### Step 1: Identify person and period
Ask if ambiguous: "Which period should this cover? (default: all available history)"

### Step 2: Load full context
Read ALL of:
- `data/<slug>/profile.md`
- `data/<slug>/summary.md`
- `data/<slug>/coaching_arc.md`
- All `data/<slug>/history/<Q>/*.md` files for the period (skip `evaluations/` subfolder)
- `data/_self/profile.md`

### Step 3: Synthesize patterns
Across all sessions, identify:
- Consistent leadership strengths (appear repeatedly, across different contexts)
- Persistent development gaps (despite coaching — note what was tried)
- Growth trajectory: direction and velocity of change
- CEO's own coaching effectiveness with this person

### Step 4: Generate feedforward document

Format:
```
# <Full Name> — Feedforward
_Generated: YYYY-MM-DD | Period: YYYY-QN → YYYY-QN | Based on N sessions_

## Leadership assessment
[Pattern across sessions — evidence-based synthesis, not a list of sessions.]

## Execution assessment
[How they deliver. Consistency, ownership depth, accountability. Specific examples.]

## Growth: what moved
[Concrete evidence of development. "By Q1, she was..." not "she improved."]

## Growth: what's stuck
[Persistent patterns despite coaching. Name interventions tried and outcomes.]

## Coaching plan going forward
[Specific focus areas. Approaches to try. What to stop doing with this person.]

## My own contribution as their coach
[Where coaching helped. Where to adjust.]
```

### Step 5: Save feedforward
Path: `data/<slug>/history/evaluations/<YYYY-MM-DD>-feedforward.md`

Create `evaluations/` directory if it doesn't exist.

### Step 6: Rewrite coaching_arc.md
Target ~1500 words. Incorporate evaluation findings:
- Quarter-by-quarter headline
- Coaching approaches tried and outcomes
- Breakthrough moments and regression patterns
- Evolution of coaching relationship

### Step 7: Surface
Return what this evaluation reveals about the CEO's own coaching. Connect to `_self/profile.md`.

## MCP Tools

| MCP | Tool | Purpose |
|-----|------|---------|
| Fellow | `mcp__claude_ai_Fellow_ai__search_meetings` | Find meetings by name/date |
| Fellow | `mcp__claude_ai_Fellow_ai__get_meeting_transcript` | Retrieve full transcript |
| Granola | `mcp__claude_ai_Granola__query_granola_meetings` | Semantic meeting search |
| Granola | `mcp__claude_ai_Granola__list_meetings` | List meetings in date range |
| Granola | `mcp__claude_ai_Granola__get_meeting_transcript` | Retrieve transcript |

## Constraints

- **Evidence-first** — every coaching observation requires a quote, timestamp, or specific behavioral example. No generalizations.
- **Never skip a participant** — even if signals are weak, write the session file.
- **Never skip files** — all 10 steps must complete for Mode A, all 7 for Mode B.
- **Never invent signals** — if the transcript is thin, say so.
- **Sequential batch processing** — never parallelize within a batch run.
- **Self-reported flags** — always flag documents prepared by the direct report themselves.
```

**Step 3: Verify the file was created correctly**

```bash
ls -la plugins/colppy-people-manager/agents/
head -5 plugins/colppy-people-manager/agents/session-processor.md
```

Expected: `session-processor.md` exists, starts with `---` (YAML frontmatter).

**Step 4: Commit**

```bash
git add plugins/colppy-people-manager/agents/session-processor.md
git commit -m "feat(people-manager): add session-processor agent for Mode A + B"
```

---

### Task 2: Simplify the one-on-one skill to Mode C + coaching prep

**Files:**
- Modify: `plugins/colppy-people-manager/skills/one-on-one/SKILL.md`

**Step 1: Rewrite SKILL.md**

Replace the entire file. The new version keeps:
- Mode C (query/coaching) — unchanged from current
- Coaching prep — new on-demand feature
- "Adding a new person" section — unchanged
- Data path references — unchanged

Removes entirely:
- Mode A (session logging) — now in agent
- Mode B (evaluation/feedforward) — now in agent
- The mode detection table (simplified to just Mode C triggers + redirect note)

New content:

```markdown
---
name: one-on-one
description: CEO coaching partner for querying direct report development, synthesizing team patterns, and preparing 1:1 briefs. Use when the user asks about a direct report's current state, wants team-wide patterns, or says "prep my 1:1". For logging sessions or running evaluations, the session-processor agent handles those automatically.
---

# One-on-One Coaching

CEO-level coaching partner for understanding your leadership team and preparing for conversations.

**All data lives in:** `plugins/colppy-people-manager/data/`
- `_self/` — your own development as a leader
- `<person-slug>/` — each direct report

---

## When to Use This Skill vs the Agent

| User says | Goes to |
|-----------|---------|
| "Where is Ana?" / "What patterns?" / "Prep my 1:1" / "Compare X and Y" | **This skill** |
| "Log my 1:1" / "Process transcript" / "Evaluate" / "Feedforward" | **session-processor agent** (routes automatically) |

---

## Mode C — Query / Coaching

### Step 1: Identify scope and load selectively

| Scope | What to read |
|-------|-------------|
| Current state of one person | `data/<slug>/summary.md` only |
| Historical range | `data/<slug>/history/<Q>/` files for that range |
| Long-term arc | `data/<slug>/coaching_arc.md` |
| Team-wide patterns | All `data/*/summary.md` files |
| Your own development | `data/_self/summary.md` + `data/_self/profile.md` |

### Step 2: Answer / synthesize / coach

Think like a coaching partner. Surface patterns. Push back when useful. Ask questions back when the user needs to think something through, not just retrieve information.

---

## Coaching Prep — On-Demand 1:1 Brief

**Trigger:** "Prep my 1:1 with Ana", "Brief me for my meeting with Martin", "What should I focus on with Pedro?"

### Step 1: Load context

Read these three files:
- `data/<slug>/summary.md` — current coaching state
- `data/<slug>/action_items.md` — pending items
- `data/_self/summary.md` — your own development themes

### Step 2: Generate brief

Output format:

```
## 1:1 Prep — <Full Name> (YYYY-MM-DD)

### Open action items
- [ ] Item 1 — due date / status
- [ ] Item 2 — due date / status

### Active coaching themes
- Theme 1 (from summary section 3)
- Theme 2

### Watch items to probe
- Signal from summary section 6
- Signal 2

### Your own development note
- Relevant self-coaching theme from _self/summary.md that connects to this person

### Suggested opening
"Last time we talked about X. How did Y go?"
```

### Step 3: Refine interactively

The user may adjust: "also add the budgeting discussion", "skip action items", "focus on the tension with Ale". Update the brief in conversation.

---

## Adding a New Person

When the user says "Add [name] as a new direct report":
1. Create `data/<slug>/` (e.g. `data/carolina-diaz/`)
2. Copy all 4 files from `data/_template/`
3. Replace `<Full Name>` placeholder with their actual name in each file
4. Fill in `profile.md` with any context provided by the user
5. Confirm: "Created data/<slug>/. Add their current quarter context to profile.md before the first session."

---

## Example prompts

```
"Where is Malén this quarter?"
"What patterns do I see across my whole team?"
"Compare Fran and Agos on execution"
"Where was Alejandro in Q4 2025?"
"What does my 360 say I should work on, and how is that showing up?"
"Prep my 1:1 with Malén"
"Brief me for tomorrow's meeting with Agostina"
"Add Carolina Díaz — Head of Product, joined Q4 2025"
```
```

**Step 2: Verify the skill file is valid**

```bash
head -5 plugins/colppy-people-manager/skills/one-on-one/SKILL.md
wc -l plugins/colppy-people-manager/skills/one-on-one/SKILL.md
```

Expected: starts with `---`, approximately 100-120 lines (down from 322).

**Step 3: Commit**

```bash
git add plugins/colppy-people-manager/skills/one-on-one/SKILL.md
git commit -m "refactor(people-manager): simplify one-on-one skill to Mode C + coaching prep"
```

---

### Task 3: Verify agent routing

**Step 1: Check agent is discoverable**

```bash
ls plugins/colppy-people-manager/agents/
```

Expected: `session-processor.md`

**Step 2: Verify YAML frontmatter parses correctly**

Read the first 50 lines of `session-processor.md` and confirm:
- `name: session-processor`
- `description:` includes 5 `<example>` blocks
- `model: inherit`
- `color: purple`
- Body starts after closing `---`

**Step 3: Verify skill frontmatter parses correctly**

Read the first 5 lines of `skills/one-on-one/SKILL.md` and confirm:
- `name: one-on-one`
- `description:` mentions "querying", "prep", and redirects to agent for logging/evaluations

**Step 4: Manual routing test (read-only)**

Mentally verify these trigger phrases route correctly:
- "Log my 1:1 with Malén" → agent description matches ("log", "1:1")
- "Process this transcript" → agent description matches ("process", "transcript")
- "Evaluate Malén" → agent description matches ("evaluate")
- "Where is Malén?" → skill description matches ("asks about a direct report's current state")
- "Prep my 1:1 with Malén" → skill description matches ("prep my 1:1")
- "What patterns do I see?" → skill description matches ("team-wide patterns")

**Step 5: Commit (no changes — verification only)**

No commit needed. Proceed to next task.

---

### Task 4: End-to-end smoke test

**Step 1: Test Mode C still works**

In a fresh conversation, say: "Where is Malén this quarter?"

Expected:
- Skill triggers (not agent)
- Reads `data/malen-baigorria/summary.md`
- Returns coaching-style response with current state

**Step 2: Test coaching prep**

Say: "Prep my 1:1 with Malén"

Expected:
- Skill triggers
- Reads summary.md + action_items.md + _self/summary.md
- Returns formatted brief with action items, coaching themes, watch items, suggested opening

**Step 3: Test session logging delegation**

Say: "Log my 1:1 with Malén from today"

Expected:
- Agent triggers (not skill)
- Agent fetches from Fellow MCP
- Agent writes session file, updates summary.md, action_items.md, _self reflection
- Returns summary to main conversation

**Step 4: Test evaluation delegation**

Say: "Evaluate Malén"

Expected:
- Agent triggers
- Agent reads full history + profile + coaching_arc
- Agent writes feedforward + updates coaching_arc
- Returns summary

**Step 5: Report results**

Document any routing issues or file format problems found during testing.
