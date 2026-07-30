# Archived Preregistered Experiment v1: Stateful IPO Workflow Composition

**Original registration date:** 2026-07-30  
**Current status:** `superseded_before_official_inference`  
**Official model calls completed:** `0`  
**Official workflow runs completed:** `0`  
**Frozen benchmark commit:** `1342e9cf8a85f6cbc4c05d52001820d4e9ead8fb`  
**Frozen benchmark branch:** `freeze/preregistered-v1-2026-07-30`  
**Original registration branch:** `registration/evisuff-stateful-ipo-v1`

## Archival notice

This protocol was validly frozen before inference, but it is no longer the active experimental plan. It was superseded on 2026-07-30 after external scientific feedback showed that the contribution needed direct same-model comparisons with recognized finance-agent benchmarks.

The quota preflight for the first planned block made zero model calls and started zero official workflows. No registered outcome was observed or discarded.

The complete original protocol remains immutably available on branch:

```text
registration/evisuff-stateful-ipo-v1
```

The detailed supersession record is:

```text
docs/preregistered_v1_supersession.md
```

The replacement bridge design is:

```text
docs/benchmark_alignment_v2.md
configs/benchmark_bridge_v2.json
configs/bridge_v2_upstream_lock.json
```

## Original V1 design summary

V1 proposed to evaluate one fixed model, `openai/gpt-oss-20b:free`, on:

- three IPO cases: Reddit 2024, CoreWeave 2025, and Rubrik 2024;
- three orchestration conditions: generalist, isolated, and multi-agent;
- three repetitions per case-condition cell;
- 27 workflow runs and 162 model calls;
- strict final enterprise success after a `v1 → v2` filing update.

Its prompts, schemas, cases, scoring rules, failure taxonomy, execution blocks, and analysis plan remain available in the original registration branch and machine-readable archival configuration:

```text
configs/preregistered_matrix_v1.json
```

## Why it was superseded

V1 studied orchestration differences only inside EviSuff-Finance. It did not produce the direct comparison demanded for clear field positioning:

- FinAR-Bench score for the same model;
- IPO Finance Agent score for the same model;
- BigFinanceBench score for the same model;
- EviSuff stateful workflow score for the same model.

V2 therefore treats EviSuff as a cross-benchmark composition test: it asks whether finance capabilities measured on recognized reference tasks remain reliable when they must compose across diligence, valuation, risk, and an ECM memo after an authoritative amendment.

## Reporting rule

V1 must never be described as completed, failed, or abandoned after observing official results. The correct description is:

> Registered and superseded before official inference; zero official calls and zero official workflow runs.
