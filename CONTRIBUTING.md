# Contributing to EviSuff-Finance

This repository supports a research benchmark. Changes to benchmark labels are
scientific changes, not routine data edits.

## Before opening a pull request

1. Explain whether the change affects code, annotations, documentation, or the
   paper.
2. Do not add SEC filing copies, API keys, unpublished questions, or private
   annotations to the repository.
3. Keep every public annotation traceable to a stable document and passage ID.
4. For a change to a minimal sufficient evidence set (MSES), include the
   rationale and an independent reviewer or adjudication note.
5. Run the validation and test commands below.

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m evisuff.cli validate data/example_annotations.jsonl
PYTHONPATH=src python -m evisuff.cli smoke --output results/smoke_metrics.json
```

## Research integrity

Never report synthetic smoke-test values as empirical model results. A result
table must identify the dataset version, model ID, prompt version, retrieval
configuration, number of repetitions, evaluator, and statistical procedure.
