# Preregistered Experiment v1: Stateful IPO Workflow Composition

**Registration date:** 2026-07-30  
**Status:** frozen before any official preregistered model call  
**Frozen benchmark commit:** `1342e9cf8a85f6cbc4c05d52001820d4e9ead8fb`  
**Frozen reference branch:** `freeze/preregistered-v1-2026-07-30`  
**Repository:** `EL-K-Code/evisuff-finance`

## 1. Purpose

This study tests whether finance-agent capabilities remain valid when they must be composed through a persistent, amendment-sensitive IPO workflow. The benchmark contains four enterprise artifacts—due diligence, valuation, risk, and an ECM committee memo—and two chronological rounds. Round 1 exposes the initial public filing packet (`v1`). Round 2 exposes a later authoritative packet (`v2`) and requires the system to revise all stale facts, calculations, risks, citations, recommendations, and handoffs.

The preregistered study compares three orchestration conditions while holding the model, source packets, prompts, schemas, scoring code, and temperature fixed:

1. `staged_generalist`: one model call per round returns all four artifacts.
2. `staged_isolated`: four independent department calls per round; no upstream department artifacts are shared.
3. `staged_multi_agent`: four department calls per round with the benchmark-defined upstream handoffs.

## 2. Separation from exploratory pilots

All OpenRouter and Gemini runs completed before this registration are exploratory engineering pilots. They are retained for transparency but are excluded from the preregistered estimates, success counts, uncertainty intervals, hypothesis tests, and primary tables.

The official results directory is `results/preregistered_runs/`. A run counts as preregistered only when its metadata contains `preregistration_id = "evisuff-stateful-ipo-v1"`, the frozen benchmark SHA, the planned repetition identifier, and the planned execution-block identifier.

## 3. Frozen experimental objects

### Cases

- `data/ipo_real_cases/reddit_2024/spec.json`
- `data/ipo_real_cases/coreweave_2025/spec.json`
- `data/ipo_real_cases/rubrik_2024/spec.json`

### Conditions

- `staged_generalist`
- `staged_isolated`
- `staged_multi_agent`

### Model and provider

- Provider interface: OpenRouter
- Requested model: `openai/gpt-oss-20b:free`
- Temperature: `0.0`
- Maximum output tokens: `4096`
- API-level retries: `0`
- Hidden benchmark retries: `0`
- OpenRouter provider routing may select a backend serving the same fixed model, but model fallback to a different model is not permitted.

The requested and returned model identifiers, provider response identifier, token counts, latency, response hash, and finish reason must be retained for every successful API response.

### Frozen implementation

The prompts, schemas, state transitions, artifact validators, financial metric definitions, scoring code, and case specifications are those reachable from the frozen commit above. No change to these objects is allowed after the first official call. Any correction discovered later must be reported as a protocol deviation and evaluated in a separately named preregistration version.

## 4. Sample size and call budget

The study contains:

- 3 cases
- 3 orchestration conditions
- 3 new repetitions per case-condition cell
- 27 official workflow runs

Calls per completed workflow:

- generalist: 2 calls
- isolated: 8 calls
- multi-agent: 8 calls

Calls per full 3-case matrix repetition:

`3 × (2 + 8 + 8) = 54 calls`

Total planned calls:

`54 × 3 = 162 calls`

Provider-technical attempts that fail before any model response are not counted toward the planned model-call total, but they must be logged in a separate technical-attempt ledger.

## 5. Counterbalanced execution order

Quota windows are split into six planned blocks. Each block contains at most 36 model calls. Case order and architecture order are rotated to reduce systematic order effects.

### Repetition 1

Architecture order within each case: generalist → isolated → multi-agent.

- Block `r1-a`: Reddit, then CoreWeave — 36 calls
- Block `r1-b`: Rubrik — 18 calls

### Repetition 2

Architecture order within each case: isolated → multi-agent → generalist.

- Block `r2-a`: Rubrik, then Reddit — 36 calls
- Block `r2-b`: CoreWeave — 18 calls

### Repetition 3

Architecture order within each case: multi-agent → generalist → isolated.

- Block `r3-a`: CoreWeave, then Rubrik — 36 calls
- Block `r3-b`: Reddit — 18 calls

A minimum 60-second routing pause is used between conditions and between issuers. No additional model call may be inserted into an official block.

## 6. Hypotheses

### Primary hypothesis

Final enterprise success after the authoritative `v2` update differs across orchestration conditions.

The primary endpoint is **strict final enterprise success**:

- `1` only when the workflow completes and `enterprise_success == true`;
- `0` when the workflow completes with `enterprise_success == false`;
- `0` when a model response is returned but the system produces invalid JSON, violates the frozen schema, or cannot produce a complete workflow state;
- missing only for a verified provider-technical failure before a model response, such as authentication failure, quota exhaustion, transport failure, or model unavailability.

### Secondary hypotheses

