# Zapier Active Zaps Inventory

> Last updated: 2026-03-10
> Source: Scraped from zapier.com/app/assets/zaps?status=on
> Account: Juan Onetto (jonetto@colppy.com) — Free plan (recently canceled Team plan)
> Total Zaps: 168 | Active (ON): 21 | Plan Tasks: 2.2k / 20k

## Summary by Category

| Category | Count | Description |
|---|---|---|
| Mixpanel Event Tracking | 7 | HubSpot/Intercom webhooks → Mixpanel events |
| Cohort Import Pipelines | 5 | Scheduled Mixpanel cohort exports → GSheet/HubSpot |
| HubSpot Property Updates | 3 | GSheet data → HubSpot contact properties (with delays) |
| Google My Business → Slack | 2 | GMB review notifications to Slack |
| Intercom → HubSpot | 1 | Multi-path routing from Intercom flows |
| Intercom User Attributes | 1 | GSheet → Intercom attribute updates |
| NPS Survey Events | 1 | NPS completion → Mixpanel + Slack |
| Feature Upvote Tracking | 1 | Feature Upvote → Mixpanel |

## Active Zaps (21)

### Mixpanel Event Tracking (7)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 1 | 336334291 | Genera evento de cambio de Lifecycle Stage de Contacto de hubspot | Webhook → Code → Mixpanel | Juan Onetto |
| 2 | 306661327 | Genera Evento en Mixpanel Confirmacion Contador Robado y Slack | Webhook → Mixpanel + Slack | Juan Onetto |
| 3 | 290476417 | Genera evento de calificacion desde WF Hubspot a Mixpanel | Webhook → Mixpanel | Juan Onetto |
| 4 | 273766708 | Genera eventos desde Serie de Intercom | Webhook → Code → Mixpanel | Juan Onetto |
| 5 | 167909302 | Track generico de evento desde Intercom a Mixpanel | Webhook → Code → Mixpanel | Juan Onetto |
| 6 | 332991791 | Genera evento de nuevo lead desde WF Hubspot a Mixpanel Sueldos | Webhook → +3 → Mixpanel | Juan Onetto |
| 7 | 90685388 | Feature upvote a Mixpanel | Feature Upvote → Mixpanel | Juan Onetto |

### Cohort Import Pipelines (5)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 8 | 337843231 | Mixpanel de cohort 5917106 de Fecha Finalizar Wizard a Hubspot | Schedule → +4 → HubSpot | Juan Onetto |
| 9 | 287024097 | Mixpanel de Cohort 5341585 to GSheet - tiempo de sesion ultimos 15 dias | Schedule → +2 → GSheet | Juan Onetto |
| 10 | 287027156 | Mixpanel de Cohort 5341604 to GSheet - Click en pagar en Trial | Schedule → +2 → GSheet | Juan Onetto |
| 11 | 265411978 | Mixpanel de Cohort 2351984 to GSheet - Hizo el evento clave en trial | Schedule → +2 → GSheet | Juan Onetto |
| 12 | 278447438 | Import Cohort Mixpanel Los registros a GSheet | Webhook → +2 → GSheet | Juan Onetto |

### HubSpot Property Updates (3)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 13 | 287026645 | Actualiza propiedad Click en pagar en Hubspot desde Evento Mixpanel | GSheet → Delay → HubSpot | Juan Onetto |
| 14 | 168981358 | Actualiza propiedad Hizo Evento Clave (PQL) en Hubspot desde Evento Mixpanel | GSheet → Delay → HubSpot | Juan Onetto |
| 15 | 287025159 | Actualiza propiedad Duracion de sesion en Hubspot desde Evento Mixpanel | GSheet → Delay → HubSpot | Juan Onetto |

### Google My Business Notifications (2)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 16 | 318578746 | Send Slack notifications for new Google My Business reviews | GMB → Slack | Daniel Sucre |
| 17 | 351618405 | Google My Bsuniness Slack Notification | GMB → Slack | Juan Onetto |

### Intercom Integrations (2)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 18 | 273799314 | Realiza diferentes interacciones en Hubspot dependiendo del flujo en Intercom | Webhook → Paths → HubSpot | Juan Onetto |
| 19 | 278460923 | Actualiza Atributo en Intercom para Usuarios recurrentes contabilidad | GSheet → Intercom | Juan Onetto |

### Other (2)

| # | Zap ID | Name | Apps | Owner |
|---|---|---|---|---|
| 20 | 300879150 | Import Cohort Mixpanel Click en Pagar a GSheet | Webhook → +2 → GSheet | Juan Onetto |
| 21 | 274272290 | Genera Evento en Mixpanel y Slack cuando termina encuesta de NPS | Webhook → +2 → Slack + Mixpanel | Juan Onetto |

## Errors Detected

| Zap ID | Name | Status |
|---|---|---|
| 332991791 | Genera evento de nuevo lead desde WF Hubspot a Mixpanel Sueldos | **Errored** — Ran 1 day ago |

## Data Flow Architecture

```
                    ┌─────────────┐
                    │   HubSpot   │
                    │  Workflows  │
                    └──────┬──────┘
                           │ webhooks (7 Zaps)
                           ▼
┌──────────┐    ┌──────────────────┐    ┌───────────┐
│ Intercom │───▶│     ZAPIER       │───▶│  Mixpanel │
│  Series  │    │  (21 active)     │    │  Events   │
└──────────┘    └──────────────────┘    └───────────┘
                     │          │
        ┌────────────┘          └────────────┐
        ▼                                    ▼
┌──────────────┐                    ┌──────────────┐
│ Google Sheets│──── Delay ────────▶│   HubSpot    │
│  (staging)   │                    │  Properties  │
└──────────────┘                    └──────────────┘
        ▲
        │ scheduled cohort imports (5 Zaps)
┌───────┴──────┐
│   Mixpanel   │
│   Cohorts    │
└──────────────┘
```

## Key Observations

1. **Duplicate GMB Zaps**: Zaps #16 and #17 both send Google My Business reviews to Slack — likely one is redundant
2. **Errored Zap**: #6 (332991791) "Genera evento de nuevo lead desde WF Hubspot a Mixpanel Sueldos" needs investigation
3. **GSheet as staging layer**: 3 Zaps use GSheet → Delay → HubSpot pattern (cohort data → property updates). The delay step suggests rate-limiting workaround
4. **Single owner risk**: 19 of 21 Zaps owned by Juan Onetto; only 1 by Daniel Sucre
5. **Plan downgrade**: Recently canceled Team plan — monitor for feature restrictions on active Zaps
6. **Connection health**: 166 total connections, many showing "Reconnect" (expired OAuth). Active Zaps appear unaffected but should be monitored
