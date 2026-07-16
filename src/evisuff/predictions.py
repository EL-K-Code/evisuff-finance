"""Validation helpers for model prediction manifests.

The benchmark deliberately separates raw model generation from scoring. A model
runner can use any provider or local runtime, but it must emit a JSONL manifest
with the fields validated here before its results are scored.
"""

from __future__ import annotations

from typing import Any, Iterable


KNOWN_CONDITIONS = {
    "full": True,
    "gold_only": True,
    "necessary_removal": False,
    "irrelevant_removal": True,
}

REQUIRED_FIELDS = {
    "item_id",
    "condition",
    "model",
    "expected_answerable",
    "correct",
    "abstained",
    "p_answerable",
}


def validate_prediction_records(records: Iterable[dict[str, Any]]) -> list[str]:
    """Return schema and paired-condition errors for prediction rows.

    This function validates only the run manifest. It cannot establish that a
    model answer or citation was judged correctly; that requires the human or
    calibrated evaluation process described in the research protocol.
    """

    errors: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    for index, row in enumerate(records, start=1):
        prefix = f"row {index}"
        missing = sorted(REQUIRED_FIELDS - set(row))
        if missing:
            errors.append(f"{prefix}: missing required fields {missing}")
            continue

        if not isinstance(row["item_id"], str) or not row["item_id"].strip():
            errors.append(f"{prefix}: item_id must be a non-empty string")
        if not isinstance(row["model"], str) or not row["model"].strip():
            errors.append(f"{prefix}: model must be a non-empty string")
        condition = row["condition"]
        if condition not in KNOWN_CONDITIONS:
            errors.append(
                f"{prefix}: condition must be one of {sorted(KNOWN_CONDITIONS)}"
            )
        else:
            expected = KNOWN_CONDITIONS[condition]
            if row["expected_answerable"] is not expected:
                errors.append(
                    f"{prefix}: expected_answerable for {condition} must be {expected}"
                )

        for field in ("expected_answerable", "correct", "abstained"):
            if not isinstance(row[field], bool):
                errors.append(f"{prefix}: {field} must be boolean")

        try:
            probability = float(row["p_answerable"])
        except (TypeError, ValueError):
            errors.append(f"{prefix}: p_answerable must be numeric")
        else:
            if not 0.0 <= probability <= 1.0:
                errors.append(f"{prefix}: p_answerable must be in [0, 1]")

        run_id = str(row.get("run_id", "0"))
        key = (str(row["item_id"]), str(condition), str(row["model"]), run_id)
        if key in seen:
            errors.append(f"{prefix}: duplicate item/condition/model/run_id manifest row")
        seen.add(key)

    return errors
