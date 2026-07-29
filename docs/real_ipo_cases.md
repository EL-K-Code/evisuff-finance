# Real IPO case pack v1

This case pack converts official SEC filings into version-sensitive IPO workflow cases. It is designed for the paired experiment comparing isolated department tasks, one generalist agent, and a specialized multi-agent team.

## Claim boundary

The three cases are benchmark inputs and gold annotations, not model results. Each case is currently marked:

`single_researcher_verified_against_official_sec_sources_second_review_pending`

No conference-grade empirical claim should be made until a second reviewer independently checks the numeric labels, risk labels, document chronology, and evidence normalization.

## Gold-label isolation and public output vocabulary

Each case contains two separate structures:

- `source_packet`: the public evidence shown to evaluated systems;
- `versions`: private gold facts and scored risk sets used only by deterministic controls and verifiers.

Hosted API prompts receive only `source_packet`. The command backend also strips the private `spec` from metadata before invoking an evaluated local agent.

Risk evidence in `source_packet` includes a public `risk_id`. This field is the canonical output vocabulary that an evaluated system must use in `risk_flags` and `top_risks`; it is not a leaked answer. The private gold structure determines which public identifiers are required for a particular version. Public and scored risk identifiers are checked for exact alignment in the test suite so a model is never asked to guess an internal label.

## Normalized field definitions

- `price_per_share_usd`: offer price associated with the packet version.
- `primary_shares_m`: issuer shares sold in the packet version, in millions. A closing update includes exercised underwriter options when officially reported.
- `existing_shares_m`: non-primary shares included in the case's post-offering denominator. This is a normalized benchmark quantity, not always identical to one filing line item; for CoreWeave it includes non-primary shares associated with the concurrent issuance and existing share classes.
- `debt_usd_m`: funded debt used by the case, in millions, at the disclosed balance-sheet date.
- `cash_usd_m`: cash measure used by the case, in millions, at the disclosed balance-sheet date. The exact definition is preserved in the evidence packet.

The valuation department derives:

- gross proceeds = price × primary shares;
- post-money equity value = price × (existing shares + primary shares);
- net debt = debt − cash;
- dilution = primary shares ÷ (existing shares + primary shares).

These are benchmark calculations, not investment recommendations or full valuation models.

### Numeric scoring contract

Source facts and cross-department handoffs are checked with an effective absolute tolerance of `1e-6`. Derived monetary metrics expressed in USD millions and dilution percentages use an absolute reporting tolerance of `0.01`. The looser derived-metric tolerance permits harmless presentation rounding while still rejecting economically meaningful calculation errors. The tolerance values must be frozen with the benchmark and disclosed in empirical reports.

## Case 1 — Reddit, Inc. (`RDDT`)

**Research stressor:** preliminary midpoint versus final price, a closing update that adds the fully exercised underwriter option, and a newly disclosed regulatory inquiry affecting the risk state.

### Version 1

- S-1/A accession `0001628280-24-010137`, filed March 11, 2024;
- assumed midpoint price: $32.50;
- primary shares: 15,276,527;
- existing shares used in the denominator: 143,707,045;
- no scored FTC data-licensing inquiry because the company had not yet received the March 14 letter.

### Version 2

- S-1/A accession `0001628280-24-011448`, filed March 15, 2024, first disclosing the FTC inquiry;
- final 424B4 accession `0001628280-24-012380`;
- closing 8-K accession `0001628280-24-012880`;
- final price: $34.00;
- primary shares at closing: 18,576,527, including the 3,300,000-share underwriter option;
- new scored risk: `ftc_data_licensing_inquiry`.

The case tests whether later departments update both the financial state and the risk memo after Reddit disclosed a non-public FTC inquiry focused on selling, licensing, or sharing user-generated content with third parties to train AI models.

## Case 2 — Rubrik, Inc. (`RBRK`)

**Research stressor:** the final IPO packet is later updated by a partially exercised underwriter option.

### Version 1

- 424B4 accession `0001193125-24-118478`;
- final price: $32.00;
- initial primary shares: 23,500,000.

### Version 2

- the same pricing prospectus plus the later 10-Q accession `0001943896-24-000030`;
- additional option shares: 3,472,252;
- total primary shares used by the closing case: 26,972,252.

The case tests whether a workflow that was locally correct at pricing remains correct after the option update.

## Case 3 — CoreWeave, Inc. (`CRWV`)

**Research stressor:** a large repricing and resizing between the preliminary and final prospectus, with high leverage and a concurrent issuance affecting the denominator.

### Version 1

- S-1/A accession `0001193125-25-058309`;
- preliminary midpoint: $51.00;
- planned primary shares: 47,178,660;
- normalized non-primary denominator: 426,302,271.

### Version 2

- final 424B4 accession `0001193125-25-067651`;
- final price: $40.00;
- final primary shares: 36,590,000;
- normalized non-primary denominator: 427,509,446.

The case tests whether agents reconcile multiple simultaneous changes rather than updating only the headline price.

## Evidence policy

Evidence text in `source_packet` is a short normalized annotation, not a verbatim quotation. Every document URL must point to the official SEC EDGAR archive. Validation rejects non-SEC URLs, missing accessions, duplicate evidence identifiers, mismatched version IDs, hidden fact leakage, public/scored risk-ontology mismatches, and a required source version that is not chronologically latest.

## Reproduce validation

```bash
make real-case-test
make privacy-test
make real-case-validate
```

The committed report is `results/real_ipo_case_validation.json`. It currently records three valid cases, eight official SEC documents, and 53 normalized evidence items. Reddit is the first case with a scored risk-set transition between versions.

## Before real-model execution

1. Complete the independent second review in `docs/annotation_review_checklist.md`.
2. Freeze the case-pack commit SHA.
3. Freeze exact model identifiers and API parameters.
4. Run all three conditions with repeated trials.
5. Inspect failed artifacts and verifier decisions before publishing aggregate scores.
