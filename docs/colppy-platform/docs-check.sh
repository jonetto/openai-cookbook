#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_FILE="$ROOT_DIR/canonical-counts.md"
FAILURES=0

fail() {
  echo "[FAIL] $1"
  FAILURES=$((FAILURES + 1))
}

echo "[1/4] Checking local Markdown links..."
while IFS= read -r file; do
  while IFS= read -r link; do
    target="$(printf '%s' "$link" | sed -E 's/.*\(([^)]+)\).*/\1/')"
    case "$target" in
      http*|mailto:*|\#*|/*)
        continue
        ;;
    esac

    target_no_anchor="${target%%#*}"
    target_no_query="${target_no_anchor%%\?*}"

    if [[ "$target_no_query" == *.md ]]; then
      candidate="$(cd "$(dirname "$file")" && pwd)/$target_no_query"
      if [[ ! -f "$candidate" ]]; then
        fail "Missing link target: $file -> $target"
      fi
    fi
  done < <(rg -o '\[[^]]+\]\(([^)]+)\)' "$file" || true)
done < <(find "$ROOT_DIR" -maxdepth 1 -type f -name '*.md' | sort)

echo "[2/4] Checking Last updated footers..."
while IFS= read -r missing; do
  [[ -z "$missing" ]] && continue
  fail "Missing Last updated footer: $missing"
done < <(grep -L -E '^\*Last updated: [0-9]{4}-[0-9]{2}-[0-9]{2}\*$' "$ROOT_DIR"/*.md || true)

echo "[3/4] Checking stale count phrases..."
declare -a STALE_PATTERNS=(
  '36\+ Provisiones'
  '36\+ business modules'
  'AWS Lambda functions: 15'
  'all 31 provisions use `1_0_0_0/`'
)

for pattern in "${STALE_PATTERNS[@]}"; do
  if rg -n "$pattern" "$ROOT_DIR"/*.md >/tmp/colppy_docs_check_stale.out 2>/dev/null; then
    fail "Stale phrase found for pattern: $pattern"
    cat /tmp/colppy_docs_check_stale.out
  fi
done

echo "[4/4] Checking canonical counts table..."
declare -a REQUIRED_CANONICAL_ROWS=(
  '^\| Total repositories \| 108 \|'
  '^\| Runtime core repos \| 9 \|'
  '^\| MFE repos \| 8 \|'
  '^\| MFE repos mounted in `app_root` \| 2 \|'
  '^\| Provisiones top-level folders \| 32 \|'
  '^\| Business Provisiones \| 31 \|'
  '^\| Lambda repos \(total\) \| 20 \|'
  '^\| MySQL tables in shared schema \| 207 \|'
)

for pattern in "${REQUIRED_CANONICAL_ROWS[@]}"; do
  if ! rg -q "$pattern" "$CANONICAL_FILE"; then
    fail "Canonical counts row missing: $pattern"
  fi
done

if [[ "$FAILURES" -gt 0 ]]; then
  echo "docs-check: $FAILURES failure(s)"
  exit 1
fi

echo "docs-check: OK"
