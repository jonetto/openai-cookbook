# Architecture Reviewer Plugin — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the `colppy-architecture-reviewer` standalone Claude Code plugin that validates engineering architecture proposals against AWS best practices and current system reality, producing actionable gap analyses.

**Architecture:** Agent + Skill pattern. A research agent fetches Jira tickets, checks AWS reference cache, and reads the system baseline, producing a condensed Research Brief. A skill applies 5 analysis lenses to the brief and outputs a structured gap analysis. A PostToolUse hook flags when platform docs change so the baseline stays fresh.

**Tech Stack:** Claude Code plugin system (AGENT.md, SKILL.md, plugin.json), Atlassian MCP (Jira), Firecrawl (AWS docs), markdown files for cache and baseline.

**Design doc:** `docs/plans/2026-03-08-architecture-reviewer-design.md`

---

### Task 1: Scaffold Plugin Directory and Manifests

**Files:**
- Create: `plugins/colppy-architecture-reviewer/.claude-plugin/plugin.json`
- Create: `plugins/colppy-architecture-reviewer/.cursor-plugin/plugin.json`

**Step 1: Create directory structure**

```bash
mkdir -p plugins/colppy-architecture-reviewer/.claude-plugin
mkdir -p plugins/colppy-architecture-reviewer/.cursor-plugin
mkdir -p plugins/colppy-architecture-reviewer/agents/architecture-researcher
mkdir -p plugins/colppy-architecture-reviewer/skills/review-architecture
mkdir -p plugins/colppy-architecture-reviewer/hooks/baseline-refresh
mkdir -p plugins/colppy-architecture-reviewer/data/aws-reference
mkdir -p plugins/colppy-architecture-reviewer/docs
```

**Step 2: Create .claude-plugin/plugin.json**

```json
{
  "name": "colppy-architecture-reviewer",
  "version": "1.0.0",
  "description": "Validates engineering architecture proposals against AWS best practices, service deprecation status, and current system architecture. Produces actionable gap analyses.",
  "author": {
    "name": "Colppy"
  }
}
```

**Step 3: Create .cursor-plugin/plugin.json**

```json
{
  "name": "colppy-architecture-reviewer",
  "version": "1.0.0",
  "description": "Validates engineering architecture proposals against AWS best practices, service deprecation status, and current system architecture. Produces actionable gap analyses.",
  "author": {
    "name": "Colppy"
  },
  "license": "MIT",
  "keywords": [
    "architecture",
    "aws",
    "review",
    "gap-analysis",
    "well-architected",
    "migration",
    "colppy"
  ]
}
```

**Step 4: Verify structure**

Run: `find plugins/colppy-architecture-reviewer -type d | sort`

Expected: All 8 directories listed.

**Step 5: Commit**

```bash
git add plugins/colppy-architecture-reviewer/
git commit -m "feat(architecture-reviewer): scaffold plugin directory and manifests"
```

---

### Task 2: Write System Baseline

**Files:**
- Create: `plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md`
- Read: `docs/colppy-platform/backend-architecture.md`
- Read: `docs/colppy-platform/deployment-and-infra.md`
- Read: `docs/colppy-platform/frontend-architecture.md`
- Read: `docs/colppy-platform/database-schema.md`
- Read: `docs/colppy-platform/auth-and-sessions.md`
- Read: `docs/colppy-platform/repo-directory.md`

**Step 1: Read all platform docs**

Read each of the 6 source files listed above to extract architecturally-relevant facts.

**Step 2: Write the baseline**

Create `plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md` with the following content. This is a structured extraction, not a summary — every line is a specific data point that matters for architecture reviews.

