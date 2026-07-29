# Paper outline — Can Benchmark Skills Compose into an IPO Workflow?

## Working title

**Can Benchmark Skills Compose After the Filing Changes? Stateful Evaluation of Finance Agents in an IPO Workflow**

Potential result-driven social title:

**Every Agent Passed the First Round. The Filing Changed. The Bank Still Failed.**

## Central problem

Most finance benchmarks score a capability on a fixed input. Real enterprise work is stateful: a department can finish a locally correct artifact, a later authoritative filing can change the facts, and stale values can propagate through valuation, risk, and committee decisions.

The paper therefore asks whether finance-agent capabilities remain reliable when the evidence changes after work has already been produced.

## Abstract claim boundary

The deterministic controls validate the environment and verifiers, not frontier-model performance. The existing single-model static smoke tests are engineering evidence only. Paper-grade claims require the stateful protocol, frozen cases and prompts, repeated model runs, independent annotation review, verifier spot checks, and uncertainty intervals.

## Research questions

1. Does success on isolated finance tasks predict successful revision of a multi-department workflow after an authoritative filing update?
2. After the update, does a specialized multi-agent workflow outperform one generalist agent once stale handoffs and cross-artifact inconsistencies are counted?
3. Do model and orchestration rankings remain stable between the initial filing state and the amendment state?
4. How much failure is attributable to stale evidence, incomplete revision, scenario mismatch, provenance loss, and cross-artifact inconsistency?
5. Which orchestration achieves the best enterprise-success rate per call, token, latency, and cost?

## Falsifiable hypotheses

- **H1 — Static overestimation:** one-shot workflow scores will overestimate enterprise success under a later filing update.
- **H2 — Composition failure:** high component scores can coexist with failed enterprise updates because one or more departments remain stale.
- **H3 — Handoff trade-off:** explicit specialist handoffs can improve local reuse while also propagating an upstream revision error to downstream artifacts.
- **H4 — Ranking instability:** at least one model or orchestration ranking will reverse between static and stateful evaluation.

## Stateful protocol

### Round 1 — initial filing

The system receives only the earliest public packet version and produces due-diligence, valuation, risk, and ECM committee artifacts. These outputs are scored against the initial state.

### Round 2 — authoritative update

The system receives only the later authoritative packet plus its own Round 1 artifacts. It must revise stale values, calculations, risk identifiers, citations, and downstream handoffs while preserving still-valid information.

Private gold labels remain outside all model prompts.

## Experimental conditions

- `staged_isolated`: four departments update independently, without revised cross-department handoffs;
- `staged_generalist`: one agent creates and later revises the complete workflow state;
- `staged_multi_agent`: four specialists revise sequentially with explicit updated handoffs.

The isolated and multi-agent conditions each use eight calls per case and repetition. The generalist condition uses two calls. Cost-normalized results must therefore accompany raw success rates.

## Primary outcomes

- Round 1 component, coordination, and workflow scores;
- final component, coordination, and workflow scores;
- composition gap;
- enterprise success;
- update success;
- stale-artifact count and stale-artifact rate;
- artifact revision map;
- ranking correlation and pairwise rank reversals;
- calls, tokens, latency, and cost per successful update.

## Deterministic controls

- an oracle control that updates every artifact to the authoritative version;
- an ignore-update control that preserves the initial artifacts after Round 2.

Across Reddit, Rubrik, and CoreWeave, the oracle must achieve 100% update success and the ignore-update control must achieve 0% enterprise success. These are software-validation results only.

## Current and target case scale

Current validated case pack:

- Reddit 2024;
- Rubrik 2024;
- CoreWeave 2025.

Paper target:

- four public IPO families, including at least one case with a material risk-disclosure change rather than only numeric repricing or resizing;
- three to four frontier models, including Chinese-lab models when stable APIs are accessible;
- all three stateful orchestration conditions;
- one complete run across the full matrix, followed by repeated runs on a prespecified stability subset;
- public deterministic verifiers, prompt templates, trajectory hashes, and analysis code.

## Statistical analysis

- paired bootstrap confidence intervals for score differences;
- enterprise-success and update-success confidence intervals;
- Kendall or Spearman rank correlation between static and stateful settings;
- explicit rank-reversal counts;
- sensitivity analysis for component/coordination weighting and numerical tolerances;
- failure taxonomy with human review of a prespecified sample of verifier decisions.

## Contribution target

The contribution is not a generic simulated bank and not a collection of existing benchmark scores. It is a compositional-validity study of whether benchmark-level finance skills remain predictive when those skills must preserve a coherent enterprise state through an authoritative evidence update.
