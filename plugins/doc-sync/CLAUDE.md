# Doc Sync

Automatically discovers and proposes documentation updates after git commits.

## When You Receive a DOC-SYNC Message

A PostToolUse hook has detected a commit and found .md files that may be stale.
Follow this process:

### Step 1: Read the diff

Run `git show HEAD` to see what changed in the commit.

### Step 2: Read each candidate doc

Open every file listed in the DOC-SYNC message.

### Step 3: Analyze relevance

For each doc, determine:
- Does it describe behavior, paths, or APIs that the commit changed?
- Are there concrete inaccuracies (wrong paths, outdated descriptions, missing new features)?
- Or is the doc still accurate despite the code change?

### Step 4: Propose edits

For docs that need updating, present to the user:
- Which file and why it's stale
- The proposed edit (use the Edit tool format)

### Step 5: Skip accurate docs silently

If a candidate doc is still accurate, don't mention it.

## Rules

- NEVER auto-edit docs. Always propose and wait for user approval.
- Keep edits minimal — update what's stale, don't rewrite.
- Match the doc's existing tone and formatting.
- If a README lists file paths, update paths. If it describes behavior, update behavior.
- For MEMORY.md: only update factual claims (paths, versions, tool names). Don't touch architectural notes or strategic context.
- Group all proposals in a single message for batch approval/rejection.

## What Counts as Stale

| Change type | Update needed? |
|---|---|
| File renamed/moved | Yes — update path references |
| Function/API signature changed | Yes — update usage examples |
| New file added to documented directory | Maybe — only if README lists files |
| Behavior change | Yes — if doc describes old behavior |
| Refactoring (same behavior) | No — unless path references changed |
| Config/env changes | Yes — if docs reference old config |

## Output Format

When proposing updates:

> **path/to/doc.md** — [reason it's stale]
> [Proposed edit]

If no docs need updating: "Checked N docs against commit — all still accurate."
