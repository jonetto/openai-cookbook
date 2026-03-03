# colppy-people-manager Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Claude Code plugin that gives a CEO persistent, compounding coaching context for their leadership team — transcript-first, files-as-RAG, zero external dependencies.

**Architecture:** A `colppy-people-manager` plugin with one skill (`one-on-one`) and a `data/` folder per person. Three-tier memory: `summary.md` (hot, always loaded), `coaching_arc.md` (warm, evaluations only), `history/` (cold, on-demand). The SKILL.md is the blueprint — it encodes all orchestration logic so Claude knows exactly what to do in every mode.

**Tech Stack:** Markdown files, Claude Code plugin system, Fellow MCP, Granola MCP (both already connected in this workspace).

---

## Task 1: Plugin scaffold

**Files:**
- Create: `plugins/colppy-people-manager/.claude-plugin/plugin.json`

**Step 1: Create the plugin directory and plugin.json**

```bash
mkdir -p plugins/colppy-people-manager/.claude-plugin
```

Create `plugins/colppy-people-manager/.claude-plugin/plugin.json`:

```json
{
  "name": "colppy-people-manager",
  "version": "1.0.0",
  "description": "CEO coaching toolkit: persistent 1:1 context, leadership development tracking, feedforward evaluations, and self-reflection across quarters. Transcript-first via Fellow and Granola MCP.",
  "author": {
    "name": "Colppy"
  }
}
```

**Step 2: Create the skills directory**

```bash
mkdir -p plugins/colppy-people-manager/skills/one-on-one
```

**Step 3: Verify structure**

```bash
ls plugins/colppy-people-manager/.claude-plugin/
```
Expected: `plugin.json`

**Step 4: Commit**

```bash
git add plugins/colppy-people-manager/.claude-plugin/
git commit -m "feat: scaffold colppy-people-manager plugin"
```

---

## Task 2: Template files

**Files:**
- Create: `plugins/colppy-people-manager/data/_template/profile.md`
- Create: `plugins/colppy-people-manager/data/_template/summary.md`
- Create: `plugins/colppy-people-manager/data/_template/coaching_arc.md`
- Create: `plugins/colppy-people-manager/data/_template/action_items.md`

**Step 1: Create template directory**

```bash
mkdir -p plugins/colppy-people-manager/data/_template
```

**Step 2: Create profile.md**

Create `plugins/colppy-people-manager/data/_template/profile.md`:

```markdown
# <Full Name> — Profile

| Field | Value |
|-------|-------|
| Role | |
| Team | |
| Tenure | |
| Direct reports | |
| Manager since | |

## Current Quarter Context
[OKRs, key projects, what they're being measured on this quarter]

## Background
[How they got here, relevant history, what shaped them as a leader]
```

**Step 3: Create summary.md**

Create `plugins/colppy-people-manager/data/_template/summary.md`:

```markdown
# <Full Name> — Coaching Summary
_Last updated: —_

## Leadership Profile
[Current strengths and development areas as a leader — how they lead people, make decisions, communicate, build their team]

## Execution Profile
[How they deliver — quality, accountability, ownership patterns, decision-making under pressure]

## Active Coaching Themes
[The 2-3 specific things being actively worked on right now]

## Growth Arc (this quarter)
[What's moving with evidence. What's stuck despite coaching.]

## My Coaching Approach
[What's working with this person. What I need to adjust as their leader.]

## Watch Items
[Early signals, risks, blind spots, questions to probe next session]

## Materials on file
[PDFs, decks, self-assessments incorporated — name and date]
```

**Step 4: Create coaching_arc.md**

Create `plugins/colppy-people-manager/data/_template/coaching_arc.md`:

```markdown
# <Full Name> — Coaching Arc
_Last updated: —_

## Development trajectory
[Quarter-by-quarter headline — e.g. "Q3-25: defensive, reactive → Q4-25: beginning to own decisions → Q1-26: leading through others"]

## Coaching approaches tried
[What you've tried with this person, what worked, what didn't — be specific]

## Breakthrough moments
[Sessions or moments where something clicked — what happened, what enabled it]

## Regression patterns
[Topics or behaviors that keep coming back despite coaching — what you've tried]

## Evolution of this coaching relationship
[How your approach to coaching this person has changed over time]
```

**Step 5: Create action_items.md**

Create `plugins/colppy-people-manager/data/_template/action_items.md`:

