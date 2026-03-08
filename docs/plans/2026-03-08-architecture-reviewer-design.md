# Architecture Reviewer Plugin — Design Doc

> Standalone Claude Code plugin that validates engineering team architecture proposals against AWS best practices, service deprecation status, and the current Colppy system architecture. Produces actionable gap analyses focused on blind spots.

## Decision Summary

| Decision | Choice | Rationale |
|---|---|---|
| Scope | Technology validation + execution risk | CEO needs both lenses |
| Location | Standalone plugin `colppy-architecture-reviewer` | Reusable by team, not just CEO |
| Output | Actionable gap analysis | Surface blind spots, not confirmations |
| AWS freshness | Cached reference + live fetch | 30/90 day staleness thresholds |
| Architecture | Agent + Skill (Approach B) | Protects context from 300K+ Jira data |
| Baseline sync | Hook + lazy regeneration | Belt and suspenders |

---

## Plugin Structure

```
plugins/colppy-architecture-reviewer/
├── plugin.json
├── agents/
│   └── architecture-researcher/
│       └── AGENT.md
├── skills/
│   └── review-architecture/
│       └── SKILL.md
├── hooks/
│   └── baseline-refresh/
│       └── hook.json
├── data/
│   └── aws-reference/
│       ├── well-architected-pillars.md
│       ├── rds-engine-lifecycle.md
│       ├── service-deprecations.md
│       └── cache-metadata.json
└── docs/
    └── colppy-system-baseline.md
```

---

## Component 1: Research Agent (`architecture-researcher`)

### Purpose

Fetch, digest, and condense all source material into a structured Research Brief that fits within reasonable context limits.

### Trigger

User invokes the skill, which spawns the agent as a subagent.

### Inputs

- Jira ticket keys (e.g., `KAN-12133 KAN-12131 KAN-12132`) or a JQL query
- Optional: specific architectural concern to focus on

### Agent Workflow

```
1. Parse input → extract Jira ticket keys or JQL
2. Fetch each Jira ticket via Atlassian MCP
3. Extract per ticket:
   - Technology choices (what they propose)
   - Acceptance criteria (what they consider "done")
   - Open refinement questions (what they're unsure about)
   - Stated rationale and business impact
4. Check AWS reference cache staleness:
   - Read data/aws-reference/cache-metadata.json
   - If last_refreshed < 30 days → use cache as-is
   - If 30-90 days → use cache + targeted Firecrawl for deprecation-sensitive items
   - If > 90 days → full Firecrawl refresh of all cached documents, update cache
5. Check system baseline staleness:
   - Compare mtime of docs/colppy-platform/*.md vs docs/colppy-system-baseline.md
   - If any source doc is newer → regenerate baseline from platform docs
6. Produce Research Brief (structured markdown, ~2-3 pages)
```

### Research Brief Format

```markdown
# Research Brief — [Date]
> Tickets analyzed: [list]
> AWS cache: refreshed [date] ([N] days ago)
> System baseline: regenerated [yes/no], last source change [date]

## Proposals Summary
### [KAN-XXXXX] [Title]
- **Proposes:** [technology/approach]
- **Rationale:** [stated reason]
- **Acceptance criteria:** [key items]
- **Open questions:** [from refinement section]
[Repeat per ticket]

## AWS Reference Data
- **RDS engine support:** [relevant engines, versions, EOL dates]
- **Well-Architected alignment:** [relevant pillar guidance]
- **Deprecation flags:** [any services/features being deprecated]
- **Migration path documentation:** [official upgrade paths that exist or don't]

## Current System Constraints
- [Key facts from baseline that intersect with proposals]
- [Known issues that proposals should address]
```

### Tools Available

Atlassian MCP, Firecrawl, Read, Glob, Grep, WebSearch

---

## Component 2: Analysis Skill (`review-architecture`)

### Purpose

Apply the gap analysis framework to the Research Brief. This is the analytical brain — the agent gathers facts, the skill finds what's missing.

### Invocation

```
/review-architecture KAN-12133 KAN-12131 KAN-12132
```

Or without arguments to be prompted for ticket keys.

### Skill Workflow

```
1. Accept Jira ticket keys from user
2. Spawn architecture-researcher agent with ticket keys
3. Receive Research Brief from agent
4. Apply 5 analysis lenses (see below)
5. Produce gap analysis output
```

### 5 Analysis Lenses

