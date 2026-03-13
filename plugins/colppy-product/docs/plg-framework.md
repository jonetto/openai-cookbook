# Product-Led Growth Framework
## Based on "Product-Led Growth" by Wes Bush

This document is the canonical PLG reference for the CPO agent. Every concept here should be applied when diagnosing activation problems, designing bumpers, or evaluating product strategy.

---

## 1. What is Product-Led Growth?

PLG is a **go-to-market strategy** where the product itself is the primary driver of acquisition, activation, retention, expansion, and referral. Instead of a sales or marketing team leading the customer to value, the product does that work.

> "If you can get your product to sell itself, you've built a product-led growth engine."

The three pillars:
- **Acquire** users through the product (free tier, viral loops, word of mouth)
- **Activate** users by guiding them to value quickly
- **Expand** revenue when users hit natural upgrade triggers inside the product

---

## 2. The MOAT Framework — Is Your Product Ready for PLG?

Before designing PLG motions, assess whether the product is suited for them:

| Letter | Question | Options |
|--------|----------|---------|
| **M** — Market Strategy | How do you win? | Dominant (best product), Disruptive (cheaper/simpler), Differentiated (unique niche) |
| **O** — Ocean Condition | What market are you in? | Blue Ocean (new category) or Red Ocean (competing for existing demand) |
| **A** — Audience | How does buying happen? | Top-Down (executive decision) or Bottom-Up (end user adopts first) |
| **T** — Time to Value | How fast does the user get value? | Immediate / Short / Long |

**For Colppy:**
- M = Differentiated (Argentine compliance + SMB simplicity)
- O = Red Ocean (competing with Tango, Bejerman, Xubio)
- A = Bottom-Up (accountants and SMBs self-serve, then expand)
- T = Short (first invoice in < 30 min is the activation benchmark)

PLG works best for **Bottom-Up + Short TTV** combinations. Colppy fits this profile — especially for Cuenta Pyme.

---

## 3. The Bowling Alley Framework

The single most important PLG activation model. Every feature rollout and onboarding flow should be designed against it.

```
  ┌─────────────────────────────────────────────┐
  │  GUTTER        LANE         GUTTER           │
  │  (left)    ▓▓▓▓▓▓▓▓▓▓▓▓▓   (right)           │
  │           ▓             ▓                    │
  │  bumper → ▓   ball →→→  ▓ ← bumper           │
  │           ▓             ▓                    │
  │           ▓▓▓▓▓▓▓▓▓▓▓▓▓                      │
  │                 ↓                            │
  │              [PIN] = Aha! moment             │
  └─────────────────────────────────────────────┘
```

### The components:
- **The pin** = the Aha! moment — the first time the user experiences core value
- **The lane** = the straight-line path from signup to the pin (minimize steps)
- **The ball** = the user
- **The gutters** = where users fall off the path
- **The bumpers** = what keeps users on the lane when they veer off

### Defining the pin for Colppy features:

| Feature | Pin (Aha! moment) |
|---------|------------------|
| Core product | First invoice sent and received by client |
| IVA Simple | First invoice with Actividad + Tipo de Operación correctly populated, no AFIP error |
| FCE MiPyME | First FCE invoice transmitted and accepted |
| Importación masiva | First batch import with 0 errors |
| Tesorería | First bank reconciliation completed |

---

## 4. Bumper Types — The Complete Reference

Bumpers are the in-product and conversational mechanisms that prevent users from falling into gutters. They are not features — they are **guardrails**.

### Tier 1 — Product Bumpers (must ship with the feature)

#### 4.1 Empty State Bumper
**What**: What the user sees when a UI element loads with no data or in a broken/disabled state.
**When**: Feature loads empty, combo is disabled, list has no items.
**Goal**: Explain why it's empty and provide the exact action to fix it.
**Bad**: Greyed-out combo with no explanation.
**Good**: "⚠️ Configurá tu actividad ARCA para emitir facturas con IVA Simple. [Configurar ahora →]"

#### 4.2 Pre-Failure Bumper
**What**: A warning that fires before a destructive or failing action — not after.
**When**: User is about to do something that will fail (import with missing config, submit form with invalid data).
**Goal**: Stop the failure before it happens, explain why, give the fix.
**Bad**: Cryptic error after the action fails (`actividad(107999) no registrada`).
**Good**: Pre-import validation: "Tu empresa no tiene actividades ARCA configuradas. Esta importación fallará. [Ir a configurar]"