```markdown
# <Full Name> — Action Items

## Pending
<!-- Format: - [ ] Owner (YYYY-MM-DD): item -->

## Completed
<!-- Format: - [x] Owner (YYYY-MM-DD): item ✓ YYYY-MM-DD -->
```

**Step 6: Verify**

```bash
ls plugins/colppy-people-manager/data/_template/
```
Expected: `action_items.md  coaching_arc.md  profile.md  summary.md`

**Step 7: Commit**

```bash
git add plugins/colppy-people-manager/data/_template/
git commit -m "feat: add _template folder with all person file templates"
```

---

## Task 3: _self/ folder (CEO's own development)

**Files:**
- Create: `plugins/colppy-people-manager/data/_self/profile.md`
- Create: `plugins/colppy-people-manager/data/_self/summary.md`
- Create: `plugins/colppy-people-manager/data/_self/coaching_arc.md`

**Step 1: Create _self directory**

```bash
mkdir -p plugins/colppy-people-manager/data/_self/history
```

**Step 2: Create _self/profile.md**

Create `plugins/colppy-people-manager/data/_self/profile.md`:

```markdown
# My Leadership Profile

_This file is the source of truth for your own development as a leader.
Add your 360 survey results, CEO feedback, and personal leadership history here.
Claude reads this to connect self-reflections from 1:1 sessions to your development areas._

---

## 360 Survey
_Date: —_

[Paste summary or full content here. Include: key themes, top strengths, development areas, verbatim quotes that resonated.]

---

## Feedback from my CEO
_Date: —_

[Notes, development areas highlighted, coaching direction received. Add entries as new feedback comes in, with dates.]

---

## My leadership history
[How you got here. What shaped you as a leader. Context about your leadership style, values, what you're working on long-term.]

---

## Materials on file
[Documents, presentations, notes incorporated — name and date]
```

**Step 3: Create _self/summary.md**

Create `plugins/colppy-people-manager/data/_self/summary.md`:

```markdown
# My Leadership — Coaching Summary
_Last updated: —_

## My Leadership Profile
[Current strengths and development areas as a CEO and leader of leaders]

## My Execution Patterns
[How I show up in high-stakes moments, decisions, team dynamics, board interactions]

## Active Development Themes
[The 2-3 things I'm actively working on now — from 360, CEO feedback, or my own observation]

## Growth Arc (this quarter)
[What's moving in my own development. What's stuck.]

## My Coaching Effectiveness
[Patterns across 1:1s: what's working as a coach, what I repeat that doesn't work, what I avoid]

## Watch Items
[Patterns I'm noticing in myself. Things my CEO or 360 flagged that keep showing up.]

## Materials on file
[360 survey, CEO notes, other inputs — with dates]
```

**Step 4: Create _self/coaching_arc.md**

Create `plugins/colppy-people-manager/data/_self/coaching_arc.md`:

```markdown
# My Leadership — Coaching Arc
_Last updated: —_

## Development trajectory
[Quarter-by-quarter headline of your own growth as a leader]

## What's working in my coaching
[Approaches that consistently help my direct reports grow]

## What I need to stop doing
[Tendencies that show up repeatedly that don't serve my team]

## Breakthrough moments (my own)
[Times I showed up differently as a leader — what enabled it]

## Evolution of my leadership style
[How my approach has changed over time — what I've learned]
```

**Step 5: Verify**

```bash
ls plugins/colppy-people-manager/data/_self/
```
Expected: `coaching_arc.md  history/  profile.md  summary.md`

**Step 6: Commit**

```bash
git add plugins/colppy-people-manager/data/_self/
git commit -m "feat: add _self/ folder for CEO leadership development tracking"
```

---

## Task 4: The SKILL.md — core blueprint

This is the most important file. It encodes the full orchestration logic. Claude reads this at conversation start (when the plugin is loaded) and follows it exactly.

**Files:**
- Create: `plugins/colppy-people-manager/skills/one-on-one/SKILL.md`

**Step 1: Create SKILL.md**

Create `plugins/colppy-people-manager/skills/one-on-one/SKILL.md`:

