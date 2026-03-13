# Mixpanel Feature Flags & Experiments — Technical Reference

> **Status**: Included in Colppy's Mixpanel Enterprise subscription. **Not yet integrated in the codebase.**
> Last updated: 2026-03-12

## Overview

Mixpanel Feature Flags decouple deployment from release. Three flag types:

| Type | Purpose | Example |
|------|---------|---------|
| **Feature Gate** | On/off toggle for targeted users | `enable_new_invoice_flow` |
| **Experiment** | A/B testing with variant measurement | `onboarding_wizard_v2` |
| **Dynamic Config** | JSON payload without redeployment | `{"cta_text": "Probar gratis", "max_items": 50}` |

## Key Concepts

- **Flag Key**: Unique identifier used in SDK code (e.g., `new_tesoreria_flow`)
- **Variant Assignment Key**: Randomization unit — `distinct_id` (logged-in), `device_id` (pre-auth), or group key like `company_id`
- **Variants**: Up to 5 per flag (e.g., control, variant_a, variant_b)
- **Sticky Variants**: Consistent assignment over time (Control is always non-sticky to allow upward migration)
- **Rollout Groups**: Up to 5 per flag — define who sees the flag via filters + percentage
- **Fallback Value**: Default when service unavailable

## Targeting

### Colppy's Four Data Levels in Mixpanel

Mixpanel tracks Colppy data at four hierarchical levels. Feature flags can target ANY of these levels via the Variant Assignment Key. Understanding this hierarchy is essential — choosing the wrong level means the flag targets the wrong entity.

| Level | Mixpanel Key | Colppy Source | Value Example | What It Represents |
|-------|-------------|---------------|---------------|-------------------|
| **Device** | `device_id` | Auto-generated | `mp-uuid-abc123` | Anonymous browser/device (pre-auth) |
| **User** | `distinct_id` | `idUsuario` (email) | `juan@empresa.com` | Individual person (cross-device after identify) |
| **Company** | Group `company` | `CUITFacturacion` | `30-71234567-9` | Billing/legal entity (CUIT). One company can have multiple product subscriptions |
| **Product** | Group `product_id` | `idEmpresaUsuario` | `41763` | Product subscription (empresa). Tied to plan, activation, usage |

**Hierarchy**: Device → User → Company → Product (one user can access multiple empresas; one CUIT can own multiple empresas; but each empresa has exactly one CUIT billing entity)

