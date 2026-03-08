---
name: review-architecture
description: >
  Validate engineering architecture proposals against AWS best practices and current system reality.
  Produces actionable gap analysis focused on blind spots.
  Use when the team presents architecture decisions, migration plans, or technology choices.
  Invoke with Jira ticket keys: /review-architecture KAN-12133 KAN-12131
---

# Architecture Review

Validate engineering architecture proposals by identifying what's missing, not confirming what's there.

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

Spawn the `architecture-researcher` agent with the ticket keys as input. The agent will:
- Fetch Jira tickets via Atlassian MCP
- Check/refresh AWS reference cache (staleness thresholds: 30/90 days)
- Check/refresh system baseline against docs/colppy-platform/
- Return a structured Research Brief

Wait for the Research Brief before proceeding to Step 3.

### Step 3: Apply Analysis Lenses

Apply each of the 5 lenses below to the Research Brief. For each lens, compare the proposals against BOTH the AWS reference data AND the system baseline from the brief.

**Only report gaps.** If a proposal aligns with best practice and the current system, do NOT elaborate — list it as a one-liner under "Confirmed Alignments."

#### Lens 1: Technology Validity

For each technology choice in the proposals, check:
- Is it supported on the specific AWS service variant Colppy uses? (e.g., Aurora Serverless v2, not just "RDS")
- Is it approaching EOL or deprecated?
- Is it appropriate for Colppy's scale (~108 repos, 207 tables, Argentine SaaS for PyMEs)?
- Does the proposed version actually exist on the target service?

Example gap: "MariaDB 10.11 is supported on standard RDS but NOT on Aurora Serverless v2. Current infra uses Aurora Serverless v2 exclusively. Adopting MariaDB would require leaving Aurora entirely."

#### Lens 2: Migration Path Reality

For each proposed migration, check:
- Does an official, documented upgrade path exist?
- Is it in-place or does it require dump+restore / DMS?
- What known breaking changes exist along the path?
- Are intermediate versions required? (e.g., MySQL 5.6 → 5.7 → 8.0, not direct)
- Does the proposal account for stored procedures, functions, triggers?
- Cross-reference with known issues in the system baseline (error codes, encoding, auth plugins)

Example gap: "MySQL 5.6 → MariaDB requires logical dump+restore. 270 stored procedures and 26 functions need syntax validation. No mention of the 3 confirmed MySQL 8.0 breaks (ERROR 1055, 1064, 1292)."

#### Lens 3: Current System Conflicts

For each proposal, check:
- Does it duplicate something that already exists? (e.g., new React setup when single-spa with 6 inactive MFEs exists)
- Does it contradict a current architectural decision?
- Does it ignore a constraint in the baseline? (e.g., shared MySQL database used by 3 different access patterns)
- Would it create a new inconsistency? (e.g., adding a 4th DB access pattern)
- Does it account for the dual auth system?

Example gap: "Proposal creates new React base project with Webpack/Vite, but app_root already uses single-spa with Webpack 5 + SystemJS 6.8.3 and 6 inactive MFEs exist (dashboard, sales, mercado_pago). Why build from scratch instead of activating existing MFEs?"

#### Lens 4: Missing Considerations

For each proposal, check what's NOT mentioned:
- Known issues from the baseline that the proposal doesn't address
- AWS Well-Architected principles that aren't covered (especially Security and Reliability pillars)
- Rollback/failure scenarios
- Cross-system impacts (e.g., Frontera + Benjamin sharing same DB during migration)
- Data integrity validation strategy
- Performance testing plan
- Cost implications (e.g., moving from serverless to provisioned instances)

Example gap: "No mention of caching_sha2_password auth plugin blocker. No mention of latin1 encoding in 9 tables. No cost analysis of moving from Aurora Serverless v2 (pay-per-ACU) to provisioned RDS MariaDB instances."

#### Lens 5: Sequencing Risk

Across ALL proposals together, check:
- Hidden dependencies between workstreams
- Multiple proposals modifying the same system component (especially the shared MySQL database)
- Natural ordering that would reduce risk
- What happens if one workstream fails or stalls — does it block others?
- Resource contention (same engineers assigned to multiple parallel workstreams)

Example gap: "DB migration (KAN-12133) and FusionAuth RBAC (KAN-12132) both require schema changes on the same MySQL database. Running in parallel risks migration conflicts. Recommend: complete DB migration first, then layer RBAC on the stable new DB."

### Step 4: Produce Output

Format the analysis using the structure below. Be specific — cite ticket numbers, AWS doc references, and baseline facts. Every gap MUST have evidence, not speculation.

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

[Repeat for each critical gap — maximum 7]

---

## Caution Areas (valid approach but incomplete)

### [Area title]
- **What's proposed works, but:** [what's missing or underspecified]
- **Consider:** [suggestion to strengthen the proposal]

[Repeat for each caution area]

---

## Confirmed Alignments (no action needed)

- [One-liner per alignment — no elaboration needed]

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
| **Critical Gap** | Must address before proceeding | Technology not supported on target service, official migration path doesn't exist, security vulnerability, data loss risk, cost explosion |
| **Caution Area** | Valid but incomplete | Missing rollback plan, unaddressed edge case, incomplete acceptance criteria, unmentioned dependency, missing cost analysis |
| **Confirmed Alignment** | No action needed | Proposal matches AWS best practice AND current system reality AND has no blind spots |

## Guardrails

- This is a REVIEW tool, not a DESIGN tool. Identify gaps, don't rewrite the architecture.
- Every gap must cite evidence (AWS doc reference, baseline fact, or Jira ticket content). No speculation.
- Do not speculate. If unsure whether something is a gap, flag it as Caution Area, not Critical.
- Do not repeat the proposal back to the user. They already read the tickets. Focus on what's MISSING.
- Keep Critical Gaps to genuine blockers — maximum 7. If everything is "critical," nothing is.
- When in doubt about severity, downgrade to Caution Area. False positives erode trust.
- Always include Sequencing Recommendations. Parallel workstreams are where the biggest hidden risks live.
