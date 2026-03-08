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
