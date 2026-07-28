# EviSuff-Finance — IPO Multi-Department Workflow Benchmark

This repository is evolving from a single-task evidence diagnostic into a **compositional finance-agent environment**. The core research question is:

> **Can benchmark-level finance skills compose into a coherent enterprise workflow?**

The first environment simulates one IPO process across four departments:

1. **Due diligence** — extract filing facts and provenance, inspired by IPO Finance Agent.
2. **Valuation** — compute proceeds, equity value, net debt, and dilution, inspired by spreadsheet-agent benchmarks.
3. **Risk** — identify material risks and amendments.
4. **ECM committee** — produce a final memo consistent with every upstream artifact.

The benchmark scores both local department quality and enterprise-level coordination. A system can therefore score well on every local task while failing the workflow because departments use different filing versions, scenarios, values, risks, or citations.

## Why this direction

Frontier-agent evaluation is moving from static prompts toward stateful environments with tools, files, verifiers, traces, and multi-round workflows. Finance is useful as a stress test because it provides verifiable numbers, provenance, cross-artifact dependencies, and consequential handoffs.

The novelty target is **not** “another simulated bank.” The research target is the **composition gap** between isolated benchmark performance and end-to-end enterprise performance.

## Current milestones

### 1. Deterministic workflow pilot

The software-validation fixture includes:

- one synthetic issuer;
- an S-1 followed by an S-1/A amendment;
- four departmental artifacts;
- local component checks;
- cross-department handoff checks;
- freshness and provenance checks;
- three deterministic controls.

The `siloed_benchmark_winners` control is internally correct within each department's declared filing but globally inconsistent because departments do not share the same authoritative version. This validates that the benchmark can expose failures that isolated task scores miss.

### 2. Empirical frontier-model runner

The runner executes a full experiment matrix across:

- multiple IPO cases;
- multiple systems or model providers;
- three conditions: `isolated`, `generalist`, and `multi_agent`;
- configurable repetitions.

It supports:

- OpenAI-compatible APIs for hosted frontier models;
- arbitrary local agents through a command-line adapter;
- retries and failure preservation;
- resumable runs;
- structured departmental handoffs;
- trajectories and response hashes;
- token, cost, and latency accounting;
- automatic workflow scoring and aggregation.

No API key is stored in the repository. Private gold labels are not included in hosted prompts and are stripped from command-backend metadata.

### 3. Real SEC IPO case pack

The first real-data pack contains:

- **Reddit 2024** — preliminary midpoint, final pricing, and a fully exercised underwriter option;
- **Rubrik 2024** — final pricing followed by a partially exercised underwriter option;
- **CoreWeave 2025** — major repricing and resizing between preliminary and final prospectuses.

The pack contains eight official SEC documents and 52 normalized evidence items. Automated validation checks official EDGAR URLs, chronology, version alignment, schema completeness, duplicate evidence IDs, and gold-label isolation.

The current annotation status is `single_researcher_verified_against_official_sec_sources_second_review_pending`. These cases are benchmark inputs, not model results. See [`docs/real_ipo_cases.md`](docs/real_ipo_cases.md) and [`docs/annotation_review_checklist.md`](docs/annotation_review_checklist.md).

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make test
make real-case-validate
make workflow-pilot
make empirical-dry-run
```

The empirical dry run uses deterministic controls on all three real IPO cases. It must never be reported as a model leaderboard.

## Run frontier models

Copy the provider template:

```bash
cp configs/ipo_empirical.example.json configs/ipo_empirical.local.json
```

Enable the selected systems, freeze their exact model identifiers, set API base URLs and keys through environment variables, then run:

```bash
PYTHONPATH=src python -m evisuff.experiment_cli run \
  configs/ipo_empirical.local.json
```

See [`docs/empirical_phase.md`](docs/empirical_phase.md) for the experiment protocol, backend contract, claim boundary, and case requirements.

## Research metrics

- **Component score** — mean quality across due diligence, valuation, risk, and memo artifacts.
- **Coordination score** — freshness, shared scenario, numerical handoffs, risk propagation, and provenance.
- **Workflow score** — `0.6 × component + 0.4 × coordination`.
- **Composition gap** — component score minus workflow score.
- **Enterprise success** — all critical local and coordination checks pass.
- **Operational metrics** — tokens, estimated cost, latency, completion rate, and failure traces.

## Repository map

```text
configs/ipo_empirical_dry_run.json     offline controls over the real cases
configs/ipo_empirical.example.json     hosted/local model template
data/ipo_workflow_pilot/spec.json      synthetic two-version fixture
data/ipo_real_cases/                   Reddit, Rubrik, and CoreWeave cases
docs/ipo_workflow_pilot.md             benchmark protocol and research questions
docs/empirical_phase.md                real-model experiment protocol
docs/real_ipo_cases.md                 source and field documentation
docs/annotation_review_checklist.md    independent second-review procedure
docs/landscape_and_novelty.md          positioning against adjacent benchmarks
src/evisuff/enterprise_workflow.py     artifact and workflow scoring
src/evisuff/workflow_cli.py            deterministic workflow pilot CLI
src/evisuff/model_backends.py          API, command, and control backends
src/evisuff/experiment_runner.py       empirical matrix orchestration
src/evisuff/experiment_cli.py          empirical experiment CLI
src/evisuff/real_cases.py              real-case validation and leak checks
src/evisuff/real_cases_cli.py          real-case validation CLI
tests/                                 workflow, runner, privacy, and data tests
results/ipo_workflow_pilot.json        software-validation report
results/real_ipo_case_validation.json  reproducible case-pack validation
paper/ipo_workflow_pilot_outline.md    paper-scale study outline
```

## Empirical study design

The study compares:

1. isolated benchmark-like departmental tasks;
2. one generalist agent completing the entire workflow;
3. a specialized multi-agent team with explicit handoffs.

The central test is whether model rankings, success rates, and cost-efficiency survive the transition from isolated skills to a shared enterprise workflow.

A conference-grade result requires independent annotation review, multiple repetitions, frozen model versions, uncertainty estimates, verifier review, and inspection of natural model failures.

## Legacy EviSuff scaffold

The original counterfactual evidence-sufficiency code remains available and continues to support validation, condition building, and scoring. It may later contribute an evidence-ablation diagnostic inside the due-diligence department.
