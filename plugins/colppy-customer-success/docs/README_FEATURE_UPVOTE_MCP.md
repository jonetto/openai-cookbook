# Feature Upvote MCP (Playwright) Guide

This document explains what the Feature Upvote MCP does, how it works, and how to use it safely.

## Scope

Server implementation:
- `plugins/colppy-customer-success/mcp/mcp-feature-upvote-playwright-server.js`

MCP tools:
- `get_feature_upvote_board_summary`
- `list_feature_requests`
- `create_feature_request`

## Why Playwright (not direct API)

For this account, Feature Upvote does not expose a public general-use REST API.
The account developer page indicates API access is intended primarily for Zapier.

Because of that, this MCP uses Playwright browser automation against:
- Feature Upvote dashboard (moderation/admin pages)
- Feature Upvote board form (live ideas portal)

## What Each Tool Does

`get_feature_upvote_board_summary`
- Logs into dashboard
- Reads board-level counters (suggestions/comments/upvotes/pending approvals)
- Returns selected board + list of boards
- Cache-first, with `force_refresh` to bypass cache

`list_feature_requests`
- Logs into moderation dashboard for a board
- Applies status/query/tag filters
- Uses dashboard Export CSV first for full coverage
- Falls back to pagination scraping if export is blocked
- Returns normalized request rows and metadata
- Cache-first, with `force_refresh` to bypass cache

`create_feature_request`
- Opens live board form (`/suggestions/add`)
- Fills title/description/name/email/consent
- Supports `dry_run=true` (validate/fill but do not submit)
- On real submit, posts suggestion through the public board form

## Important Runtime Behavior

Cache behavior:
- Reads are cache-first (TTL from `FEATURE_UPVOTE_CACHE_TTL_MINUTES`, default `30`)
- `force_refresh=true` forces live fetch

Headless behavior:
- Default is headless (`FEATURE_UPVOTE_HEADLESS=true`)
- No local visible Chrome window in normal backend mode

Session persistence:
- Reuses/saves Playwright storage state at:
  `FEATURE_UPVOTE_STORAGE_STATE_PATH` (default `mcp/.cache/feature-upvote/feature-upvote-storage-state.json`)
- Controlled by `FEATURE_UPVOTE_PERSIST_STORAGE_STATE` (default `true`)

Cloudflare handling:
- Robust navigation retries + challenge waits are built-in
- If persistent challenge happens, do one bootstrap run with:
  - `FEATURE_UPVOTE_HEADLESS=false`
  - then switch back to `FEATURE_UPVOTE_HEADLESS=true`

## Required and Optional Environment Variables

Required:
- `FEATURE_UPVOTE_EMAIL`
- `FEATURE_UPVOTE_PASSWORD`

Recommended:
- `FEATURE_UPVOTE_HEADLESS=true`
- `FEATURE_UPVOTE_CACHE_TTL_MINUTES=30`
- `FEATURE_UPVOTE_PERSIST_STORAGE_STATE=true`

Optional:
- `FEATURE_UPVOTE_BOARD_URL` (default: `https://ideas.colppy.com`)
- `FEATURE_UPVOTE_SIGNIN_URL` (default: `https://app.featureupvote.com/signin`)
- `FEATURE_UPVOTE_DASHBOARD_URL` (default: `https://app.featureupvote.com/dashboard/`)
- `FEATURE_UPVOTE_STORAGE_STATE_PATH`
- `FEATURE_UPVOTE_USER_AGENT`
- `FEATURE_UPVOTE_LOCALE` (default: `en-US`)
- `FEATURE_UPVOTE_TIMEZONE` (default: `America/Argentina/Buenos_Aires`)

## Typical Workflows

Get latest moderation feedback:
1. Call `list_feature_requests` with:
   - `status: "all"`
   - `limit: 2000`
   - `force_refresh: true` (when needed)
2. Use `query` and `tag` for narrower pulls.

Get board summary:
1. Call `get_feature_upvote_board_summary`
2. Optionally pass `board_ref` if you want a specific board

Create suggestion safely:
1. Call `create_feature_request` with `dry_run: true`
2. Verify returned payload
3. Call again with `dry_run: false` to submit

## LLM Triage Flow (Feature Upvote CSV)

If you want "real ideas" vs support complaints classification:

1. Prepare LLM input from Feature Upvote CSV:
```bash
cd plugins/colppy-customer-success
node scripts/feature_upvote_prepare_llm_input.mjs \
  --csv docs/feature_upvote_export_all_YYYY-MM-DD.csv \
  --from 2025-09-01 \
  --to 2026-02-28 \
  --cache-out docs/feature_upvote_cache_sep2025_feb2026.json \
  --results-out docs/feature_upvote_scan_sep2025_feb2026.json
```

2. Run classifier:
```bash
node scripts/llm_classify.mjs \
  --cache docs/feature_upvote_cache_sep2025_feb2026.json \
  --results docs/feature_upvote_scan_sep2025_feb2026.json \
  --topic skills/feature-upvote-idea-triage/topic.json \
  --output docs/feature_upvote_llm_classified_sep2025_feb2026.json \
  --report docs/feature_upvote_llm_report_sep2025_feb2026.md \
  --review docs/feature_upvote_llm_review_sep2025_feb2026.json \
  --model gpt-4o-mini
```

3. Split into final artifacts:
```bash
node scripts/feature_upvote_apply_llm_labels.mjs \
  --cache docs/feature_upvote_cache_sep2025_feb2026.json \
  --classified docs/feature_upvote_llm_classified_sep2025_feb2026.json \
  --real-out docs/feature_upvote_real_ideas_sep2025_feb2026_llm.csv \
  --complaints-out docs/feature_upvote_support_complaints_sep2025_feb2026_llm.csv \
  --summary-out docs/feature_upvote_ideas_summary_sep2025_feb2026_llm.md
```

## Operational Notes

- This MCP is intentionally backend-oriented and headless by default.
- It is designed to mimic the same "no visible browser" strategy used in bank-feed automation.
- Data extraction prefers CSV export to avoid missing items from UI pagination.

## Troubleshooting

`Missing credentials`:
- Set `FEATURE_UPVOTE_EMAIL` and `FEATURE_UPVOTE_PASSWORD`.

`Persistent Cloudflare challenge`:
- Temporarily run with `FEATURE_UPVOTE_HEADLESS=false` once to refresh session state.

`Partial/empty results in UI crawl mode`:
- Re-run with `force_refresh=true`.
- Confirm Export CSV is available on moderation page (the server already prefers it).

`Form submit issues`:
- Run `create_feature_request` with `dry_run=true` to validate fields before posting.
