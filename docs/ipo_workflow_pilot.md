# IPO Multi-Department Workflow Pilot

## Research question

Can systems that perform well on isolated finance benchmarks compose those capabilities into one coherent, auditable IPO workflow?

## Motivation

Current benchmarks isolate valuable capabilities: long-document financial research, spreadsheet manipulation, risk analysis, or document production. Real enterprise work requires these capabilities to interact through handoffs, shared assumptions, evolving evidence, and cross-artifact consistency.

The pilot measures the gap between:

- **local correctness**: each department produces an internally correct artifact;
- **enterprise correctness**: all departments use the same authoritative filing, scenario, numbers, risks, and provenance.

## Environment

The synthetic fixture contains two authoritative versions:

- `v1`: initial S-1;
- `v2`: S-1/A amendment changing offer price, primary shares, customer concentration, and risk disclosures.

Four departments produce artifacts:

| Department | Artifact | Core responsibility |
|---|---|---|
| Due diligence | `diligence.json` | facts and filing citations |
| Valuation | `valuation.json` | inputs and computed metrics |
| Risk | `risk.json` | material risk flags |
| ECM committee | `memo.json` | final recommendation and integrated evidence |

## Paired evaluation

The study will eventually compare the same underlying IPO facts under:

1. isolated questions/tasks;
2. a single-agent end-to-end workflow;
3. a multi-agent departmental workflow.

This pairing is important: the goal is not merely to show that a longer task is harder, but to test whether benchmark-level performance predicts enterprise-level coordination.

## Metrics

### Component score

Mean of the four department scores, where each artifact is judged relative to the source version it declares.

### Coordination score

Checks whether all artifacts:

- use the required latest source version;
- share one scenario;
- propagate diligence facts into valuation;
- propagate valuation outputs into the memo;
- propagate risk findings into the memo;
- cite the latest authoritative filing.

### Composition gap

`component_score - workflow_score`

A positive gap indicates that isolated task quality overstates enterprise workflow quality.

### Enterprise success

Binary success requiring every critical local and coordination check to pass.

## Synthetic controls

- `coordinated_team`: latest evidence and consistent handoffs; expected to pass.
- `siloed_benchmark_winners`: each department is internally correct, but valuation and memo use the old filing; expected to expose a composition gap.
- `partial_handoff`: latest filing is used, but a new risk and final provenance update are missed.

These are software-validation controls, not claims about any real model.

## Pilot GO criteria for real models

Proceed to a paper-scale study if at least two of the following occur:

1. isolated task scores exceed workflow scores by at least 10 percentage points;
2. at least one model ranking changes between isolated and workflow conditions;
3. multi-agent specialization improves component scores but worsens handoff consistency;
4. a model completes all local tasks yet fails enterprise success;
5. amendment injection causes stale claims or inconsistent artifacts in at least 10% of runs.

## Kill or narrow criteria

Narrow the project if workflow failures are almost entirely explained by one trivial formatting issue, if all rankings remain identical with negligible composition gaps, or if the environment adds complexity without revealing a new capability distinction.
