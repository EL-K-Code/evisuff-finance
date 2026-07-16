# Paper source

`main.tex` is the V0.1 paper: a protocol, literature audit, and reproducible
upstream audit. It deliberately does **not** claim model-evaluation results.

## Build

```bash
make pdf
```

This uses `latexmk` and writes `EviSuff-Finance-v0.pdf` in this directory.

The repository includes a vendored `neurips_2026.sty` for local compilation.
Before a real submission, replace it with a fresh copy from the official
NeurIPS/Overleaf template and compile under the correct track option. The V0
uses `preprint` only; it is not a declaration of a NeurIPS submission.

## Submission edits still required

- Confirm workshop, track, and paper deadline.
- Confirm authors, affiliations, author order, and acknowledgements.
- Replace the V0 preliminary audit with real model results after human MSES
  annotation and the preregistered experiment.
- Run the official NeurIPS checklist for the chosen track.