| # | Lens | What it checks | Example gap |
|---|---|---|---|
| 1 | **Technology validity** | Is the proposed tech supported, not deprecated, appropriate for scale and context? | "MariaDB 10.11 is supported on RDS but NOT on Aurora Serverless v2. Current infra uses Aurora Serverless v2 exclusively (see rds.tf)." |
| 2 | **Migration path reality** | Does the official upgrade path exist? What breaks along the way? | "MySQL 5.6 → MariaDB requires logical dump+restore, not in-place upgrade. 296 stored procedures and 26 functions need syntax validation against MariaDB dialect." |
| 3 | **Current system conflicts** | Does the proposal contradict or ignore something in the existing architecture? | "Proposal creates new React base project, but single-spa shell already exists with 6 inactive MFEs (dashboards, sales, mercado_pago). Why build from scratch?" |
| 4 | **Missing considerations** | What did the proposal not address that it should have? | "No mention of the 3 confirmed MySQL 8.0 breaks already identified (ERROR 1055 GROUP BY, 1064 `system` reserved word, 1292 zero dates). No mention of latin1 encoding in 9 tables." |
| 5 | **Sequencing risk** | Are parallel workstreams creating hidden dependencies or conflicts? | "DB migration (KAN-12133) and FusionAuth RBAC (KAN-12132) both require schema changes on the same MySQL database. Running in parallel risks migration conflicts." |

### Output Format

```markdown
# Architecture Review — [Date]

> **AWS reference cache:** last refreshed [date] ([N] days ago)
> **System baseline:** last regenerated [date]
> **Tickets reviewed:** KAN-XXXXX, KAN-XXXXX, ...

---

## Critical Gaps (must address before proceeding)

### [Gap title]
- **Proposal says:** [what the ticket states]
- **Reality:** [what AWS docs / current system / known issues say]
- **Risk:** [what happens if this isn't addressed]
- **Recommendation:** [specific action]

---

## Caution Areas (valid approach but incomplete)

### [Area title]
- **What's proposed works, but:** [what's missing]
- **Consider:** [suggestion]

---

## Confirmed Alignments (no action needed)
- [Brief one-liner per alignment — no elaboration]

---

## Sequencing Recommendations

1. [Recommended order of workstreams with dependency rationale]
2. [...]

---

## Appendix: Sources Referenced
- [AWS doc URLs consulted]
- [Platform doc files used]
- [Jira tickets analyzed]
```

---

## Component 3: System Baseline (`colppy-system-baseline.md`)

### Purpose

A distilled, architecturally-relevant snapshot of the current Colppy platform. Not a copy of the platform docs — a condensed version focused on facts that matter for architecture reviews.

### Content Structure

```markdown
# Colppy System Baseline
> Auto-generated from docs/colppy-platform/. Last regenerated: [date]

## Database
- Engine: MySQL 5.6 on Aurora Serverless v2 (Aurora MySQL 8.0 engine 3.08.2)
- Tables: 207 across 6 domains (Core, AR, AP, GL, ST, TX)
- Stored procedures: 296 | Functions: 26
- Known breaks on MySQL 8.0: ERROR 1055, 1064, 1292
- Known blockers: caching_sha2_password auth, latin1 in 9 tables
- Access patterns: raw PDO (Frontera), Eloquent (Benjamin), TypeORM+raw SQL (NestJS)

## Backend
- Layer 1: Frontera 2.0 — PHP 5.6 gateway, 31 Provisiones
- Layer 2: Benjamin — Laravel 5.4, 207 Eloquent models, /api/v1/*
- Layer 3: 9 NestJS microservices on EKS
- Layer 4: 20 Lambda functions (14 app + 6 infra)
- BenjaminConnector: Guzzle HTTP bridge adds latency for migrated ops

## Frontend
- Shell: single-spa (app_root)
- Active MFEs: 2 (auth, onboarding)
- Inactive MFEs: 6 (dashboard, sales, mercado_pago, vue, ...)
- Legacy: Vue SPA (colppy-vue)

## Auth
- Dual system: FusionAuth (modern IdP) + legacy session (claveSesion)
- Bridge: svc_settings decodes JWT → queries MySQL (6+ JOINs)
- FusionAuth runs on ECS Fargate (not EKS)

## Infrastructure
- AWS accounts: 5 (main, prod, stg, test, sec)
- Compute: EKS clusters per env (t3a.large/xlarge nodes)
- DB: Aurora Serverless v2 (multiple clusters per env)
- CI/CD: GitHub Actions via inf_workflows hub (~37 repos)
- Deployment: Docker → ECR → Helm → EKS (backend), S3+CloudFront (frontend)
- IaC: Terraform data-driven engine pattern (inf_terraform_aws)

## Repos
- Total: 108 across 2 GitHub orgs (colppy/, nubox-spa/)
- Two deployment flows coexist: Classic (develop/release/master) and GitLab Flow (test/staging/master)
```