```markdown
---
name: one-on-one
description: CEO coaching tool for 1:1s with direct reports. Log sessions from Fellow/Granola transcripts or documents, track leadership development over quarters, generate feedforward evaluations, and reflect on your own growth as a leader. Use when the user says "log my 1:1", "evaluate", "feedforward", or asks about a direct report.
---

# One-on-One Coaching

CEO-level coaching system for developing a leadership team and tracking your own growth as a leader.

**Transcript-first:** Primary input is Fellow or Granola MCP. Also accepts pasted notes, PDFs, slides, or documents prepared by the direct report.

**All data lives in:** `plugins/colppy-people-manager/data/`
- `_self/` — your own development as a leader
- `<person-slug>/` — each direct report (e.g. `ana-gomez`, `martin-lopez`)

---

## Detect operating mode

| User says | Mode |
|-----------|------|
| "Log my 1:1 with Ana" / "Process this transcript" / "Add this doc from Martin" | **A — Session** |
| "Evaluate Ana" / "Feedforward for Martin" / "I need to review Pedro" | **B — Evaluation** |
| "Where is Ana?" / "What patterns do I see?" / "What was Martin like in Q4?" | **C — Query / Coach** |

---

## MODE A — Session Logging

Handles both **1:1 sessions** and **group calls** (3–8 participants). The same blueprint runs for both — the difference is detected in Step 1 and determines whether one or N session files are written.

### [D] Step 1: Detect session type and identify participants

Read the transcript header or speaker labels (Fellow and Granola label speakers by name automatically).

**Count distinct speakers** (excluding yourself):
- **1 speaker** → 1:1 mode. Proceed with that one person.
- **2+ speakers** → Group call mode. List all participants found.

For each participant, derive their slug: first-last lowercase hyphenated (e.g. `ana-gomez`).
If a participant's name is ambiguous or missing a last name, ask the user to clarify before proceeding.

If **any participant has no folder** in `data/`: note them, offer to create — "I found [Name] in the transcript but no folder exists. Create one now?"

### [D] Step 2: Hydrate context — ALWAYS DO THIS FIRST

Read for **every participant** before doing any extraction:
- `plugins/colppy-people-manager/data/<slug>/profile.md`
- `plugins/colppy-people-manager/data/<slug>/summary.md`

Also read once (applies to all):
- `plugins/colppy-people-manager/data/_self/summary.md`

If a person folder doesn't exist and the user confirmed creation: copy all 4 files from `_template/`, replace `<Full Name>` with their actual name.

### [D] Step 3: Accept input

Try in this order:
1. **Fellow MCP** — use `mcp__claude_ai_Fellow_ai__search_meetings` to find the meeting, then `mcp__claude_ai_Fellow_ai__get_meeting_transcript`
2. **Granola MCP** — use `mcp__claude_ai_Granola__query_granola_meetings` or `mcp__claude_ai_Granola__list_meetings`
3. **Pasted text** — user pasted transcript or notes directly
4. **Attached file** — PDF, image, slides (Claude reads natively)

If a document was **prepared by a participant** (self-assessment, plan, deck): flag it — *"self-reported from [Name]: weight as their own voice and perception, not external observation."*

Multiple inputs can be combined (e.g. transcript + attached self-assessment from one person).

### [A] Step 4: Extract coaching signals — per person

Run this extraction **once per participant**. For group calls: loop through each person.

**Leadership signals** — how they lead. In a 1:1: how they communicate, give feedback, handle conflict, build their team. In a group call: how they show up with peers — vocal vs. silent, how they handle disagreement, whether they build on others' ideas or stay isolated, how they respond to challenge.

**Execution signals** — how they deliver. Ownership depth, accountability, decision quality under pressure, stakeholder management, follow-through on commitments.

**Group dynamics signals** (group calls only) — how they interact with specific peers. Who they align with, who they challenge, who they ignore. Patterns across the group that reveal something about their leadership style not visible in 1:1s.

**Growth vs last session** — compare against that person's current `summary.md`:
- What concretely moved? (evidence required)
- What's still stuck? (name what was tried before)

**Coaching intervention** (1:1 only — not applicable in group calls unless you intervened directly with one person in front of others) — what frame or approach you used. Be specific.

**Self-reflection** (once for the whole session, not per person) — what you noticed about yourself. In a group call: how you facilitated, who you gave airtime to, who you ignored, how you handled tension. In a 1:1: what you did well and what you'd do differently as their coach.

### [D] Step 5: Write session files — one per participant

Path per person: `plugins/colppy-people-manager/data/<slug>/history/<YYYY-QN>/<YYYY-MM-DD>.md`

Quarter format: `2026-Q1`, `2025-Q4`, etc. (Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)

**Always write all files. Do not skip any participant even if signals were weak.**

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
[1:1 only: what frame or approach was used, what happened. For group calls: write "—" unless you directly coached this person in the group.]

## Self-reflection (me as their coach)
[What I noticed about my own coaching/leadership relevant to this person in this session.]
```

### [D] Step 6: Write self-reflection entry