#### 4.3 Progress / Setup Completion Indicator
**What**: Visual state that shows whether a prerequisite is met.
**When**: A feature requires setup that the user may have skipped.
**Goal**: Make hidden state legible. The user should never wonder "is this configured?"
**Example**: In Configuración > Datos Generales: 🟠 "Actividades ARCA: No configuradas" vs ✅ "3 actividades sincronizadas · última sync 10/03/2026"

#### 4.4 Sample Data / Pre-population
**What**: Pre-populate the product with realistic example data so users see value before they've added their own.
**When**: A feature is powerful but requires significant setup to show value.
**Goal**: Accelerate TTV by removing the "empty product" problem.
**Note**: Only use when data can be safely removed later.

### Tier 2 — Guided Onboarding Bumpers

#### 4.5 Onboarding Checklist
**What**: A visible task list in the dashboard/home screen showing activation steps.
**When**: First N sessions without reaching the Aha! moment.
**Goal**: Give users a map. Reduces "I don't know what to do next" abandonment.
**Rules**:
- Maximum 5 items (more = overwhelming)
- Each item should be completable in < 2 minutes
- Auto-dismiss when all items are checked
- Never re-show once dismissed

#### 4.6 Contextual Tooltips
**What**: Small explanatory messages attached to UI elements, triggered on hover or first visit.
**When**: A control has non-obvious behavior or a term the user may not know.
**Goal**: In-context education without leaving the flow.
**Note**: Use sparingly — too many tooltips = the product itself is too complex.

#### 4.7 Welcome Sequence / First-Run Experience
**What**: A guided walkthrough on first login, typically a modal or overlay flow.
**When**: The product has a "setup" phase before first value delivery.
**Goal**: Collect the information needed to personalize the path to value.
**Rules**: Maximum 3 screens. Every screen must reduce TTV — if it doesn't, cut it.

### Tier 3 — Conversational Bumpers (ship after product bumpers)

#### 4.8 Behavioral Email / In-App Message
**What**: Triggered message based on a specific user behavior (or absence of it).
**When**: User opened the invoice form but didn't complete it. User imported a file but got errors. User hasn't logged in for 3 days during trial.
**Goal**: Re-engage users who left the lane without completing the action.
**Critical rule**: Conversational bumpers **compensate for product gaps** — they are not a substitute. If you need an email to explain how to use a feature, the feature's empty state is broken.

#### 4.9 Intercom Series (Automated Sequences)
**What**: Multi-step message sequences triggered by behavioral events.
**When**: Complex activation journeys that require multiple touchpoints.
**Goal**: Guide users through a multi-day activation path.
**For Colppy**: Trigger conditions should always be behavioral (product event), not time-based (day 3 of trial). Behavioral triggers = higher relevance = higher conversion.

---

## 5. Time to Value (TTV)

The single most important activation metric. Shorter TTV = higher activation = better retention.

| TTV Category | Range | PLG implication |
|---|---|---|
| Immediate | Seconds to minutes | Best for freemium, viral adoption |
| Short | Hours to days | Good for free trial |
| Long | Weeks to months | Requires high-touch onboarding |

