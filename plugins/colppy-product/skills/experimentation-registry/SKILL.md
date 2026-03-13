---
name: experimentation-registry
description: >
  Colppy's feature flag and experiment registry — decision framework, lifecycle
  management, and active flag tracking. Apply when designing new features,
  troubleshooting product problems, brainstorming solutions, or reviewing
  rollout strategy. This skill ensures every product conversation considers
  whether a feature gate, experiment, or dynamic config is appropriate.
---

# Experimentation Registry

Decision framework and living registry for Mixpanel Feature Flags & Experiments at Colppy.

Full technical reference (SDK, API, assignment keys): `docs/mixpanel-feature-flags.md`

---

## When to Use What

Every product decision falls into one of these patterns. Ask this question first:

| You're thinking... | Use | Why |
|---------------------|-----|-----|
| "We know what to build, let's ship safely" | **Feature Gate** | Gradual rollout with kill-switch. No measurement needed — just risk management. |
| "We have two ideas, which one works better?" | **Experiment** | A/B test with statistical rigor. Data decides, not opinions. |
| "We need to tune copy/limits/thresholds" | **Dynamic Config** | Change values without deployment. No variants, just configuration. |
| "Regulatory change, must ship now" | **Feature Gate at 100%** | Compliance can't wait for gradual rollout, but kill-switch protects against bugs. |
| "We're not sure if users will even notice" | **Experiment** | If the change is subtle, you need measurement to know if it worked. |
| "Support tickets are spiking on a new feature" | **Feature Gate → disable** | Kill-switch is the emergency brake. Roll back to 0% instantly. |

### Feature Gate vs Experiment — The Core Distinction

**Feature Gate** = "We know WHAT, we're managing HOW FAST"
- Binary: on/off for targeted percentage
- Monitoring: watch dashboards for regressions
- Decision: PM expands or kills based on judgment
- Duration: temporary — graduate (hardcode) once at 100%

**Experiment** = "We don't know WHICH, so we measure BOTH"
- Variants: control + 1-4 alternatives, running simultaneously
- Measurement: `$experiment_started` event → Mixpanel statistical engine
- Decision: data decides — ship variant, ship none, or iterate
- Duration: runs until statistical significance or timeout
- Requires: pre-committed hypothesis, metrics, and decision rules

**Dynamic Config** = "We know WHAT, we need to tune HOW MUCH"
- Payload: JSON key-value pairs served at runtime
- No measurement: PM tunes values based on feedback/intuition
- Duration: can live forever — no graduation needed
- Use for: CTA copy, feature limits, thresholds, UI toggles

---

## Assignment Key Decision Tree

Choose the assignment key based on WHAT ENTITY the feature affects:

```
Is the feature pre-authentication (wizard, landing)?
  → device_id (Device level)

Is this a per-person experience (dashboard layout, notifications)?
  → distinct_id (User level)

Does this affect billing, fiscal, or regulatory rules?
  → company group (Company level = CUITFacturacion)
  ⚠ This affects ALL empresas under that CUIT

Does this affect plan features, activation, or module access?
  → product_id group (Product level = idEmpresaUsuario)
  ✓ This affects only that specific empresa/subscription
```

**Sample size implication**: Company-level experiments have fewer units than Product-level (one CUIT → many empresas). For faster significance, prefer `product_id` when both levels could work.

---

## Flag Lifecycle

```
draft → staging → production → [graduated | archived]
                      │
                      └── experiments: → analyzing → decided → graduated
```

| State | Meaning | Who | Next action |
|-------|---------|-----|-------------|
| **draft** | Spec written by PM, not yet in Mixpanel | PM | Create in Mixpanel staging UI |
| **staging** | Created in project 2797423, QA with whitelist | PM + QA | Validate in staging, create in prod |
| **production** | Live in project 2201475, rollout in progress | PM | Monitor metrics, expand or kill |
| **analyzing** | Experiment running, waiting for significance | PM + Data | Wait for stats, check SRM |
| **decided** | Experiment concluded: ship / kill / iterate | PM | Communicate decision, plan graduation |
| **graduated** | Winning behavior hardcoded, flag check removed | Engineering | Remove flag from Mixpanel |
| **archived** | Flag disabled, no longer needed | PM | Clean up registry |

**Hygiene rule**: Flags should not stay in `production` state indefinitely. Feature gates graduate within one quarter. Experiments have a pre-set duration. Dynamic configs are the exception — they can live as long as they're useful.

---

## Experiment Design Checklist

When the PM designs an experiment (with CPO agent guidance), the spec must include ALL of these:

1. **Hypothesis**: "Changing [X] will improve [metric] by [Y%] because [reasoning]"
2. **Variants**: control (current behavior) + variant_a [+ variant_b]
3. **Assignment key**: Which of the four levels? (with rationale)
4. **Primary metric**: The ONE metric that determines success
5. **Guardrail metric**: The metric that must NOT degrade (e.g., churn, support tickets, error rate)
6. **Secondary metrics**: Contextual metrics that explain WHY (optional but recommended)
7. **Statistical model**: Sequential (>10% expected lift, allows peeking) or Frequentist (<10%, must run full duration)
8. **Duration**: Sample size estimate OR minimum days
9. **Success criteria**: "[Primary metric] improves by [X%] at 95% confidence → Ship variant"
10. **Kill criteria**: "[Guardrail] degrades by [Y%] → Disable immediately"

---

## Naming Convention

```
{domain}_{feature}_{type}
```

| Part | Options | Examples |
|------|---------|---------|
| domain | `onboarding`, `invoice`, `tesoreria`, `compliance`, `dashboard`, `sueldos` | — |
| feature | descriptive snake_case | `wizard_step2`, `empty_state_guide`, `fce_checkbox` |
| type | `gate`, `experiment`, `config` | — |

Examples:
- `onboarding_product_tour_experiment`
- `invoice_empty_state_gate`
- `compliance_fce_mipyme_gate`
- `dashboard_module_discovery_experiment`
- `onboarding_cta_copy_config`

---

## Registry

The registry tracks all flags across their lifecycle. Each entry is added when the PM specs a flag (draft state) and updated as it progresses.

**Current flags**: See `registry.md` in this skill directory.

**When to consult the registry**:
- Before designing a new flag → check for conflicts or overlap with existing flags
- During `/product-review` → reference active experiments that may interact
- When troubleshooting → check if a flag could be causing the issue
- Quarterly → audit for zombie flags that should be graduated or archived
