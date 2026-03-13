---
name: cos-status
description: "Action items and accountability. Pulls Fellow actions for leadership team, cross-references OKR progress, checks calendar deadlines, reads people-manager flags. Use when the user asks 'who owes what', 'status check', or 'what's overdue'."
---

# /cos-status — Action Items & Accountability

Per-person accountability snapshot across the leadership team. Shows who owes what, what's overdue, OKR progress by area, and people flags — ending with a "CEO attention needed" summary.

---

## Leadership Team

| Name | Role | Area | People-Manager Dir |
|------|------|------|--------------------|
| Malén Baigorria | HRBP | People | `malen-baigorria` |
| Agostina Bisso | Head of Customer | Customer | `agostina-bisso` |
| Alejandro Soto | Head of Product Engineering | Product & Engineering | `alejandro-soto` |
| Jorge Ross | Tech Lead (reports to Alejandro) | Product & Engineering | — (no profile) |
| Agustín Páez de Robles | Head of Revenue | Revenue | `agustin-paez-de-robles` |
| Yamila Sosa | PM — Liquidación de Sueldos | Sueldos | `yamila-sosa` |
| Francisca Horton | RevOps Lead | Revenue Operations | `francisca-horton` |

---

## Step 1: Pull Fellow Action Items

For each leader, search Fellow for their action items:

```
get_action_items(assignee="{person name}")
```

Categorize each item:
- **Completed** — marked done in Fellow
- **Pending** — open, not yet due
- **Overdue** — open, past due date

If Fellow search by assignee doesn't work, search recent meetings with each person and extract action items from those.

---

## Step 2: Read OKR Progress

Read the current quarter's OKR file:

```
${CLAUDE_PLUGIN_ROOT}/data/okrs/q2-2026.md
```

For each area owner, check:
- Are actuals being tracked? (columns filled vs "—")
- If tracked, are they on track vs target?
- If area section is empty (not yet populated post-planning), note "OKRs not yet defined"

---

## Step 3: Check Calendar

Use Google Calendar MCP to check the next 2 weeks:

```
gcal_list_events(time_min=today, time_max=today+14d)
```

For each leader, identify:
- Next meeting with Juan
- Any deadlines or milestones mentioned in calendar events
- Conflicts or scheduling issues

---

## Step 4: Read People-Manager Flags

For each of the 6 leaders with profiles, read their summary:

```
plugins/colppy-people-manager/data/{directory}/summary.md
```

Look for:
- Exit signals or retention risks
- Underperformance patterns
- Critical coaching items in progress
- Morale concerns
- Recent wins or development milestones

Jorge Ross has no people-manager profile — his context is part of Alejandro's leadership.

---

## Step 5: Output

Present a per-person status card for each leader:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 {Name} — {Role} ({Area})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Action Items: {pending_count} pending, {overdue_count} overdue
   Overdue:
   - {action} (due {date})
   - ...

📈 OKR Status: {on track / behind / not yet defined}
   {brief detail if behind}

🚩 Flags: {from people-manager, or "none"}

📅 Next: {next meeting with Juan} | {upcoming deadline}
```

### CEO Attention Needed

End with a prioritized summary — the top 3 items requiring Juan's intervention:

```
🔴 CEO Attention Needed
1. {most urgent item — who, what, why}
2. {second item}
3. {third item}
```

Prioritize by: overdue items > people flags > OKR gaps > upcoming deadlines.

**Do NOT send to Slack automatically.** Output in chat. Juan decides what to share.
