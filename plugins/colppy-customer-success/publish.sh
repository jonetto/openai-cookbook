#!/bin/bash
# Build colppy-customer-success plugin zip for Claude Cowork upload.
# Output: ../../tools/outputs/colppy-customer-success-plugin-full.zip

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGINS_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$REPO_ROOT/tools/outputs"
ZIP_NAME="colppy-customer-success-plugin-full.zip"

mkdir -p "$OUTPUT_DIR"

echo "Building plugin zip..."
cd "$SCRIPT_DIR"
zip -r "$OUTPUT_DIR/$ZIP_NAME" . \
  -x "*.git*" \
  -x "./publish.sh" \
  -x "*.DS_Store" \
  -x "./node_modules/*" \
  -x "./mcp/node_modules/*"
echo "Created: $OUTPUT_DIR/$ZIP_NAME"
