# Doc Sync Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a two-layer system that discovers and updates stale documentation after every git commit — interactively in Claude Code, automatically outside it.

**Architecture:** Claude Code plugin (`doc-sync`) with a PostToolUse shell hook for discovery + CLAUDE.md for analysis instructions. Git post-commit hook as safety net that invokes `claude --print` headlessly. Loop prevention via commit message tags.

**Tech Stack:** Bash (shell hooks), jq (JSON parsing), grep/find (discovery), Claude CLI (`--print` mode)

**Spec:** `docs/superpowers/specs/2026-03-10-doc-sync-design.md`

---

## File Structure

| File | Responsibility |
|---|---|
| `plugins/doc-sync/.claude-plugin/plugin.json` | Plugin manifest — name, version, description |
| `plugins/doc-sync/hooks/hooks.json` | Hook wiring — PostToolUse on Bash → discovery script |
| `plugins/doc-sync/hooks/discover-related-docs.sh` | Core discovery — detect commit, find related .md files, return candidates |
| `plugins/doc-sync/CLAUDE.md` | Analysis brain — tells Claude how to review candidates and propose edits |
| `plugins/doc-sync/install.sh` | Setup — installs git post-commit hook, verifies deps |
| `plugins/doc-sync/git-hooks/post-commit` | Post-commit hook template (tracked in repo, copied to .git/hooks/ by install.sh) |
| `.git/hooks/post-commit` | Safety net — headless discovery + Claude CLI + auto-commit (not tracked, installed from template) |

---

## Chunk 1: Plugin Scaffold + Discovery Script

### Task 1: Create plugin manifest

**Files:**
- Create: `plugins/doc-sync/.claude-plugin/plugin.json`

- [ ] **Step 1: Create plugin directory and manifest**

```json
{
  "name": "doc-sync",
  "version": "1.0.0",
  "description": "Discovers and proposes documentation updates after git commits. Finds .md files that reference changed code and flags them for review.",
  "author": {
    "name": "Colppy"
  }
}
```

- [ ] **Step 2: Verify manifest is valid JSON**

Run: `cat plugins/doc-sync/.claude-plugin/plugin.json | jq .`
Expected: Pretty-printed JSON with no errors.

- [ ] **Step 3: Commit**

```bash
git add plugins/doc-sync/.claude-plugin/plugin.json
git commit -m "feat(doc-sync): scaffold plugin manifest"
```

---

### Task 2: Write the discovery shell script

**Files:**
- Create: `plugins/doc-sync/hooks/discover-related-docs.sh`

This is the core logic. It reads PostToolUse stdin, detects `git commit`, discovers related `.md` files, and returns `additionalContext` via `hookSpecificOutput`.

- [ ] **Step 1: Create the script with commit detection gate**

```bash
#!/bin/bash
set -uo pipefail
# NOTE: not using set -e because this hook should fail silently on any error.
# All critical commands use explicit || guards instead.

# PostToolUse hook: detect git commits and discover related docs.
# Reads tool_input JSON from stdin. Exits silently for non-commit commands.

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Gate: only proceed if this was a git commit
if ! echo "$command" | grep -qE '\bgit\s+commit\b'; then
  exit 0
fi
```

- [ ] **Step 2: Test the gate logic**

Run from repo root:
```bash
echo '{"tool_input":{"command":"git status"}}' | bash plugins/doc-sync/hooks/discover-related-docs.sh
echo "Exit code: $?"
```
Expected: Exit code 0, no output (non-commit command skipped).

