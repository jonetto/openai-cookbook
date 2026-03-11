# Bug Detective & Bug Fixer — Design Spec

> Two-agent system for bug triage and resolution within the `colppy-product` plugin.
> Approved: 2026-03-10

## Problem

Colppy has bug signals scattered across Intercom conversations, Jira tickets, commit history, and staging behavior. Today, correlating these signals and turning them into fixes is a manual, reactive process. There is no systematic way to detect bug patterns across systems, triage them with evidence, and produce fixes with minimal human overhead.

## Solution

Two standalone agents in `colppy-product`:

1. **Bug Detective** — read-only investigator that correlates bug signals across Intercom, Jira, commits, and staging DB/UI. Produces a structured triage report and notifies via Slack DM.
2. **Bug Fixer** — code-writing agent that receives a diagnosed bug, clones the relevant repo, writes the minimal fix, and opens a PR. Notifies via Slack DM.

Human-gated handoff: the Detective recommends, you decide, the Fixer executes.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Two agents vs. one | Two standalone | Different tool profiles (read-only vs. code-write). Different trust boundaries. Parallelizable. |
| Fixer autonomy | PR only, human reviews and merges | 108-repo codebase with multiple deployment flows. No autonomous merges. |
| Repo access | Dynamic — Detective identifies repo, Fixer clones into worktree | Too many repos to pre-configure. Detective's triage naturally points to the right repo. |
| DB access | Staging (free query) + prod read-only (existing `juan_onetto`) | Staging is safe for investigation. Prod read-only for confirmation. Both via existing VPN. |
| Communication | Slack DM (channel `DE91378PM`) | User's preferred channel. Jira comments are secondary (Detective can comment on existing tickets). |
| Handoff | Human-gated | Detective might flag a feature change as a bug. Human is the circuit breaker. |

## Bug Detective Agent

### Trigger Sources

| # | Source | Mechanism | Tools |
|---|--------|-----------|-------|
| 1 | Intercom | Scan conversations for error patterns ("no funciona", "error", "no puedo") | Intercom MCP: `search_conversations`, `get_conversation`, `search_contacts` |
| 2 | Jira | Watch for new bug-type tickets in KAN project | Atlassian MCP: `jira_search_issues`, `jira_get_issue` |
| 3 | Commits | Monitor recent commits for risky changes (migrations, stored procs, ARCA) | `gh` CLI |
| 4 | Manual | Direct invocation with Jira key, Intercom link, or description | Conversation context |

### Investigation Workflow

1. **Signal intake** — Classify: Intercom complaint, Jira bug, risky commit, or manual request
2. **Cross-reference** — Check the other systems. Intercom signal → search Jira + check commits. Jira signal → search Intercom + check commits.
3. **DB verification** — Query staging DB (and optionally prod read-only) to verify data state
4. **Staging test** — If UI-reproducible, use Playwright to navigate staging and confirm/reproduce
5. **Triage report** — Structured output with severity, root cause hypothesis, affected systems, recommendation

### Triage Report Format

```
┌─────────────────────────────────────────────────┐
│ BUG TRIAGE: [title]                             │
│ Severity: [CRITICAL / HIGH / MEDIUM / LOW]      │
│ Source: [Intercom / Jira / Commit / Manual]     │
│ Affected layer: [Frontera / Benjamin / NestJS / Vue / MFE] │
│ Repo: [org/repo-name]                           │
│ Reproducible: [Yes (staging) / No / Untested]   │
│ Related Jira: [KAN-XXXX or "none found"]        │
│ Related Intercom: [count] conversations         │
│ Root cause hypothesis: [1-2 sentences]          │
│ Recommendation: [Fix / Monitor / Known issue]   │
└─────────────────────────────────────────────────┘
```

Plus detailed evidence section: source data, DB query results, staging screenshots.

### Slack Notification Format

> **Bug Detective** — [severity emoji] [title]
> Source: Intercom (N conversations) + Jira KAN-XXXX
> Layer: [affected layer] → [component]
> Repo: `org/repo-name`
> Recommendation: Hand to Bug Fixer

### Constraints

- Read-only across all systems (Intercom, Jira, GitHub, DB)
- Exception: can add comments to existing Jira tickets with triage findings
- Never creates Jira tickets (reports to you via Slack — you decide what becomes a ticket)
- Never invokes the Bug Fixer directly (human-gated)
- Never modifies data in Intercom, HubSpot, or the database

## Bug Fixer Agent

### Input

- A triage report from the Bug Detective (structured, with repo + root cause hypothesis + evidence)
- OR a Jira ticket key provided directly by the user

### Fix Workflow

1. **Understand the bug** — Read triage report or Jira ticket. Identify repo, layer, suspected code path.
2. **Clone & isolate** — Clone relevant repo into a git worktree. Create branch `fix/KAN-XXXX-brief-slug`.
3. **Root cause analysis** — Trace the code path. Read files, grep for failing logic, check DB schema if needed.
4. **Write the fix** — Minimal fix only. Follow existing code conventions per layer.
5. **Validate** — Lint, type check locally. Playwright on staging if UI-visible.
6. **Open PR** — Push branch, open PR with structured description.

