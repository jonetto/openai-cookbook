---
name: schwab-investment-portfolio
description: "Extract investment portfolio snapshot from Charles Schwab using Playwright MCP tools. Logs in, navigates to Account Summary/Positions, extracts holdings, cash, and linked external accounts."
trigger: "When user asks to check Schwab investments, update Schwab portfolio, or take a Schwab snapshot."
---

# Schwab Investment Portfolio Extractor

## Purpose

Automate extraction of Juan's investment portfolio from Charles Schwab brokerage. Produces structured JSON snapshots and updates the combined holdings summary.

## Prerequisites

- **Playwright MCP tools** must be available (browser_navigate, browser_snapshot, browser_click, browser_type, browser_run_code, browser_close)
- **Schwab credentials:** Login ID: `jonetto`, Password: stored in user's memory (do not hardcode)
- **2FA:** Schwab uses device trust. First login requires mobile approval. Once trusted, subsequent logins from the same browser profile skip 2FA.

## Data Storage

```
plugins/colppy-ceo-assistant/data/investments/
├── holdings_current.md                ← combined Galicia + Schwab summary
└── snapshots/
    ├── 2026-03-03-schwab.json         ← first snapshot
    ├── YYYY-MM-DD-schwab.json         ← subsequent snapshots
    └── ...
```

## Extraction Steps

### Step 1: Navigate to Login

```
browser_navigate → https://client.schwab.com/Areas/Access/Login
```

The login form is inside an **iframe** (`#lmsIframe`). Element refs will have `f2e` prefix (frame refs).

### Step 2: Fill Credentials

```
browser_type ref=f2e16 text="jonetto" slowly=true     → Login ID field
browser_type ref=f2e20 text="[password]" slowly=true   → Password field
browser_click ref=f2e30                                 → Log in button
```

**Important:** The ref numbers may change between sessions. Always take a `browser_snapshot` first if refs don't work.

### Step 3: Handle 2FA / Device Trust

After clicking Log in, Schwab may:

1. **Redirect to "Confirm Your Identity"** → requires mobile approval via Schwab app. Wait for user to approve, then page auto-advances.
2. **Show "Trust this device"** → select "Yes, trust this device" and click Continue. This is a one-time step per browser profile.
3. **Go directly to Account Summary** → device already trusted from prior session.

### Step 4: Extract Account Summary

Once on `client.schwab.com/app/accounts/summary/`:

```javascript
async (page) => {
  await page.waitForTimeout(3000);
  const bodyText = await page.locator('body').innerText();
  return bodyText.substring(0, 5000);
}
```

Parse from the text:
- **Total Value** (all accounts)
- **Day Change** ($ and %)
- **1-Month Change** ($ and %)
- **Brokerage account:** cash, positions with price/qty/value/cost basis/gain-loss
- **External accounts:** Citi checking + savings balances

### Step 5: Check Positions Detail (optional)

If the summary doesn't show all positions, navigate to the **Positions** tab:
- Click "Accounts" in the top nav
- Click "Positions" sub-tab
- Extract the full positions table

### Step 6: Store Snapshot

1. Write JSON snapshot to `data/investments/snapshots/YYYY-MM-DD-schwab.json`
2. Update the Schwab section in `data/investments/holdings_current.md`
3. Update the Combined Portfolio section
4. If pending orders exist, note them in the snapshot

### Step 7: Logout & Close

```
browser_click → "Log Out" link in the top nav bar
browser_close
```

## JSON Schema

```json
{
  "date": "YYYY-MM-DD",
  "source": "schwab-online-playwright",
  "extracted_at": "ISO-8601",
  "schwab_last_updated": "ISO-8601",
  "account": {
    "name": "string",
    "broker": "Charles Schwab",
    "account_type": "Individual Brokerage",
    "account_ending": "string"
  },
  "total_value": {
    "all_accounts": "number",
    "investment_only": "number",
    "external_only": "number",
    "day_change_usd": "number",
    "day_change_pct": "number",
    "one_month_change_usd": "number",
    "one_month_change_pct": "number"
  },
  "brokerage": {
    "cash": "number",
    "positions": [
      {
        "ticker": "string",
        "name": "string",
        "quantity": "integer",
        "price_usd": "number",
        "market_value_usd": "number",
        "day_change_usd": "number",
        "cost_basis_usd": "number",
        "gain_loss_usd": "number"
      }
    ],
    "total_value": "number"
  },
  "pending_orders": {
    "note": "string",
    "orders": [
      {
        "ticker": "string",
        "action": "string",
        "quantity": "integer",
        "estimated_price": "number",
        "estimated_value": "number"
      }
    ]
  },
  "external_accounts": [
    {
      "name": "string",
      "institution": "string",
      "account_ending": "string",
      "balance_usd": "number",
      "last_updated": "string"
    }
  ]
}
```

## Known Gotchas

- **Iframe login form**: The login fields are inside `#lmsIframe`. Playwright MCP handles this with frame-prefixed refs (`f2e16`, etc.), but the numbers shift between sessions.
- **2FA mobile approval**: First login on a new device requires approving a push notification on the Schwab mobile app. Cannot be automated — user must approve manually.
- **Device trust**: After first 2FA, select "Yes, trust this device" to skip 2FA on subsequent logins from same browser profile.
- **External accounts lag**: Citi balances show "as of X hours ago" — they're not real-time.
- **Market hours**: Positions show last close prices outside market hours.
- **Start page selector**: The login form has a "Start Page" dropdown — default is "Accounts Summary" which is what we want. Can be changed to "Positions" for direct access to holdings.
- **Session timeout**: Schwab sessions expire after ~30 min of inactivity. If extracting fails, may need to re-login.
