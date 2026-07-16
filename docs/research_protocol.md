# Complete research protocol

## Final theme

**When Relevant Evidence Is Not Enough: Counterfactual Evidence-Sufficiency
Evaluation for Long-Document Financial Agents**

Short benchmark name: **EviSuff-Finance**.

## Central claim to test

Current financial-agent evaluations reward answer content but do not directly
test whether the agent's behavior is causally sensitive to evidence required
for that answer. EviSuff-Finance will construct paired contexts where necessary
evidence is present or removed while topical relevance and most surface content
remain similar.

The paper must not claim that a new agent is better. Its main contribution is a
diagnostic evaluation and an empirical finding about frontier and open-weight
agents.

## Research questions and preregistered hypotheses

### RQ1: Counterfactual evidence sensitivity

Do agents answer with support under sufficient evidence and abstain after a
minimal intervention breaks all sufficient evidence sets?

- H1: Unsupported persistence after necessary-evidence removal is greater than
  20% for every evaluated model.
- Primary metric: Paired Behavior Success (PBS).

### RQ2: Retrieval versus evidence-use bottlenecks

How much failure remains when gold evidence is supplied?

- H2: Oracle evidence substantially improves answer accuracy but does not
  eliminate unsupported persistence.
- Primary comparison: normal retrieval versus `gold_only`.

### RQ3: Relevance versus sufficiency

Are agents more sensitive to necessary removal than to irrelevant removal?

- H3: behavior changes after necessary removal but remains stable after
  irrelevant removal; models that merely follow topical relevance will fail
  this contrast.

Citation fidelity and calibration are secondary outcomes, not separate papers.
Temporal and contradiction interventions are extensions only after the core
study passes its go/no-go criteria.

## Formal task

For question `q`, corpus `D`, and minimal sufficient evidence sets
`M = {M1, ..., Mk}`, an answerable context contains at least one complete `Mi`.
A necessary-removal intervention removes a smallest hitting set `H` such that
`H` intersects every `Mi`. The resulting context is labelled unanswerable from
the allowed corpus.

This definition prevents a common experimental error: removing one passage
from one evidence path while leaving an alternative complete path intact.

## Dataset construction

### Seed questions

Use the 70 public IPO Finance Agent questions only as candidates. Select items
that have verifiable answers in the permitted filing corpus and can be reduced
to atomic claims. Exclude questions that depend primarily on subjective market
judgment, unstated external priors, or unstable web information.

Suggested first-pass inclusion by category:

| Category | Target |
|---|---:|
| Quantitative/multi-table | 18 |
| Disclosure/absence of disclosure | 14 |
| Accounting/forensic | 12 |
| Governance/control | 8 |
| Comparative, with frozen external sources | 8 |
| Total target | 60 |

### Issuer diversity

Minimum: 3 filings. Preferred: 5 filings. Use public S-1/F-1 filings from SEC
EDGAR and freeze exact accession numbers, filing dates, HTML/PDF hashes, and
extraction code. Keep SpaceX below 40% of the final test items.

### Annotation unit

Each record requires:

- question and reference answer;
- atomic answer claims;
- stable document, section, page/HTML-node, and passage identifiers;
- one or more minimal sufficient evidence sets;
- distractor passages;
- answerability label;
- optional cutoff date;
- annotator and adjudication metadata.

Negative disclosure questions need special treatment. Evidence of absence is
not a single missing string. Annotators must define the bounded search scope
(for example, all revenue-disaggregation sections and referenced notes) and a
verification protocol. Such items should be reported separately.

### Annotation quality

- Train annotators on 10 pilot items.
- Double-annotate at least 25% of the dataset.
- Report agreement on answerability with Cohen's kappa.
- Report evidence-unit overlap with set-level precision, recall, and F1; plain
  kappa is inappropriate for free evidence spans.
- Adjudicate every disagreement.
- Freeze data before model evaluation.
- Keep a hidden final subset if operationally possible.

### Go/no-go after two weeks

Proceed only if:

- at least 20 paired items are validated;
- answerability agreement is at least 0.80 kappa or disagreements can be
  resolved through clearer guidelines;
- at least 70% of items have an unambiguous minimal evidence set;
- necessary-removal pairs pass manual verification by two people.

Otherwise reduce scope to quantitative and disclosure items with deterministic
evidence.

## Experimental design

### Context conditions

1. `full`: full retrieved or curated context.
2. `gold_only`: a minimal sufficient evidence set only.
3. `necessary_removal`: a minimal hitting set removed; expected unanswerable.
4. `irrelevant_removal`: a distractor removed; expected behavior unchanged.

Optional after the main experiment:

5. topical distractor injection;
6. contradiction injection with source/date credibility metadata.

### Retrieval systems

Use retrieval systems as controlled factors, not as the claimed innovation:

- BM25;
- BGE-M3 dense retrieval;
- reciprocal-rank-fusion hybrid;
- contextual hybrid retrieval plus reranking;
- gold-evidence oracle.

Chunk sizes: 512 and 1,024 tokens with 128-token overlap. Evaluate top-k in
`{5, 10, 20}` during development, then freeze one configuration per system.

### Generation models

Minimum defensible set:

1. one OpenAI frontier reasoning model available through the API at experiment
   freeze time;
2. one Anthropic Sonnet/Opus model available through the API at freeze time;
3. one Google Gemini Pro model available through the API at freeze time;
4. one open-weight instruct model in the 8B--14B class;
5. optional open-weight 30B--70B model if compute is available.

