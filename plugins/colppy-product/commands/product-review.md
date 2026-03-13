---
name: product-review
description: Run a full PLG product review on any signal — support pattern, metric drop, regulatory change, or feature request. Outputs activation diagnosis, bowling alley bumper designs, and a Jira-ready spec. Usage: /product-review <brief description of the problem or signal>
---

# /product-review

Run a structured CPO-level product review using the PLG bowling alley framework. Takes any signal and produces: diagnosis → bumper designs → prioritized spec → handoff.

## Usage

```
/product-review IVA Simple generating support tickets — users can't import
/product-review Why is FCE checkbox adoption low?
/product-review ARCA is adding mandatory Tipo de Comprobante field in May
/product-review We want to add activity preview before ARCA sync
```

## Reference

Read `docs/plg-framework.md` before executing — it contains all framework definitions, bumper types, and Colppy-specific patterns.

---

## Execution

### Step 1 — Classify the Signal

Determine which type of problem this is:

| Type | Signal | Approach |
|------|--------|----------|
| **Activation gap** | Feature exists, low usage | Trace friction → bumper design |
| **Compliance breaking change** | New ARCA/AFIP requirement | Pre-launch bumper spec |
| **Support spike** | Intercom tickets on specific topic | Root cause → emergency bumper |
| **Feature request** | New capability needed | Activation moment → spec |
| **Prioritization** | Multiple competing options | Effort/impact ranking |

### Step 2 — Diagnose the Friction

For activation gap or support spike problems:

1. **Define the pin**: What is the Aha! moment for this feature? (see `docs/plg-framework.md` §3)
2. **Identify the gutters**: Where does the user fall off before reaching the pin?
3. **Validate**: If possible, confirm friction in staging (`https://app.stg.colppy.com/`) or trace the code. Don't spec what you haven't confirmed.

Ask:
- Is this a **discovery gap** (users don't know the feature exists)?
- Is this an **empty state gap** (feature loads broken with no guidance)?
- Is this a **prerequisite gap** (feature requires setup that users don't know about)?
- Is this a **import/bulk action gap** (breaking change to a template or API)?

### Step 3 — Design the Bumpers

For each gutter identified, design the appropriate bumper (in priority order):

**Tier 1 — Product Bumpers** (spec for engineering):

```
Bumper: [type]
Where: [exact UI location — component, page, modal]
Trigger condition: [precise state in pseudocode, e.g.: actividadesARCA == [] AND condicionIva == 'RI']
Copy: "[exact message text — brief, action-oriented]"
CTA: "[button label]" → [deep-link destination]
Auto-resolves when: [condition]
Effort: [Low = frontend only | Medium = needs API | High = needs new data model]
```

**Tier 2 — Conversational Bumpers** (spec for CS/RevOps):
```
Channel: [Intercom Series | In-app message]
Trigger event: [behavioral event name]
Trigger condition: [exact logic]
Message: "[copy]"
CTA: "[label]" → [URL]
Sends: [once | every N days until resolved]
```

### Step 4 — Feature Flag & Rollout Strategy

For every feature or fix, define the rollout plan using Mixpanel Feature Flags. References: `docs/mixpanel-feature-flags.md` (technical), `skills/experimentation-registry/SKILL.md` (decision framework + registry). Check the registry for conflicts with existing flags before designing a new one.

```
Flag key: {domain}_{feature}_{type}  (e.g., invoice_new_flow_gate)
Flag type: Feature Gate | Experiment | Dynamic Config
Assignment key: device_id | distinct_id | company (group) | product_id (group)
Rollout plan: [gradual percentages or full rollout for compliance]
Kill-switch criteria: [metric that triggers instant disable]
Success criteria: [metric that triggers 100% rollout]
```

**If Experiment:**
```
Hypothesis: [changing X will improve Y by Z%]
Variants: control, variant_a [, variant_b]
Primary metric: [conversion event or rate]
Guardrail metric: [metric that must NOT degrade, e.g. churn, support tickets]
Statistical model: Sequential (large effects >=10%) | Frequentist (small effects ~1%)
Sample size / duration: [estimated users or days needed]
```

### Step 5 — Priority Table

Output a prioritization table:

| # | Bumper | Effort | Impact | Owner | Flag Key | Ship with feature? |
|---|--------|--------|--------|-------|----------|-------------------|
| 1 | ... | Low/Med/High | High/Med/Low | Eng/CS/RevOps | flag_key | Yes/No |

**Rule**: Tier 1 bumpers (empty state, pre-failure, setup indicator) always ship with the feature behind a feature flag. Tier 2 bumpers ship within 2 weeks of launch.

### Step 6 — Jira Spec Output

For each Tier 1 bumper, output a Jira-ready ticket:

```
Title: [Bumper type] — [Feature name] — [brief description]
Type: Bug (if fixing existing friction) | Story (if new bumper)
Points: [1-3 based on effort]

Description:
**Problem**: [1 sentence — what breaks and when]
**User impact**: [support ticket volume or activation drop, if known]

**Acceptance criteria**:
- [ ] When [trigger condition], show [message]
- [ ] CTA "[label]" links to [destination]
- [ ] Bumper auto-dismisses when [condition]
- [ ] Does not show when [exclusion condition]

**Design notes**: [any visual guidance]
**Backend dependency**: [yes/no — what's needed]
```

---

## Output Format

Always structure the full output as:

1. **Signal classification** — 1 line
2. **Activation diagnosis** — pin + gutters (2-3 paragraphs)
3. **Bumper designs** — each bumper in the spec format above
4. **Feature flag & rollout strategy** — flag key, type, assignment, rollout plan, experiment design if applicable
5. **Priority table** — effort × impact ranking (includes flag key column)
6. **Jira specs** — one per Tier 1 bumper, ready to paste (include flag key in acceptance criteria)
7. **Handoff** — who gets what (Eng spec | CS Intercom Series | PM creates flag in Mixpanel UI | CPO ratification needed?)

---

## Colppy Context

- **Staging**: `https://app.stg.colppy.com/` · test user `joaquin.baigorri@colppy.com` · pass `Colppy2023`
- **Two ICPs**: Cuenta Contador (accountant firms) vs Cuenta Pyme (direct SMBs) — may need different bumpers
- **Compliance rule**: Every ARCA/AFIP feature ships with Tier 1 bumpers. No exceptions.
- **PLG framework**: Full reference in `docs/plg-framework.md`
