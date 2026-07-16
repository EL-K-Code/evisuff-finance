# Literature and novelty audit

Audit date: 13 July 2026. Only primary papers, official lab publications, and
official repositories were used for the novelty decision.

## Final verdict

The broad theme "evidence sufficiency and calibrated abstention in
long-document financial agents" is **not novel by itself**. Evidence
sufficiency, RAG abstention, unanswerable search, citation evaluation,
conflicting evidence, temporal mismatch, financial retrieval, and stage-wise
diagnosis all have direct prior art.

The narrower contribution remains defensible:

> Pair each real financial question with controlled evidence interventions
> derived from human-verified minimal sufficient evidence sets, and measure
> whether an agent's answer/abstention behavior is causally sensitive to the
> presence of necessary evidence while remaining stable to irrelevant removal.

No reviewed work combines this paired-intervention design with real IPO filing
tasks, evidence-set completeness, claim-level citations, and explicit
retrieval-versus-generation oracles. This is a **provisional novelty claim**,
not a claim of being the first; it must be rechecked immediately before
submission.

## Direct overlaps and how the final theme differs

| Prior work | Already covers | Remaining distinction |
|---|---|---|
| IPO Finance Agent (2026) | IPO questions, contextual retrieval, automated rubrics, SpaceX S-1 | No minimal evidence sets or paired necessary-evidence removal; component effects not isolated |
| Fin-RATE (2026) | SEC tasks, oracle versus RAG, longitudinal/entity/time errors | Does not make answerability change through paired evidence interventions |
| Sufficient Context (2024) | Definition/classification of sufficient context and selective generation | Mostly labels naturally occurring contexts; does not construct question-level minimal evidence sets in IPO workflows |
| OverSearchQA (2026) | Answerable/unanswerable search and abstention | Not long-document IPO analysis; no claim-level evidence-set interventions |
| LIT-RAGBench (2026) | Integration, reasoning, tables, abstention | Small fictional benchmark; generator isolated from retrieval; no real SEC workflow |
| RAGuard/MAGIC/ArbGraph | Misleading or conflicting evidence | Conflict is optional here; the core manipulation is removal of necessary evidence |
| ALCE (2023) | Citation correctness and completeness | Does not test whether citation/answer behavior changes when required evidence is removed |
| Cited but Not Verified (2026) | End-to-end source attribution quality | Web reports and citation validation, not controlled answerability interventions |
| LOFin/HiREC (2025) | Large-scale SEC retrieval and evidence curation | Focuses on retrieval quality, not counterfactual sufficiency behavior |
| FinAgentBench (2025) | Document and passage selection in financial agentic retrieval | Retrieval-centric; no abstention under broken evidence sets |
| ResearchRubrics/Mind2Web 2 | Rubric-based deep-research evaluation | Open web and broad tasks; no minimal-evidence causal intervention |

## Upstream IPO Finance Agent audit

The public repository contains 70 SpaceX questions:

- 28 quantitative;
- 21 disclosure;
- 8 forensic;
- 6 comparative;
- 4 governance;
- 3 modeling.

The questions cover seven domains and six professional workflows. This is a
useful seed set, but it is not sufficient as the final dataset because it
centers on one issuer and a high-profile filing.

The repository's seventh checked rubric pass contains 70 rubric records. Its
own automated quality block reports:

- mean overall quality: 0.896;
- 23 `stop`, 43 `repair`, and 4 `enrich` recommendations;
- 149 listed issues;
- no top-level passage/evidence identifier field.

These numbers are a reproducible repository audit, not a claim that all final
grading rubrics are wrong. They show why model-derived answer criteria cannot
serve as the only gold standard for an evidence-grounding paper. The proposed
dataset must link every atomic claim to stable, human-verified passages.

One public 70-answer Qwen result artifact provides an additional format-level
diagnostic: all 70 runs succeeded, 68 answers contained at least one URL, but
none used Markdown inline citations or exposed stable evidence/chunk/passage
identifier tokens. The median was one URL per answer. This does not measure
factual correctness and must not be generalized to every model run; it shows
that document-level source links alone cannot support claim-level evidence
completeness evaluation. A public q001 trajectory also returns synthesized
retrieval summaries rather than stable verbatim passage objects.

## Sources

- IPO Finance Agent: https://arxiv.org/abs/2606.23032
- IPO Finance Agent repository: https://github.com/benstaf/ipoagent
- Fin-RATE: https://arxiv.org/abs/2602.07294
- Sufficient Context: https://arxiv.org/abs/2411.06037
- Over-Searching / OverSearchQA: https://arxiv.org/abs/2601.05503
- LIT-RAGBench: https://arxiv.org/abs/2603.06198
- ERA: https://arxiv.org/abs/2604.20854
- MAGIC: https://arxiv.org/abs/2507.21544
- ArbGraph: https://arxiv.org/abs/2604.18362
- ALCE: https://arxiv.org/abs/2305.14627
- Cited but Not Verified: https://arxiv.org/abs/2605.06635
- FinAgentBench: https://arxiv.org/abs/2508.14052
- LOFin/HiREC: https://arxiv.org/abs/2505.20368
- FinSage: https://arxiv.org/abs/2504.14493
- ResearchRubrics: https://arxiv.org/abs/2511.07685
- Mind2Web 2: https://arxiv.org/abs/2506.21506
- BrowseComp (OpenAI): https://openai.com/index/browsecomp/
- Contextual Retrieval (Anthropic): https://www.anthropic.com/engineering/contextual-retrieval
- FACTS Grounding (Google DeepMind): https://deepmind.google/blog/facts-grounding-a-new-benchmark-for-evaluating-the-factuality-of-large-language-models/
- Look-Ahead-Bench: https://arxiv.org/abs/2601.13770
