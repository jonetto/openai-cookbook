#!/bin/bash
set -euo pipefail

# PostToolUse hook: detect edits to docs/colppy-platform/*.md
# and flag that the architecture reviewer baseline may be stale.

input=$(cat)
file_path=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [ -z "$file_path" ]; then
  exit 0
fi

# Check if the edited file is a platform doc
if [[ "$file_path" == *"docs/colppy-platform/"* && "$file_path" == *".md" ]]; then
  echo '{"systemMessage": "Platform docs changed. The architecture reviewer system baseline (plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md) may now be stale. It will auto-refresh on next /review-architecture invocation."}'
fi

exit 0