Do not hard-code future model names in the paper before runs. Record exact
provider model IDs, access date, API version, prompt, temperature, token limits,
and pricing snapshot. Run three repetitions per configuration; five on the
reduced primary matrix if budget allows.

### Prompt contract

Require structured JSON containing:

- `answerable`: yes/no;
- `p_answerable`: 0--1;
- `answer`;
- atomic claims;
- citation IDs for every claim;
- missing information when abstaining.

The main prompt must explicitly permit abstention but must not reveal the
condition name. A no-abstention-instruction prompt is an ablation.

## Metrics

### Primary

**Paired Behavior Success (PBS)**: proportion of pairs where the model answers
correctly under `full` and abstains under `necessary_removal`.

**Unsupported Persistence Rate (UPR)**: proportion of necessary-removal cases
where the model still answers.

**Counterfactual Abstention Shift (CAS)**:

`P(abstain | necessary removal) - P(abstain | full)`.

### Retrieval

- Recall@k and nDCG@k;
- Complete Evidence Recall: at least one entire minimal evidence set retrieved;
- evidence redundancy and retrieval cost.

Complete Evidence Recall is more important than individual passage recall for
multi-evidence questions.

### Answer, citations, and calibration

- claim precision/recall against atomic gold claims;
- citation precision: emitted citations that support their claims;
- citation completeness: required claims with adequate citations;
- selective accuracy and risk-coverage/AURC;
- Brier score for `p_answerable`;
- ECE only as a secondary, bin-sensitive metric;
- latency, input/output tokens, tool calls, and estimated cost.

### Controls

- irrelevant-removal stability;
- closed-book response to detect likely parametric-answer leakage;
- answer-given evidence-location task;
- shuffled evidence order to test positional sensitivity.

## Evaluation policy

Use deterministic arithmetic/exact checks wherever possible. For open answers:

1. decompose output into atomic claims;
2. run NLI/LLM judging per claim and citation;
3. calibrate the judge on at least 150 human-labelled claim-citation pairs;
4. report judge-human agreement and error analysis;
5. manually audit all primary-model disagreements and at least 10% of outputs.

Never use a single model family to generate questions, create gold labels,
answer them, and judge its own answers.

## Statistical analysis

- Unit of inference: question, not individual generated claim.
- 95% cluster bootstrap confidence intervals, resampling question pairs.
- McNemar test for paired binary behavior.
- Mixed-effects logistic regression for model, condition, retrieval system,
  category, and issuer, with question as a random intercept.
- Holm correction for the preregistered family of model comparisons.
- Report effect sizes and confidence intervals, not only p-values.

Main interaction:

`model × necessary_removal`, contrasted with `model × irrelevant_removal`.

## Computing plan

### API-first recommended setup

- laptop or VM with 8--16 CPU cores;
- 32 GB RAM minimum, 64 GB preferred;
- 100 GB SSD;
- no GPU required for closed-model experiments;
- Docker or Python 3.11 environment.

### Local/open-weight setup

- RTX 4090 or A10G, 24 GB VRAM, for embeddings/reranking and 8B--14B
  quantized generation;
- 64 GB system RAM;
- 200 GB SSD;
- use vLLM for batched inference when serving an open model.

For 32B models, prefer A100 40/80 GB or multi-GPU. A 70B model is optional and
should not become a critical dependency. The strongest scientific use of the
budget is human annotation and repeated paired runs, not the largest local
model.

### Reproducibility

- Python 3.11;
- pinned lock file;
- fixed random seeds;
- immutable corpus manifest with SHA-256 hashes;
- cached retrieval outputs;
- raw model outputs and metadata;
- one command per table/figure;
- no API keys or private benchmark items committed.

## Results plan

Do not populate paper tables before experiments. Required tables:

1. dataset and annotation statistics;
2. answerability/evidence agreement;
3. primary PBS/UPR/CAS by model;
4. retrieval versus oracle decomposition;
5. citation and calibration metrics;
6. ablations;
7. failure taxonomy with manually verified examples;
8. cost/latency.

Publishable negative outcomes include:

- oracle evidence improves accuracy but not abstention;
- contextual retrieval improves passage recall but worsens unsupported
  persistence through additional plausible context;
- models detect total evidence absence but fail under partial evidence;
- citation precision remains high while citation completeness collapses;
- larger models are more accurate but less willing to abstain.

## Eight-week execution plan

| Week | Deliverable |
|---|---|
| 1 | corpus freeze, literature matrix, annotation guide v1 |
| 2 | 20-item double-annotated pilot and go/no-go |
| 3 | 40--60 frozen items and adjudication |
| 4 | retrieval/oracle pipelines and evaluator calibration |
| 5 | primary model runs |
| 6 | repetitions, statistics, ablations, failure analysis |
| 7 | NeurIPS-format draft, figures, complete GitHub reproduction |
| 8 | red-team reviews, reference audit, SSRN/arXiv-ready release |

## Main risks and mitigations

- **Subjective minimality:** narrow to deterministic quantitative/disclosure
  questions and adjudicate.
- **SpaceX memorization:** use multiple issuers, closed-book controls, and report
  issuer-stratified results.
- **Prompt sensitivity:** freeze prompts and include one prompt ablation.
- **LLM judge circularity:** human-calibrate and use different model families.
- **API drift:** record exact IDs/dates and finish core runs in a short window.
- **Scope creep:** contradictions and temporal evidence remain optional.
- **Benchmark leakage:** do not publish hidden test answers before final runs;
  include canary text and corpus hashes where appropriate.

