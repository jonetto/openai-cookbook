/**
 * MCP tool definitions for Feature Upvote Playwright automation server.
 *
 * This server uses browser automation to work with the
 * Feature Upvote dashboard + board UI.
 */

export const FEATURE_UPVOTE_PLAYWRIGHT_TOOL_DEFINITIONS = [
  {
    name: 'get_feature_upvote_board_summary',
    description:
      'Get board-level metrics from Feature Upvote dashboard (suggestions, comments, upvotes, approval counts). Cache-first with optional force_refresh.',
    inputSchema: {
      type: 'object',
      properties: {
        board_ref: {
          type: 'string',
          description:
            'Optional board reference (example: pr_ny43flcuuwdgmxg). If omitted, uses the first board visible in dashboard.',
        },
        force_refresh: {
          type: 'boolean',
          description: 'If true, bypass cache and fetch live from Feature Upvote.',
          default: false,
        },
        use_export_csv: {
          type: 'boolean',
          description:
            'If true (default), use the moderation Export CSV download for complete coverage, then parse results. Falls back to pagination when export is blocked.',
          default: true,
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: 'list_feature_requests',
    description:
      'List feature requests from the moderation dashboard via Playwright. Supports status filtering, query/tag filters, pagination limits, and cache-first behavior.',
    inputSchema: {
      type: 'object',
      properties: {
        board_ref: {
          type: 'string',
          description:
            'Optional board reference (example: pr_ny43flcuuwdgmxg). If omitted, uses the first board visible in dashboard.',
        },
        status: {
          type: 'string',
          description: 'Status filter on moderation page.',
          enum: [
            'awaiting_moderation',
            'under_review',
            'planned',
            'not_planned',
            'done',
            'deleted',
            'spam',
            'all',
          ],
          default: 'awaiting_moderation',
        },
        query: {
          type: 'string',
          description: 'Search text for title/description (dashboard q filter).',
        },
        tag: {
          type: 'string',
          description: 'Tag name for filtering (dashboard tag filter).',
        },
        max_pages: {
          type: 'number',
          description: 'Max moderation pages to crawl (50 rows per page).',
          minimum: 1,
          maximum: 30,
          default: 5,
        },
        limit: {
          type: 'number',
          description: 'Max items to return after crawling.',
          minimum: 1,
          maximum: 2000,
          default: 200,
        },
        force_refresh: {
          type: 'boolean',
          description: 'If true, bypass cache and fetch live from Feature Upvote.',
          default: false,
        },
      },
      additionalProperties: false,
    },
  },
  {
    name: 'create_feature_request',
    description:
      'Create a feature request on the live board form (Ideas portal) via Playwright. Can run in dry_run mode for safe validation before posting.',
    inputSchema: {
      type: 'object',
      properties: {
        title: {
          type: 'string',
          description: 'Feature request title (max 100 chars in UI).',
        },
        description: {
          type: 'string',
          description: 'Feature request description/body (optional).',
        },
        board_url: {
          type: 'string',
          description:
            'Board URL, e.g. https://ideas.colppy.com. Defaults to FEATURE_UPVOTE_BOARD_URL env var.',
        },
        name: {
          type: 'string',
          description: 'Contributor display name for the suggestion form.',
        },
        email: {
          type: 'string',
          description: 'Contributor email for the suggestion form.',
        },
        consent: {
          type: 'boolean',
          description: 'Check privacy consent checkbox before submit.',
          default: true,
        },
        dry_run: {
          type: 'boolean',
          description: 'If true, fill + validate form but do not click submit.',
          default: false,
        },
      },
      required: ['title'],
      additionalProperties: false,
    },
  },
];
