# Doc Sync — Auto-Update Documentation on Commit

**Date**: 2026-03-10
**Status**: Approved

## Problem

Documentation drifts from code. Files get renamed, APIs change, directories are restructured — but the READMEs, CLAUDE.md files, memory files, and guides that reference them go stale silently.

## Solution

Two-layer system that discovers and updates stale documentation after every commit.

## Architecture

```
Layer 1: Claude Code Plugin (interactive, proposes for review)
Layer 2: Git post-commit hook (safety net, auto-commits updates)
```

### Layer 1: Claude Code Plugin (`doc-sync`)

A PostToolUse hook on Bash that fires after `git commit`:

1. **Shell discovery** (`discover-related-docs.sh`):
   - Extracts changed files from the commit via `git diff-tree`
   - Splits into code files vs changed docs
   - Greps all `.md` files for references to changed files (by filename, path segments, directory)
   - Checks for sibling README.md and parent CLAUDE.md files
   - Checks memory files for references
   - Deduplicates and excludes docs already modified in the commit
   - Returns candidate list as `additionalContext` (via PostToolUse `hookSpecificOutput`)

2. **Claude analysis** (guided by CLAUDE.md):
   - Reads the diff (`git show HEAD`)
   - Reads each candidate doc
   - Determines if the doc is now stale or inaccurate
   - Proposes specific edits for user approval
   - Never auto-edits — always waits for user review

### Layer 2: Git Post-Commit Hook (safety net)

Fires after every commit made outside Claude Code:

1. Same discovery logic as Layer 1
2. Invokes `claude --print` headlessly with the diff and candidate list
3. Parses output for file edits
4. Creates a follow-up commit: `docs: auto-sync documentation after <sha> [skip-doc-sync]`

### Loop Prevention

| Scenario | Prevention |
|---|---|
| Doc-sync commit triggers another doc-sync | Commit msg contains `[skip-doc-sync]` — both layers skip |
| Layer 1 + Layer 2 both fire on same commit | Layer 2 checks `CLAUDE_CODE_SESSION` env var — skips |
| User manually commits docs with `docs:` prefix | Both layers skip `docs:*` prefixed messages |
| Pure doc commit (only .md changes) | No code files changed — discovery exits silently |

### Performance Guardrails

- Discovery grep excludes: `node_modules/`, `.venv/`, `ceo_assistant_env/`, `.git/`
- Candidate cap: max 20 docs per analysis
- Shell hook timeout: 15 seconds
- Short-circuit: commits with only `.md` files skip entirely

### Staleness Rules

| Change type | Doc update needed |
|---|---|
| File renamed/moved | Yes — update path references |
| Function/API signature changed | Yes — update usage examples |
| New file added to documented directory | Maybe — if the README lists files |
| Behavior change | Yes — if doc describes old behavior |
| Refactoring (same behavior) | No — unless path references changed |
| Config/env changes | Yes — if docs reference old config |

## File Inventory

| File | Purpose |
|---|---|
| `plugins/doc-sync/.claude-plugin/plugin.json` | Plugin manifest |
| `plugins/doc-sync/hooks/hooks.json` | PostToolUse hook definition |
| `plugins/doc-sync/hooks/discover-related-docs.sh` | Discovery logic |
| `plugins/doc-sync/CLAUDE.md` | Analysis instructions for Claude |
| `plugins/doc-sync/install.sh` | Installs the git post-commit hook |
| `plugins/doc-sync/git-hooks/post-commit` | Post-commit hook template (tracked in repo) |
| `.git/hooks/post-commit` | Safety net layer (installed from template, not tracked by git) |

## Scope of Documentation Covered

- Plugin READMEs and CLAUDE.md files (`plugins/*/`)
- Platform/architecture docs (`docs/colppy-platform/`)
- Tool and script READMEs (`tools/*/README.md`)
- Auto-memory files (`~/.claude/projects/*/memory/*.md`)
- Any `.md` file in the repo that references changed code
