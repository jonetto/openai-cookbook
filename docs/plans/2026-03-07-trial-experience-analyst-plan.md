# Trial Experience Analyst — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a multi-source agent that connects Intercom friction, Mixpanel behavior, and HubSpot conversion data to produce trial experience reports for Marketing and Product.

**Architecture:** One agent (`trial-experience-analyst.md`) backed by two new skills (`user-lifecycle-framework`, `trial-data-model`) inside the existing `colppy-customer-success` plugin. Auto-discovered by convention — no plugin.json changes needed.

**Tech Stack:** Markdown agent/skill definitions (no code). Leverages existing MCP tools (Intercom, Mixpanel, HubSpot) and scripts (`analyze_onboarding.py`, `llm_classify.mjs`, `export_cache_for_local_scan.mjs`).

**Design doc:** `docs/plans/2026-03-07-trial-experience-analyst-design.md`

---

## Task 1: Create Skill — User Lifecycle Framework

**Files:**
- Create: `plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md`

**Context:** This skill encodes the "Framework de Product Insights en Producto" (source: `.firecrawl/framework-producto.md`) as machine-readable context for agents. It defines behavioral personas, trial lifecycle stages, activation thresholds, and the wizard-vs-reality gap.

**Step 1: Create the skill directory**

```bash
mkdir -p plugins/colppy-customer-success/skills/user-lifecycle-framework
```

**Step 2: Write the SKILL.md**

Create `plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md` with:

```markdown
---
name: user-lifecycle-framework
description: >
  Colppy's product lifecycle framework: behavioral personas, trial stages,
  activation thresholds, PQL definitions, and user lifecycle cuts (beginners,
  retained, resurrected, dormants). Source of truth for understanding how
  users move through the product. Apply when analyzing trial experience,
  activation, onboarding, retention, or behavioral segmentation.
---

# User Lifecycle Framework — Colppy

Encoded from Colppy's "Framework de Product Insights en Producto."
Source of truth for how users progress through the product lifecycle.

---

## Trial Window

| Parameter | Value |
|-----------|-------|
| Duration | 7 days free |
| Plan during trial | "Pendiente de Pago" (in Mixpanel events and Colppy DB) |
| Conversion signal | First payment (`primerPago=1` in Colppy) |
| Activation signal | `activo=true` + `fecha_activo` populated in HubSpot |

---

## Behavioral Personas

Determined by **product behavior** (Mixpanel events), NOT by wizard `rol_wizard` selection.
A user who selects "Contador" in the wizard but only does compra/venta is an **Operador**, not a true accountant.

| Persona | Critical Events (Mixpanel) | Description |
|---------|---------------------------|-------------|
| **Lleva la administración** | `Generó comprobante de compra`, `Generó comprobante de venta` | Core persona — invoicing, buying/selling. Most common. |
| **Lleva la contabilidad** | Accounting events (asientos contables, plan de cuentas) | True bookkeeping — journal entries, chart of accounts |
| **Lleva inventario** | Inventory events (stock movements, item management) | Inventory-focused usage |
| **Operador** | Same events as "Lleva la administración" BUT `contact_es_contador=true` AND operates across multiple client `id_empresa` values | Accountant behaving as administrator for their clients' companies |

### Wizard vs Reality Gap

The wizard captures *declared intent*. Mixpanel captures *actual behavior*. These frequently diverge:

| Wizard `rol_wizard` | Actual Behavior | Classification |
|---------------------|-----------------|----------------|
| Contador → operates client empresas | Admin events across multiple id_empresa | **Operador** (accountant-as-admin) |
| Contador → does contabilidad | Accounting events (asientos) | **Contador** (true accountant) |
| Pyme → does admin | Compra/venta events | **Pyme admin** (expected, aligned) |
| Pyme → barely uses product | Few/no critical events in 7-day trial | **At risk** — not activated |

---

## Trial Lifecycle Stages

| Stage | Signal | Source | Funnel Name |
|-------|--------|--------|-------------|
| **Evaluating** | Signed up + validated email | HubSpot `createdate` | MQL |
| **Activated** | Performed critical event during trial | Mixpanel + HubSpot `activo=true`, `fecha_activo` | PQL |
| **Converted** | First payment made | Colppy `primerPago=1` / HubSpot deal `hs_is_closed_won` | Customer |
| **Churned from trial** | 7 days passed, no payment | Absence of primerPago after trial window | — |

---

## Activation Threshold

**Default (from historical Mixpanel Signal report):** 4+ comprobantes de compra within 7 days correlates with week-2 retention.

**IMPORTANT:** This threshold needs periodic refresh. It can be validated by:
1. Mixpanel UI → Signal report (fast, manual)
2. API Method B: `run_retention_query` + `run_segmentation_query` to compute conversion rate at N=1,2,3,4,5,6+ events (automatable)

The threshold is a correlation, not causation. Use it as a health indicator, not a guarantee.

---

## User Lifecycle Cuts

From the lifecycle framework. These classify ALL active users, not just trial:

| Cut | Definition | Strategy |
|-----|-----------|----------|
| **Beginners (Nuevos)** | First time using the product in the period | First impression — critical window for activation |
| **Retained (Current)** | Consistent usage over time | Push toward power user; potential champions |
| **Resurrected (Revividos)** | Were active, went dormant, came back | Cheaper to reactivate than acquire new |
| **Dormants (Dormidos)** | Were active, now inactive | Understand pre-churn patterns |

---

## Health Metrics

| Metric | Formula | Source | Interpretation |
|--------|---------|--------|----------------|
| **Pulse** | (New + Resurrected) / Dormants | Mixpanel lifecycle | >1 = growing, <1 = shrinking |
| **Stickiness** | Days per month user performs critical event | Mixpanel | Higher = more engaged. Retained users typically 5-7pp above beginners |
| **PQL rate** | Activated / MQLs | HubSpot `activo` + `fecha_activo` | Target: >40% |
| **Trial conversion** | Converted / MQLs | HubSpot deals / Colppy primerPago | — |

---

## Mixpanel Custom Events Reference

| Custom Event | Component Events | Persona |
|-------------|-----------------|---------|
| Eventos clave del usuario que lleva la administración | Generó comprobante de compra + Generó comprobante de venta | Lleva la administración |
| (to be confirmed) | Accounting-specific events | Lleva la contabilidad |
| (to be confirmed) | Inventory-specific events | Lleva inventario |

**Note:** Exact Mixpanel event names for contabilidad and inventario personas need confirmation from the Mixpanel project. The administración events are confirmed.
```