Path: `plugins/colppy-people-manager/data/_self/history/<YYYY-QN>/<YYYY-MM-DD>.md`

One entry for the whole session — written once, even if it was a group call.
If a file already exists for this date (multiple sessions in one day), **append** — do not overwrite.

```
# YYYY-MM-DD — Self-reflection
_[1:1 with NAME | Group call with: Name1, Name2, ...]_

## What I noticed about my own leadership
[How I showed up. In group calls: facilitation, airtime distribution, how I handled tension, who I centered and who I left out.]

## Connection to my development areas
[How this connects to themes in _self/profile.md — 360, CEO feedback, personal history. If no clear connection, write "—".]
```

### [A] Step 7: Rewrite each person's summary.md

Run once per participant. Incorporate their session signals. Rewrite the whole file — do not append.
**Target: under 700 words.** Update "Last updated" date.

Seven sections, all required:
1. **Leadership Profile** — current strengths and development areas as a leader
2. **Execution Profile** — how they deliver, accountability patterns
3. **Active Coaching Themes** — the 2-3 things being actively worked on now
4. **Growth Arc (this quarter)** — what's moving (with evidence), what's stuck
5. **My Coaching Approach** — what's working, what you need to adjust as their leader
6. **Watch Items** — early signals, blind spots, questions to probe next session
7. **Materials on file** — any PDFs/docs incorporated, with dates

### [A] Step 8: Update _self/summary.md

Incorporate the self-reflection from this session. Rewrite — do not append.
Target: under 700 words. Update "Last updated" date.

### [D] Step 9: Update action_items.md per person

For each participant: mark items done if mentioned in transcript (add ✓ + date), add new ones.

### [A] Step 10: Surface coaching observations

**For 1:1s:** 1-2 specific observations to act on before next session with that person.

**For group calls:** 1-2 observations about the group dynamic + 1 observation about your own facilitation. Example: "Martin went silent every time Ana made a strong assertion — worth exploring privately whether that's deference, conflict avoidance, or something else. In your facilitation: you consistently resolved tension before it developed — experiment with letting it sit next time."

---

## MODE B — Evaluation / Feedforward

Can be triggered **anytime** — not gated to quarter boundaries.

### [D] Step 1: Identify person and period
Ask if ambiguous: "Which period should this cover? (default: all available history)"

### [D] Step 2: Load full context
Read ALL of:
- `data/<slug>/profile.md`
- `data/<slug>/summary.md`
- `data/<slug>/coaching_arc.md`
- All `data/<slug>/history/<Q>/*.md` files for the period (skip `evaluations/` subfolder)

### [A] Step 3: Synthesize patterns
Across all sessions, identify:
- Consistent leadership strengths (appear repeatedly, across different contexts)
- Persistent development gaps (despite coaching — note what was tried and what happened)
- Growth trajectory: direction and velocity of change
- Your own coaching effectiveness with this person

### [A] Step 4: Generate feedforward document

```
# <Full Name> — Feedforward
_Generated: YYYY-MM-DD | Period: YYYY-QN → YYYY-QN | Based on N sessions_

## Leadership assessment
[Pattern across sessions — how they lead. Evidence-based, specific. Not a list of sessions — a synthesis of what the pattern reveals about them as a leader.]

## Execution assessment
[How they deliver. Consistency, ownership depth, accountability. Specific examples.]

## Growth: what moved
[Concrete evidence of development across the period. "By Q1, she was..." not "she improved."]

## Growth: what's stuck
[Persistent patterns despite coaching. Name the interventions tried and what happened each time.]

## Coaching plan going forward
[Specific focus areas. Approaches to try. What to stop doing with this person.]

## My own contribution as their coach
[Where my coaching helped this person grow. Where I need to adjust.]
```

### [D] Step 5: Save feedforward
Path: `data/<slug>/history/evaluations/<YYYY-MM-DD>-feedforward.md`
Create `evaluations/` directory if it doesn't exist.

### [A] Step 6: Rewrite coaching_arc.md
Target ~1500 words. Update the longitudinal story to incorporate evaluation findings:
- Quarter-by-quarter headline
- Coaching approaches tried and outcomes
- Breakthrough moments and regression patterns
- Evolution of your coaching relationship

### [A] Step 7: Surface
What does this evaluation reveal about your own coaching of this person? Connect to `_self/profile.md`.

---

## MODE C — Query / Coaching

