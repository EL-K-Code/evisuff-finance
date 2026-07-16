# Proposed paper outline

## Title

When Relevant Evidence Is Not Enough: Counterfactual Evidence-Sufficiency
Evaluation for Long-Document Financial Agents

## Abstract structure

1. Agents increasingly analyze long, high-stakes filings.
2. Existing benchmarks conflate retrieval, sufficiency, and synthesis.
3. Introduce paired interventions built from minimal sufficient evidence sets.
4. Describe dataset size, filings, models, and primary metrics.
5. State only executed results with confidence intervals.
6. State the general implication for reliable research agents.

## 1. Introduction

- Practical failure: relevant passages can still be insufficient.
- Why answer-only rubrics cannot identify this behavior.
- Core intervention: break every minimal evidence path.
- Three contributions, without overclaiming firstness.

## 2. Related work

- financial QA and financial agents;
- RAG retrieval and contextual retrieval;
- sufficient context, abstention, and calibration;
- citation attribution and completeness;
- conflicting and temporal evidence;
- deep-research-agent evaluation.

## 3. Task definition

- atomic claims;
- minimal sufficient evidence sets;
- hitting-set removal;
- full, gold-only, necessary-removal, and control conditions;
- paired behavior metrics.

## 4. EviSuff-Finance dataset

- source filings and licensing;
- question selection;
- annotation and adjudication;
- negative disclosure cases;
- quality and agreement;
- contamination controls.

## 5. Experimental setup

- retrieval systems;
- models and exact versions;
- prompts and repetitions;
- deterministic and model-based evaluators;
- statistical analysis;
- compute and cost.

## 6. Results

- primary paired behavior;
- retrieval versus gold-evidence oracle;
- relevance versus sufficiency control;
- citation completeness;
- calibration and risk-coverage;
- cost and latency.

## 7. Analysis

- failure taxonomy;
- quantitative versus disclosure questions;
- issuer and model-family differences;
- prompt and top-k sensitivity;
- representative verified cases.

## 8. Limitations

- benchmark size and finance specialization;
- subjectivity of evidence minimality;
- API drift;
- residual parametric knowledge;
- limited causal claims outside controlled context interventions.

## 9. Conclusion

Keep the conclusion narrow: whether agents track necessary evidence, not whether
they are generally reliable financial analysts.

