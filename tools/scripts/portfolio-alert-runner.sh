#!/bin/bash
# portfolio-alert-runner.sh — Unattended portfolio alert via Claude Code CLI
#
# Runs the portfolio-alert blueprint in headless mode (claude -p).
# Designed to be triggered by macOS launchd twice daily (10am + 6pm ART).
# The blueprint scans Gmail, web news, and earnings, then sends a Slack DM.
#
# Usage:
#   bash portfolio-alert-runner.sh          # normal run
#   bash portfolio-alert-runner.sh --force  # skip weekday check
#
# Exit codes:
#   0 = success (or clean skip on weekends)
#   1 = claude binary not found
#   2 = blueprint file not found
#   3 = working directory not found
#   4 = claude execution failed

set -euo pipefail

# ─── Configuration ────────────────────────────────────────────────────────────

# Cowork session directory where portfolio data lives.
# Update this if the "Financial Analyst" Cowork session is recreated.
PORTFOLIO_DIR="$HOME/Library/Application Support/Claude/local-agent-mode-sessions/2de0c85a-a7ac-4c9e-91c1-bd8362c29e4f/edc3f46d-20a2-4e0f-91ea-29281346908f/local_2a66053c-635e-4708-ac3a-294fdcbd0904"

# Blueprint file (relative to PORTFOLIO_DIR)
BLUEPRINT_PATH=".claude/commands/portfolio-alert.md"

# Log directory
LOG_DIR="$HOME/Library/Logs/portfolio-alert"

# Max agentic turns (safety valve — prevents runaway loops)
MAX_TURNS=30

# ─── Clear Nested Session Detection ───────────────────────────────────────────
# When testing from inside Claude Code, unset this to avoid "nested session" error.
# In production (launchd), this variable won't exist anyway.
unset CLAUDECODE 2>/dev/null || true

# ─── Weekday Check ────────────────────────────────────────────────────────────

if [[ "${1:-}" != "--force" ]]; then
    DAY_OF_WEEK=$(date +%u)  # 1=Monday, 7=Sunday
    if (( DAY_OF_WEEK > 5 )); then
        echo "$(date '+%Y-%m-%d %H:%M:%S') — Weekend (day $DAY_OF_WEEK), skipping."
        exit 0
    fi
fi

# ─── Find Claude Binary ──────────────────────────────────────────────────────
# The binary path includes a version number that changes on updates:
#   ~/Library/Application Support/Claude/claude-code/<VERSION>/claude
# We find the latest version dynamically.

CLAUDE_CODE_DIR="$HOME/Library/Application Support/Claude/claude-code"
CLAUDE_BIN=$(find "$CLAUDE_CODE_DIR" -name "claude" -type f 2>/dev/null | sort -V | tail -1)

if [[ -z "$CLAUDE_BIN" ]]; then
    echo "ERROR: Claude Code binary not found in $CLAUDE_CODE_DIR" >&2
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') — Using Claude binary: $CLAUDE_BIN"

# ─── Validate Paths ──────────────────────────────────────────────────────────

if [[ ! -d "$PORTFOLIO_DIR" ]]; then
    echo "ERROR: Portfolio directory not found: $PORTFOLIO_DIR" >&2
    exit 3
fi

BLUEPRINT_FULL="$PORTFOLIO_DIR/$BLUEPRINT_PATH"
if [[ ! -f "$BLUEPRINT_FULL" ]]; then
    echo "ERROR: Blueprint file not found: $BLUEPRINT_FULL" >&2
    exit 2
fi

# ─── Prepare Log ──────────────────────────────────────────────────────────────

mkdir -p "$LOG_DIR"
TIMESTAMP=$(date '+%Y-%m-%d-%Hh')
RUN_LOG="$LOG_DIR/$TIMESTAMP.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Portfolio alert starting" | tee -a "$RUN_LOG"
echo "Working directory: $PORTFOLIO_DIR" | tee -a "$RUN_LOG"

# ─── Build Prompt ─────────────────────────────────────────────────────────────
# Read the blueprint and wrap it with an instruction to execute it.

BLUEPRINT_CONTENT=$(cat "$BLUEPRINT_FULL")

PROMPT="You are running as an unattended scheduled task. Execute the following portfolio alert blueprint exactly as written. This is a non-interactive run — you cannot ask the user questions. If today is Monday, skip the screenshot request and proceed with existing portfolio data.

IMPORTANT: The Slack DM delivery (Step 6) is MANDATORY. Do not skip it.

--- BEGIN BLUEPRINT ---
$BLUEPRINT_CONTENT
--- END BLUEPRINT ---"

# ─── Allowed Tools ────────────────────────────────────────────────────────────
# Whitelist only the tools the blueprint needs. No Bash = smaller blast radius.

ALLOWED_TOOLS=(
    "Read"
    "Write"
    "Edit"
    "Glob"
    "Grep"
    "WebSearch"
    "WebFetch"
    "mcp__claude_ai_Gmail__gmail_search_messages"
    "mcp__claude_ai_Gmail__gmail_read_message"
    "mcp__claude_ai_Gmail__gmail_read_thread"
    "mcp__claude_ai_Slack__slack_send_message"
)

# Join with commas for CLI flag
TOOLS_CSV=$(IFS=,; echo "${ALLOWED_TOOLS[*]}")

# ─── Execute ──────────────────────────────────────────────────────────────────

echo "$(date '+%Y-%m-%d %H:%M:%S') — Invoking claude -p with max_turns=$MAX_TURNS" | tee -a "$RUN_LOG"

cd "$PORTFOLIO_DIR"

set +e  # Don't exit on claude failure — we want to log the exit code
"$CLAUDE_BIN" -p "$PROMPT" \
    --allowedTools "$TOOLS_CSV" \
    --max-turns "$MAX_TURNS" \
    --output-format text \
    --verbose \
    2>&1 | tee -a "$RUN_LOG"

CLAUDE_EXIT=$?
set -e

# ─── Report ───────────────────────────────────────────────────────────────────

if [[ $CLAUDE_EXIT -eq 0 ]]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Portfolio alert completed successfully (exit $CLAUDE_EXIT)" | tee -a "$RUN_LOG"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') — Portfolio alert FAILED (exit $CLAUDE_EXIT)" | tee -a "$RUN_LOG"
    exit 4
fi
