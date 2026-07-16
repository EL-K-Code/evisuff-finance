# Results policy

This directory currently contains two kinds of artifacts:

- `upstream_repository_audit.json`: a reproducible descriptive audit of one
  public IPO Finance Agent revision. It is not an independent estimate of model
  accuracy or rubric quality.
- `smoke_metrics.json`: deterministic results from fictional fixtures. It
  validates the software only and is not a research result.

Every future empirical result must be stored with a run manifest containing:
dataset version, item IDs, condition, model ID, provider/access date, prompt
hash, retrieval configuration, seed or run ID, costs, evaluator version, and
statistical analysis plan.
