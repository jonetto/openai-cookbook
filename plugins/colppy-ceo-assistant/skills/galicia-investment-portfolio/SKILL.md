---
name: galicia-investment-portfolio
description: "Extract investment portfolio snapshot from Banco Galicia Eminent Online Banking using Playwright MCP tools. Navigates to Inversiones, extracts all positions (CEDEARs, Fondos FIMA, cash), and stores dated snapshots for historical tracking."
trigger: "When user asks to check investments, update portfolio, take a portfolio snapshot, or compare investment evolution."
---

# Galicia Investment Portfolio Extractor

## Purpose

Automate extraction of Juan's investment portfolio from Banco Galicia Eminent Online Banking. Produces structured JSON snapshots and human-readable summaries for historical comparison.

## Prerequisites

- **Playwright MCP tools** must be available (browser_navigate, browser_snapshot, browser_click, browser_run_code, browser_close)
- **Galicia credentials** in `arca-prototype/.env`: `GALICIA_DNI`, `GALICIA_USER`, `GALICIA_PASS`
- The login page may remember the user (cookie-based) — in that case, only the password (clave) is needed

## Data Storage

```
plugins/colppy-ceo-assistant/data/investments/
├── holdings_current.md           ← human-readable current state
└── snapshots/
    ├── 2026-03-03.json           ← first snapshot
    ├── YYYY-MM-DD.json           ← subsequent snapshots
    └── ...
```

## Extraction Steps

### Step 1: Navigate to Login

```
browser_navigate → https://onlinebanking.bancogalicia.com.ar/login
browser_snapshot → check if "¡Hola Juan!" (session remembered) or full login form
```

**If session remembered** (only password field visible):
- Read password from `arca-prototype/.env` (GALICIA_PASS)
- Type slowly into the "Tu clave Galicia" textbox (`slowly: true` — React controlled inputs need character-by-character events)
- Click "iniciar sesión" button

**If full login form:**
- Type DNI into "Tu DNI" field (slowly)
- Type username into "Tu usuario Galicia" field (slowly)
- Type password into "Tu clave Galicia" field (slowly)
- Click "iniciar sesión"

### Step 2: Navigate to Inversiones

After login lands on `/inicio`:
- Click "Inversiones" link in the sidebar navigation
- Wait for page to load at `inversiones.bancogalicia.com.ar/inversiones/inicio`

### Step 3: Extract Portfolio Data

Use `browser_run_code` to extract full page text:

```javascript
async (page) => {
  await page.waitForTimeout(3000);
  const bodyText = await page.locator('body').innerText();
  return bodyText;
}
```

Then take a `browser_snapshot` for structured element data.

**Important:** The CEDEAR table initially shows only 5 positions. Click "ver más" link to expand all positions before extracting.

### Step 4: Parse Extracted Data

From the text/snapshot, extract:

1. **Portfolio total**: "Inversiones en pesos" heading (e.g., `$263.644.026,10`)
2. **Allocation breakdown**: Acciones %, CEDEARs %, FIMA %
3. **Cash**: "Tus cuentas en pesos" + "Tus cuentas en dólares"
4. **Fondos FIMA**: Fund name, cuotapartes, price, TNA, variation, value
5. **CEDEARs table**: For each row — ticker, name, quantity, price, variation%, PPC, return ARS, return%, value

**Argentine number format**: dots = thousands separator, comma = decimal (e.g., `$7.750,00` = 7750.00)

### Step 5: Store Snapshot

1. Write JSON snapshot to `data/investments/snapshots/YYYY-MM-DD.json`
2. Update `data/investments/holdings_current.md` with new data
3. If previous snapshots exist, compute deltas (position changes, P&L evolution)

### Step 6: Logout & Close

- Click "Cerrar Sesión" in the sidebar
- Call `browser_close`

## JSON Schema

```json
{
  "date": "YYYY-MM-DD",
  "source": "galicia-online-banking-playwright",
  "extracted_at": "ISO-8601",
  "account": {
    "name": "string",
    "broker": "Banco Galicia Eminent",
    "cuenta_inversora": "string",
    "investment_officer": "string"
  },
  "portfolio_total": {
    "investments_ars": "number",
    "investments_usd": "number",
    "allocation": {
      "acciones_pct": "number",
      "cedears_pct": "number",
      "fima_pct": "number"
    }
  },
  "cash": {
    "cuentas_ars": "number",
    "cuentas_usd": "number"
  },
  "fondos_fima": [
    {
      "fund": "string",
      "cuotapartes": "number",
      "price_ars": "number",
      "variation_pct": "number",
      "tna_pct": "number",
      "value_ars": "number"
    }
  ],
  "cedears": {
    "total_ars": "number",
    "total_usd": "number",
    "cumulative_return_ars": "number",
    "cumulative_return_pct": "number",
    "positions": [
      {
        "ticker": "string",
        "name": "string",
        "quantity": "integer",
        "price_ars": "number",
        "variation_pct": "number",
        "ppc_ars": "number",
        "return_ars": "number",
        "return_pct": "number",
        "value_ars": "number"
      }
    ]
  }
}
```

## Comparing Snapshots

When multiple snapshots exist, produce an evolution report:

```markdown
## Portfolio Evolution: {date_old} → {date_new}

| Metric | Old | New | Delta |
|--------|-----|-----|-------|
| Total ARS | ... | ... | +/-% |
| CEDEAR Return | ... | ... | ... |

### Position Changes
- {ticker}: qty {old} → {new}, price {old} → {new}, P&L {old} → {new}
- NEW: {ticker} (not in previous snapshot)
- REMOVED: {ticker} (in previous, not in current)
```

## Known Gotchas

- **React login form**: Must use `slowly: true` when typing into login fields — Galicia uses React controlled components that don't fire onChange on direct fill()
- **Session cookies**: The browser often remembers "¡Hola Juan!" and only asks for clave — check snapshot before filling all 3 fields
- **Market hours**: Variation% shows 0.00% outside market hours — prices are last close
- **"ver más" button**: CEDEAR table truncates to 5 rows — must click expand before extracting
- **Plazos Fijos**: Not currently held but section exists — extract if populated
- **Bonos**: Section exists under "Bonos, Acciones y CEDEARs" — extract if populated