```markdown
# Colppy System Baseline

> Auto-generated from docs/colppy-platform/. Last regenerated: 2026-03-08

## Database

- Engine: MySQL 5.6 (production), Aurora Serverless v2 with Aurora MySQL 8.0 engine 3.08.2
- Tables: 207 across 6 domains (Core 31, AR 24, AP 19, GL 15, ST 10, TX 8)
- Stored procedures: 296 | Functions: 26
- Known breaks on MySQL 8.0: ERROR 1055 (GROUP BY), 1064 (`system` reserved word), 1292 (zero dates)
- Known blockers: caching_sha2_password auth plugin, latin1 encoding in 9 tables
- Access patterns: raw PDO via AbstractDAO (Frontera), Eloquent ORM (Benjamin), TypeORM + raw SQL (NestJS)
- Clusters per env: microservices (Aurora MySQL), microservices-pgsql (Aurora PostgreSQL 15.12), afip-pgsql (Aurora PostgreSQL 15.12), paybook (Aurora MySQL), fusionauth (Aurora PostgreSQL)
- Serverless v2 ACU range: 0.5-3 (most), 0.5-7 (AFIP)
- Auto-pause: 600s idle (non-prod)
- Backup retention: 12 days (prod)

## Backend

- Layer 1: Frontera 2.0 — PHP 5.6, no type hints, 31 Provisiones + ColppyCommon, singleton MainController
- Layer 2: Benjamin — Laravel 5.4, 207 Eloquent models, OAuth2 via Passport, /api/v1/*, 109 migrations
- Layer 3: NestJS — 9 active microservices on EKS (svc_settings, svc_security, svc_afip, svc_inventory, svc_sales, svc_mercado_pago, svc_importer_data, svc_utils, svc_backoffice)
- Layer 4: Lambda — 20 functions (14 application + 6 infrastructure), deployed via SAM
- BenjaminConnector: Guzzle HTTP bridge, OAuth2 tokens in usuario_external_tokens, synchronous refresh blocks requests
- Migration status: 7 fully migrated provisions (Inventario, Tax, PriceList, Cliente, Tercero, Contabilidad, Empresa), 5 partial, 16 legacy
- Shared MySQL database: Frontera DAOs and Benjamin Eloquent read/write same tables, no schema isolation

## Frontend

- Shell: single-spa (app_root), S3 + CloudFront
- Active MFEs: 2 (mfe_authentication, mfe_onboarding)
- Inactive MFEs: 6 (mfe_dashboard, mfe_sales, mfe_mercado_pago, mfe_vue, mfe_mercado_pago — exist in repos but not mounted)
- Legacy: Vue SPA (colppy-vue), PHP-rendered views
- Build: pnpm, Node.js 21 base image, S3 sync + CloudFront invalidation

## Auth

- Dual system: FusionAuth (modern IdP, ECS Fargate) + legacy session (claveSesion, MySQL-based)
- Bridge: svc_settings decodes FusionAuth JWT → raw SQL query (6+ JOINs across usuario, empresa, usuario_empresa, plan, usuario_sesion) → returns unified session
- OAuth2: Laravel Passport in Benjamin, tokens in usuario_external_tokens
- Current vulnerability: profile/role hardcoded in API request params, no backend permission validation

## Infrastructure

- AWS accounts: 5 (main/185428918146, prod/185428918146, stg/599636274800, test/828685354428, sec/962781397405)
- Compute: EKS managed node groups per env (prod: 6x t3a.large, stg: 2x t3a.large, test: 1x t3a.xlarge)
- FusionAuth: ECS Fargate (only service not on EKS)
- CI/CD: GitHub Actions via inf_workflows hub, ~37 repos reference it
- Deployment: Docker → ECR → Helm → EKS (backend), S3 + CloudFront (frontend), SAM (Lambda)
- IaC: Terraform data-driven engine pattern (inf_terraform_aws), ~50 .tf files, per-account data dirs
- Cross-account: Transit Gateway for VPC connectivity
- Monitoring: New Relic Kubernetes integration + CloudWatch alarms
- Cost: auto-shutdown Lambdas for non-prod EKS + RDS (nights/weekends)
- Security scanning: Semgrep (SAST) + Trivy (container) — advisory only, non-blocking
- Base images: PHP 5.6/7.1/7.4/8.2, Node.js 21, Nginx (in inf_docker_images ECR)

## Repos

- Total: 108 across 2 GitHub orgs (colppy/, nubox-spa/)
- Core runtime: 9 repos
- MFEs: 8 repos (2 active)
- NestJS: 9 repos
- Laravel: 6 repos
- Lambda: 15 repos
- Infrastructure: 12 repos
- Two deployment flows: Classic (develop/release/master) and GitLab Flow (test/staging/master)
- Branch-to-env: master→prod, release/*→stg, develop→test, feature/*→test (build only, no deploy), migration/*→develop
```