**Step 3: Verify the file exists and renders correctly**

```bash
head -5 plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md
```

Expected: YAML frontmatter starting with `---` and `name: user-lifecycle-framework`

**Step 4: Commit**

```bash
git add plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md
git commit -m "feat(customer-success): add user-lifecycle-framework skill

Encodes Framework de Producto as machine-readable context:
behavioral personas, trial stages, activation thresholds,
wizard-vs-reality gap, and lifecycle cuts."
```

---

## Task 2: Create Skill — Trial Data Model

**Files:**
- Create: `plugins/colppy-customer-success/skills/trial-data-model/SKILL.md`

**Context:** This skill documents how to join a user across Intercom, Mixpanel, and HubSpot. It defines the identity keys (email at person level, id_empresa at subscription level), what each system contributes, and which tools/scripts to use.

**Step 1: Create the skill directory**

```bash
mkdir -p plugins/colppy-customer-success/skills/trial-data-model
```

**Step 2: Write the SKILL.md**

Create `plugins/colppy-customer-success/skills/trial-data-model/SKILL.md` with:

```markdown
---
name: trial-data-model
description: >
  Cross-system data model for trial user analysis: how to join Intercom
  conversations, Mixpanel product events, and HubSpot CRM data for the
  same user. Defines identity keys, what each system contributes, and
  available tools/scripts. Apply when analyzing trial users across
  multiple data sources.
---

# Trial Data Model — Cross-System Joins

How to connect a single user's experience across Intercom, Mixpanel, and HubSpot.

---

## Identity Levels

| Level | Key | Meaning | Example |
|-------|-----|---------|---------|
| **Person** | `email` | The human being | `maria@estudio.com` |
| **Subscription** | `id_empresa` | The company/plan they operate in | `500` (Maria's firm), `501` (her client) |

A single person (email) can have Mixpanel events across multiple `id_empresa` values — this is the **Operador** signal (accountant operating client companies).

---

## Identity Map

```
                    email (person)
    Intercom ◄──────────────────► HubSpot ◄──────► Mixpanel
  (conversations)                (contacts)      (distinct_id = email)
                                    │
                              id_empresa (subscription)
                                    │
                              Colppy DB ◄──────► Mixpanel
                            (billing, plans)   (id_empresa = super property
                                                on each event = which
                                                subscription the action
                                                was performed in)
