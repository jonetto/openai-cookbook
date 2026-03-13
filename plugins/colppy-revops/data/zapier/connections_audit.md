# Zapier App Connections Audit

> Last updated: 2026-03-10
> Total connections: 166 (across 7 pages)
> Source: Scraped from zapier.com/app/assets/connections

## Connection Health Summary (Page 1 — Most Recent)

### Healthy (Working)

| Name | App | Version | Zaps | Last Modified |
|---|---|---|---|---|
| Mariela Sandroni | Google Sheets | 2.9.1 | 4 | 1 day ago |
| @franco.alvarez (SUMA+) | Slack | 1.37.6 | 2 | Feb 27, 2026 |
| Google Business Profile | Google Business Profile | — | 2 | Feb 27, 2026 |
| daniel.sucre@colppy.com | Intercom | 1.36.1 | 1 | Dec 19, 2025 |
| HubSpot Hub: 19877595 | HubSpot | 1.12.6 | 3 | Jul 15, 2025 |
| Intercom mariela.sandroni | Intercom | 1.36.1 | 1 | May 30, 2025 |
| Hotjar Site 2769400 | Hotjar | 1.2.6 | 0 | May 22, 2025 |
| Hello Bar marlene.ramirez | Hello Bar | 1.1.1 | 2 | May 22, 2025 |

### Broken (Need Reconnect)

| Name | App | Version | Zaps | Last Modified |
|---|---|---|---|---|
| daniel.sucre@colppy.com | Google Sheets | 2.9.1 | 2 | Jan 30, 2026 |
| daniel.sucre@colppy.com | Google Forms | 1.0.7 | 1 | Jan 30, 2026 |
| Mariela Sandroni - LinkedIn Conversions | LinkedIn Conversions | 1.0.8 | 0 | May 26, 2025 |
| Mariela Sandroni - LinkedIn Conversions #2 | LinkedIn Conversions | 1.0.8 | 0 | May 26, 2025 |
| Google Sheets pamela.viarengo | Google Sheets | 2.1.12 | 0 | May 22, 2025 |
| Google Sheets jonetto@colppy.com #2 | Google Sheets | 2.1.12 | 0 | May 22, 2025 |
| Google Analytics | Google Analytics 4 | 1.6.0 | 2 | May 22, 2025 |
| Salesforce #2 | Salesforce | 2.27.0 | 0 | May 22, 2025 |
| Google Drive angela.camelo | Google Drive | 1.11.0 | 0 | May 22, 2025 |
| Jira Software colppy | Jira Software Cloud | 2.27.0 | 0 | May 22, 2025 |
| Google Drive marcelo.aguilera #2 | Google Drive | 1.11.0 | 0 | May 22, 2025 |
| Google Drive marcelo.aguilera | Google Drive | 1.11.0 | 0 | May 22, 2025 |
| Google Sheets juanignacio.haun | Google Sheets | 2.1.12 | 0 | May 22, 2025 |
| Facebook Custom Audiences Marlene | Facebook Custom Audiences | — | 2 | May 22, 2025 |
| jonetto@colppy.com Google Docs | Google Docs | 1.2.2 | 0 | May 22, 2025 |
| Google Drive jonetto@colppy.com | Google Drive | 1.11.0 | 0 | May 22, 2025 |
| jonetto@colppy.com Google Calendar | Google Calendar | 1.8.0 | 0 | May 22, 2025 |

## Key Findings

1. **15 of 25 connections on page 1 need reconnection** — mostly Google OAuth expirations from May 2025
2. **Critical active connections** (powering ON Zaps): HubSpot Hub:19877595, Slack @franco.alvarez, Google Sheets (Mariela), Intercom (both)
3. **Former employee connections**: angela.camelo, marcelo.aguilera, juanignacio.haun, marlene.ramirez — all broken, 0 Zaps, safe to delete
4. **Duplicate connections**: Multiple Google Drive, Google Sheets, LinkedIn Conversions entries per person
5. **Premium apps with broken connections**: Salesforce, Facebook Custom Audiences — cost implications if reactivated

## Cleanup Recommendations

### Safe to Delete (0 Zaps + Broken)
- All Google Drive/Sheets/Docs/Calendar connections for former employees (angela.camelo, marcelo.aguilera, juanignacio.haun)
- LinkedIn Conversions x2 (Mariela Sandroni, 0 Zaps)
- Salesforce #2 (0 Zaps)
- Jira Software colppy (0 Zaps)
- Google Sheets jonetto@colppy.com #2 (0 Zaps)

### Monitor (Has Zaps but Broken)
- daniel.sucre@colppy.com Google Sheets (2 Zaps) — may affect DS | Descarga Zaps
- Google Analytics (2 Zaps) — reconnect if GA tracking Zaps are re-enabled
- Facebook Custom Audiences (2 Zaps) — reconnect if MKT Zaps are re-enabled

### Remaining pages (2-7) not yet audited
- 141 additional connections across pages 2-7
- Likely many more stale/broken connections from May 2025 batch
