# Benchmark Alignment v2: From Finance Subskills to Stateful IPO Workflow Reliability

**Status:** design specification; no v2 official inference has started  
**Supersedes:** `evisuff-stateful-ipo-v1` before official inference  
**Working title:** **Do Finance Agents Compose? From FinAR-Bench, IPO Finance Agent, and BigFinanceBench to Stateful IPO Workflows**

## 1. Precise positioning

EviSuff-Finance does not claim to replace existing finance benchmarks. It tests a downstream validity question that those benchmarks leave open:

> **Do scores obtained on recognized finance-agent tasks predict whether the same model can maintain a correct, auditable, multi-artifact workflow after an authoritative filing amendment?**

The contribution is a cross-benchmark composition study rather than an isolated new leaderboard.

| Reference surface | Unit of evaluation | Main capability measured | Public evaluation object | Remaining gap addressed by EviSuff v2 |
|---|---|---|---|---|
| FinAR-Bench | financial-statement task | information extraction, indicator computation, logical reasoning | 100 SSE companies; 13 tasks per company: 6 fact, 6 indicator, 1 reasoning | does separately measured competence survive composition across departments and time? |
| IPO Finance Agent | IPO due-diligence question | retrieval and reasoning over long S-1 / registration documents | 1,000 questions, including 70 public SpaceX questions, with rubric-based evaluation | can due-diligence evidence be converted into mutually consistent valuation, risk, and committee artifacts? |
| BigFinanceBench | open-ended analyst workflow | auditable derivation: source, definition, assumptions, adjustments, calculation | 928 expert-authored items and a 50-item public subset with weighted rubrics and traces | does a good single-task derivation remain valid when several outputs must be updated and handed off? |
| EviSuff Stateful IPO Workflow | two-round enterprise workflow | four-artifact composition under `v1 → v2` amendments | Reddit, Rubrik, CoreWeave; diligence, valuation, risk, ECM memo; three orchestration designs | measures stateful composition, handoff validity, amendment resilience, and strict enterprise success |

## 2. What is new

The V2 study contributes four tests that are not supplied jointly by the reference benchmarks:

1. **Cross-level predictive validity.** It measures whether atomic and single-task finance scores predict enterprise-workflow success for the same model.
2. **Stateful amendment resilience.** It evaluates the same workflow before and after a later authoritative filing changes the available evidence.
3. **Correctness-versus-coordination separation.** It distinguishes internally consistent handoffs from factually and numerically valid handoffs.
4. **Architecture-conditioned composition.** It compares a generalist, isolated departments, and a handoff-enabled multi-agent workflow while keeping the model and evidence fixed.

The main falsifiable claim is not “multi-agent is worse.” It is:

> **High finance-benchmark performance is not sufficient for reliable stateful workflow composition, and the size and type of the loss depend on both architecture and case.**

## 3. Direct comparison design — the “PSG / Bayern / Real” table

Every evaluated model must receive a score on four surfaces:

| Surface | V2 score |
|---|---|
| FinAR-Bench matched subset | extraction F1, indicator numerical accuracy, reasoning score |
| IPO Finance Agent public subset | rubric accuracy and completion rate |
| BigFinanceBench public subset | rubric score and final-answer accuracy |
| EviSuff stateful workflow | strict enterprise success, workflow score, amendment transition, coordination validity |

The paper’s main model table must display these scores side by side. Narrative similarity between benchmarks is not sufficient.

## 4. Bridge pilot: frozen evaluation surfaces

The bridge pilot validates the comparison harness. It is exploratory and excluded from the later confirmatory V2 estimates.

### 4.1 FinAR-Bench — 12 official test tasks

Select exactly 12 items from the official `test.txt` split:

- 4 `fact` tasks;
- 4 `indicator` tasks;
- 4 `reasoning` tasks.

Selection procedure:

1. sort companies by `company_code`;
2. sort each company’s instances by `task_id`;
3. use deterministic seed `20260730`;
4. sample without replacement within task type;
5. commit the exact 12 task IDs before any bridge inference.

This procedure must be materialized into a checked-in item manifest. No task may be replaced after a model response is observed.

### 4.2 IPO Finance Agent — 12 public SpaceX questions

Use the one-based question positions below from `data/public_spacex_70.txt` in the official `benstaf/ipoagent` repository:

`[1, 2, 5, 9, 12, 16, 18, 19, 25, 29, 35, 46]`

Coverage:

- quantitative growth and ARPU;
- segment accounting and capital intensity;
- operating KPI definitions;
- IPO amendment missingness;
- non-GAAP construction;
- execution risk;
- segment FCF and valuation;
- concentration risk;
- offering decisions blocked before price-range disclosure.

The official question text and rubric must be copied by script from the pinned upstream revision; manual paraphrasing is not allowed.

### 4.3 BigFinanceBench — 12 public item IDs

Use these exact IDs from the official 50-item public subset:

