# Protocol status: preregistration v1 superseded before official inference

**Original preregistration:** `evisuff-stateful-ipo-v1`  
**Original registration date:** 2026-07-30  
**Supersession date:** 2026-07-30  
**Status:** `superseded_before_official_inference`  
**Official v1 model calls completed:** `0`  
**Official v1 workflow runs completed:** `0`

## Decision

The v1 protocol is archived and will not be executed as the confirmatory study. Its frozen benchmark branch, configuration, tests, quota preflight, and exploratory pilots remain in the repository for auditability.

The supersession occurred before any official preregistered inference. The quota preflight for block `r1-a` made zero model calls and started zero official workflows. Therefore, no v1 outcome was observed after registration and no confirmatory result is being discarded.

## Reason

External feedback identified that the contribution was insufficiently anchored to the finance-agent benchmarks that currently define the field. The v1 protocol compared orchestration architectures only inside EviSuff-Finance. It did not provide direct, same-model results against recognized external reference surfaces.

The replacement design must position the contribution quantitatively against:

1. **FinAR-Bench** — information extraction, indicator computation, and logical reasoning in fundamental analysis;
2. **IPO Finance Agent** — long-document IPO due diligence over registration statements with rubric grading;
3. **BigFinanceBench** — workflow-grounded financial research with auditable, point-weighted derivations;
4. **EviSuff Stateful IPO Workflow** — persistent four-artifact workflow composition across an authoritative `v1 → v2` amendment.

## What remains valid

The following remain valid exploratory engineering evidence, but are excluded from all future confirmatory estimates:

- the three real IPO cases: Reddit 2024, Rubrik 2024, and CoreWeave 2025;
- the staged workflow runner and scoring implementation;
- the generalist, isolated, and multi-agent orchestration conditions;
- the exploratory OpenRouter and Gemini trajectories;
- the observed failure taxonomy: unit/scale errors, arithmetic drift, handoff inconsistency, and downstream override;
- the finding that perfect coordination can coexist with enterprise failure.

## Replacement boundary

The replacement protocol will be registered under a new identifier after:

- exact external benchmark item IDs are frozen;
- the evaluated model panel is frozen;
- judge models and grading rules are frozen;
- direct benchmark-to-workflow metrics are frozen;
- a small bridge pilot validates the harness without being included in confirmatory estimates.

No v2 confirmatory inference may begin before those objects are committed and a new registration branch is created.