**Step 3: Verify the baseline is self-contained**

Read the file back and confirm every section has concrete data points (numbers, versions, names), not vague descriptions.

**Step 4: Commit**

```bash
git add plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md
git commit -m "feat(architecture-reviewer): add system baseline with current platform snapshot"
```

---

### Task 3: Seed AWS Reference Cache

**Files:**
- Create: `plugins/colppy-architecture-reviewer/data/aws-reference/well-architected-pillars.md`
- Create: `plugins/colppy-architecture-reviewer/data/aws-reference/rds-engine-lifecycle.md`
- Create: `plugins/colppy-architecture-reviewer/data/aws-reference/service-deprecations.md`
- Create: `plugins/colppy-architecture-reviewer/data/aws-reference/cache-metadata.json`

**Step 1: Fetch Well-Architected Framework via Firecrawl**

Use the `firecrawl` skill to fetch the AWS Well-Architected Framework overview page. Extract the 6 pillar summaries (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability). Focus on the key design principles and best practices per pillar. Write to `well-architected-pillars.md`.

Format:

```markdown
# AWS Well-Architected Framework — Pillar Summaries

> Source: AWS Well-Architected docs | Fetched: 2026-03-08

## Operational Excellence
- [Key design principles relevant to architecture review]

## Security
- [Key design principles]

## Reliability
- [Key design principles]

## Performance Efficiency
- [Key design principles]

## Cost Optimization
- [Key design principles]

## Sustainability
- [Key design principles]
```

**Step 2: Fetch RDS Engine Lifecycle via Firecrawl**

Use `firecrawl` to fetch the AWS RDS engine version support page. Extract:
- Aurora MySQL supported versions and EOL dates
- Aurora PostgreSQL supported versions and EOL dates
- RDS MariaDB supported versions and EOL dates
- RDS MySQL supported versions and EOL dates
- Any announced deprecations or end-of-standard-support dates

Write to `rds-engine-lifecycle.md`.

Format:

```markdown
# AWS RDS Engine Lifecycle

> Source: AWS RDS version support docs | Fetched: 2026-03-08

## Aurora MySQL
| Version | Engine | Standard Support End | Extended Support End |
|---|---|---|---|
| ... | ... | ... | ... |

## Aurora PostgreSQL
| Version | Engine | Standard Support End | Extended Support End |
|---|---|---|---|
| ... | ... | ... | ... |

## RDS MariaDB
| Version | Standard Support End | Extended Support End |
|---|---|---|
| ... | ... | ... |

## RDS MySQL
| Version | Standard Support End | Extended Support End |
|---|---|---|
| ... | ... | ... |

## Key Notes
- [Migration path constraints, in-place upgrade support, etc.]
```

**Step 3: Create service deprecations file**

Use `firecrawl` to search for recent AWS deprecation announcements relevant to the Colppy stack (EKS, ECS, Lambda, Aurora, RDS, S3, CloudFront, Secrets Manager, CodeDeploy). Write findings to `service-deprecations.md`.

Format:

```markdown
# AWS Service Deprecations — Colppy Stack

> Source: AWS announcements | Fetched: 2026-03-08

## Active Deprecations
| Service | What's Deprecated | Deadline | Impact on Colppy |
|---|---|---|---|
| ... | ... | ... | ... |

## Recently Completed Deprecations
| Service | What Was Deprecated | Completed | Notes |
|---|---|---|---|
| ... | ... | ... | ... |

## Upcoming Changes (Pre-Announced)
| Service | Change | Expected Date | Impact |
|---|---|---|---|
| ... | ... | ... | ... |
```

**Step 4: Create cache-metadata.json**

