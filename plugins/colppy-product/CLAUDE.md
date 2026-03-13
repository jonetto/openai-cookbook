# Colppy Product — Plugin Instructions

## Purpose

This plugin contains product strategy and bug investigation agents for Colppy. The CPO agent bridges signal to execution (specs, bumper designs, prioritization). The Bug Detective and Bug Fixer agents handle defect triage and resolution.

## Bug Investigation Agents

| Agent | Role | Access |
|-------|------|--------|
| `bug-detective` | Read-only investigator — correlates Intercom, Jira, commits, and DB signals into a structured triage report | Read-only everywhere + Jira comments |
| `bug-fixer` | Code-writing agent — receives a triage report, clones the repo, writes the minimal fix, opens a PR | Code write (in worktree only) |

**Handoff**: Detective investigates → triage report → user decides → Fixer executes. Human-gated.

**Command**: `/investigate-bug KAN-1234` or `/investigate-bug "description"` or `/investigate-bug` (proactive scan)

**Triage cache**: `data/bug-triage/` — JSON files, local only, .gitignored.

## CPO Agent Capabilities

The CPO agent operates in two modes:

1. **Reactive mode** (default): Takes a signal (support spike, metric drop, feature request) → diagnoses → designs bumpers → specs for handoff
2. **Onboarding Pulse mode**: Proactive weekly funnel monitoring — measures the product funnel from **Mixpanel** (source of truth), with HubSpot providing cohort classification (`fit_score_contador` ≥40 = high-touch, <40 = no-touch). Two explicit cohorts measured separately since **2026-03-13** (day zero). Pre-change baseline saved in `data/onboarding-pulse-baseline-prechange.md`. Produces funnel health dashboard with cohort split and diagnoses anomalies through the bowling alley framework with two-horizon output (Product Requirement + Bumper containment). Trigger with: *"run the onboarding pulse"* or *"how is the product funnel this week?"*

## Available Data Sources

The CPO agent does not query data directly — it delegates to specialist agents and then synthesizes:

| Signal | Agent/Tool | What it gives you |
|--------|-----------|-------------------|
| Support patterns | `trial-experience-analyst`, `churn-investigator` (colppy-customer-success) | Intercom friction by topic, volume, ICP |
| Product behavior | Mixpanel via `tools/scripts/mixpanel/` | Activation rates, feature usage, trial cohorts |
| Revenue/conversion | `saas-metrics-analyst` (colppy-revenue) | Conversion by segment, MRR impact |
| Architecture risk | `architecture-reviewer` (colppy-architecture-reviewer) | Technical feasibility, breaking changes |
| Staging validation | Playwright MCP | Live confirmation of friction in staging |
| Feature flags | Mixpanel Feature Flags (Enterprise) | Controlled rollouts, A/B experiments, dynamic configs |

## PLG Framework Reference

This plugin uses Wes Bush's **bowling alley framework** as the default mental model:
- **Pin** = Aha! moment (first time user gets value from a feature)
- **Gutters** = Activation drop-offs
- **Bumpers** = Product and conversational guardrails

Bumper priority order:
1. Empty state (fix at the moment of friction)
2. Pre-failure (prevent before it breaks)
3. Setup indicator (make prerequisite state visible)
4. Onboarding checklist (proactive before first use)
5. Intercom Series (conversational fallback)

## Feature Flags & Experiments

Every feature shipped should include a **rollout strategy** using Mixpanel Feature Flags. Full technical reference: `docs/mixpanel-feature-flags.md`.

- **Feature Gates**: On/off toggles for gradual rollout (5% → 25% → 50% → 100%)
- **Experiments**: A/B tests with Mixpanel's statistical engine (Sequential or Frequentist models)
- **Dynamic Configs**: JSON payloads to tune UI behavior without redeployment
- **Kill-switch**: Every flag can be instantly disabled if metrics drop
- **Four assignment levels** matching Mixpanel data model: `device_id` (pre-auth), `distinct_id` (per-user), `company` group (per-CUIT billing entity), `product_id` group (per-empresa subscription)
- **No CRUD API**: Flags must be created in Mixpanel UI — agent specs the design, PM/eng creates it

## Colppy Product Conventions

- **Compliance features** (ARCA/AFIP) always carry activation risk — every new mandatory field needs bumpers at launch, not as a follow-up
- **Two ICPs behave differently**: Cuenta Contador manages multiple companies (bulk actions matter); Cuenta Pyme is self-service (onboarding clarity matters)
- **Staging**: `https://app.stg.colppy.com/` — same user accounts as production, test user `joaquin.baigorri@colppy.com`
- **Every feature ships behind a flag**: Deploy code with flag key + safe fallback, then rollout via Mixpanel UI. Compliance features use flags too (for kill-switch), but rollout at 100% immediately
