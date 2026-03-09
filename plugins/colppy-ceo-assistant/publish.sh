#!/bin/bash
# Build colppy-ceo-assistant plugin zip for Claude Cowork upload.
# Output: ../../tools/outputs/colppy-ceo-assistant-plugin-full.zip
#
# Usage:
#   ./publish.sh           # Zip only — use current data files as-is
#
# Monday update workflow:
#   1. Go to Financial Analyst Cowork session and provide portfolio screenshots
#   2. Claude updates outputs/financial-advisor/references/ and history/ in that session
#   3. Copy updated files here:
#      cp <session-dir>/outputs/financial-advisor/references/*.md data/portfolio-alert/references/
#      cp <session-dir>/outputs/financial-advisor/history/transactions.md data/portfolio-alert/history/
#   4. Run this script
#   5. Upload the new ZIP to Cowork

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/tools/outputs"
ZIP_NAME="colppy-ceo-assistant-plugin-full.zip"

mkdir -p "$OUTPUT_DIR"

echo "Building plugin zip..."
cd "$SCRIPT_DIR"
zip -r "$OUTPUT_DIR/$ZIP_NAME" . \
  -x "*.git*" \
  -x "./publish.sh" \
  -x "*.DS_Store" \
  -x "./data/portfolio-alert/alerts/*" \
  -x ".gitkeep"

echo "Created: $OUTPUT_DIR/$ZIP_NAME"
echo ""
echo "Next step: upload $ZIP_NAME to Cowork via + > Plugins > Add plugin"
