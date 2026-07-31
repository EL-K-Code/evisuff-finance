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

Each department receives the source packet but no upstream artifact. This approximates evaluating due diligence, valuation, risk analysis, and memo production as separate benchmark tasks. It requires four calls per case.

### Generalist

One model call produces all four artifacts and is instructed to reconcile them before returning. It requires one call per case.

### Multi-agent

Four sequential specialist calls are used. Due diligence hands facts to valuation and risk; all upstream artifacts are handed to the ECM memo agent. It requires four calls per case.

The complete design therefore uses nine calls per case and repetition. With three cases and three repetitions, each evaluated system requires 81 calls.

## Required systems

Freeze exact provider and model identifiers before execution. The initial comparison should include at least:

- two models from Chinese frontier labs when accessible;
- one strong Western frontier model;
- one additional cost-efficient or open-weight baseline.

The repository includes adapters for Qwen, Kimi, OpenAI-compatible providers, Anthropic's native Messages API, and local command agents. Never use moving aliases such as `latest` when a dated or immutable identifier is available. Save the complete run config and case-pack commit SHA with the results.

## Repetitions

Use at least three repetitions per `case × system × condition`. Increase repetitions when outputs remain highly variable or when rank conclusions depend on small score differences.

## Secure provider configuration

1. Copy `sample.env` to `.env`.
2. Enable only selected providers.
3. Enter API keys, endpoints, exact model identifiers, and dated token prices.
4. Run `make prepare-real-run`.
5. Review the printed systems and planned call count.
6. Run `make run-real-models`.

The generated `configs/ipo_empirical.local.json` contains no API key and is ignored by Git. The experiment command reloads `.env` at execution time through `--env-file .env`.

## Backend contract

### OpenAI-compatible hosted models

The dependency-free backend sends only:

- system prompt;
- task prompt containing `source_packet`;
- frozen generation parameters.

It supports JSON response mode, retries, custom headers, and provider-specific request fields.

### Anthropic hosted models

The native Messages backend sends the system prompt separately, uses the Messages endpoint, reads native token usage, and parses the returned text as the required JSON artifact.

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
cp sample.env .env
make prepare-real-run
make run-real-models
```

Direct execution without `make`:

```bash
python tools/prepare_real_run.py --env .env --output configs/ipo_empirical.local.json
PYTHONPATH=src python -m evisuff.experiment_cli run \
  configs/ipo_empirical.local.json --env-file .env
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
