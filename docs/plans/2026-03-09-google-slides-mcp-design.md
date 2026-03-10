# Google Slides MCP Server — Design

**Date:** 2026-03-09
**Status:** Approved
**Location:** `tools/scripts/google-slides/`

## Problem

Reading Google Slides presentations (e.g., MBR decks) requires manual browser navigation or fragile scraping. We need a reusable MCP tool that takes a URL and extracts all content (text, tables, charts).

## Constraints

- No Google Cloud Console access — cannot create OAuth client credentials or service accounts
- Auth limited to Google Workspace login as jonetto@colppy.com
- Read-only scope

## Approach: Export URLs via Playwright Session

Playwright authenticates to Google once (stores session cookies). The MCP server uses those cookies to fetch Google Slides export URLs (PDF) without needing the Slides API or GCP credentials.

## Architecture

```
Claude ──stdio──▶ MCP Server (Node.js + Playwright)
                  tools/scripts/google-slides/mcp-google-slides-server.js

                  1. Playwright authenticates to Google (one-time, stores cookies)
                  2. Uses cookies to fetch /export/pdf URL
                  3. Saves PDF locally to cache/
                  4. Claude reads PDF with Read tool (text + visual charts)
```

## MCP Tools

| Tool | Input | Output |
|------|-------|--------|
| `google_slides_authenticate` | — | Opens browser for Google login. Stores session to `google-session.json`. One-time setup. |
| `google_slides_read` | `url` (presentation URL or ID) | Downloads PDF export using stored cookies. Saves to `cache/`. Returns file path + slide count. |
| `google_slides_screenshot` | `url`, `slide_number` | Opens presentation in Playwright, navigates to slide, screenshots it. Returns base64 PNG. Fallback for charts needing higher-res vision. |

### URL Parsing

All tools accept any Google Slides URL format:
- `https://docs.google.com/presentation/d/{id}/edit`
- `https://docs.google.com/presentation/d/{id}/edit#slide=id.p2`
- Just the presentation ID directly

### PDF Export URL

```
https://docs.google.com/presentation/d/{id}/export/pdf
```

Fetched with Playwright cookies — works for any presentation the authenticated user can access.

## File Structure

```
tools/scripts/google-slides/
├── mcp-google-slides-server.js   # MCP server
├── package.json                   # @modelcontextprotocol/sdk, playwright
├── google-session.json            # Auth state (gitignored)
└── cache/                         # Downloaded PDFs (gitignored)
```

## Auth Flow

1. Call `google_slides_authenticate` tool
2. Playwright opens a visible browser window
3. User logs in as jonetto@colppy.com (including 2FA if needed)
4. Session cookies saved to `google-session.json`
5. Subsequent `google_slides_read` calls use cookies — no browser window needed
6. If cookies expire, re-run `google_slides_authenticate`

## Integration

Referenced from `.mcp.json` in any plugin that needs it:

```json
{
  "mcpServers": {
    "google-slides": {
      "command": "node",
      "args": ["tools/scripts/google-slides/mcp-google-slides-server.js"]
    }
  }
}
```

No env vars needed — session file and cache are relative to the server script.
