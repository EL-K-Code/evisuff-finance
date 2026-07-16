# EviSuff-Finance annotation guidelines

## Objective

For each question, record the smallest sets of passages that are sufficient to
support every required atomic claim. The goal is not merely to locate relevant
text: the annotation must make it possible to prove that a counterfactual
removal makes the question unanswerable from the permitted corpus.

## Unit of annotation

One record contains:

1. a question and a bounded allowed corpus;
2. a reference answer decomposed into atomic claims;
3. evidence units with stable IDs;
4. one or more minimal sufficient evidence sets (MSES);
5. optional distractor units;
6. answerability and temporal-cutoff metadata;
7. annotator, reviewer, and adjudication metadata.

An evidence unit should be the smallest stable passage that can be retrieved
without losing its meaning. In a filing HTML document, use an accession number,
section name, DOM or paragraph anchor, and character offsets. For a table, keep
table identifier, row/column labels, and a serialized cell range.

## Minimal sufficient evidence sets

An MSES is sufficient if it supports all claims required by the question. It is
minimal if deleting any of its evidence units makes it insufficient. Record all
distinct complete evidence paths that are reasonably available in the permitted
corpus. Do not declare an item unanswerable by removing one passage if an
alternative complete path remains.

For a question with MSES family `M`, the implementation removes a minimum
hitting set: a smallest set of units that intersects every member of `M`.

## Annotation workflow

1. Read the question and freeze the allowed documents and any temporal cutoff.
2. Write the reference answer as atomic, independently checkable claims.
3. Locate candidate passages and verify them against the source filing.
4. Build all complete MSES paths and test minimality manually.
5. Mark at least one clearly irrelevant but topically plausible distractor when
   possible.
6. Create the `necessary_removal` condition and verify independently that no
   MSES remains intact.
7. A second annotator reviews the item without seeing the first annotation.
8. Adjudicate disagreements, preserve the reason, and freeze the record.

## Disclosure-of-absence items

Claims such as "the filing does not disclose standalone revenue" require a
bounded search scope. Annotators must state which sections, tables, and notes
were searched, how synonyms were handled, and why the conclusion is valid only
within that scope. Report these items separately from affirmative-evidence
questions.

## Quality gates

- Double annotate at least 25% of the full benchmark and 100% of the MVP.
- Report Cohen's kappa for answerability.
- Report evidence-unit precision, recall, and F1 rather than applying kappa to
  free-form spans.
- Require two-person verification for every necessary-removal pair.
- Exclude items with unresolved ambiguity or subjective market judgment.