```json
{
  "last_refreshed": "2026-03-08",
  "sources": [
    {
      "file": "well-architected-pillars.md",
      "url": "<actual-url-fetched>",
      "fetched": "2026-03-08"
    },
    {
      "file": "rds-engine-lifecycle.md",
      "url": "<actual-url-fetched>",
      "fetched": "2026-03-08"
    },
    {
      "file": "service-deprecations.md",
      "url": "<actual-url-fetched>",
      "fetched": "2026-03-08"
    }
  ],
  "refresh_log": [
    { "date": "2026-03-08", "type": "full", "trigger": "initial-seed" }
  ]
}
```

**Step 5: Commit**

```bash
git add plugins/colppy-architecture-reviewer/data/aws-reference/
git commit -m "feat(architecture-reviewer): seed AWS reference cache with WAF, RDS lifecycle, deprecations"
```

---

### Task 4: Write Research Agent

**Files:**
- Create: `plugins/colppy-architecture-reviewer/agents/architecture-researcher/AGENT.md`

**Step 1: Write the agent**

Follow the conventions from existing agents (colppy-revops/agents/reconciliation-analyst.md pattern): YAML frontmatter with name, description (including example triggers), model, color; then full prompt with workflow, tools reference, output format, and constraints.

```markdown
---
name: architecture-researcher
description: >
  Use this agent to research and digest architecture proposals from Jira tickets,
  cross-referenced against AWS best practices and the current Colppy system baseline.

  Produces a structured Research Brief that condenses 300K+ characters of Jira/AWS data
  into a ~2-3 page summary ready for gap analysis.

  <example>
  Context: User wants to review migration architecture tickets
  user: "/review-architecture KAN-12133 KAN-12131 KAN-12132"
  assistant: "I'll use the architecture-researcher agent to fetch and digest these proposals."
  <commentary>The skill spawns this agent to handle the heavy research in a protected context.</commentary>
  </example>

  <example>
  Context: User wants to check a single architecture proposal
  user: "Can you review the DB migration proposal in KAN-12133?"
  assistant: "I'll use the architecture-researcher agent to analyze this ticket against AWS best practices."
  <commentary>Even a single ticket benefits from the agent because Jira payloads are massive.</commentary>
  </example>

  <example>
  Context: User asks about architecture decisions broadly
  user: "What architecture decisions has the team proposed recently?"
  assistant: "I'll use the architecture-researcher agent to search Jira for recent architecture tickets."
  <commentary>Agent can accept JQL queries to discover tickets, not just specific keys.</commentary>
  </example>
model: inherit
color: cyan
---

# Architecture Researcher

You are a research agent that fetches, digests, and condenses architecture proposal data
from multiple sources into a structured Research Brief.

## Your Job

You gather facts. You do NOT analyze, judge, or recommend. Your output is a neutral,
structured summary that the review-architecture skill will analyze.

## Inputs

You receive either:
- Specific Jira ticket keys (e.g., `KAN-12133 KAN-12131`)
- A JQL query (e.g., `text ~ "migration" AND created >= "2025-11-01"`)
- A natural language request (e.g., "find recent architecture proposals")

## Workflow

### Step 1: Resolve Jira Tickets

If given ticket keys:
- Fetch each ticket via Atlassian MCP (`getJiraIssue`)
- CloudId: `35330ef3-2d31-4816-afc6-0f6838e04830`

If given JQL or natural language:
- Search via `searchJiraIssuesUsingJql`
- Filter to architecture-relevant tickets (look for: migration, arquitectura, architecture, discovery, infrastructure, security labels)

### Step 2: Extract Proposal Data

For each ticket, extract:
1. **Technology choices** — What specific technologies/versions are proposed?
2. **Acceptance criteria** — What does "done" look like?
3. **Open refinement questions** — What is the team unsure about?
4. **Stated rationale** — Why do they want this?
5. **Business impact claims** — Revenue/performance/security numbers cited
6. **Assignee and status** — Who owns it, where is it?

Ignore: Jira metadata fields, custom fields, workflow transitions, vote counts.

### Step 3: Check AWS Reference Cache

Read `${CLAUDE_PLUGIN_ROOT}/data/aws-reference/cache-metadata.json`.

Calculate cache age from `last_refreshed` date:

| Cache age | Action |
|---|---|
| < 30 days | Read cached files directly from `${CLAUDE_PLUGIN_ROOT}/data/aws-reference/` |
| 30-90 days | Read cache + use Firecrawl to check for new deprecation announcements |
| > 90 days | Full Firecrawl refresh: re-fetch all 3 cached documents, update files and metadata |

When refreshing via Firecrawl:
- `well-architected-pillars.md`: Fetch AWS Well-Architected Framework overview
- `rds-engine-lifecycle.md`: Fetch AWS RDS engine version support matrix
- `service-deprecations.md`: Search for recent AWS deprecation announcements for: EKS, ECS, Lambda, Aurora, RDS, S3, CloudFront, Secrets Manager, CodeDeploy

After refresh: update `cache-metadata.json` with new dates and URLs.

### Step 4: Check System Baseline

Read `${CLAUDE_PLUGIN_ROOT}/docs/colppy-system-baseline.md`.

Check if any file in `docs/colppy-platform/` has been modified more recently than the baseline file. If so:
1. Read all `docs/colppy-platform/*.md` files
2. Extract architecturally-relevant facts (versions, counts, service names, known issues)
3. Rewrite `colppy-system-baseline.md` following the existing section structure
4. Note in the Research Brief: "System baseline regenerated"

### Step 5: Produce Research Brief

Output a single markdown document following this exact format:

```
# Research Brief — [YYYY-MM-DD]

> Tickets analyzed: [KAN-XXXXX, KAN-XXXXX, ...]
> AWS cache: refreshed [date] ([N] days ago)
> System baseline: [regenerated | current], last source change [date]

## Proposals Summary

### [KAN-XXXXX] [Ticket Title]
- **Proposes:** [specific technology/version/approach]
- **Rationale:** [stated reason from ticket]
- **Acceptance criteria:** [key measurable items]
- **Open questions:** [from refinement section — these are gaps the team already knows about]
- **Status:** [Jira status] | **Assignee:** [name]

[Repeat for each ticket]

## AWS Reference Data

### RDS Engine Support
- [Versions and EOL dates relevant to proposals]

### Well-Architected Alignment
- [Pillar guidance relevant to proposals — not all 6 pillars, only the relevant ones]

### Deprecation Flags
- [Any services/features being deprecated that affect the proposals]

### Migration Path Documentation
- [Official upgrade paths that exist or DON'T exist for proposed migrations]

## Current System Constraints
- [Facts from the baseline that directly intersect with proposals]
- [Known issues the proposals should address]
- [Existing capabilities the proposals might be duplicating]
```

## Constraints

- DO NOT analyze or judge the proposals. That is the skill's job.
- DO NOT recommend alternatives. Just report what exists.
- DO NOT skip the AWS cache check. Stale data leads to wrong conclusions.
- DO include direct quotes from Jira tickets when relevant (especially acceptance criteria).
- DO flag when a proposal references something that doesn't match the baseline (e.g., "ticket says MySQL 5.6 but Aurora runs 8.0 engine").
- Keep the Research Brief under 3 pages. Condense aggressively — the skill needs room to reason.
```

**Step 2: Verify the agent file**

Read back `AGENT.md` and confirm:
- Frontmatter has name, description with examples, model: inherit, color
- Workflow has all 5 steps
- Constraints section exists
- `${CLAUDE_PLUGIN_ROOT}` used for all plugin-relative paths
- CloudId hardcoded for Atlassian MCP calls

**Step 3: Commit**

```bash
git add plugins/colppy-architecture-reviewer/agents/
git commit -m "feat(architecture-reviewer): add research agent with Jira/AWS/baseline workflow"
```

---

### Task 5: Write Analysis Skill

**Files:**
- Create: `plugins/colppy-architecture-reviewer/skills/review-architecture/SKILL.md`

**Step 1: Write the skill**

Follow conventions from existing skills (user-lifecycle-framework/SKILL.md pattern): YAML frontmatter with name and description, then structured content with the analytical framework.

```markdown
---
name: review-architecture
description: >
  Validate engineering architecture proposals against AWS best practices and current system reality.
  Produces actionable gap analysis focused on blind spots.
  Use when the team presents architecture decisions, migration plans, or technology choices.
  Invoke with Jira ticket keys: /review-architecture KAN-12133 KAN-12131
---

# Architecture Review

Validate engineering architecture proposals by identifying what's missing,
not confirming what's there.

## Invocation

```
/review-architecture KAN-12133 KAN-12131 KAN-12132
```

Without arguments: prompt user for Jira ticket keys or JQL query.

## Workflow

### Step 1: Gather Input

Accept Jira ticket keys from the user arguments. If none provided, ask:
"Which Jira tickets contain the architecture proposals? Provide ticket keys (e.g., KAN-12133) or a search term."

### Step 2: Dispatch Research Agent

Spawn the `architecture-researcher` agent with the ticket keys. This agent:
- Fetches Jira tickets
- Checks/refreshes AWS reference cache
- Checks/refreshes system baseline
- Returns a structured Research Brief

Wait for the Research Brief before proceeding.

### Step 3: Apply Analysis Lenses

Apply each of the 5 lenses below to the Research Brief. For each lens, compare the proposals
against the AWS reference data AND the system baseline.

**Only report gaps.** If a proposal aligns with best practice and the current system,
do NOT elaborate — list it as a one-liner under "Confirmed Alignments."

#### Lens 1: Technology Validity

For each technology choice in the proposals:
- Is it supported on the AWS services Colppy uses? (check rds-engine-lifecycle.md)
- Is it approaching EOL or deprecated? (check service-deprecations.md)
- Is it appropriate for Colppy's scale and context?
- Does the version exist on the specific AWS service variant used? (e.g., Aurora Serverless v2 vs standard RDS)

#### Lens 2: Migration Path Reality

For each proposed migration:
- Does an official, documented upgrade path exist?
- Is it in-place or does it require dump+restore?
- What known breaking changes exist along the path?
- Are there intermediate versions required? (e.g., 5.6 → 5.7 → 8.0, not 5.6 → 8.0 direct)
- Cross-reference with known issues in the system baseline

#### Lens 3: Current System Conflicts

For each proposal:
- Does it duplicate something that already exists? (e.g., proposing new React setup when single-spa with 6 MFEs exists)
- Does it contradict a current architectural decision?
- Does it ignore a constraint documented in the baseline? (e.g., shared MySQL database, dual auth system)
- Would it create a new inconsistency? (e.g., adding a 4th DB access pattern)

#### Lens 4: Missing Considerations

For each proposal:
- What known issues from the baseline are not mentioned? (e.g., stored procedures, encoding, auth plugins)
- What AWS Well-Architected principles are not addressed? (check well-architected-pillars.md)
- What rollback/failure scenarios are not covered?
- What cross-system impacts are not considered? (e.g., Frontera + Benjamin sharing the same DB during migration)

#### Lens 5: Sequencing Risk

Across ALL proposals together:
- Are there hidden dependencies between workstreams?
- Do multiple proposals modify the same system component?
- Is there a natural ordering that reduces risk?
- What happens if one workstream fails or stalls — does it block others?

### Step 4: Produce Output

Format the analysis as follows. Be specific — cite ticket numbers, AWS doc references,
and baseline facts. Every gap must have evidence.

```
# Architecture Review — [YYYY-MM-DD]

> **AWS reference cache:** last refreshed [date] ([N] days ago)
> **System baseline:** last regenerated [date]
> **Tickets reviewed:** KAN-XXXXX, KAN-XXXXX, ...

---

## Critical Gaps (must address before proceeding)

### [Gap title — specific and actionable]
- **Proposal says:** [direct quote or paraphrase from ticket]
- **Reality:** [what AWS docs / system baseline / known issues actually say]
- **Risk:** [concrete consequence if not addressed]
- **Recommendation:** [specific next action for the team]

[Repeat for each critical gap]

---

## Caution Areas (valid approach but incomplete)

### [Area title]
- **What's proposed works, but:** [what's missing or underspecified]
- **Consider:** [suggestion to strengthen the proposal]

[Repeat for each caution area]

---

## Confirmed Alignments (no action needed)

- [One-liner per alignment — no elaboration]

---

## Sequencing Recommendations

1. [Recommended order with dependency rationale]
2. [...]

---

## Appendix: Sources Referenced

- **AWS docs:** [URLs from cache or live fetch]
- **Platform baseline:** colppy-system-baseline.md (regenerated: [date])
- **Jira tickets:** [list with titles]
```

## Severity Classification

| Severity | Definition | Criteria |
|---|---|---|
| **Critical Gap** | Must address before proceeding | Technology not supported, official path doesn't exist, security vulnerability, data loss risk |
| **Caution Area** | Valid but incomplete | Missing rollback plan, unaddressed edge case, incomplete acceptance criteria, unmentioned dependency |
| **Confirmed Alignment** | No action needed | Proposal matches AWS best practice AND current system reality |

## Guardrails

- This is a REVIEW tool, not a DESIGN tool. Identify gaps, don't rewrite the architecture.
- Every gap must cite evidence (AWS doc, baseline fact, or Jira ticket content).
- Do not speculate. If you're unsure whether something is a gap, flag it as a Caution Area, not Critical.
- Do not repeat the proposal back to the user. They already read the tickets. Focus on what's MISSING.
- Keep Critical Gaps to genuine blockers (max 5-7). If everything is "critical," nothing is.
```

**Step 2: Verify the skill file**

Read back `SKILL.md` and confirm:
- Frontmatter has name and description
- All 5 analysis lenses are defined with clear criteria
- Output format matches the design doc
- Severity classification table exists
- Guardrails section prevents scope creep

**Step 3: Commit**

```bash
git add plugins/colppy-architecture-reviewer/skills/
git commit -m "feat(architecture-reviewer): add review-architecture skill with 5 analysis lenses"
```

---

### Task 6: Write Baseline Refresh Hook

**Files:**
- Create: `plugins/colppy-architecture-reviewer/hooks/baseline-refresh/hook.json`

**Step 1: Write the hook configuration**

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "matcher": {
        "tool_name": "Edit|Write",
        "file_path": "docs/colppy-platform/.*\\.md$"
      },
      "prompt": "IMPORTANT: A Colppy platform documentation file was just modified. The architecture reviewer system baseline at plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md may now be stale. The baseline will auto-refresh on next /review-architecture invocation. No action needed now."
    }
  ]
}
```

Note: Check the exact hook format supported by Claude Code plugins. The conventions exploration showed hook support exists but no concrete examples were found in existing plugins. Verify against plugin-dev:hook-development skill documentation if the format above doesn't work.

**Step 2: Verify hook syntax**

Read back hook.json and confirm it matches Claude Code's expected hook format. If unsure, invoke the `plugin-dev:hook-development` skill to validate.

**Step 3: Commit**

```bash
git add plugins/colppy-architecture-reviewer/hooks/
git commit -m "feat(architecture-reviewer): add PostToolUse hook for baseline staleness detection"
```

---

### Task 7: Write Plugin CLAUDE.md

**Files:**
- Create: `plugins/colppy-architecture-reviewer/CLAUDE.md`

**Step 1: Write CLAUDE.md**

Follow conventions from existing plugins (colppy-revops/CLAUDE.md pattern):

```markdown
# Architecture Reviewer

Validates engineering architecture proposals against AWS best practices, service deprecation
status, and the current Colppy system architecture.

## Usage

```
/review-architecture KAN-12133 KAN-12131 KAN-12132
```

Provide Jira ticket keys containing architecture proposals. The skill will:
1. Spawn a research agent to fetch tickets, check AWS docs, and read the system baseline
2. Apply 5 analysis lenses to find gaps
3. Output a structured gap analysis

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

The cache metadata is at `data/aws-reference/cache-metadata.json`. The output always shows
when the cache was last refreshed.

## System Baseline

The baseline at `docs/colppy-system-baseline.md` is a condensed version of `docs/colppy-platform/`.
It auto-regenerates when:
- A PostToolUse hook detects edits to platform docs (flags for next refresh)
- The research agent finds source docs newer than the baseline (regenerates inline)

## Do NOT

- Use this tool to DESIGN architecture. It only REVIEWS proposals.
- Treat the output as a go/no-go decision. It informs decisions.
- Skip the AWS cache check. Stale data leads to wrong gap analysis.
```

**Step 2: Commit**

```bash
git add plugins/colppy-architecture-reviewer/CLAUDE.md
git commit -m "feat(architecture-reviewer): add CLAUDE.md plugin guidance"
```

---

### Task 8: Validate Plugin Structure

**Step 1: Verify all files exist**

Run: `find plugins/colppy-architecture-reviewer -type f | sort`

Expected output:
```
plugins/colppy-architecture-reviewer/.claude-plugin/plugin.json
plugins/colppy-architecture-reviewer/.cursor-plugin/plugin.json
plugins/colppy-architecture-reviewer/CLAUDE.md
plugins/colppy-architecture-reviewer/agents/architecture-researcher/AGENT.md
plugins/colppy-architecture-reviewer/data/aws-reference/cache-metadata.json
plugins/colppy-architecture-reviewer/data/aws-reference/rds-engine-lifecycle.md
plugins/colppy-architecture-reviewer/data/aws-reference/service-deprecations.md
plugins/colppy-architecture-reviewer/data/aws-reference/well-architected-pillars.md
plugins/colppy-architecture-reviewer/docs/colppy-system-baseline.md
plugins/colppy-architecture-reviewer/hooks/baseline-refresh/hook.json
plugins/colppy-architecture-reviewer/skills/review-architecture/SKILL.md
```

**Step 2: Validate plugin.json files parse as valid JSON**

Run: `python3 -m json.tool plugins/colppy-architecture-reviewer/.claude-plugin/plugin.json > /dev/null && echo "OK"`
Run: `python3 -m json.tool plugins/colppy-architecture-reviewer/.cursor-plugin/plugin.json > /dev/null && echo "OK"`
Run: `python3 -m json.tool plugins/colppy-architecture-reviewer/data/aws-reference/cache-metadata.json > /dev/null && echo "OK"`

Expected: All print "OK".

**Step 3: Validate hook.json parses as valid JSON**

Run: `python3 -m json.tool plugins/colppy-architecture-reviewer/hooks/baseline-refresh/hook.json > /dev/null && echo "OK"`

Expected: "OK"

**Step 4: Verify frontmatter in AGENT.md and SKILL.md**

Read the first 10 lines of each file and confirm YAML frontmatter is present with required fields (name, description).

---

### Task 9: End-to-End Smoke Test

**Step 1: Test the skill invocation**

Invoke `/review-architecture KAN-12133 KAN-12131 KAN-12132` and verify:
1. The research agent is spawned
2. Jira tickets are fetched successfully
3. AWS cache is read (should be fresh from Task 3)
4. System baseline is read
5. Research Brief is produced
6. Gap analysis output follows the expected format
7. At least one Critical Gap is identified (the MariaDB on Aurora Serverless v2 compatibility question is a known gap)

**Step 2: Verify output quality**

The gap analysis should identify at minimum these known issues:
- MariaDB 10.11 compatibility with Aurora Serverless v2
- MySQL 5.6 → MariaDB migration path (dump+restore, not in-place)
- 296 stored procedures needing syntax validation
- 3 confirmed MySQL 8.0 breaks (ERROR 1055, 1064, 1292)
- Existing single-spa + 6 inactive MFEs vs new React proposal
- FusionAuth RBAC + DB migration parallel sequencing risk

**Step 3: Fix any issues found during smoke test**

If the output is missing expected gaps or the format is wrong, iterate on the SKILL.md and AGENT.md.

**Step 4: Final commit**

```bash
git add -A plugins/colppy-architecture-reviewer/
git commit -m "feat(architecture-reviewer): complete plugin with smoke test validation"
```