### [D] Step 1: Identify scope and load selectively
- Current state of one person → read `summary.md` only
- Historical range → read `history/<Q>/` files for that range
- Long-term arc → read `coaching_arc.md`
- Team-wide patterns → read all `summary.md` files across `data/`

### [A] Step 2: Answer / synthesize / coach
Think like a coaching partner. Surface patterns. Push back when useful. Ask questions back when the user needs to think something through, not just retrieve information.

---

## Adding a new person

When the user says "Add <name> as a new direct report":
1. Create `data/<slug>/` (e.g. `data/carolina-diaz/`)
2. Copy all 4 files from `data/_template/`
3. Replace `<Full Name>` placeholder with their actual name in each file
4. Fill in `profile.md` with any context provided by the user
5. Confirm: "Created data/<slug>/. Add their current quarter context to profile.md before the first session."

---

## Example prompts

```
"Log my 1:1 with Ana from today"
"Process the transcript from my meeting with Martin"
"Add this self-assessment from Pedro" [attach PDF]
"Evaluate Ana — give me a feedforward"
"I need to do a feedforward for Martin for his performance review"
"Where is Ana this quarter?"
"What patterns do I see across my whole team?"
"Where was Pedro in Q4 2025?"
"What does my 360 say I should work on, and how is that showing up in my sessions?"
"Add Carolina Díaz — Head of Product, joined Q4 2025"
```
```

**Step 2: Verify the file was created**

```bash
wc -l plugins/colppy-people-manager/skills/one-on-one/SKILL.md
```
Expected: 200+ lines

**Step 3: Commit**

```bash
git add plugins/colppy-people-manager/skills/one-on-one/SKILL.md
git commit -m "feat: add one-on-one SKILL.md — full coaching blueprint with session/evaluation/query modes"
```

---

## Task 5: Smoke test — add a real person and run a session

This is the end-to-end verification. Do this in a live Claude Code conversation with the plugin loaded.

**Step 1: Reload the plugin**

In Claude Code, the plugin is auto-detected from `plugins/colppy-people-manager/.claude-plugin/plugin.json`. Start a new conversation or use `/reload` if available.

**Step 2: Add a test person**

Say to Claude:
```
Add <name of one of your direct reports> as a new direct report — <role>, <team>
```

Expected: Claude creates `data/<slug>/` with all 4 files copied from `_template/`, name replaced.

**Step 3: Verify file structure**

```bash
ls plugins/colppy-people-manager/data/<slug>/
```
Expected: `action_items.md  coaching_arc.md  profile.md  summary.md`

**Step 4: Run a session with a real or test transcript**

Say to Claude:
```
Log my 1:1 with <name> from today
```

Expected:
- Claude tries Fellow/Granola MCP first
- If no transcript found, Claude asks you to paste one or provide input
- Claude extracts coaching signals, writes session file, rewrites summary.md, writes _self entry

**Step 5: Verify output files**

```bash
ls plugins/colppy-people-manager/data/<slug>/history/
ls plugins/colppy-people-manager/data/_self/history/
```
Expected: Both have a dated session file.

**Step 6: Verify summary was updated**

```bash
head -5 plugins/colppy-people-manager/data/<slug>/summary.md
```
Expected: "Last updated: <today's date>"

**Step 7: Commit if everything looks right**

```bash
git add plugins/colppy-people-manager/data/
git commit -m "feat: first real session logged — people-manager working end-to-end"
```

---

## Task 6: Fill in _self/profile.md with your own material

This is done by the user (you), not Claude — it's your personal leadership data.

**Step 1: Open the file**

Open `plugins/colppy-people-manager/data/_self/profile.md`

**Step 2: Add your 360 survey results**

Paste the summary or full content under the `## 360 Survey` section. Include the date.

**Step 3: Add CEO feedback notes**

Add any notes from your own CEO, development areas, coaching direction under `## Feedback from my CEO`. Include the date.

**Step 4: Add personal leadership history**

Fill in the `## My leadership history` section — how you got here, your leadership style, what you're working on long-term.

**Step 5: Commit**

```bash
git add plugins/colppy-people-manager/data/_self/profile.md
git commit -m "chore: add personal leadership profile to _self"
```

Note: if this file contains sensitive information you don't want in git history, add it to `.gitignore`:
```bash
echo "plugins/colppy-people-manager/data/_self/profile.md" >> .gitignore
```

---

## What's NOT in Phase 1

Save for Phase 2:
- MCP server for Claude.ai / Cowork sharing
- Automated Fellow/Granola sync (not needed — MCP handles it live)
- Any UI or web interface
- Export or reporting scripts
