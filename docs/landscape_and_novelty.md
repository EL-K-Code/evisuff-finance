# Landscape and novelty boundary

## Anchors

- **IPO Finance Agent** extends Finance Agent v2 toward IPO due diligence on long S-1 filings, contextual retrieval, and question-level rubric evaluation: https://arxiv.org/abs/2606.23032
- **SpreadsheetBench 2** evaluates end-to-end spreadsheet generation, debugging, and visualization on realistic multi-sheet workflows: https://arxiv.org/abs/2606.29955
- **BankerToolBench** evaluates end-to-end investment-banking tasks with data rooms and multi-file deliverables: https://arxiv.org/abs/2604.11304
- **BenchFlow** frames agent evaluation around stateful environments with files, tools, verifiers, traces, replay, and multi-agent scenes: https://www.benchflow.ai/about

## What this project must not claim

It must not claim to be:

- the first realistic finance-agent environment;
- the first end-to-end banking benchmark;
- the first spreadsheet workflow benchmark;
- the first multi-agent enterprise simulation.

## Defensible contribution target

The target is a **compositional validity study**:

> Do capabilities measured separately by finance benchmarks remain predictive when they must be composed through departmental handoffs in one persistent workflow?

The key design features are:

1. paired isolated and workflow versions of the same underlying financial content;
2. explicit departmental handoffs;
3. versioned authoritative evidence;
4. cross-artifact consistency checks;
5. local scores separated from enterprise success;
6. model and harness rank-transfer analysis.

## Why the verifier work remains useful

A realistic workflow can still be mismeasured by weak verifiers. The existing verifier stress-testing work therefore becomes infrastructure for checking numerical correctness, dynamic spreadsheet behavior, provenance, and cross-artifact consistency inside the environment.

## Frontier-lab relevance

The output should tell frontier labs whether:

- benchmark winners remain winners under workflow composition;
- single-agent or multi-agent scaffolds coordinate better;
- specialization creates handoff failures;
- current finance benchmarks overstate operational readiness;
- new trajectories are useful for post-training on coordination and recovery.
