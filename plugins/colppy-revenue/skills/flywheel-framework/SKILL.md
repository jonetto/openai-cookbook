---
name: flywheel-framework
description: Colppy's Product Insights Framework — the flywheel lifecycle model for user growth. Defines lifecycle stages (Evaluator, Beginner, Retained, Dormant, Resurrected), behavioral personas, critical events, usage intervals, PQL criteria, and the User Pulse metric. Use when analyzing user lifecycle, growth health, acquisition quality, or retention dynamics. Triggers on flywheel, lifecycle, pulse, evaluators, dormant, resurrected, stickiness, or critical events.
---

# Product Insights Framework — Flywheel

This skill encodes Colppy's product flywheel model. The flywheel replaces the traditional linear funnel with a cyclical, product-centric growth model.

Source: Product Insights Framework (Google Doc)

---

## The Flywheel

The product flywheel rotates through these stages:

```
Evaluators → New Users (Beginners) → Adopted/Retained → Connectors → back to Evaluators
```

Growth comes from spinning the wheel faster — converting evaluators into retained users who connect new evaluators into the ecosystem.

**Terminology**: We use "connections", NOT "referrals." Accountants **connect** SMBs to Colppy. SMBs **connect** colleagues or connect to their accountants. The product provides the mechanisms for conversion without human intervention (PLG).

---

## Lifecycle Stages

| Stage | Definition | Key Signal |
|-------|-----------|------------|
| **Evaluators** | Users exploring Colppy (trial period, wizard) | Signed up, haven't performed critical events yet |
| **Beginners (New Users)** | First-time product users receiving initial impressions | Recently performed first critical event |
| **Retained (Current)** | Consistent, long-term users performing critical events monthly | 80%+ target: critical event at least once per 30-day interval |
| **Dormant** | Previously active users who became inactive | Stopped performing critical events |
| **Resurrected** | Previously inactive users who returned | Re-performed critical events after dormancy period |

---

## Critical Events

Events closest to the core value proposition. For Colppy:

| Persona | Critical Events |
|---------|----------------|
| Administrative users | Generated purchase receipts, generated sales receipts |
| Accounting users | (Defined per accounting workflow — tax filing, ledger operations) |
| Inventory users | (Defined per inventory workflow) |

**Usage Interval**: 30-day cycle. Target: 80%+ of paying users performing critical events at least monthly.

---

## Behavioral Personas

Three primary user types exist in the product, independent of lifecycle stage:

| Persona | What they do |
|---------|-------------|
| **Accounting users** | Tax, ledger, compliance workflows |
| **Administrative users** | Invoicing, purchase/sales receipts, cash flow |
| **Inventory management users** | Stock, products, warehouse operations |

A single user may exhibit behaviors across personas. Classification is based on dominant usage pattern.

---

## ICP Dimension (Company Level)

The flywheel operates at the **user level**, but each user belongs to a **company** with an ICP classification:

| ICP Type | Company Type | How users enter the flywheel |
|----------|-------------|------------------------------|
| **Cuenta Contador** | Accountant firm | Accountant signs up, may connect multiple client companies |
| **Cuenta Pyme** | SMB (direct) | Owner/admin signs up directly, usually IS the decision maker |

For SMBs: the evaluator is typically the decision maker — short acquisition cycle.
For Canal Contador: accountants can be both direct users AND connectors who bring SMB companies into the ecosystem.

**Connection dynamics:**

- Accountants **connect** their SMB clients to Colppy (Canal Contador)
- SMBs **connect** colleagues to Colppy (peer connections)
- SMBs **connect** to their accountants (reverse connection — accountant discovers Colppy through client)
- Product owns the conversion mechanism — PLG model, no human intervention required ideally

See `icp-classification` skill for the full ICP rules and HubSpot field mappings.

---

## User Pulse Metric

The north star for growth health:

```
Pulse = (New Users + Resurrected Users) / Dormant Users
```

| Pulse Value | Meaning |
|-------------|---------|
| **> 1** | Real growth — gaining more users than losing |
| **= 1** | Flat — replacing losses but not growing |
| **< 1** | Declining — losing more users than gaining |

**Data source**: Mixpanel lifecycle analysis (new, resurrected, dormant segments).

---

## Stickiness

**Definition**: Frequency with which people use the product.

**Measurement**: Days performing critical events within a monthly period.

**Recommended interval**: Monthly (not weekly) for Colppy's usage pattern, since accounting workflows are month-end heavy.

---

## Product Qualified Lead (PQL)

**Definition**: Any user who, after initial login during the trial period, completes key behavioral events.

**HubSpot mapping**: `activo = true` + `fecha_activo` populated. See `funnel-definitions` skill for exact fields and rules.

**Flywheel mapping**: A PQL is an Evaluator who crossed into Beginner by performing meaningful product actions.

---

## Analysis Methodologies

### Signal Reports
Identify correlations between events and retention outcomes — which behaviors generate user stickiness.

### Segmentation Analysis
Examine new and retained users by:
- **UTM source** (demand generation impact)
- **Device type** (mobile vs desktop)
- **Subscription plan**
- **First critical event timing**

### Flow Analysis
Map user journeys before reaching critical events — common pathways and dropout points.

---

## Demand Generation Connection

The demand gen function owns the **Evaluator → Beginner** transition:
- Which channels attract evaluators who reach critical events?
- Which ICP/persona combinations convert fastest?
- What is the evaluator quality by campaign source?

The flywheel tells us: optimizing for volume of evaluators is wrong. Optimize for evaluators who will become retained users and eventually connectors.

**Ownership model:**

- **Demand Gen** — brings evaluators in (paid channels + connections from accountants/SMBs)
- **Customer** — everything post-evaluator (onboarding pre+post sale, trial experience, retention, channel fidelization, dormant re-engagement)
- **Product** — owns the entire flywheel; provides conversion mechanisms without human intervention (PLG)
- Customer's **channel fidelization** sub-team sends connection opportunities back to demand gen

---

## Related Skills

- **funnel-definitions** — MQL/PQL/SQL/Customer definitions and HubSpot fields
- **icp-classification** — Cuenta Contador vs Cuenta Pyme rules
- **mixpanel-analytics** — Event tracking and Mixpanel API patterns
- **business-context** — Company overview and glossary