```

---

## What Each System Contributes

| Question | Source | Tool / Method |
|----------|--------|---------------|
| What did the user struggle with? | **Intercom** | `scan_customer_feedback` or `scan_full_text` with `team_assignee_id: "2334166"` (Primeros 90 días) |
| What topics are trending? | **Intercom** | `analyze_onboarding.py --llm` or `llm_classify.mjs` with topic config |
| Is the user accountant or SMB? | **Intercom** `contact_es_contador` / **HubSpot** company `type` | Cached in Intercom export; fallback: HubSpot API by email |
| What did the user do in product? | **Mixpanel** | `run_segmentation_query` on critical events, filter by plan="Pendiente de Pago" |
| How far through the activation funnel? | **Mixpanel** | `run_funnels_query` (login → critical event → payment) |
| Did they activate (PQL)? | **HubSpot** | Contact: `activo=true` AND `fecha_activo` populated |
| Did they convert to paid? | **HubSpot** / **Colppy** | Deal `hs_is_closed_won=true` or Colppy `primerPago=1` |
| What behavioral persona? | **Mixpanel** | Event type distribution per distinct_id / id_empresa |
| What wizard role did they select? | **HubSpot** | Contact property `rol_wizard` |

---

## Tools Available

### Intercom (customer-success plugin MCP)

| Tool | Purpose | Speed |
|------|---------|-------|
| `scan_customer_feedback` | Scan first message by keywords + team inbox | Fast |
| `scan_full_text` | Scan all messages including agent replies | Slower — keep date ranges narrow (5-7 days) |
| `get_conversation_feedback` | Deep-dive specific conversation IDs | Per-conversation |
| `analyze_onboarding_first_invoice` | Segmented onboarding classification | Batch analysis |

### Mixpanel (Mixpanel MCP)

| Tool | Purpose |
|------|---------|
| `run_segmentation_query` | Event counts over time, breakdown by property |
| `run_funnels_query` | Multi-step conversion funnels |
| `run_retention_query` | Cohort retention (born_event → return_event) |

### HubSpot (HubSpot MCP)

| Tool | Purpose |
|------|---------|
| `search_crm_objects` | Search contacts/deals by filters |
| `get_crm_objects` | Fetch specific records by ID |

### Scripts (run via Bash)

| Script | Purpose |
|--------|---------|
| `tools/scripts/intercom/export_cache_for_local_scan.mjs` | Export Intercom conversations with contact attributes to local cache |
| `tools/scripts/intercom/analyze_onboarding.py` | Segmented onboarding analysis (--user-type smb/accountant --llm) |
| `plugins/colppy-customer-success/scripts/llm_classify.mjs` | LLM topic classification with few-shot learning |

---

## HubSpot Contact Properties for Trial Analysis

Always request these when querying trial contacts:

```
email, createdate, lifecyclestage, lead_source, rol_wizard,
activo, fecha_activo, hs_v2_date_entered_opportunity,
hs_v2_date_entered_customer, num_associated_deals
```

### Filtering Rules

- **Exclude invitations:** `lead_source HAS_PROPERTY` AND `lead_source NEQ "Usuario Invitado"` (both filters required — NEQ alone includes nulls)
- **Timezone:** HubSpot API returns UTC. Argentina is UTC-3. ~25 contacts at month boundaries may shift — acceptable.

---

## Intercom Cache Convention

Cached exports live in:
```
plugins/colppy-customer-success/skills/intercom-developer-api-research/cache/
  conversations_YYYY-MM-DD_YYYY-MM-DD_team2334166.json