```bash
echo '{"tool_input":{"command":"git commit -m \"test\""}}' | bash plugins/doc-sync/hooks/discover-related-docs.sh
echo "Exit code: $?"
```
Expected: Exit code 0 (passes gate, but may error on git diff-tree since no real commit — that's fine for now).

- [ ] **Step 3: Add loop prevention checks**

Append after the gate:

```bash
# Loop prevention: skip doc-sync's own commits
commit_msg=$(git log -1 --pretty=%B 2>/dev/null || echo "")
if [[ "$commit_msg" == docs:* ]] || [[ "$commit_msg" == *"[skip-doc-sync]"* ]]; then
  exit 0
fi
```

- [ ] **Step 4: Add changed files extraction and code/doc split**

Append:

```bash
# Get changed files from the last commit
changed_files=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || echo "")
if [[ -z "$changed_files" ]]; then
  exit 0
fi

# Split: code files (trigger discovery) vs docs (already updated, exclude)
code_files=$(echo "$changed_files" | grep -v '\.md$' || true)
changed_docs=$(echo "$changed_files" | grep '\.md$' || true)

if [[ -z "$code_files" ]]; then
  exit 0  # Pure doc commit — nothing to check
fi
```

- [ ] **Step 5: Add discovery logic — grep for references + sibling/parent docs**

Append:

```bash
# Directories to exclude from search
EXCLUDE_DIRS="node_modules .venv ceo_assistant_env .git .playwright-cli"
exclude_args=""
for dir in $EXCLUDE_DIRS; do
  exclude_args="$exclude_args --exclude-dir=$dir"
done

candidates=""

while IFS= read -r file; do
  [[ -z "$file" ]] && continue

  base=$(basename "$file")
  dirpath=$(dirname "$file")

  # Search .md files for references to this filename or directory
  matches=$(grep -rl --include="*.md" $exclude_args \
    -e "$base" -e "$dirpath/" . 2>/dev/null || true)
  candidates="$candidates"$'\n'"$matches"

  # Check for sibling README.md
  if [[ -f "$dirpath/README.md" ]]; then
    candidates="$candidates"$'\n'"$dirpath/README.md"
  fi

  # Walk up for CLAUDE.md files
  walkdir="$dirpath"
  while [[ "$walkdir" != "." && "$walkdir" != "/" ]]; do
    if [[ -f "$walkdir/CLAUDE.md" ]]; then
      candidates="$candidates"$'\n'"$walkdir/CLAUDE.md"
    fi
    walkdir=$(dirname "$walkdir")
  done
done <<< "$code_files"

# Check memory files
memory_dir="$HOME/.claude/projects"
if [[ -d "$memory_dir" ]]; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    base=$(basename "$file")
    mem_matches=$(grep -rl --include="*.md" -e "$base" "$memory_dir"/*/memory/ 2>/dev/null || true)
    candidates="$candidates"$'\n'"$mem_matches"
  done <<< "$code_files"
fi
```

- [ ] **Step 6: Add deduplication, exclusion, and output**

Append:

```bash
# Deduplicate, normalize paths, remove blanks
candidates=$(echo "$candidates" | sed 's|^\./||' | sort -u | sed '/^$/d')

# Remove docs that were already modified in this commit
if [[ -n "$changed_docs" ]]; then
  while IFS= read -r doc; do
    [[ -z "$doc" ]] && continue
    candidates=$(echo "$candidates" | grep -v "^${doc}$" || true)
  done <<< "$changed_docs"
fi

# Remove blanks again after filtering
candidates=$(echo "$candidates" | sed '/^$/d')

# Cap at 20 candidates
candidates=$(echo "$candidates" | head -20)

if [[ -z "$candidates" ]]; then
  exit 0
fi

# Format candidate list with bullet points
candidate_list=""
while IFS= read -r doc; do
  [[ -z "$doc" ]] && continue
  candidate_list="$candidate_list"$'\n'"  - $doc"
done <<< "$candidates"

commit_sha=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
num_files=$(echo "$code_files" | wc -l | tr -d ' ')

# Build the message body
msg_body="DOC-SYNC: Commit $commit_sha changed $num_files code file(s). The following docs may need updates:
$candidate_list

Review each doc against the commit diff (git show HEAD). For each:
1. Read the doc and the relevant diff
2. If stale or inaccurate, propose specific edits
3. If still accurate, skip it

Present all proposed changes for user approval before editing."

# Output as hookSpecificOutput with additionalContext for PostToolUse
jq -n --arg msg "$msg_body" '{"hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":$msg}}'
```

- [ ] **Step 7: Make script executable**

Run: `chmod +x plugins/doc-sync/hooks/discover-related-docs.sh`

- [ ] **Step 8: Test full script with a real commit scenario**

Run: `bash -n plugins/doc-sync/hooks/discover-related-docs.sh`
Expected: No syntax errors.

Run a simulated test (from repo root, using the last real commit):
```bash
echo '{"tool_input":{"command":"git commit -m \"test\""}}' | bash plugins/doc-sync/hooks/discover-related-docs.sh
```
Expected: Either a JSON `systemMessage` with candidate docs, or no output (if the last commit was a docs-only commit). Inspect the output to verify candidates make sense.

- [ ] **Step 9: Commit**

```bash
git add plugins/doc-sync/hooks/discover-related-docs.sh
git commit -m "feat(doc-sync): add discovery shell script for related docs"
```

---

### Task 3: Wire the hook

**Files:**
- Create: `plugins/doc-sync/hooks/hooks.json`

- [ ] **Step 1: Create hooks.json**

```json
{
  "description": "Detects git commits and discovers .md files that may need updating",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/discover-related-docs.sh",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Validate JSON**

Run: `cat plugins/doc-sync/hooks/hooks.json | jq .`
Expected: Valid JSON, no errors.

- [ ] **Step 3: Commit**

```bash
git add plugins/doc-sync/hooks/hooks.json
git commit -m "feat(doc-sync): wire PostToolUse hook to discovery script"
```

---

## Chunk 2: Analysis Instructions + Git Hook

### Task 4: Write CLAUDE.md (analysis brain)

**Files:**
- Create: `plugins/doc-sync/CLAUDE.md`

- [ ] **Step 1: Create CLAUDE.md with analysis instructions**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add plugins/doc-sync/CLAUDE.md
git commit -m "feat(doc-sync): add CLAUDE.md analysis instructions"
```

---

### Task 5: Write the git post-commit hook (safety net)

**Files:**
- Create: `plugins/doc-sync/git-hooks/post-commit` (template, tracked in repo)

We store the template in the plugin directory (tracked by git). The install script copies it to `.git/hooks/`.

- [ ] **Step 1: Create the post-commit hook script**

```bash
#!/bin/bash
set -uo pipefail
# NOTE: not using set -e because this hook should fail silently on any error.
# All critical commands use explicit || guards instead.

# Safety net: discover stale docs and auto-update via Claude CLI.
# Skips if inside Claude Code (Layer 1 handles it) or if commit is a doc-sync.

# --- Loop prevention ---
commit_msg=$(git log -1 --pretty=%B 2>/dev/null || echo "")
if [[ "$commit_msg" == docs:* ]] || [[ "$commit_msg" == *"[skip-doc-sync]"* ]]; then
  exit 0
fi

# --- Skip if inside Claude Code session ---
if [[ -n "${CLAUDE_CODE_SESSION:-}" ]]; then
  exit 0
fi

# --- Check claude CLI is available ---
if ! command -v claude &>/dev/null; then
  exit 0  # Can't run without CLI, fail silently
fi

# --- Get changed files ---
changed_files=$(git diff-tree --no-commit-id --name-only -r HEAD 2>/dev/null || echo "")
code_files=$(echo "$changed_files" | grep -v '\.md$' || true)

if [[ -z "$code_files" ]]; then
  exit 0
fi

# --- Discovery ---
escape_grep_bre() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/[.*^$[\]]/\\&/g'; }
EXCLUDE_DIRS="node_modules .venv ceo_assistant_env .git .playwright-cli"
exclude_args=""
for dir in $EXCLUDE_DIRS; do
  exclude_args="$exclude_args --exclude-dir=$dir"
done

candidates=""
while IFS= read -r file; do
  [[ -z "$file" ]] && continue
  base=$(basename "$file")
  dirpath=$(dirname "$file")
  base_esc=$(escape_grep_bre "$base")
  dirpath_esc=$(escape_grep_bre "$dirpath/")

  matches=$(grep -rl --include="*.md" $exclude_args \
    -e "$base_esc" -e "$dirpath_esc" . 2>/dev/null || true)
  candidates="$candidates"$'\n'"$matches"

  if [[ -f "$dirpath/README.md" ]]; then
    candidates="$candidates"$'\n'"$dirpath/README.md"
  fi

  # Walk up for CLAUDE.md files
  walkdir="$dirpath"
  while [[ "$walkdir" != "." && "$walkdir" != "/" ]]; do
    if [[ -f "$walkdir/CLAUDE.md" ]]; then
      candidates="$candidates"$'\n'"$walkdir/CLAUDE.md"
    fi
    walkdir=$(dirname "$walkdir")
  done
done <<< "$code_files"

# Check memory files
memory_dir="$HOME/.claude/projects"
if [[ -d "$memory_dir" ]]; then
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    base=$(basename "$file")
    base_esc=$(escape_grep_bre "$base")
    mem_matches=$(grep -rl --include="*.md" -e "$base_esc" "$memory_dir"/*/memory/ 2>/dev/null || true)
    candidates="$candidates"$'\n'"$mem_matches"
  done <<< "$code_files"
fi

# Deduplicate and exclude already-changed docs
candidates=$(echo "$candidates" | sed 's|^\./||' | sort -u | sed '/^$/d')
changed_docs=$(echo "$changed_files" | grep '\.md$' || true)
if [[ -n "$changed_docs" ]]; then
  while IFS= read -r doc; do
    [[ -z "$doc" ]] && continue
    doc_esc=$(escape_grep_bre "$doc")
    candidates=$(echo "$candidates" | grep -v "^${doc_esc}$" || true)
  done <<< "$changed_docs"
fi
candidates=$(echo "$candidates" | sed '/^$/d' | head -20)

if [[ -z "$candidates" ]]; then
  exit 0
fi

# --- Invoke Claude CLI ---
# Use full diff (truncated at 8000 chars to limit token usage)
diff_content=$(git show HEAD | head -c 8000)
candidate_list=$(echo "$candidates")

output=$(claude --print "$(cat <<EOF
A git commit just landed with these changes:

$diff_content

The following .md docs may reference the changed files:
$candidate_list

For each doc, read it and check if anything is now stale or inaccurate.

If a doc needs updating, output ONLY:
--- FILE: path/to/doc.md
[complete updated file content]
--- END

If no docs need updating, output exactly: NO_UPDATES_NEEDED
EOF
)" 2>/dev/null) || exit 0

# --- Apply updates ---
if echo "$output" | grep -q "NO_UPDATES_NEEDED"; then
  exit 0
fi

updated=false
# Escape file_path for sed regex: \ . * ^ $ [ ] and / (delimiter)
escape_sed_pattern() { printf '%s' "$1" | sed 's/\\/\\\\/g; s/[.*^$[\]]/\\&/g; s|/|\\/|g'; }
while IFS= read -r file_path; do
  [[ -z "$file_path" ]] && continue
  escaped_path=$(escape_sed_pattern "$file_path")
  content=$(echo "$output" | sed -n "/^--- FILE: ${escaped_path}$/,/^--- END$/p" \
    | sed '1d;$d')
  if [[ -n "$content" ]]; then
    echo "$content" > "$file_path"
    git add "$file_path"
    updated=true
  fi
done <<< "$(echo "$output" | grep '^--- FILE: ' | sed 's/^--- FILE: //')"

if [[ "$updated" == true ]]; then
  short_sha=$(git rev-parse --short HEAD)
  git commit -m "docs: auto-sync documentation after ${short_sha} [skip-doc-sync]"
fi
```

- [ ] **Step 2: Make executable**

Run: `chmod +x plugins/doc-sync/git-hooks/post-commit`

- [ ] **Step 3: Validate syntax**

Run: `bash -n plugins/doc-sync/git-hooks/post-commit`
Expected: No output (no syntax errors).

- [ ] **Step 4: Test the file-extraction parser**

Create a mock output and verify the parser extracts content correctly:

```bash
test_output=$(cat <<'TESTEOF'
--- FILE: test-doc.md
# Updated Doc
Some content here
--- END
--- FILE: another/readme.md
# Another
More content
--- END
TESTEOF
)

# Verify file list extraction
echo "$test_output" | grep '^--- FILE: ' | sed 's/^--- FILE: //'
# Expected output:
# test-doc.md
# another/readme.md

# Verify content extraction for first file
echo "$test_output" | sed -n '/^--- FILE: test-doc.md$/,/^--- END$/p' | sed '1d;$d'
# Expected output:
# # Updated Doc
# Some content here
```

- [ ] **Step 5: Commit**

```bash
git add plugins/doc-sync/git-hooks/post-commit
git commit -m "feat(doc-sync): add git post-commit hook template (safety net)"
```

---

### Task 6: Write install script

**Files:**
- Create: `plugins/doc-sync/install.sh`

- [ ] **Step 1: Create install.sh**

```bash
#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
HOOK_SRC="$SCRIPT_DIR/git-hooks/post-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/post-commit"

echo "Doc Sync — Installing git post-commit hook"

# Check prerequisites
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found. Discovery hook needs jq. Install with: brew install jq"
fi

if ! command -v claude &>/dev/null; then
  echo "WARNING: claude CLI not found. Layer 2 (safety net) won't work without it."
  echo "  Layer 1 (Claude Code plugin) will still work fine."
fi

# Make discovery script executable
chmod +x "$SCRIPT_DIR/hooks/discover-related-docs.sh"

# Install post-commit hook
if [[ -f "$HOOK_DST" ]]; then
  echo "WARNING: $HOOK_DST already exists."
  echo "  Existing content:"
  head -3 "$HOOK_DST"
  echo "  ..."
  read -p "Overwrite? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Skipped post-commit hook installation."
    echo "To install manually: cp $HOOK_SRC $HOOK_DST"
    exit 0
  fi
fi

cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

echo "Done. Post-commit hook installed at $HOOK_DST"
echo ""
echo "Layer 1 (Claude Code plugin): Active when plugin is enabled"
echo "Layer 2 (Git safety net):     Active for all commits outside Claude Code"
```

- [ ] **Step 2: Make executable**

Run: `chmod +x plugins/doc-sync/install.sh`

- [ ] **Step 3: Validate syntax**

Run: `bash -n plugins/doc-sync/install.sh`
Expected: No errors.

- [ ] **Step 4: Commit**

```bash
git add plugins/doc-sync/install.sh
git commit -m "feat(doc-sync): add install script for git post-commit hook"
```

---

## Chunk 3: Integration Testing + Plugin Activation

### Task 7: Enable plugin and test end-to-end

**Files:**
- Possibly modify: `.claude/settings.json` (only if auto-discovery fails)

- [ ] **Step 1: Verify plugin auto-discovery**

Existing local plugins (e.g., `colppy-architecture-reviewer`, `colppy-revenue`) are NOT listed in `.claude/settings.json` `enabledPlugins` — yet their hooks work. This means local plugins in `plugins/` are auto-discovered.

Verify this: check that the doc-sync plugin is detected by Claude Code without any settings changes. If auto-discovery does not pick it up, investigate how the existing local plugins are registered and follow the same mechanism.

Do NOT modify `.claude/settings.json` unless auto-discovery fails.

- [ ] **Step 2: Run the install script to set up git hook**

Run: `bash plugins/doc-sync/install.sh`
Expected: "Done. Post-commit hook installed" message. Warnings about missing `claude` CLI are OK if not installed globally.

- [ ] **Step 3: Validate plugin structure matches existing plugins**

Run:
```bash
ls -la plugins/doc-sync/.claude-plugin/plugin.json
ls -la plugins/doc-sync/hooks/hooks.json
ls -la plugins/doc-sync/hooks/discover-related-docs.sh
ls -la plugins/doc-sync/CLAUDE.md
ls -la plugins/doc-sync/install.sh
ls -la plugins/doc-sync/git-hooks/post-commit
```
Expected: All files exist, shell scripts are executable.

- [ ] **Step 4: Test Layer 1 manually — make a trivial code change and commit**

Make a small change to a tracked code file (e.g., add a comment to a script), commit it, and observe:
- The PostToolUse hook should fire
- The discovery script should run and output a systemMessage (or nothing if no docs reference that file)
- If candidates are found, Claude should propose edits

This is a manual smoke test inside Claude Code.

- [ ] **Step 5: Test Layer 2 manually — commit from terminal**

Open a separate terminal (not Claude Code). Make a trivial change, commit it.
- The post-commit hook should run
- If `claude` CLI is available and docs are stale, a follow-up commit appears
- If no `claude` CLI, the hook exits silently

- [ ] **Step 6: Test loop prevention — verify doc-sync commits don't re-trigger**

After Layer 2 creates a `docs: auto-sync...` commit, verify that the post-commit hook exits immediately (check by adding a temporary `echo "HOOK FIRED"` at the top of the hook).

- [ ] **Step 7: Final commit (if any settings changes were needed)**

Only if Step 1 required settings changes:
```bash
git add .claude/settings.json
git commit -m "feat(doc-sync): enable plugin in settings"
```

If auto-discovery worked, no commit needed for this step.
