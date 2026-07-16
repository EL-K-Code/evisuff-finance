# Reproducibility protocol

## Immutable inputs

For each run, freeze and record:

- dataset release tag and SHA-256 hashes of filing extracts;
- allowed corpus and cutoff date;
- retrieval index version, chunking policy, embedding/reranker IDs, and top-k;
- prompt template and SHA-256 hash;
- model/provider ID, API version, access date, decoding settings, and run ID;
- evaluator version, human-label calibration set, and statistical code version.

## Execution order

1. Validate annotations with `evisuff validate`.
2. Evaluate retrieval alone using Recall@k, nDCG@k, and Complete Evidence
   Recall.
3. Freeze a retrieval configuration on development data.
4. Run `full`, `gold_only`, `necessary_removal`, and `irrelevant_removal` with
   the same output contract.
5. Calculate paired metrics with question-level bootstrap confidence intervals.
6. Audit primary-model disagreements manually and publish a failure taxonomy.

## Required result manifest

Each result JSONL row should include at least:

```json
{
  "item_id": "...",
  "condition": "necessary_removal",
  "model": "provider-model-id",
  "run_id": "...",
  "expected_answerable": false,
  "abstained": true,
  "p_answerable": 0.08,
  "correct": false,
  "citation_ids": [],
  "prompt_hash": "...",
  "retrieval_config": "...",
  "dataset_version": "..."
}
```

`correct` is only meaningful for answerable conditions. For unanswerable
conditions, the primary behavioral target is abstention, not a synthetic gold
answer.
