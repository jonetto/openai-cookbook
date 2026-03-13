---
name: cos-debrief
description: "Extract decisions, action items, and OKR changes from a completed meeting. Searches Fellow for transcript + summary, proposes OKR updates for user confirmation. Use when the user asks to 'debrief [meeting]', 'process the planning', or 'what came out of yesterday's meeting'."
---

# /cos-debrief — Post-Meeting Extraction

Process a completed meeting to extract structured outcomes: decisions, action items, and proposed OKR changes. Searches Fellow for the meeting data, structures the output, and presents OKR updates for Juan's approval before writing anything.

---

## Step 1: Find the Meeting

Search Fellow for the target meeting:

1. If user specifies a meeting name or date → search by that
2. If ambiguous → list the top 3-5 candidate meetings and ask the user to pick

**Search Fellow:**
```
search_meetings(query="{user's argument or 'Planning'}", limit=5)
```

Match by: date, title keywords, participant names.

**If no Fellow result found:** Ask the user to provide the meeting title or date. Do not guess.

---

## Step 2: Get Full Meeting Data

Once the meeting is identified, fetch all available data:

1. **Meeting summary** — `get_meeting_summary(meeting_id)`
2. **Transcript** — `get_meeting_transcript(meeting_id)` (may be empty for some meetings)
3. **Action items** — `get_action_items(meeting_id)` — Fellow's AI-detected action items

If the transcript is empty but the summary/notes are rich, work from those.

---

## Step 3: Extract Structured Outcomes

Analyze the meeting data and extract:

### Decisions Made
- Bullet list of what was decided
- Include context: who proposed it, what the alternatives were (if discussed)
- Flag any decisions that were provisional/conditional

### OKRs Discussed or Agreed
- Any targets mentioned (new KRs, adjusted targets, dropped objectives)
- Area-level OKR proposals
- Company-level changes

### Action Items
For each action item:

| Owner | Action | Due Date | Source |
|-------|--------|----------|--------|
| {name} | {what} | {when} | Fellow AI / transcript |

- Include both Fellow's AI-detected items AND any commitments found in the transcript that Fellow missed
- If no due date was mentioned, flag it as "no date set"

### Open Questions
- Items left unresolved that need follow-up
- Decisions that were deferred
- Topics that were raised but not fully discussed

---

## Step 4: Propose OKR Updates

If the meeting discussed OKR targets or progress, propose changes to the quarterly OKR file.

Read the current file:
```
${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md
```

For each proposed change, present it as:

```
📝 Proposed OKR Change:
  Section: {area name}
  KPI: {kpi name}
  Current: {current value or "empty"}
  Proposed: {new value}
  Source: {quote from transcript/summary}
```

**⚠️ CRITICAL: Do NOT write any changes to the OKR file without explicit user confirmation.**

Ask:
> "Here are the OKR changes I extracted from the meeting. Should I apply all of them, some of them, or none? You can also modify any values before I write them."

Wait for Juan's response. Only after he confirms, update the file.

---

## Special Case: Post-Planning Debrief

When debriefing a **quarterly planning session** (identified by title containing "Planning" or "Estratégica" with 4+ leadership team attendees):

The output should also populate the area-level OKR sections that are currently empty in the quarterly file. Walk through each area:

1. **Revenue** (Owner: Agustín Páez de Robles) — KPIs and Q2 targets discussed
2. **Product/Engineering** (Owner: Alejandro Soto) — KPIs and Q2 targets discussed
3. **Customer** (Owner: Agostina Bisso) — KPIs and Q2 targets discussed
4. **People** (Owner: Malén Baigorria) — KPIs and Q2 targets discussed
5. **Sueldos** (Owner: Yamila Sosa) — KPIs and Q2 targets discussed

For each area, propose a table:

```markdown
## {Area} (Owner: {Name})

| KPI | Q2 Target | Apr | May | Jun | Source |
|-----|-----------|-----|-----|-----|--------|
| {kpi} | {target from planning} | — | — | — | {source} |
```

Present all area tables for confirmation before writing.

---

## Step 5: Output

Present the structured debrief in chat:

```
📋 Meeting Debrief — {meeting title}
Date: {meeting date}
Participants: {list}
```

Then each section:
1. **Decisions** — bullet list
2. **Action Items** — table with owner/action/due date
3. **OKR Changes** — proposed changes (pending confirmation)
4. **Open Questions** — items needing follow-up

Keep it scannable. Juan should be able to read the debrief in 3 minutes and know exactly what happened and what needs his attention.

**Do NOT send to Slack automatically.** Output in chat. Juan decides what to share.
