---
name: cos-agenda
description: "Calendar briefing with context. Reads Google Calendar, enriches meetings with people-manager profiles and Fellow history, flags conflicts. Use when the user asks 'what's on my calendar', 'prep me for tomorrow', or 'brief me for today'."
---

# /cos-agenda — Calendar Briefing

Contextual calendar briefing — not just a schedule dump. For each meeting with a leadership team member, enrich it with coaching context, recent meeting history, and open action items so Juan walks in prepared.

---

## Step 1: Read Calendar

Use Google Calendar MCP to get events for the target range:

```
gcal_list_events(time_min={range_start}, time_max={range_end})
```

**Default range:** Today + tomorrow.

If user specifies a different range (e.g. "this week", "Monday", "next 3 days"), use that instead.

---

## Step 2: Identify Leadership Meetings

For each calendar event, check if any attendee matches the leadership team:

| Name | Email patterns to match |
|------|------------------------|
| Malén Baigorria | malen, baigorria |
| Agostina Bisso | agostina, bisso |
| Alejandro Soto | alejandro, soto |
| Jorge Ross | jorge, ross |
| Agustín Páez de Robles | agustin, paez |
| Yamila Sosa | yamila, sosa |
| Francisca Horton | francisca, horton |

Match by checking attendee names or email addresses against these patterns (case-insensitive substring match).

Tag each event as either:
- **Leadership meeting** — has at least one leadership team member
- **Other** — external meeting, personal event, etc.

---

## Step 3: Enrich Leadership Meetings

For each meeting tagged as leadership:

### Read People-Manager Profile

For the team member(s) in the meeting, read:
- `plugins/colppy-people-manager/data/{directory}/profile.md` — role, coaching themes, development areas
- `plugins/colppy-people-manager/data/{directory}/summary.md` — recent flags, patterns

| Person | Directory |
|--------|-----------|
| Malén Baigorria | `malen-baigorria` |
| Agostina Bisso | `agostina-bisso` |
| Alejandro Soto | `alejandro-soto` |
| Agustín Páez de Robles | `agustin-paez-de-robles` |
| Francisca Horton | `francisca-horton` |
| Yamila Sosa | `yamila-sosa` |

Jorge Ross has no people-manager profile — search Fellow for recent meetings instead.

### Search Fellow History

Search Fellow for the last 2-3 meetings between Juan and that person:
```
search_meetings(query="{person name}", limit=3)
```

For each recent meeting, get:
- Summary (brief)
- Open action items between Juan and that person

### Compile Context Card

For each leadership meeting, produce:
- **Coaching themes** currently in focus for that person
- **Last meeting summary** (1-2 sentences)
- **Open action items** between Juan and this person
- **Suggested focus** — what Juan should bring up or follow up on

---

## Step 4: Flag Issues

Scan the full calendar for:

- **Back-to-back meetings** — no gap between consecutive events (no prep time)
- **Conflicts** — overlapping events
- **Meetings without agenda/notes** — events with no description or Fellow notes
- **People with overdue actions** — if any attendee has overdue Fellow items, flag it

---

## Step 5: Output

Present a chronological briefing:

```
📅 Calendar Briefing — {date range}
Generated: {today}
```

For each event (in chronological order):

**Leadership meeting:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 {time} — {title}
   With: {attendee names}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   🎯 Coaching themes: {themes from profile}
   📝 Last meeting: {1-2 sentence summary}
   📋 Open items:
      - {action item 1}
      - {action item 2}
   💡 Suggested focus: {what to bring up}
```

**Other meeting:**
```
🕐 {time} — {title}
   With: {attendees}
   {description if available}
```

### Flags

```
⚠️ Flags
- {back-to-back: event A → event B, no prep time}
- {conflict: event X overlaps event Y}
- {overdue: {person} has {N} overdue items}
```

Keep the entire briefing readable in **2 minutes**. Juan should be able to scan this before his first meeting and know what to focus on.

**Do NOT send to Slack automatically.** Output in chat. Juan decides what to share.
