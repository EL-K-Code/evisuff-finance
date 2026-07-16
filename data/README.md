# Data policy

`example_annotations.jsonl` is a fictional three-item fixture used only to test
the schema and metrics. It is not financial data and it must never be used to
claim benchmark performance.

The released EviSuff-Finance dataset will contain only items that have passed
the annotation protocol in `docs/annotation_guidelines.md`. Each public record
will preserve stable source provenance, including accession number, document
hash, section, passage identifier, and a citation URL where redistribution is
permitted.

Raw filings, working notes, double-annotation disagreements, and held-out test
items belong in `data/raw/` or `data/private/`, which are ignored by Git.
