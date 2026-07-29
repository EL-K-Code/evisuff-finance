# Stateful IPO amendment protocol

## Why this protocol exists

The static pilot exposes all filing versions at once. That is useful for validating
the software, but it does not reproduce the operational failure that motivates the
paper: a department can finish valid work, a later filing can change the enterprise
state, and downstream artifacts can remain stale.

The staged protocol therefore evaluates update behavior rather than one-shot reading.

## Two-round environment

### Round 1 — initial filing

The system receives only the earliest public packet version, normally `v1`.
It produces due-diligence, valuation, risk, and ECM committee artifacts that are
scored against that initial state.

### Round 2 — authoritative update

The system then receives:

- only the later authoritative packet, normally `v2`;
- its own Round 1 artifacts;
- the shared scenario identifier;
- the same output contracts used in the static benchmark.

It must revise stale values, calculations, risks, provenance, and downstream
handoffs while preserving information that remains valid.

Private gold facts remain outside prompts. Hosted providers see only the selected
public packet and previous model artifacts. Command backends continue to strip the
private `spec` object before invocation.

## Conditions

### `staged_isolated`

Four departments work independently in each round. They see the filing update and
their own prior artifact, but no other department's revised output.

Calls per case and repetition: **8**.

### `staged_generalist`

One generalist creates the complete Round 1 workflow state and one generalist call
revises the complete state after the amendment.

Calls per case and repetition: **2**.

### `staged_multi_agent`

Four specialists work sequentially with explicit handoffs in each round. During
the update round, valuation and risk consume revised diligence, and the ECM memo
consumes all revised upstream artifacts.

Calls per case and repetition: **8**.

The isolated and multi-agent conditions therefore have a matched call budget.

## Primary measures

The staged runner reports:

- Round 1 workflow score and enterprise success;
- final component, coordination, and workflow scores;
- final enterprise success;
- update success;
- stale artifacts remaining after the update;
- which artifacts changed between rounds;
- calls, tokens, latency, response hashes, and estimated cost.

A run succeeds only when the final workflow passes the existing critical local and
coordination checks and no artifact still declares the initial filing version.

## Deterministic controls

`staged-oracle-control` updates every artifact to the authoritative version and must
pass.

`staged-ignore-update-control` keeps the initial artifacts after Round 2 and must be
caught as stale. These are software controls, never model results.

## Reproduction

```bash
make staged-test
make staged-dry-run
```

The dry run covers three IPO cases, three staged conditions, and two deterministic
controls without making API calls.

## Claim boundary

The staged dry run validates the environment and verifiers only. Model comparisons
require frozen prompts, model identifiers, repeated trials, independent annotation
review, verifier spot checks, and uncertainty intervals.