**How to reduce TTV:**
1. Remove steps from the straight line (can the user skip setup and still get value?)
2. Pre-populate data where possible
3. Use progressive disclosure (don't ask for everything upfront)
4. Fix empty states (a broken state at step 1 = TTV = ∞)

**For Colppy**, the TTV benchmark is: **first invoice sent in < 30 minutes** from account creation. Every friction point that extends this is a TTV problem.

---

## 6. Product Qualified Leads (PQLs)

PQLs are users who have experienced meaningful value in the product — making them more likely to convert than MQLs (marketing) or SQLs (sales).

> "A PQL is someone who has used your product enough to understand its value and is ready to buy."

### PQL definition for Colppy (proposed):
A free/trial user who has:
- Sent at least 1 electronic invoice (FE) **AND**
- Has ≥ 3 active clients **AND**
- Has logged in ≥ 3 times in the last 7 days

These are the users sales should call — not every trial signup.

### PQL vs MQL vs SQL:
| Type | Signal | Quality |
|------|--------|---------|
| MQL | Downloaded content, attended webinar | Low intent |
| SQL | Sales rep deemed qualified | Medium intent |
| PQL | Used the product to do real work | High intent |

---

## 7. The PLG Flywheel (vs. Traditional Funnel)

### Traditional SaaS funnel (linear, leaky):
```
Awareness → Interest → Consideration → Intent → Evaluation → Purchase
```
Each step loses users. Acquisition drives growth. Sales is the engine.

### PLG flywheel (self-reinforcing):
```
         ┌──────────────┐
    ┌────→│   Acquire    │←────┐
    │     └──────┬───────┘     │
    │            ↓             │
  Refer     Activate      Expand
    │            ↓             │
    │     ┌──────┴───────┐     │
    └─────│    Retain    │─────┘
          └──────────────┘
```

In the flywheel: **retention is the foundation**. Acquired users who activate and retain become the referral and expansion engine. This is why activation metrics matter more than acquisition metrics in PLG.

---

## 8. Ocean Strategy Applied to PLG

### Red Ocean (Colppy's current position):
- Competing on features and price against established players
- PLG motion: **Disruptive simplicity** — be easier to use, faster to value
- Key lever: Reduce TTV below competitors
- Compliance as a moat: ARCA/AFIP integration that competitors haven't built

### Blue Ocean opportunity:
- The "accountant as distribution channel" motion — Cuenta Contador is a network effect play
- One accountant firm onboards 20-50 Pyme clients → viral expansion
- PLG lever: Make it trivially easy for accountants to invite and manage Pyme clients

---

## 9. Freemium vs. Free Trial Decision Framework

Bush's "Swipe Left, Swipe Right" model:

### Choose Freemium when:
- Large addressable market (millions of potential users)
- Short TTV (users get value in minutes)
- Product has network effects or viral loops
- Cost of serving a free user is very low

### Choose Free Trial when:
- Smaller market, higher ACV
- Product requires some setup before value (medium TTV)
- No strong network effects
- Need behavioral data to qualify leads

**For Colppy**: Free trial is the right model. The product requires company setup (CUIT, talonarios, configuración) before first value — that's medium TTV. Freemium would create a large base of non-activated users with high support cost.

---

## 10. Segmentation in PLG

Not all users should follow the same path to value. Segment by:

### Segmentation axes for Colppy:
| Axis | Segments | Different path? |
|------|----------|-----------------|
| ICP | Cuenta Contador vs Cuenta Pyme | Yes — accountants manage multiple companies; Pymes are self-service |
| Condición IVA | RI vs Monotributista vs Exento | Yes — different compliance requirements |
| Company size | Solo / SMB / Mid-market | Yes — solo needs fastest TTV; mid-market needs training |
| Use case | Solo invoicing / Full accounting / Payroll | Yes — different Aha! moments |

**The activation mistake**: Showing everyone the same onboarding. The Accountant's Aha! moment (managing 10 clients efficiently) is different from the Pyme's Aha! moment (sending first invoice without an accountant).

---

## 11. The "Straight Line" Principle

The shortest path from signup to the Aha! moment. Every step not on the straight line is a potential gutter.

### How to find the straight line:
1. Define the Aha! moment for each user segment
2. List every step the user currently takes to get there
3. Ask for each step: "Is this necessary, or can we remove/defer it?"
4. Remove or defer everything that doesn't contribute directly to value

### For Colppy's invoice flow straight line:
```
Registro → Wizard empresa → [SKIP optional steps] → Alta cliente → Factura → Enviar
```
Every field in the wizard that isn't needed to send the first invoice is a straight-line obstacle.

---

## 12. The "Three Strikes" Rule

If a user has tried to complete an action 3 times without success, they need a different intervention. The product bumper alone is not enough — escalate to:
1. A more prominent in-app message (modal, not tooltip)
2. A proactive Intercom message from a human
3. A product fix (the friction is real, not user error)

---

## 13. Key PLG Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **TTV** | Time from signup to Aha! moment | Minimize continuously |
| **Activation rate** | % of signups who reach Aha! moment | > 40% in first 7 days |
| **PQL rate** | % of activated users who meet PQL criteria | Track and improve |
| **Feature adoption rate** | % of active users using a specific feature | Baseline by feature |
| **Bumper conversion** | % of users who click a bumper CTA | > 20% is strong |
| **Expansion MRR** | MRR from upgrades by existing users | Should grow > New MRR in mature PLG |
| **Time to PQL** | Days from signup to PQL threshold | Minimize |

---

## 14. Compliance Features as Activation Risk — Colppy-Specific Pattern

Every ARCA/AFIP regulatory change follows the same risk pattern:

```
Regulatory change announced
        ↓
Dev builds the feature
        ↓
Feature ships (mandatory field, new flow, new template column)
        ↓
[WITHOUT BUMPERS]: Users discover the change when something breaks
        ↓
Support ticket spike
        ↓
Reactive Intercom response (too late, too manual)

[WITH BUMPERS]: Users are guided to configure before breaking
        ↓
Activation happens proactively
        ↓
Zero support tickets on launch
```

**The rule**: Every compliance feature ships with a Tier 1 bumper (empty state + pre-failure) on the same PR. No exceptions.
