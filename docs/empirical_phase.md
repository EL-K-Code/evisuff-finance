# Empirical phase: frontier-model composition study

## Research question

Do finance-agent capabilities measured in isolated tasks remain predictive when those capabilities must be composed through a version-sensitive IPO workflow?

## Frozen case pack

The first empirical pack is indexed by `data/ipo_real_cases/index.json` and contains Reddit 2024, Rubrik 2024, and CoreWeave 2025. Each case includes:

- at least two chronologically ordered evidence packets;
- official SEC EDGAR document URLs and accessions;
- a public `source_packet` shown to systems;
- private gold facts and risks used only by verifiers;
- a required latest source version;
- a single shared valuation scenario.

The current annotation status requires an independent second review before paper-grade real-model runs. See `docs/real_ipo_cases.md` and `docs/annotation_review_checklist.md`.

## Experimental conditions

### Isolated

Each department receives the source packet but no upstream artifact. This approximates evaluating due diligence, valuation, risk analysis, and memo production as separate benchmark tasks.

### Generalist

One model call produces all four artifacts and is instructed to reconcile them before returning.

### Multi-agent

Four sequential specialist calls are used. Due diligence hands facts to valuation and risk; all upstream artifacts are handed to the ECM memo agent.

## Required systems

Freeze exact provider and model identifiers before execution. The initial comparison should include at least:

- two models from Chinese frontier labs when accessible;
- one strong Western frontier model;
- one additional cost-efficient or open-weight baseline.

Never use moving aliases such as `latest` when a dated or immutable identifier is available. Save the complete run config and case-pack commit SHA with the results.

## Repetitions

Use at least three repetitions per `case × system × condition`. Increase repetitions when outputs remain highly variable or when rank conclusions depend on small score differences.

## Backend contract

### Hosted models

The dependency-free OpenAI-compatible backend sends only:

- system prompt;
- task prompt containing `source_packet`;
- frozen generation parameters.

API keys and base URLs come from environment variables. They must never be committed.

### Local command agents

The command backend sends JSON over stdin and expects a JSON envelope over stdout. Private `spec` metadata is stripped before invocation so local systems cannot access gold facts or risk labels.

## Outputs preserved per run

- four department artifacts;
- raw response summaries;
- call trajectory;
- response hashes;
- token usage;
- estimated cost;
- latency;
- verifier report;
- failures and exception text.

Completed runs are resumable unless `--overwrite` is used.

## Primary metrics

- component score;
- coordination score;
- workflow score;
- composition gap;
- enterprise-success rate;
- completion rate;
- stale-version failure rate;
- token use, estimated cost, and latency.

## Core comparisons

1. Within each system, compare isolated, generalist, and multi-agent conditions.
2. Compare model rankings across conditions.
3. Measure whether locally strong systems develop larger or smaller composition gaps.
4. Attribute failures to stale versions, numerical handoffs, missing risk propagation, provenance, malformed artifacts, or execution failure.
5. Report cost per successful enterprise workflow, not only cost per call.

## Claim boundary

Deterministic controls validate software and verifier behavior; they are not model results. Real-model aggregate scores are not paper-ready until:

- case annotations are independently reviewed and adjudicated;
- exact model identifiers and prompts are frozen;
- repeated runs are complete;
- failed traces are manually inspected;
- verifier decisions are spot-checked;
- uncertainty or paired bootstrap intervals are reported;
- rank conclusions are tested for sensitivity to scoring weights.

## Commands

```bash
make real-case-validate
make empirical-dry-run
cp configs/ipo_empirical.example.json configs/ipo_empirical.local.json
PYTHONPATH=src python -m evisuff.experiment_cli run configs/ipo_empirical.local.json
```

## Minimum paper-grade table

For each system and condition, report:

- number of attempted and completed workflows;
- component, coordination, and workflow scores;
- enterprise-success rate;
- composition gap;
- stale-version and handoff failure rates;
- total and per-success tokens, cost, and latency;
- confidence intervals across paired cases and repetitions.
