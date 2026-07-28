# EviSuff-Finance — IPO Multi-Department Workflow Pilot

This repository is evolving from a single-task evidence diagnostic into a **compositional finance-agent environment**. The pilot asks a sharper question:

> **Can benchmark-level finance skills compose into a coherent enterprise workflow?**

The first environment simulates one IPO process across four departments:

1. **Due diligence** — extract filing facts and provenance, inspired by IPO Finance Agent.
2. **Valuation** — compute proceeds, equity value, net debt, and dilution, inspired by spreadsheet-agent benchmarks.
3. **Risk** — identify material risks and amendments.
4. **ECM committee** — produce a final memo consistent with every upstream artifact.

The benchmark scores both local department quality and enterprise-level coordination. A system can therefore score well on every local task while failing the overall workflow because departments use different filing versions, scenarios, values, risks, or citations.

## Why this direction

Frontier agent evaluation is moving from static prompts toward stateful environments with tools, files, verifiers, traces, and multi-round workflows. The finance use case is useful because it provides verifiable numbers, provenance, cross-artifact dependencies, and high-value handoffs.

The novelty target is **not** “another simulated bank.” The research target is the **composition gap** between isolated benchmark performance and end-to-end enterprise performance.

## Pilot status

The current pilot is a deterministic software-validation fixture, not a model leaderboard. It includes:

- one synthetic issuer;
- an S-1 followed by an S-1/A amendment;
- four departmental artifacts;
- local component checks;
- cross-department handoff checks;
- freshness and provenance checks;
- three synthetic systems that validate the scoring logic.

The `siloed_benchmark_winners` control is intentionally locally correct for each department's declared filing, but globally inconsistent because departments do not share the same authoritative version. This validates that the benchmark can expose a composition failure that isolated task scores miss.

## Run the pilot

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
make workflow-test
make workflow-pilot
```

Or directly:

```bash
PYTHONPATH=src python -m evisuff.workflow_cli synthetic-pilot \
  data/ipo_workflow_pilot/spec.json \
  --runs-dir results/ipo_pilot_runs \
  --output results/ipo_workflow_pilot.json
```

## Research metrics

- **Component score**: mean quality across due diligence, valuation, risk, and memo artifacts.
- **Coordination score**: freshness, shared scenario, numerical handoffs, risk propagation, and provenance.
- **Workflow score**: `0.6 × component + 0.4 × coordination`.
- **Composition gap**: component score minus workflow score.
- **Enterprise success**: all critical local and coordination checks pass.

## Repository map

```text
data/ipo_workflow_pilot/spec.json   synthetic two-version IPO fixture
docs/ipo_workflow_pilot.md         experimental protocol and research questions
docs/landscape_and_novelty.md      positioning against adjacent benchmarks
src/evisuff/enterprise_workflow.py scoring and synthetic baseline generation
src/evisuff/workflow_cli.py         workflow pilot CLI
tests/test_enterprise_workflow.py  deterministic tests
results/ipo_workflow_pilot.json     generated software-validation report
paper/ipo_workflow_pilot_outline.md paper-scale study outline
```

## Next empirical phase

The real study will replace synthetic systems with frontier models and compare:

1. isolated benchmark tasks;
2. one generalist agent completing the workflow;
3. a multi-agent team with departmental handoffs.

The key empirical test is whether model rankings and success rates survive the transition from isolated skills to a shared enterprise workflow.

## Legacy EviSuff scaffold

The original counterfactual evidence-sufficiency code remains available in the repository and continues to support its existing validation, condition-building, and scoring commands. It may later contribute an evidence-ablation diagnostic inside the due-diligence department.
