# Feature Upvote Top 15 Roadmap Candidates (LLM-Triaged)

Date range analyzed: 2025-09-01 to 2026-02-28  
Input set: 85 suggestions  
Real ideas after LLM triage: 57

Prioritization approach:
- Deduplicated by intent/theme.
- Ranked by combined signal: frequency of similar requests, operational impact, compliance risk, and cross-module leverage.

## Top 15

1. Fiscal compliance automation suite (IVA/ARBA/retenciones/percepciones)
   - What it is: End-to-end support for local tax workflows and regulator-compatible outputs.
   - Why it matters: Highest compliance and churn risk if missing; repeated across multiple entries.
   - Source IDs: 693599, 689701, 666728, 666585, 666516, 666491, 664081, 664044, 678211, 679724

2. Treasury payment/collection reporting and bank export pack
   - What it is: Reliable OP/recibos/cheques reporting with clear totals and bank-ready exports.
   - Why it matters: Directly reduces manual reconciliation and spreadsheet work.
   - Source IDs: 680349, 678261, 678219, 675315, 666318, 666303, 666083, 687113

3. Multi-currency operations hardening (USD across invoicing + treasury)
   - What it is: Improve USD imports, credit notes, bank accounts, reporting, and exchange-rate behavior.
   - Why it matters: Critical for finance correctness in real operations.
   - Source IDs: 686771, 676133, 681399, 683549, 669547

4. High-volume collections and invoice-entry usability overhaul
   - What it is: Bigger/consistent panels, better filters, more visible rows, less interrupted workflows.
   - Why it matters: Daily-use productivity issue for heavy users.
   - Source IDs: 693146, 693002, 688860, 683552, 672205, 668585, 666296

5. Invoice traceability by customer order/project + flexible filtering
   - What it is: Add PO/project/offer fields and allow filtering/sorting by key columns.
   - Why it matters: Strong B2B traceability requirement and sales-admin efficiency gain.
   - Source IDs: 696308, 696295

6. Bulk operations toolkit
   - What it is: Mass update product costs, mass accounting reclassification, bulk collections import.
   - Why it matters: Eliminates high-friction repetitive manual work.
   - Source IDs: 664432, 667872, 665111, 674948

7. Invoice communication reliability (deliverability + reminders + formatting)
   - What it is: Email delivery status/reasons, manual reminder send with templates, proper amount formatting.
   - Why it matters: Reduces payment delays and support load.
   - Source IDs: 680424, 680258, 680296

8. ARCA sync recovery flow
   - What it is: Allow manual backfill when invoice exists in ARCA but not in Colppy.
   - Why it matters: Prevents accounting/reporting gaps and customer-facing issues.
   - Source IDs: 667577

9. Purchase order talonario with auto-numbering
   - What it is: Add purchase-order document series and automatic numbering.
   - Why it matters: Basic procurement control and audit trail expectation.
   - Source IDs: 667792

10. Accounting integrity controls
   - What it is: Validate balanced entries before save and reserve entry #1 for opening.
   - Why it matters: Prevents hard-to-detect bookkeeping errors.
   - Source IDs: 674254, 685346

11. Inventory history visibility
   - What it is: Historical stock by depot at a specific date + last ingress/purchase date in availability.
   - Why it matters: Better inventory aging and planning decisions.
   - Source IDs: 674147, 687824

12. Payment application guardrails
   - What it is: Disallow applying one payment order against another payment order.
   - Why it matters: Avoids incorrect account-current applications.
   - Source IDs: 692562

13. Document compliance fields in operational forms
   - What it is: Add key legal/commercial fields in core documents (example: CAI in remitos).
   - Why it matters: Frequent request where legal or customer-process requirements exist.
   - Source IDs: 696934

14. Finance/analytics reporting upgrade
   - What it is: Broader dashboard periodization/drill-down and more formal customer-facing statements/reports.
   - Why it matters: Improves management visibility and external communication quality.
   - Source IDs: 688873, 688446, 683044

15. Commerce integration quality-of-life
   - What it is: Product photo support in inventory records for downstream commerce usage.
   - Why it matters: Speeds catalog workflows and external channel readiness.
   - Source IDs: 666295

## Notes

- This list is deduplicated by intent. Several single suggestions are represented inside a broader theme.
- Some source titles are terse/noisy; prioritization used title + description semantics.
- Full artifacts for traceability:
  - `docs/feature_upvote_real_ideas_sep2025_feb2026_llm.csv`
  - `docs/feature_upvote_support_complaints_sep2025_feb2026_llm.csv`
  - `docs/feature_upvote_llm_classified_sep2025_feb2026.json`
