---
name: investigate-bug
description: Trigger the Bug Detective to investigate a bug by Jira key, Intercom link, or free-text description. Usage: /investigate-bug KAN-1234 or /investigate-bug "users can't generate factura de venta" or /investigate-bug (no args = proactive scan)
argument: The bug to investigate — a Jira key (KAN-1234, CI-7061), Intercom conversation ID, free-text description, or nothing for a proactive scan
---

# /investigate-bug

Dispatch the **Bug Detective** agent to investigate a bug signal.

## Parsing the argument

1. **Jira key** (matches `[A-Z]+-\d+`): Fetch the ticket, then cross-reference with Intercom and commits
2. **Numeric ID** (matches `\d{10,}`): Treat as Intercom conversation ID, read it, then cross-reference
3. **Free-text description**: Search all sources for matching patterns
4. **No argument**: Run a proactive scan of Intercom + Jira (default: last 7 days)
5. **`--days N`**: Override the scan window (e.g., `/investigate-bug --days 30` for a monthly scan)

## Execution

Dispatch the `bug-detective` agent with the parsed input. The detective runs its full 6-step workflow:

1. Signal intake (classify input)
2. Cross-reference (check other systems)
3. DB verification (if data-related)
4. Code trace (if code path is identifiable)
5. Triage report (structured output)
6. Save + notify (JSON cache + Slack DM)

## After the triage

Show the triage report in the conversation, then ask:

> "Want me to dispatch the Bug Fixer to open a PR?"

- If **yes**: The user invokes the Bug Fixer with the triage context (human-gated)
- If **not now**: Save the triage for later reference
- If **need more info**: Detective continues investigating with the user's guidance
