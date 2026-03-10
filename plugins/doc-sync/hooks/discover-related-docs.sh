#!/bin/bash
set -uo pipefail
# NOTE: not using set -e because this hook should fail silently on any error.
# All critical commands use explicit || guards instead.

# PostToolUse hook: detect git commits and discover related docs.
# Reads tool_input JSON from stdin. Exits silently for non-commit commands.

# Escape string for use as literal in grep BRE (avoids . * etc. matching as regex)
# BRE special chars: . * ^ $ [ ] \ — must escape these for literal match.
# In BRE, ( ) | { } ? + are LITERAL by default; escaping them would make them special (wrong).
escape_grep_bre() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/[.*^$[\]]/\\&/g'
}

input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Gate: only proceed if this was a git commit (not anchored — must match chained commands)
if ! echo "$command" | grep -qE '\bgit\s+commit\b'; then
  exit 0
fi

# Loop prevention: skip doc-sync's own commits
commit_msg=$(git log -1 --pretty=%B 2>/dev/null || echo "")
if [[ "$commit_msg" == docs:* ]] || [[ "$commit_msg" == *"[skip-doc-sync]"* ]]; then
  exit 0
fi

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

# Directories to exclude from search
EXCLUDE_DIRS="node_modules .venv ceo_assistant_env .git .playwright-cli .claude"
exclude_args=()
for dir in $EXCLUDE_DIRS; do
  exclude_args+=("--exclude-dir=$dir")
done

candidates=""

while IFS= read -r file; do
  [[ -z "$file" ]] && continue

  base=$(basename "$file")
  dirpath=$(dirname "$file")
  base_esc=$(escape_grep_bre "$base")
  dirpath_esc=$(escape_grep_bre "$dirpath/")

  # Search .md files for references to this filename or directory
  matches=$(grep -rl --include="*.md" "${exclude_args[@]}" \
    -e "$base_esc" -e "$dirpath_esc" . 2>/dev/null || true)
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
    base_esc=$(escape_grep_bre "$base")
    mem_matches=$(grep -rl --include="*.md" -e "$base_esc" "$memory_dir"/*/memory/ 2>/dev/null || true)
    candidates="$candidates"$'\n'"$mem_matches"
  done <<< "$code_files"
fi

# Deduplicate, normalize paths, remove blanks
candidates=$(echo "$candidates" | sed 's|^\./||' | sort -u | sed '/^$/d')

# Remove docs that were already modified in this commit
if [[ -n "$changed_docs" ]]; then
  while IFS= read -r doc; do
    [[ -z "$doc" ]] && continue
    doc_esc=$(escape_grep_bre "$doc")
    candidates=$(echo "$candidates" | grep -v "^${doc_esc}$" || true)
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
jq -n --arg msg "$msg_body" '{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": $msg
  }
}' || exit 0
