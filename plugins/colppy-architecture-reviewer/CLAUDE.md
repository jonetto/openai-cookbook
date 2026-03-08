# Architecture Reviewer

Validates engineering architecture proposals against AWS best practices, service deprecation status, and the current Colppy system architecture.

## Usage

```
/review-architecture KAN-12133 KAN-12131 KAN-12132
```

Provide Jira ticket keys containing architecture proposals. The skill will:
1. Spawn a research agent to fetch tickets, check AWS docs, and read the system baseline
2. Apply 5 analysis lenses to find gaps
3. Output a structured gap analysis focused on blind spots

## How It Works

| Component | Role |
|---|---|
| **architecture-researcher** agent | Fetches Jira tickets, checks AWS cache, reads baseline → produces Research Brief |
| **review-architecture** skill | Applies 5 lenses to Research Brief → produces gap analysis |
| **System baseline** | Condensed snapshot of current Colppy architecture (auto-refreshes) |
| **AWS reference cache** | Cached AWS docs with staleness-based refresh (30/90 day thresholds) |

## AWS Cache Freshness

| Cache age | Behavior |
|---|---|
| < 30 days | Uses cache directly |
| 30-90 days | Cache + targeted live check for deprecations |
| > 90 days | Full refresh before analysis |

Cache metadata: `data/aws-reference/cache-metadata.json`. Output always shows when cache was last refreshed.

## System Baseline

The baseline at `docs/colppy-system-baseline.md` is a condensed version of `docs/colppy-platform/`. It auto-refreshes when:
- A PostToolUse hook detects edits to platform docs (flags for next refresh)
- The research agent finds source docs newer than the baseline (regenerates inline)

## Analysis Lenses

1. **Technology validity** — Is the proposed tech supported on the specific AWS services we use?
2. **Migration path reality** — Does the official upgrade path exist? What breaks?
3. **Current system conflicts** — Does the proposal contradict or duplicate existing architecture?
4. **Missing considerations** — What did the proposal not address that it should?
5. **Sequencing risk** — Are parallel workstreams creating hidden dependencies?

## Do NOT

- Use this to DESIGN architecture. It only REVIEWS proposals.
- Treat the output as go/no-go. It informs decisions.
- Skip the AWS cache check. Stale data leads to wrong gap analysis.
- Use this for operational issues (that's monitoring/runbooks, not architecture review).
