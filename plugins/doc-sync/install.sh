#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel)"
HOOK_SRC="$SCRIPT_DIR/git-hooks/post-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/post-commit"

echo "Doc Sync v1.0.1 — Installing git post-commit hook"

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
