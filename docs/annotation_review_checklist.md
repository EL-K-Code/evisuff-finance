# Independent annotation review checklist

Use this checklist for every case before the benchmark is frozen for real-model experiments.

## Reviewer independence

- The second reviewer receives the official SEC URLs and field definitions.
- The reviewer records values independently before seeing the existing gold labels.
- Disagreements are preserved in an adjudication log; they are not silently overwritten.

## Document chronology

- Confirm issuer, ticker, CIK, form type, accession, and filing date.
- Confirm that each URL points to the official SEC EDGAR archive.
- Confirm that the required version is the chronologically latest authoritative packet.
- Confirm whether an 8-K or 10-Q adds a closing or underwriter-option update.

## Numeric labels

For every version, independently verify:

- offer price per share;
- issuer primary shares;
- non-primary denominator used by the case;
- funded debt measure and balance date;
- cash measure and balance date;
- units and conversion to millions.

Recalculate and compare:

- gross proceeds;
- post-money equity value;
- net debt;
- dilution.

Record any ambiguity in field interpretation, particularly around concurrent issuances, option exercises, restricted cash, marketable securities, and debt net of discounts.

## Risk labels

- Locate filing support for every risk identifier.
- Confirm that the label is material to the case and not merely generic boilerplate.
- Confirm that no unsupported risk was added.
- Record whether a risk is new, removed, or substantively changed across versions.

## Evidence packet

- Confirm that every normalized evidence sentence is faithful to the filing.
- Confirm that paraphrases do not strengthen or weaken the source claim.
- Confirm evidence IDs are unique within each version.
- Confirm no private gold `facts` or `risk_flags` appear in `source_packet`.

## Adjudication record

For each disagreement, record:

- case and version;
- field or risk label;
- annotator A value;
- annotator B value;
- source passage or table;
- final adjudicated value;
- reason for the decision.

## Freeze gate

A case may be marked `double_reviewed_and_adjudicated` only after:

- every checklist item passes;
- all disagreements are adjudicated;
- automated validation passes;
- the case-pack commit SHA is recorded;
- the real-model run configuration references that frozen SHA.
