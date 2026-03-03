# MCP Servers (Colppy Customer Success)

This folder contains the MCP server implementations used by the plugin.

## Servers

- `mcp-intercom-server.js`
  - Intercom export/search/classification support
- `mcp-feature-upvote-playwright-server.js`
  - Feature Upvote integration through Playwright automation
  - Tools:
    - `get_feature_upvote_board_summary`
    - `list_feature_requests` (Export CSV first, pagination fallback)
    - `create_feature_request`

## Feature Upvote architecture choice

Feature Upvote does not expose a public general-use REST API for this account.
The account Developer page states API access is intended primarily for Zapier.

Because of this, the integration is implemented with browser automation.

## Headless mode (no local Chrome window)

The Feature Upvote MCP server is configured to run headless by default:

- `FEATURE_UPVOTE_HEADLESS=true`

To improve reliability under anti-bot checks, the server uses:

- browser launch arg: `--disable-blink-features=AutomationControlled`
- explicit user-agent/locale/timezone context
- persisted storage state (`FEATURE_UPVOTE_STORAGE_STATE_PATH`) so calls can reuse session cookies
- retry + challenge-clear waits on navigation

This mirrors a backend scraper pattern where the browser is not opened visibly.

Full Feature Upvote MCP guide:
- `../docs/README_FEATURE_UPVOTE_MCP.md`

## Environment variables

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
- `FEATURE_UPVOTE_LOCALE`
- `FEATURE_UPVOTE_TIMEZONE`

## Bootstrap/fallback flow

If Cloudflare temporarily challenges headless login repeatedly:

1. Run one request with `FEATURE_UPVOTE_HEADLESS=false` to refresh session.
2. Keep `FEATURE_UPVOTE_PERSIST_STORAGE_STATE=true`.
3. Switch back to `FEATURE_UPVOTE_HEADLESS=true`.

## Smoke test (local)

From this directory:

```bash
FEATURE_UPVOTE_EMAIL='...' \
FEATURE_UPVOTE_PASSWORD='...' \
FEATURE_UPVOTE_HEADLESS='true' \
node --input-type=module - <<'NODE'
import { FeatureUpvotePlaywrightMCPServer } from './mcp-feature-upvote-playwright-server.js';
const server = new FeatureUpvotePlaywrightMCPServer();
const parse = (resp) => JSON.parse(resp.content?.[0]?.text || '{}');
const summary = parse(await server.getBoardSummary({ force_refresh: true }));
const list = parse(await server.listFeatureRequests({ status: 'all', limit: 3, max_pages: 1, force_refresh: true }));
console.log(summary.board?.board_ref, list.total_returned);
NODE
```