```

Check for existing caches before making fresh API calls. If cache covers the requested period, use it.

---

## Segmentation Logic

| Segment | Signal | Source |
|---------|--------|--------|
| **SMB** | `contact_es_contador = false` or company type = "Cuenta Pyme" | Intercom export / HubSpot |
| **Accountant** | `contact_es_contador = true` or company type in ACCOUNTANT_COMPANY_TYPES | Intercom export / HubSpot |
| **Operador** (sub-segment of Accountant) | Accountant + admin events across multiple id_empresa | Mixpanel behavioral analysis |
```

**Step 3: Verify**

```bash
head -5 plugins/colppy-customer-success/skills/trial-data-model/SKILL.md
```

Expected: YAML frontmatter with `name: trial-data-model`

**Step 4: Commit**

```bash
git add plugins/colppy-customer-success/skills/trial-data-model/SKILL.md
git commit -m "feat(customer-success): add trial-data-model skill

Cross-system identity map and tool reference for joining
Intercom, Mixpanel, and HubSpot data during trial analysis."
```

---

## Task 3: Create Agent — Trial Experience Analyst

**Files:**
- Create: `plugins/colppy-customer-success/agents/trial-experience-analyst.md`

**Context:** This is the main agent. It follows the same pattern as `colppy-revops/agents/reconciliation-analyst.md`: YAML frontmatter with trigger examples, then a system prompt with data model, workflow steps, output tables, and constraints. The agent orchestrates Intercom, Mixpanel, and HubSpot to produce a unified trial experience report.

**References to study before writing:**
- `plugins/colppy-revops/agents/reconciliation-analyst.md` — structural pattern (frontmatter + examples + workflow)
- `plugins/colppy-revops/agents/facturacion-analyst.md` — simpler example of same pattern
- `docs/plans/2026-03-07-trial-experience-analyst-design.md` — full design with all tables and workflow steps

**Step 1: Create the agents directory**

```bash
mkdir -p plugins/colppy-customer-success/agents
```

**Step 2: Write the agent**

Create `plugins/colppy-customer-success/agents/trial-experience-analyst.md` with the full agent definition. The content should include:

1. **YAML frontmatter** with:
   - `name: trial-experience-analyst`
   - `description:` with 4-5 trigger examples (matching reconciliation-analyst pattern)
   - `model: inherit`
   - `color: green`

2. **System prompt** containing:
   - Role statement: "You are a Colppy trial experience analyst..."
   - Data model reference (behavioral personas table, trial stages table)
   - Cross-system identity explanation (email = person, id_empresa = subscription)
   - Tools and scripts reference tables
   - **Workflow steps** (from design doc):
     - Step 1: Determine cohort & scope
     - Step 2: Intercom friction analysis (check cache → export if needed → classify)
     - Step 3: Mixpanel behavioral analysis (segmentation + funnel queries)
     - Step 4: HubSpot conversion cross-reference
     - Step 5: Present full results (4 tables: cohort summary, friction report, persona distribution, wizard-vs-reality matrix)
     - Step 6: Interpret & recommend (TL;DR, Marketing actions, Product actions, health score)
   - **Constraints** (read-only, never invent data, never skip tables, always segment by ICP, Argentine currency format)

**Source for full content:** Copy the Agent Workflow section from `docs/plans/2026-03-07-trial-experience-analyst-design.md` (lines 167-299) and adapt it into the agent markdown format, following the structure of `plugins/colppy-revops/agents/reconciliation-analyst.md`.

**Key structural elements to include:**

Frontmatter trigger examples (4-5, following this pattern):
```yaml
  <example>
  Context: User wants a trial experience report for a time period
  user: "Trial experience report for February"
  assistant: "I'll delegate this to the trial experience analyst to analyze Feb trial cohort across Intercom, Mixpanel, and HubSpot."
  <commentary>
  Direct trial analysis request for a specific period.
  </commentary>
  </example>
```