### PR Format

```
Title: fix(KAN-XXXX): [brief description]

## Bug
[1-2 sentences from triage report]

## Root Cause
[What was actually wrong — code path + logic error]

## Fix
[What this PR changes and why]

## Evidence
- Triage report: [link or summary]
- Intercom: [X] related conversations
- Staging verified: [yes/no]

## Test Plan
- [ ] [specific verification steps]

🤖 Generated with Bug Fixer agent
```

### Convention Awareness

The Fixer must detect and follow the repo's existing patterns:

| Layer | Conventions |
|-------|------------|
| Frontera (PHP 5.6) | No type hints, DAO pattern, raw SQL, MD5 auth |
| Benjamin (Laravel 5.4) | Repository + Service + Controller, Eloquent ORM |
| NestJS services | TypeORM, service pattern, decorators |
| Vue 2 (colppy-vue) | Vuex, Bootstrap 4, Options API |
| MFEs (React 18) | MUI, Redux Toolkit, react-hook-form, Vite |

### Constraints

- Minimal fixes only — no refactoring, no "while we're here" improvements
- Never touches infrastructure (Terraform, CI/CD, Docker, Helm)
- Never modifies DB directly — if migration needed, includes migration file in PR
- Never merges PRs or pushes to `master`/`release/*` branches
- Never deploys anything
- Branch naming: `fix/KAN-XXXX-brief-slug`

## Handoff Protocol

```
Detective investigates
        ↓
Triage report produced
        ↓
Slack DM: "Recommendation: Hand to Bug Fixer"
        ↓
USER decides: "fix it" / "not now" / "need more info"
        ↓
User invokes Bug Fixer with Jira key
        ↓
Fixer clones repo → writes fix → opens PR
        ↓
Slack DM: "PR ready for review"
        ↓
USER reviews and merges
```

## CPO Agent Integration

The CPO agent's routing table adds two entries:

| Signal | CPO dispatches to... |
|--------|---------------------|
| Support pattern about a feature gap | `trial-experience-analyst` or `churn-investigator` |
| Support pattern about a **bug/defect** | **`bug-detective`** |
| Diagnosed bug needs a fix | **`bug-fixer`** |
| Architecture review | `architecture-reviewer` |
| Metric drop | `saas-metrics-analyst` |

Key distinction: **product friction** (missing bumper, UX gap) → CPO's own workflow; **actual defect** (broken code, data error) → Bug Detective.

## Invocation Patterns

### 1. Manual trigger
```
/investigate-bug KAN-1234
→ Bug Detective runs investigation → Slack triage
"Fix it"
→ Bug Fixer opens PR → Slack PR link
```

### 2. Proactive scan (via /loop)
```
/loop 30m "Scan Intercom for new bug-pattern conversations and Jira for new bug tickets"
→ Bug Detective polls → Slack: "Found N new signals"
```

### 3. CPO agent routing
```
"IVA Simple is broken for some users"
→ CPO classifies as defect → dispatches Bug Detective
→ Detective triages → you approve → Fixer opens PR
```

## Tool Profiles

### Bug Detective (read-only)

| Integration | Tools | Access |
|-------------|-------|--------|
| Intercom | `search_conversations`, `get_conversation`, `search_contacts` | Read |
| Jira | `jira_search_issues`, `jira_get_issue`, `jira_add_comment` | Read + comment |
| GitHub | `gh api`, `gh pr list` | Read |
| Staging DB | `mysql` CLI | SELECT only |
| Prod DB | `mysql` CLI (`juan_onetto` user) | SELECT on 10 tables |
| Playwright | `browser_navigate`, `browser_snapshot`, `browser_take_screenshot` | Read (staging) |
| Slack | `slack_send_message` | Send to DM |

### Bug Fixer (writes code only)

| Integration | Tools | Access |
|-------------|-------|--------|
| Jira | `jira_get_issue` | Read |
| GitHub | `gh repo clone`, `gh pr create`, git ops | Clone + branch + PR |
| Staging DB | `mysql` CLI | SELECT only |
| Playwright | Navigation + snapshot | Read (staging) |
| Slack | `slack_send_message` | Send to DM |
| Code | Read, Edit, Write, Grep, Glob, Bash | Full (within worktree) |

## File Structure

```
plugins/colppy-product/
├── CLAUDE.md                          (update: add bug agents)
├── agents/
│   ├── cpo-agent.md                   (update: add routing)
│   ├── bug-detective.md               (new)
│   └── bug-fixer.md                   (new)
├── commands/
│   ├── product-review.md              (existing)
│   └── investigate-bug.md             (new)
├── docs/
│   └── plg-framework.md              (existing)
└── data/
    └── bug-triage/                    (new — local cache, .gitignored)
        └── .gitkeep
```

## Out of Scope

- CI/CD failure monitoring (GitHub Actions) — future addition
- Automatic Jira ticket creation by the Detective
- Automatic merge or deployment by the Fixer
- HubSpot integration (not relevant for bug triage)
- Running in headless/scheduled mode without VPN (requires infra work)
