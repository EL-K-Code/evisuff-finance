# EviSuff-Finance

Research scaffold for **counterfactual evidence-sufficiency evaluation** of
long-document financial agents.

The consolidated French research dossier is available in
[`DOSSIER_RECHERCHE_FR.md`](DOSSIER_RECHERCHE_FR.md).

The paper source and compiled V0 are in [`paper/`](paper/). It is intentionally
a protocol-and-audit draft: it does not claim empirical model results before
the human-verified benchmark exists.

The central question is not only whether an agent retrieves relevant text, but
whether it changes its answer appropriately when evidence required for the
answer is removed. The benchmark therefore represents each question with one
or more **minimal sufficient evidence sets** and creates paired conditions:

- `full`: all available evidence;
- `gold_only`: only a minimal sufficient evidence set;
- `necessary_removal`: a smallest hitting set is removed so that every minimal
  evidence set is broken;
- `irrelevant_removal`: a distractor is removed as a stability control.

## What is already implemented

- JSONL annotation schema;
- validation of minimal sufficient evidence sets;
- deterministic construction of paired counterfactual conditions;
- metrics for answer quality, abstention, calibration, citation quality,
  complete-evidence retrieval, and paired evidence sensitivity;
- paired bootstrap confidence intervals;
- validation of provider-agnostic prediction manifests and model-wise scoring;
- eight unit tests and a synthetic smoke test;
- research protocol, annotation guide, literature audit, paper source/PDF, and
  experiment config.

## Reproduce locally

```bash
make test
make validate
make smoke
make paper
```

The repository includes a GitHub Actions workflow that runs the public fixture
validation and unit tests on every pull request.

## From annotations to model metrics

```bash
evisuff build-conditions annotations.jsonl --output conditions.jsonl
evisuff score predictions.jsonl --output results/model_metrics.json
```

`build-conditions` produces the paired contexts. `score` validates a provider-
agnostic prediction manifest and computes metrics per model. It does not judge
whether an answer or citation is correct; apply the documented human or
calibrated judging process first.

The synthetic smoke-test scores are software-validation results, **not paper
results**.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
PYTHONPATH=src python -m unittest discover -s tests -v
evisuff smoke --output results/smoke_metrics.json
evisuff validate data/example_annotations.jsonl
```

## Required real-data workflow

1. Select 40--80 questions from IPO Finance Agent across at least 3 S-1/F-1
   filings.
2. Annotate atomic claims and minimal sufficient evidence sets with stable
   passage IDs.
3. Double-annotate at least 25% of items and adjudicate disagreements.
4. Freeze the benchmark before running model experiments.
5. Run the factorial experiment described in `docs/research_protocol.md`.
6. Treat all LLM-judge outputs as auxiliary until calibrated against human
   labels.

## Repository map

```text
configs/experiment.yaml       experiment matrix
data/example_annotations.jsonl
docs/literature_audit.md      novelty audit
docs/research_protocol.md     complete study design
paper/outline.md              proposed paper structure
paper/main.tex                NeurIPS-formatted V0 source
paper/EviSuff-Finance-v0.pdf  compiled V0 (protocol and audit)
src/evisuff/                  benchmark and metrics code
tests/                        unit tests
results/                      generated results only
```

## Upstream project

This work is designed as an evidence-grounded diagnostic extension of
[IPO Finance Agent](https://github.com/benstaf/ipoagent), not as a replacement
or a claim that its original benchmark is invalid.