Output tables (from design doc section 5):
- 5a: Cohort Summary (MQL, PQL, conversion by SMB vs Accountant)
- 5b: Friction Report (Intercom topics by segment with clickable URLs)
- 5c: Behavioral Persona Distribution (admin, contabilidad, operador, not activated)
- 5d: Wizard vs Reality Matrix (declared role vs actual behavior vs conversion)

Recommendation sections:
- For Marketing: UTM analysis, persona mismatch, messaging
- For Product: friction ranking, feature gaps, stickiness signal
- Health score: Healthy / Needs attention / At risk (thresholds from design doc)

**Step 3: Verify agent is discovered**

```bash
head -5 plugins/colppy-customer-success/agents/trial-experience-analyst.md
```

Expected: YAML frontmatter with `name: trial-experience-analyst`

Also verify the existing agents are still picked up:
```bash
ls plugins/colppy-revops/agents/
```

Expected: `facturacion-analyst.md  reconciliation-analyst.md`

**Step 4: Commit**

```bash
git add plugins/colppy-customer-success/agents/trial-experience-analyst.md
git commit -m "feat(customer-success): add trial-experience-analyst agent

Multi-source agent connecting Intercom friction, Mixpanel behavior,
and HubSpot conversion for trial cohort analysis. Produces segmented
reports with behavioral persona detection and wizard-vs-reality matrix."
```

---

## Task 4: Verify Full Plugin Structure

**Step 1: Verify all new files exist in correct locations**

```bash
find plugins/colppy-customer-success/agents -name "*.md" -type f
find plugins/colppy-customer-success/skills/user-lifecycle-framework -name "*.md" -type f
find plugins/colppy-customer-success/skills/trial-data-model -name "*.md" -type f
```

Expected:
```
plugins/colppy-customer-success/agents/trial-experience-analyst.md
plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md
plugins/colppy-customer-success/skills/trial-data-model/SKILL.md
```

**Step 2: Verify YAML frontmatter parses correctly for all three files**

```bash
for f in \
  plugins/colppy-customer-success/agents/trial-experience-analyst.md \
  plugins/colppy-customer-success/skills/user-lifecycle-framework/SKILL.md \
  plugins/colppy-customer-success/skills/trial-data-model/SKILL.md; do
  echo "=== $f ==="
  head -3 "$f"
  echo ""
done
```

Expected: Each file starts with `---` on line 1, followed by `name:` on line 2.

**Step 3: Verify plugin.json still valid (no changes needed)**

```bash
cat plugins/colppy-customer-success/.claude-plugin/plugin.json
```

Expected: Unchanged — agents and skills are auto-discovered by convention.

---

## Task 5: Smoke Test — Dry Run the Agent

**Context:** Test the agent by asking a trial experience question. This validates that:
1. The agent is discovered and triggered
2. The skills are loaded as context
3. The workflow steps execute in order

**Step 1: Test agent trigger**

In a new Claude Code session, ask:
```
How is onboarding going this week?
```

Expected: Claude should delegate to the `trial-experience-analyst` agent (visible in the output as a green-colored subagent).

**Step 2: Verify the agent attempts the workflow**

The agent should:
1. Check for cached Intercom exports
2. Attempt Mixpanel queries (may fail if MCP not connected — that's OK for smoke test)
3. Attempt HubSpot queries
4. Present whatever partial results are available

**Step 3: Note any issues for iteration**

Common issues to watch for:
- Agent not triggered (description needs better trigger keywords)
- Mixpanel event names wrong (update `user-lifecycle-framework` skill)
- HubSpot filter syntax wrong (update `trial-data-model` skill)
- Output tables missing columns (update agent workflow section)

---

## Summary

| Task | Creates | Depends On |
|------|---------|------------|
| 1 | `skills/user-lifecycle-framework/SKILL.md` | — |
| 2 | `skills/trial-data-model/SKILL.md` | — |
| 3 | `agents/trial-experience-analyst.md` | Tasks 1 & 2 (references both skills) |
| 4 | Verification | Tasks 1, 2, 3 |
| 5 | Smoke test | Task 4 |

Tasks 1 and 2 are independent and can be done in parallel.
Task 3 depends on 1 and 2 being committed (so the agent can reference the skills).
Tasks 4 and 5 are sequential verification.

---

*Generated: 2026-03-07*
