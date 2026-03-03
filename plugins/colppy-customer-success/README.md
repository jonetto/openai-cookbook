# Colppy Customer Success Plugin

Customer Success toolkit for Colppy — Intercom conversation research, onboarding analysis, LLM classification with few-shot learning, and user feedback insights.

## Skills

| Skill | Purpose |
|-------|---------|
| `business-context` | Foundational Colppy business context (ICP, product, market) |
| `intercom-customer-research` | Intercom conversation scanning and feedback extraction |
| `intercom-developer-api-research` | Developer/API conversation classification |
| `intercom-onboarding-setup` | Onboarding topic classification (setup, first invoice) |
| `intercom-conciliacion-bancaria` | Bank reconciliation topic classification |

## Commands

| Command | Description |
|---------|-------------|
| `/intercom-research` | Scan Intercom for customer feedback on a topic |
| `/intercom-developer-api-research` | Classify developer/API conversations |

## MCP Tools (intercom-research)

| Tool | Description |
|------|-------------|
| `export_intercom_conversations` | Export conversations to CSV/JSON by date range |
| `count_intercom_conversations` | Count conversations matching filters |
| `get_intercom_conversation_stats` | Stats without full export |
| `search_intercom_conversations` | Search by criteria |
| `scan_customer_feedback` | Quick scan for topic/keywords |
| `scan_full_text` | Full-text search across all messages |
| `get_conversation_feedback` | Deep dive into specific conversations |
| `analyze_onboarding_first_invoice` | Onboarding analysis segmented by user type |

## MCP Tools (feature-upvote-playwright)

| Tool | Description |
|------|-------------|
| `get_feature_upvote_board_summary` | Board-level metrics from the Feature Upvote dashboard (cache-first) |
| `list_feature_requests` | Moderation queue extraction with status/query/tag filters; uses Export CSV by default for full coverage, with pagination fallback (cache-first) |
| `create_feature_request` | Submit a suggestion on the live Feature Upvote board form (supports `dry_run`) |

This server uses browser automation (Playwright) because Feature Upvote does not provide a public general-use REST API.
Implementation/runtime notes are in `mcp/README.md`.
Complete onboarding and operations guide: `docs/README_FEATURE_UPVOTE_MCP.md`.

### Feature Upvote integration status (verified)

- Verified on **March 2, 2026** in `https://app.featureupvote.com/dashboard/apikey` for this account:
  - API key exists
  - API is intended primarily for Zapier
  - General-use API access is not offered
- Integration decision in this plugin:
  - Use Playwright MCP server for live board operations
  - Keep cache-first reads with `force_refresh` support
  - Avoid FeatureOS references (different company/product)

### Feature Upvote MCP operations

- `get_feature_upvote_board_summary`:
  - Reads board metrics (suggestions/comments/upvotes and approval counts)
- `list_feature_requests`:
  - Reads moderation queue with status/query/tag filters
  - Uses dashboard Export CSV by default (all rows), then parses to structured items
  - Falls back to page crawling if export is blocked
- `create_feature_request`:
  - Posts through board form (`dry_run` mode supported)

### Backend/API reality check

- No public Feature Upvote REST API is available for direct backend calls.
- Zapier can be used as a bridge (event-driven sync), but it is not a full direct API replacement.
- Direct `curl`/HTTP scraping without a real browser is not reliable due Cloudflare challenge flows.
- Practical production approach:
  - Run Playwright automation in a backend worker (headless)
  - Reuse persisted browser session state to reduce re-login/challenge frequency
  - Use a headed bootstrap only if Cloudflare blocks headless for a period

## LLM Classification

The `scripts/llm_classify.mjs` classifier uses GPT-4o-mini with few-shot learning to categorize Intercom conversations by topic. Classification accuracy improves over time through a human review feedback loop.

### Topic configs

| File | Purpose |
|------|---------|
| `skills/intercom-onboarding-setup/topic.json` | Broader onboarding/setup (11 categories) |
| `skills/intercom-onboarding-setup/topic_first_invoice.json` | First invoice / time-to-value (6 categories) |

Each topic config contains: category definitions, true/false positive guidance, keywords, and **few-shot examples** — verified conversation snippets that teach the model how to handle edge cases.

### Usage

```bash
# Classify onboarding conversations segmented by user type
python tools/scripts/intercom/analyze_onboarding.py \
  --cache plugins/colppy-customer-success/skills/intercom-developer-api-research/cache/conversations_YYYY-MM-DD_YYYY-MM-DD_team2334166.json \
  --user-type accountant --llm \
  --topic plugins/colppy-customer-success/skills/intercom-onboarding-setup/topic.json

# Direct LLM classification with review output
cd plugins/colppy-customer-success
node scripts/llm_classify.mjs \
  --cache skills/intercom-developer-api-research/cache/conversations.json \
  --topic skills/intercom-onboarding-setup/topic.json \
  --all --review /tmp/review_output.json
```

### Training loop (review → correct → improve)

The classifier improves through a feedback loop:

1. **Classify with `--review`** — generates a review JSON with each result + conversation snippet
2. **Human reviews** — set `correct: true/false`, `override_category`, `promote_to_example: true`
3. **Apply corrections with `--apply-review`** — promoted examples are appended to the topic config's `few_shot_examples`
4. **Re-run** — next classification uses the new examples in the prompt

```bash
# Apply reviewed corrections back to the topic config
node scripts/llm_classify.mjs \
  --apply-review /tmp/review_output.json \
  --topic skills/intercom-onboarding-setup/topic_first_invoice.json
```

See [intercom-onboarding-setup/README.md](skills/intercom-onboarding-setup/README.md) for the full step-by-step workflow.

## Setup

1. Set `INTERCOM_ACCESS_TOKEN` in `.env` or Cursor MCP settings
2. Set `FEATURE_UPVOTE_EMAIL` and `FEATURE_UPVOTE_PASSWORD` in `.env` or Cursor MCP settings
3. Optional Feature Upvote env vars:
   - `FEATURE_UPVOTE_BOARD_URL` (default: `https://ideas.colppy.com`)
   - `FEATURE_UPVOTE_HEADLESS` (default: `true`, no local Chrome window)
   - `FEATURE_UPVOTE_CACHE_TTL_MINUTES` (default: `30`)
   - `FEATURE_UPVOTE_SIGNIN_URL` (default: `https://app.featureupvote.com/signin`)
   - `FEATURE_UPVOTE_DASHBOARD_URL` (default: `https://app.featureupvote.com/dashboard/`)
   - `FEATURE_UPVOTE_STORAGE_STATE_PATH` (default: `mcp/.cache/feature-upvote/feature-upvote-storage-state.json`)
   - `FEATURE_UPVOTE_PERSIST_STORAGE_STATE` (default: `true`)
   - `FEATURE_UPVOTE_USER_AGENT` (optional override)
   - `FEATURE_UPVOTE_LOCALE` (default: `en-US`)
   - `FEATURE_UPVOTE_TIMEZONE` (default: `America/Argentina/Buenos_Aires`)
4. Set `OPENAI_API_KEY` in `.env` for LLM classification
5. MCP servers start automatically when the plugin is loaded
