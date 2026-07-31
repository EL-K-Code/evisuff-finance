# IPO Finance Agent rubric protocol for the V2 bridge

**Status:** frozen before rubric generation and before any evaluated-model inference  
**Upstream revision:** `benstaf/ipoagent@091f06913e39738ef464ac3548ad4b533ac47c50`

## Finding from the public release

The 70 SpaceX questions are public and the repository contains the scripts used to construct, audit, enrich, and repair grading rubrics. The pinned public revision does not contain a static final rubric artifact mapped question by question to those 70 public questions.

The V2 bridge therefore must not describe an invented rubric as an official IPO Finance Agent rubric. It will use one of two routes, selected before evaluated-model inference:

1. obtain author-approved frozen rubrics for the 12 selected questions; or
2. reproduce the pinned evaluator-optimizer pipeline and have the resulting rubrics reviewed and frozen by human experts.

## Reproduced pipeline

The pinned orchestrator defines the following process:

1. **Independent fact extraction:** extract atomic facts from five independently generated answer sets.
2. **Fact consolidation:** cluster equivalent facts and retain claims supported by at least two answer sets.
3. **Rubric induction:** classify retained facts into `critical`, `important`, and `optional` tiers.
4. **Rubric audit:** check omissions, hallucinations, contradictions, mistiering, and redundancy.
5. **Enrichment:** run targeted enrichment, consolidation, and re-audit for at most five iterations.
6. **Repair:** run targeted repair and re-audit for at most five iterations.
7. **Human review:** review the final machine-generated rubric before it can be frozen for scoring.

The exact machine-readable parameters and output paths are recorded in `configs/bridge_v2_ipo_rubric_protocol.json`.

## Bias controls added for this study

- Rubric-construction answers are never included in evaluated-model scores.
- The five construction models and all rubric judge models must be frozen before rubric generation.
- Every intermediate rubric, audit decision, enrichment, repair, and human edit is retained.
- Rubrics cannot be edited after the first evaluated-model answer.
- Human adjudication should be blinded to evaluated-model identity.

## Reporting boundary

Until author-approved rubrics and equivalent tool access are available, results on this surface will be labelled:

> **Reproduced IPO Finance Agent public subset**

They will not be described as an official leaderboard reproduction. This preserves the direct comparison requested for the paper without overstating equivalence to the authors' private evaluation artifacts.

## Remaining gate

The protocol is resolved, but inference remains blocked until:

- the five rubric-construction model IDs are frozen;
- the rubric judge IDs are frozen;
- machine rubrics are generated;
- human expert review is documented;
- final rubric hashes are committed.
