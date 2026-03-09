# Financial History Index

**Last snapshot:** 2026-03-06 (FULL UPDATE — all 4 accounts confirmed)
**Transactions:** 14 entries from 2026-02-19 → 2026-03-06 (all reconciled)
**Snapshots available:** 2026-01-01 → present (weekly from next Monday onward)

## Key Events
- 2026-02-19: NVDA trim 7,773→2,911 CEDEARs, opened V CEDEAR position (Georgette 5% rebalance)
- 2026-02-27: First SGOV share filled (Schwab)
- 2026-03-02: Schwab $15K deployment — BRK/B x16, SGOV x53, SCHD x62 (market orders, fills expected Mar 3)
- 2026-03-05: Galicia→Allaria USD MEP transfer (amount TBD — ask Juan for exact amount)
- 2026-03-05: Subscribed to AL DINA D MEP A (Allaria Dólar Dinámico fund) — M$23,000.83 full Allaria balance. Order #4490877, cuenta 16430.
- 2026-03-05: ON selection algorithm updated with MEP/Cable gate (Step 1.5), BYC2P blocked Cable-only
- 2026-03-06: Portfolio alert scheduler registered (was broken since creation — alerts only worked in interactive sessions)
- 2026-03-06: Full portfolio snapshot update — all 4 accounts confirmed. Net worth ~$534K (+2.8% vs Mar 2). Cash dropped 40%→28% as ~$83K deployed to fixed income (SGOV, FIMA USD, AL DINA D)
- 2026-03-06: All 5 previously untracked transactions logged to ledger with approx dates (late Feb / early Mar 2026): SGOV +299, FIMA USD $30K, Citi→Schwab ~$30K wire, Galicia→Allaria $23K, AL DINA D settled

## How to Query History

| Question | Where to look |
|----------|--------------|
| Current positions | `references/portfolio-snapshot.md` |
| Cost basis for a position | `history/transactions.md` — filter by asset |
| Portfolio state on a past date | `history/snapshots/YYYY-MM-DD.md` |
| What signals drove a past decision | `alerts/YYYY-MM-DD-HH.md` |
| Pending orders | `references/portfolio-snapshot.md` → Pending Orders section |

## Broker References
- **Allaria DMA Manual** → `references/allaria-dma-manual.pdf` — Full user manual for dma.allaria.com.ar (login, orders, cotizaciones, widgets, order management). Added 2026-03-05.
- **Key Allaria details**: Limit/Market/MTL/Stop orders, settlement Cdo/24hs/48hs, order by Cantidad or Monto, Profundidad de Mercado for bid/ask depth.
- **Allaria banking (USD)**: Banco de Valores S.A. (Nº 198 BCRA), CC Dólares Nº 102287, CUIT 30-68079080-5, CBU 1980001790000001022871. Include cuenta comitente number in transfer reference.
- **Allaria banking (ARS)**: Banco de Valores S.A. (Nº 198 BCRA), CC Pesos Nº 2865/5, CUIT 30-68079080-5, CBU 1980001730000000286551.
- **Galicia constraint**: Secondary market ON minimum = USD 100,000. Primary market (licitaciones) minimum = USD 100.
- **USD MEP vs Cable (learned Mar 5 2026)**: Local bank transfers (Galicia→Allaria) = USD MEP. Some ONs only trade in Cable species (e.g., BYC2P). MEP→Cable conversion possible via bond parking (AL30/GD30), costs ~0.5-1.5% spread + T+1. Always verify ON species with broker before ordering. BYC2P confirmed Cable-only with no liquidity by Agustin @ Allaria.

## File Map

| File | Purpose | Updated |
|------|---------|---------|
| `references/portfolio-snapshot.md` | Current state — all positions, pending orders, allocation | Every Monday |
| `references/index.md` | This file — navigation guide | Every Monday |
| `references/allaria-dma-manual.pdf` | Allaria DMA platform user manual | 2026-03-05 |
| `references/allaria-dolar-dinamico-fund.pdf` | AL DINA D MEP A fund factsheet — 100% ONs, 75MM USD AUM, AA+ Fix SCR, ~6% expected annual net, T+1 rescue | 2026-03-06 |
| `history/transactions.md` | Append-only trade ledger | When new trades confirmed |
| `history/snapshots/YYYY-MM-DD.md` | Weekly point-in-time archives | Every Monday |
| `alerts/YYYY-MM-DD-HH.md` | Compiled alert archive (what was sent to Slack) | Twice daily |
| `alerts/FAILED-YYYY-MM-DD-HH.md` | Failed Slack delivery marker | On delivery failure |