**How groups are set in production** (from [FuncionesGlobales.js:1206](github-jonetto/nubox-spa/colppy-app/resources/js/ColppyManager/FuncionesGlobales.js#L1206)):
```javascript
var companyGroupId = CUITFacturacion ? String(CUITFacturacion) : String(idEmpresaUsuario);
mixpanel.set_group('company', companyGroupId);       // Billing entity
mixpanel.set_group('product_id', String(idEmpresaUsuario));  // Product subscription
```

### Assignment Keys (choose ONE per flag, cannot change after enabling)

| Key | Mixpanel Type | Colppy Application |
|-----|--------------|-------------------|
| `device_id` | Device | Pre-auth flows: wizard, landing page experiments |
| `distinct_id` | User | Per-user UX: dashboard layout, notification preferences |
| `company` (group) | Company | Billing/fiscal: invoicing rules, condición IVA, ARCA compliance |
| `product_id` (group) | Product | Plan/subscription: feature entitlements, activation experiments, module access |

### Rollout Group Filters

1. **Cohort filters** — Mixpanel audiences (~2h refresh cadence)
2. **Runtime property filters** — Immediate: platform, country, plan, ICP type
3. **Runtime event filters** — Trigger on tracked actions (client SDKs only)

### QA Testing

Whitelist testers by `$email` property. Use this for staging validation before broad rollout.

## SDK Integration

### Client-Side (JavaScript Web) — For Colppy Frontend

**Minimum version**: `mixpanel-browser` v2.71.0

```javascript
// Initialization — add to existing mixpanel.init()
// Must pass BOTH group keys so flags can target either level
mixpanel.init("TOKEN", {
  flags: {
    context: {
      company: companyGroupId,          // Group key = CUITFacturacion (billing entity)
      product_id: idEmpresaUsuario,     // Group key = idEmpresaUsuario (subscription)
      custom_properties: {
        plan: planName,                 // For plan-based targeting
        icp_type: icpType,             // 'contador' | 'pyme'
        condicion_iva: condicionIva    // For compliance feature flags
      }
    }
  }
});

// Feature Gate (boolean on/off)
const showNewFlow = await mixpanel.flags.is_enabled("new_invoice_flow", false);

// Experiment Variant
const variant = await mixpanel.flags.get_variant_value("onboarding_experiment", "control");

// Sync versions (check areFlagsReady() first)
if (mixpanel.flags.areFlagsReady()) {
  const enabled = mixpanel.flags.isEnabledSync("new_invoice_flow", false);
}

// Context update (e.g., after company/empresa switch)
mixpanel.flags.update_context({
  company: newCUITFacturacion,
  product_id: newIdEmpresaUsuario,
  custom_properties: { plan: newPlan }
});
```

**Key behaviors:**
- `identify()` automatically triggers flag reload
- `is_enabled()` and `get_variant_value()` **auto-track** `$experiment_started` exposure events
- Initialization with `flags: true` triggers ONE outbound request that evaluates ALL active flags

### Server-Side (Python/Node.js) — For Backend Services

**Two evaluation modes:**

| Mode | Latency | Cohort Targeting | Sticky Variants | Use Case |
|------|---------|-----------------|-----------------|----------|
| **Local** | Low (in-memory) | No | No | High-throughput APIs |
| **Remote** | Higher (network) | Yes | Yes | Complex targeting |

```python
# Python — Local Evaluation (for svc_importer, frontera2)
import mixpanel

local_config = mixpanel.LocalFlagsConfig(
    api_host="https://api.mixpanel.com",
    enable_polling=True,
    poll_interval=60  # seconds
)
mp = mixpanel.Mixpanel("TOKEN", local_flags_config=local_config)
mp.local_flags.start_polling_for_definitions()

user_context = {
    "distinct_id": "user@empresa.com",
    "company": "30-71234567-9",        # CUITFacturacion (billing entity)
    "product_id": "41763",              # idEmpresaUsuario (subscription)
    "custom_properties": {"plan": "pro", "icp_type": "pyme"}
}
variant = mp.local_flags.get_variant_value("new_flow", "control", user_context)

# Python — Remote Evaluation (for complex cohort targeting)
remote_config = mixpanel.RemoteFlagsConfig(
    api_host="https://api.mixpanel.com",
    request_timeout_in_seconds=5
)
mp = mixpanel.Mixpanel("TOKEN", remote_flags_config=remote_config)
variant = mp.remote_flags.get_variant_value("new_flow", "control", user_context)
# Manual exposure tracking (server-side doesn't auto-track)
mp.remote_flags.track_exposure_event("new_flow", variant, user_context)
```

```javascript
// Node.js — for NestJS services (svc_importer_data, etc.)
const Mixpanel = require('mixpanel');
// Similar pattern — local or remote evaluation
```

### Core SDK Methods (All Platforms)

| Method | Purpose | Auto-tracks exposure? |
|--------|---------|----------------------|
| `is_enabled(key, fallback)` | Boolean gate check | Yes (client) / No (server) |
| `get_variant_value(key, fallback)` | Get variant string | Yes (client) / No (server) |
| `get_all_variants(context)` | Batch evaluation | No |
| `track_exposure_event(key, variant, context)` | Manual exposure | N/A |

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `https://api.mixpanel.com/flags/definitions` | All enabled flag definitions (for local eval polling) |
| GET | `https://api.mixpanel.com/flags/evaluate` | Evaluate all flags for a user context |

**Auth**: Service Account or Project Token.

**Limitation**: No CRUD API. Flags must be created/edited/deleted in Mixpanel UI.

## Experiments (A/B Testing)

### The `$experiment_started` Event

This is the bridge between feature flags and experiment analysis:

```javascript
// Auto-tracked by client SDKs when using is_enabled() or get_variant_value()
// Manual tracking for server-side:
mixpanel.track('$experiment_started', {
  'Experiment name': 'onboarding_wizard_v2',
  'Variant name': 'variant_a'
});
```

**Rules:**
- Track ONLY on **actual user exposure** (seeing the UI), not assignment
- Track only **first exposure** per user per experiment
- System associates behavior for max **90 days** post-exposure

### Statistical Models

| Model | Best For | Early Stopping? | Min Detectable Lift |
|-------|----------|-----------------|---------------------|
| **Sequential** (default) | Large effects (>=10% lift) | Yes | ~10% |
| **Frequentist** | Small effects (~1% lift) | No (must run full duration) | ~1% |

### Experiment Workflow

1. Create Experiment-type flag in Mixpanel UI with variants + splits
2. Deploy code referencing the flag key with fallback values
3. Configure metrics in Mixpanel: primary (conversion), guardrail (churn), secondary
4. Set test duration (sample size or calendar days)
5. Monitor for Sample Ratio Mismatch (SRM) — indicates implementation bugs
6. Wait for statistical significance → Ship Variant / Ship None / Defer

### Advanced Features

- **CUPED**: Uses pre-experiment behavioral data for narrower confidence intervals
- **Bonferroni Correction**: Adjusts for multiple comparisons
- **Winsorization**: Caps outlier values (useful for revenue metrics)
- **Retrospective-AA**: Examines 2 weeks of pre-experiment baseline for bias

## Colppy-Specific Patterns

### Recommended Flag Naming Convention

```
{domain}_{feature}_{type}
```

Examples:
- `invoice_new_flow_gate` — Feature gate for new invoice flow
- `onboarding_wizard_v2_experiment` — Experiment testing wizard redesign
- `tesoreria_bank_recon_config` — Dynamic config for bank reconciliation settings
- `compliance_fce_mipyme_gate` — Feature gate for FCE MiPyME rollout

### Colppy Rollout Strategy

```
1. Create flag in Mixpanel UI (no CRUD API — UI only)
2. Deploy code with flag key + safe fallback (fallback = current behavior)
3. QA whitelist: joaquin.baigorri@colppy.com in staging
4. Rollout: 5% → 25% → 50% → 100%
   - For compliance features: 100% immediately (with Tier 1 bumpers)
   - For experiments: 50/50 split with Sequential model
5. Monitor: activation rate, support tickets, Mixpanel metrics
6. Kill-switch: disable flag instantly if issues arise
```

### Assignment Key by Feature Domain

| Domain | Assignment Key | Level | Rationale |
|--------|---------------|-------|-----------|
| Onboarding/wizard | `device_id` | Device | Pre-authentication flow, no identity yet |
| Dashboard/UX | `distinct_id` | User | Per-user experience (layout, notifications) |
| Invoice/fiscal features | `company` (group) | Company | Billing entity = CUIT. Tax regime, condición IVA, ARCA rules are per-CUIT |
| Plan entitlements | `product_id` (group) | Product | Subscription = empresa. Module access, feature limits are per-plan |
| Activation experiments | `product_id` (group) | Product | Trial activation, onboarding completion are per-empresa |
| Compliance (ARCA/FCE) | `company` (group) | Company | Regulatory obligations are per-CUIT, not per-empresa |

**Key distinction**: A contador firm has ONE `company` (CUIT) but MANY `product_id`s (one per client empresa). A flag on `company` affects ALL empresas under that CUIT. A flag on `product_id` affects only that specific empresa/subscription.

### Replacing the Manual Product Tour A/B Test

Current implementation in `mfe_onboarding` uses `Math.random() < 0.5` + localStorage.
Should be migrated to:

```javascript
// BEFORE (manual)
const randomValue = Math.random() < 0.5 ? 'A' : 'B';
localStorage.setItem('intercom_product_tour_experiment', randomValue);

// AFTER (Mixpanel Feature Flags)
const variant = await mixpanel.flags.get_variant_value(
  "product_tour_experiment",
  "control"  // fallback
);
// Automatically: sticky assignment, exposure tracking, experiment analytics
```

## Pricing Notes

- Charged per **Feature Flag API Request** (one call evaluates all active flags)
- Priced by active (enabled) flag count: 50 / 200 / 1,000 tiers
- Estimated requests ~ 1.5x monthly user sessions
- Experiments priced separately via **Monthly Experiment Users (MEUs)**
- Up to 3 free experiments per project for non-subscribers (we have Enterprise)

## Environment Setup

| Environment | Mixpanel Project | Purpose |
|-------------|-----------------|---------|
| Production | 2201475 | Customer-facing flags |
| Staging | 2797423 | QA + pre-launch validation |

**Recommended**: Use matching flag keys across both projects. Test in staging → promote to production.
