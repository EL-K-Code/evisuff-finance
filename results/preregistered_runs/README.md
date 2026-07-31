# Preregistered Runs v1

This directory is reserved for official runs governed by:

- `docs/preregistered_experiment_v1.md`
- `configs/preregistered_matrix_v1.json`
- frozen benchmark commit `1342e9cf8a85f6cbc4c05d52001820d4e9ead8fb`
- frozen reference branch `freeze/preregistered-v1-2026-07-30`

Exploratory Gemini and OpenRouter pilot results must not be copied into this directory or included in preregistered estimates.

## Required structure

Each official execution block must write to a separate directory:

```text
results/preregistered_runs/<block_id>/
```

Expected block identifiers:

- `r1-a`
- `r1-b`
- `r2-a`
- `r2-b`
- `r3-a`
- `r3-b`

Each block must retain:

- the secret-free execution configuration;
- workflow summaries;
- raw model trajectories;
- response hashes and response identifiers;
- requested and returned model identifiers;
- token counts and latencies;
- provider-attempt ledger, including quota and transport failures;
- frozen commit SHA and preregistration ID;
- an explicit deviation log, even when empty.

## Inclusion rule

A workflow belongs to the official analysis only when it contains all required metadata from `configs/preregistered_matrix_v1.json` and was executed against the frozen benchmark commit. Model-originated JSON or schema failures count as strict enterprise failures. Provider failures before any model output are non-evaluable and remain in the technical-attempt ledger.

## Audit policy

Official outputs are append-only. Do not overwrite or manually edit model artifacts. Corrections, reruns, exclusions, and adjudications must be added as new records with timestamps and reasons.
