# RNS API Integration into HubSpot Industry Enrichment Workflow

**Date:** 2026-03-04
**Status:** Approved
**Workflow:** https://app.hubspot.com/workflows/19877595/platform/flow/1693911922/edit

## Problem

The HubSpot custom code (`hubspot_industry_enrichment.js`) scrapes dateas.com for ARCA activity text, which:
- Has no creation date (behind paywall)
- Is fragile (HTML scraping with regex)
- Returns less structured data

Meanwhile, our own Cloudflare RNS API (`rns-cuit-enrichment.colppy-tools.workers.dev`) already returns both `actividad_descripcion` AND `fecha_contrato_social` as structured JSON from 1.24M companies.

## Solution

Integrate the RNS API as the **primary** CUIT lookup source, with dateas.com as fallback for activity-only when the CUIT is not in RNS (~17% miss rate).

### Data Flow

```
CUIT input
    |
    v
1. Call RNS API (GET /enrich?cuit=XXXXXXXXXXX)
   -> actividad_descripcion, fecha_contrato_social, tipo_societario, provincia
    |
    found=true? --yes--> Return activity + creation date
    |
    no
    |
    v
2. Fallback: dateas.com (existing HTML scraping)
   -> activity text only (no creation date available)
```

### Changes to hubspot_industry_enrichment.js

1. **New function: `searchCompanyByRNS(cuit)`** — calls Cloudflare API, returns structured result
2. **Modified `searchCompanyByCUIT()`** — tries RNS first, falls back to dateas.com if not found
3. **In `exports.main`** — fetch and save `fecha_de_creacion_de_compania_segun_arca` property
4. **Slack notification** — add "Fecha Creacion" field

### HubSpot Property Mapping

| RNS API field | HubSpot property | Type |
|---|---|---|
| `actividad_descripcion` | `actividad_de_la_compania_segun_arca` | string (existing) |
| `fecha_contrato_social` | `fecha_de_creacion_de_compania_segun_arca` | date (new) |

### Edge Cases

- RNS returns `fecha_contrato_social: null` — skip, don't overwrite
- HubSpot date format: midnight UTC timestamp in ms (`"2012-08-17"` -> `1345161600000`)
- RNS API timeout: 5s, same as dateas.com. If timeout, fall through to dateas
- Existing `fecha_de_creacion_de_compania_segun_arca` already populated — skip update
