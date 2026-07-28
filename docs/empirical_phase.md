# Empirical Phase: Frontier Models in an IPO Enterprise Workflow

## Objective

The empirical phase tests whether finance capabilities measured in isolation remain predictive when they must compose into one persistent IPO workflow.

The same model or system is evaluated under three conditions:

1. **isolated** — each department works independently with no upstream artifacts;
2. **generalist** — one agent produces all four artifacts in one call;
3. **multi_agent** — specialized departmental calls pass structured handoffs downstream.

The four departments are due diligence, valuation, risk, and the ECM committee.

## Primary hypotheses

- **H1 — composition gap:** component scores will exceed workflow scores for at least some systems.
- **H2 — rank instability:** rankings on isolated tasks may not survive the transition to the full workflow.
- **H3 — coordination sensitivity:** multi-agent specialization may improve local quality while increasing handoff failures.
- **H4 — freshness:** filing amendments will expose stale-version errors that isolated task scores miss.

## Runner outputs

Every run creates a dedicated directory containing:

- `diligence.json`;
- `valuation.json`;
- `risk.json`;
- `memo.json`;
- `run_metadata.json`;
- `trajectory.jsonl`;
- `score.json`.

The metadata records the system, condition, repetition, timing, token usage, estimated cost, response hashes, and the hash of the case specification.

## Offline validation

Run the deterministic controls before any paid model experiment:

```bash
make experiment-test
make empirical-dry-run
```

The oracle control must pass all three conditions. The stale-silo control must complete locally but fail enterprise success because departments use inconsistent filing versions.

These controls are software-validation results, not model results.

## Configure frontier models

Copy the example configuration:

```bash
cp configs/ipo_empirical.example.json configs/ipo_empirical.local.json
```

For each system:

1. set `enabled` to `true`;
2. replace `MODEL_NAME_HERE` with the exact frozen model identifier;
3. set the provider base URL and API key environment variables;
4. enter the documented token prices used on the experiment date;
5. preserve temperature, prompt, cases, and repetitions across systems.

Example environment variables:

```bash
export QWEN_API_BASE='https://provider.example/v1'
export QWEN_API_KEY='...'
export KIMI_API_BASE='https://provider.example/v1'
export KIMI_API_KEY='...'
```

Then run:

```bash
PYTHONPATH=src python -m evisuff.experiment_cli run \
  configs/ipo_empirical.local.json
```

Use `--overwrite` only when intentionally replacing an existing run. By default, completed runs are resumed from disk.

## Backends

### OpenAI-compatible API

Use `type: openai_compatible` for providers exposing a chat-completions-compatible endpoint. The runner supports JSON mode, retries on rate limits/server failures, custom headers, and provider-specific extra request fields.

### Local command or custom harness

Use `type: command` to evaluate a local agent, open-weight model, or richer browser/tool harness. The command receives one JSON request on standard input and must emit a JSON envelope on standard output:

```json
{
  "parsed": {"...": "department artifact or generalist bundle"},
  "input_tokens": 0,
  "output_tokens": 0
}
```

This keeps the benchmark independent of a specific model SDK.

## Case expansion

The current CI fixture is synthetic. The research experiment should add at least three public IPO families with:

- an initial S-1 or F-1;
- at least one amendment;
- stable document/version identifiers;
- verified offer, capitalization, and risk facts;
- source packets containing the evidence shown to the model;
- a frozen gold specification reviewed before model execution.

Cases must be split by issuer. Do not tune prompts or scoring rules after seeing held-out model outputs.

## Analysis plan

Report, per system and condition:

- component score;
- coordination score;
- workflow score;
- composition gap;
- enterprise-success rate;
- stale-version and handoff failures;
- input/output tokens;
- estimated cost;
- latency.

The central analysis compares rank order across isolated, generalist, and multi-agent conditions. Any leaderboard claim requires multiple cases and repetitions, uncertainty intervals, and inspection of failed artifacts.

## Claim boundary

The runner enables frontier-model experiments but does not itself establish that any model or laboratory is better. Do not report deterministic controls as model results. Outputs from external models require verifier review and, for ambiguous qualitative criteria, human validation.