### Regeneration

Triggered by:
1. **Hook** — PostToolUse hook detects edits to `docs/colppy-platform/*.md` during Claude Code sessions
2. **Lazy check** — Research agent compares file mtimes at invocation; regenerates if source is newer

Regeneration process: Read all `docs/colppy-platform/*.md` files, extract architecturally-relevant facts, write condensed baseline. Not a summarization — a structured extraction of specific data points.

---

## Component 4: Baseline Refresh Hook

### Hook Configuration

```json
{
  "event": "PostToolUse",
  "tools": ["Edit", "Write"],
  "match_files": ["docs/colppy-platform/**/*.md"],
  "action": "flag",
  "message": "Platform docs changed. System baseline (docs/colppy-system-baseline.md) may need regeneration. Run /review-architecture to auto-refresh, or manually regenerate."
}
```

The hook does NOT auto-regenerate (that would be disruptive mid-task). It flags that regeneration is needed. The research agent handles actual regeneration at next invocation.

---

## AWS Reference Cache

### Cached Documents

| File | Source | Refresh sensitivity |
|---|---|---|
| `well-architected-pillars.md` | AWS Well-Architected Framework (6 pillars) | Low — changes 2-3x/year |
| `rds-engine-lifecycle.md` | AWS RDS engine version support matrix + EOL dates | Medium — new versions quarterly |
| `service-deprecations.md` | AWS deprecation announcements relevant to Colppy stack | High — changes unpredictably |

### Staleness Thresholds

| Cache age | Behavior |
|---|---|
| < 30 days | Use cache directly |
| 30-90 days | Use cache + targeted Firecrawl for deprecation-sensitive items |
| > 90 days | Full Firecrawl refresh of all cached documents before analysis |

### `cache-metadata.json` Schema

```json
{
  "last_refreshed": "2026-03-08",
  "sources": [
    {
      "file": "well-architected-pillars.md",
      "url": "<fetched-from>",
      "fetched": "2026-03-08"
    }
  ],
  "refresh_log": [
    { "date": "2026-03-08", "type": "full", "trigger": "initial" }
  ]
}
```

---

## Usage Flow

```
User: /review-architecture KAN-12133 KAN-12131 KAN-12132

Skill activates:
  → Spawns architecture-researcher agent
    → Agent fetches 3 Jira tickets via Atlassian MCP
    → Agent checks AWS cache (7 days old → uses cache)
    → Agent checks baseline (platform docs unchanged → uses existing)
    → Agent produces Research Brief
  → Skill receives Research Brief
  → Skill applies 5 analysis lenses
  → Skill produces gap analysis output

User receives:
  - Critical gaps with evidence
  - Caution areas with suggestions
  - Confirmed alignments (brief)
  - Sequencing recommendations
```

---

## Initial AWS Cache Seeding

On first use, the research agent will need to do a full Firecrawl fetch to populate the cache. Target pages:

1. **RDS engine lifecycle** — Aurora MySQL and MariaDB supported versions, EOL dates
2. **Well-Architected Framework** — 6 pillar summaries (operational excellence, security, reliability, performance, cost optimization, sustainability)
3. **Service deprecations** — Recent deprecation announcements for services in Colppy stack (ECS, EKS, Lambda, S3, CloudFront, Aurora, RDS, Secrets Manager)

---

## Scope Boundaries

**In scope:**
- Validating technology choices against AWS best practices and deprecation status
- Identifying gaps between proposals and current system reality
- Flagging sequencing risks across parallel workstreams
- Producing structured, evidence-based gap analyses

**Out of scope:**
- Writing the architecture for the team (this is a review tool, not a design tool)
- Making go/no-go decisions (the output informs decisions, doesn't make them)
- Tracking implementation progress (that's Jira's job)
- Coaching feedback on Alejandro (that's the people-manager plugin)