- `bf-0a8c20169a`
- `bf-0e2b33b21b`
- `bf-14e00db503`
- `bf-20474b5540`
- `bf-2c01534176`
- `bf-36d4a10aa8`
- `bf-37f81aef9b`
- `bf-39bacf8580`
- `bf-50f29af2ed`
- `bf-51844d71db`
- `bf-55f33faa82`
- `bf-5b4cd39939`

These items cover retrieval, accounting definitions, adjustments, leverage, valuation, capital allocation, restructuring, MOIC/IRR, and multi-step calculations. The official harness, reference answers, point-weighted rubrics, and tool surface must be preserved.

### 4.4 EviSuff — one complete stateful case

Use Reddit 2024 under all three conditions:

- `staged_generalist` — 2 model calls;
- `staged_isolated` — 8 model calls;
- `staged_multi_agent` — 8 model calls.

This produces the first direct benchmark-to-workflow comparison without spending the full three-case budget.

## 5. Model panel

The bridge pilot requires at least:

1. **one OpenAI frontier anchor** with a publicly reported score on BigFinanceBench; and
2. **one lower-cost or open-weight control** that can be run across all four surfaces.

Candidate anchor order:

1. GPT-5.6 Terra or Sol, using the exact authenticated API identifier available at execution time;
2. GPT-5.5, which also has public FinanceAgent and BigFinanceBench reference scores;
3. another frontier model only through a dated protocol amendment.

The existing `openai/gpt-oss-20b:free` trajectories remain an engineering control, not the sole headline model.

Before inference, freeze:

- requested and returned model identifiers;
- API provider and date;
- temperature and output limits;
- tool availability per benchmark;
- judge models;
- prices and call budget.

## 6. Call accounting

Per evaluated model, the bridge pilot contains:

- 12 FinAR responses;
- 12 IPO Finance Agent responses;
- 12 BigFinanceBench responses;
- 18 EviSuff workflow responses.

Total evaluated-model responses per model: **54**.

Judge and grading calls are budgeted and reported separately. They must never be silently mixed with evaluated-model call counts.

## 7. Metrics

All scores are converted to `[0, 1]` only for cross-surface summaries; original benchmark metrics are also reported unchanged.

### External competence score

`reference_competence = mean(FinAR extraction, FinAR indicator, FinAR reasoning, IPO rubric, BFB rubric)`

The five components must also remain visible; the mean is not a replacement for the detailed scores.

### Workflow outcomes

- `strict_enterprise_success_v2`;
- `workflow_score_v1`;
- `workflow_score_v2`;
- `coordination_score_v2`;
- `component_score_v2`;
- `composition_gap`;
- model-format and completion rates.

### New cross-benchmark measures

- `benchmark_to_workflow_gap = reference_competence - workflow_score_v2`
- `composition_retention = workflow_score_v2 / reference_competence`, reported only when the denominator is positive
- `amendment_delta = workflow_score_v2 - workflow_score_v1`
- `coordination_validity_gap = coordination_score_v2 - component_score_v2`

A positive coordination-validity gap indicates that internal consistency exceeds factual/component correctness. It is descriptive and must not be interpreted as causal evidence.

## 8. Headline analyses

1. **Scoreboard:** same-model scores on FinAR, IPO Finance Agent, BigFinanceBench, and EviSuff.
2. **Predictive validity:** association between reference competence and workflow outcomes.
3. **Static-to-stateful transitions:** success→success, success→failure, failure→success, failure→failure.
4. **Architecture comparison:** generalist versus isolated versus multi-agent on the same case and model.
5. **Error localization:** retrieval, definition, arithmetic, unit/scale, stale evidence, handoff inconsistency, and downstream override.
6. **Published-reference comparison:** place fresh public-subset scores beside the scores reported by benchmark authors and OpenAI, without treating different harnesses as directly interchangeable.

## 9. Claim boundary

The bridge pilot will establish harness feasibility and produce an interpretable comparison table. It will not support population-level claims from one IPO case or one run. A confirmatory V2 protocol will be registered only after the bridge harness, exact item manifests, grading, and cost controls are validated.

## 10. Primary sources

- FinAR-Bench paper: `https://arxiv.org/abs/2506.07315`
- FinAR-Bench repository: `https://github.com/SAIFS-AIHub/FinAR-Bench`
- FinAR-Bench dataset: `https://huggingface.co/datasets/SAIFS-AiHub/FinAR-Bench`
- IPO Finance Agent paper: `https://arxiv.org/abs/2606.23032`
- IPO Finance Agent repository: `https://github.com/benstaf/ipoagent`
- BigFinanceBench paper: `https://arxiv.org/abs/2606.03829`
- BigFinanceBench repository: `https://github.com/Rogo-Technologies/big-finance-benchmark`
- BigFinanceBench public dataset: `https://huggingface.co/datasets/RogoAI/big-finance-benchmark`
- OpenAI GPT-5.6 benchmark report: `https://openai.com/index/gpt-5-6/`