1. Perfect coordination can coexist with enterprise failure when agents propagate the same incorrect value.
2. Stateful amendments can create failures after a successful first round or repair failures present in the first round.
3. Architecture effects are case-dependent rather than uniformly ordered.
4. Unit-scale, arithmetic, and downstream handoff failures will account for a meaningful fraction of strict enterprise failures.

## 7. Outcomes

### Primary outcome

- `strict_enterprise_success_v2`

### Secondary outcomes

- native `enterprise_success`
- `update_success`
- `workflow_score`
- `component_score`
- `coordination_score`
- `composition_gap`
- `round1_workflow_score`
- round-1 enterprise success
- stale artifact count after update
- artifact-change indicators
- completion rate
- schema/format failure rate
- input tokens, output tokens, latency, and call count

Workflow scores are summarized only for completed, scoreable workflows. Strict enterprise success includes model-originated format and schema failures as failures.

## 8. Failure and rerun rules

### Provider-technical failure before model output

Examples: HTTP 401/403, verified quota exhaustion, network failure, unavailable endpoint, or the fixed model absent from the authenticated catalog.

Action:

- mark the attempt `non_evaluable_provider_failure`;
- do not assign a zero workflow score;
- preserve the complete error and quota headers;
- rerun the same planned cell in the next available quota window with the same repetition ID and architecture order;
- do not treat the rerun as an additional repetition.

### Model-originated structured-output failure

If the provider returns a model response but the content cannot satisfy the frozen JSON/schema contract, the cell receives `strict_enterprise_success_v2 = 0`. The native workflow score remains missing if the frozen scorer cannot construct artifacts. No replacement call is made.

### Partial workflow completion

If some department calls succeed and a later model call fails for model-originated reasons, the workflow receives strict failure. All completed trajectories are preserved. No replacement call is made.

### Fixed-model unavailability

- If `openai/gpt-oss-20b:free` becomes unavailable before the first official call, this registration is not started. A dated protocol amendment must freeze a replacement model before any official inference.
- If the model becomes unavailable after official runs have begun, execution pauses. Completed runs remain valid for that model. A replacement model is never mixed into the same model block or label.

### Security

API keys remain GitHub repository secrets and must never be printed, committed, included in artifacts, or copied into configuration files.

## 9. Error taxonomy

Every strict failure is assigned one or more preregistered categories:

1. `freshness_or_version`: stale `v1` facts, citations, risks, or recommendation remain after `v2`.
2. `unit_or_scale`: decimal-versus-percentage, shares-versus-millions, currency scale, sign, or related semantic-unit error.
3. `arithmetic`: incorrect calculation despite correct source inputs and units.
4. `unsupported_fact_or_risk`: invented, unsupported, or omitted required fact/risk.
5. `citation_or_provenance`: missing, stale, or unsupported citation/source version.
6. `handoff_inconsistency`: downstream artifact disagrees with an upstream artifact without a valid documented reason.
7. `downstream_override`: memo or downstream department replaces a correct upstream value with an incorrect recalculation.
8. `recommendation`: recommendation contradicts the validated facts, risks, or benchmark rule.
9. `schema_or_format`: model output violates the frozen structured-output contract.
10. `provider_technical`: no evaluable model output due to provider infrastructure.

A second reviewer should independently code failures from blinded trajectory identifiers. Disagreements are adjudicated and both original labels are retained.

## 10. Analysis plan

### Descriptive analysis

For each case, condition, and repetition, report all frozen outcomes and the error taxonomy. Report success counts without hiding model-format failures.

For each condition across the 9 case-repetition units, report:

- strict enterprise successes / 9;
- Wilson 95% confidence interval;
- mean and median workflow score among scoreable workflows;
- completion and schema-failure rates;
- distribution of error categories.

### Paired architecture comparisons

Architecture comparisons use matched case-repetition units. Report paired differences for strict success and workflow score. Because the study contains only three cases and three repetitions, inferential statistics are exploratory and must not be presented as population-level proof. Exact paired tests or bootstrap intervals may be reported only alongside raw paired outcomes and case-stratified results.

### Stateful transitions

Classify each completed run as one of:

- success → success
- success → failure
- failure → success
- failure → failure

Round-1 and round-2 outcomes must be shown together.

### Missingness

Provider-technical missingness is reported separately by block, date, and cause. No imputation is performed. Model-originated schema failures are not missing; they are strict failures.

## 11. Stopping and exclusion rules

Execution stops after the 27 planned workflow runs are evaluable or when the fixed model is permanently unavailable. No early stopping based on favorable or unfavorable scores is allowed.

A run is excluded only when:

- its frozen commit SHA is incorrect;
- its case, condition, repetition, or block was not preregistered;
- a provider-technical failure occurred before model output;
- secrets or private gold labels were exposed to the model.

All exclusions and deviations remain in an audit ledger.

## 12. Reporting boundary

The preregistered study evaluates one fixed model on three IPO cases. It does not establish a universal ranking of generalist, isolated, and multi-agent systems. Claims must remain limited to the observed model, cases, schemas, and workflow. A second-model study will be registered separately after this study is complete.
