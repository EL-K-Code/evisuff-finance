from __future__ import annotations

import math
import random
from collections import defaultdict
from statistics import mean
from typing import Iterable


def _safe_div(numerator: float, denominator: float) -> float | None:
    return numerator / denominator if denominator else None


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None or precision + recall == 0:
        return None
    return 2 * precision * recall / (precision + recall)


def compute_metrics(records: Iterable[dict]) -> dict[str, float | int | None]:
    rows = list(records)
    if not rows:
        raise ValueError("at least one prediction record is required")

    answered = [r for r in rows if not r["abstained"]]
    answerable = [r for r in rows if r["expected_answerable"]]
    unanswerable = [r for r in rows if not r["expected_answerable"]]
    predicted_abstain = [r for r in rows if r["abstained"]]
    correct_abstentions = [
        r for r in rows if r["abstained"] and not r["expected_answerable"]
    ]

    abstention_precision = _safe_div(len(correct_abstentions), len(predicted_abstain))
    abstention_recall = _safe_div(len(correct_abstentions), len(unanswerable))

    grouped: dict[tuple[str, str, str], dict[str, dict]] = defaultdict(dict)
    for row in rows:
        key = (row["model"], str(row.get("run_id", "0")), row["item_id"])
        grouped[key][row["condition"]] = row

    paired = []
    for conditions in grouped.values():
        if "full" in conditions and "necessary_removal" in conditions:
            full = conditions["full"]
            removed = conditions["necessary_removal"]
            paired.append(
                {
                    "paired_success": float(
                        full["correct"]
                        and not full["abstained"]
                        and removed["abstained"]
                    ),
                    "unsupported_persistence": float(not removed["abstained"]),
                    "abstention_shift": float(removed["abstained"])
                    - float(full["abstained"]),
                    "answerability_probability_drop": float(full["p_answerable"])
                    - float(removed["p_answerable"]),
                }
            )

    control_pairs = []
    for conditions in grouped.values():
        if "full" in conditions and "irrelevant_removal" in conditions:
            full = conditions["full"]
            control = conditions["irrelevant_removal"]
            control_pairs.append(
                float(
                    full["correct"]
                    and control["correct"]
                    and full["abstained"] == control["abstained"]
                )
            )

    citation_rows = [
        r for r in rows if r["expected_answerable"] and not r["abstained"]
    ]
    citation_total = sum(int(r.get("citations_total", 0)) for r in citation_rows)
    citations_supported = sum(
        int(r.get("citations_supported", 0)) for r in citation_rows
    )
    gold_claims_total = sum(
        int(r.get("gold_claims_total", 0)) for r in citation_rows
    )
    gold_claims_cited = sum(
        int(r.get("gold_claims_cited", 0)) for r in citation_rows
    )
    retrieval_rows = [
        r
        for r in rows
        if r["expected_answerable"] and "complete_evidence_retrieved" in r
    ]

    brier = mean(
        (float(r["p_answerable"]) - float(r["expected_answerable"])) ** 2
        for r in rows
    )

    return {
        "n_predictions": len(rows),
        "n_pairs": len(paired),
        "answer_accuracy_on_answerable": (
            mean(float(r["correct"] and not r["abstained"]) for r in answerable)
            if answerable
            else None
        ),
        "behavior_accuracy": mean(
            float(
                (r["expected_answerable"] and r["correct"] and not r["abstained"])
                or (not r["expected_answerable"] and r["abstained"])
            )
            for r in rows
        ),
        "selective_accuracy": (
            mean(float(r["correct"]) for r in answered) if answered else None
        ),
        "coverage": len(answered) / len(rows),
        "abstention_precision": abstention_precision,
        "abstention_recall": abstention_recall,
        "abstention_f1": _f1(abstention_precision, abstention_recall),
        "brier_answerability": brier,
        "paired_behavior_success": (
            mean(x["paired_success"] for x in paired) if paired else None
        ),
        "unsupported_persistence_rate": (
            mean(x["unsupported_persistence"] for x in paired) if paired else None
        ),
        "counterfactual_abstention_shift": (
            mean(x["abstention_shift"] for x in paired) if paired else None
        ),
        "answerability_probability_drop": (
            mean(x["answerability_probability_drop"] for x in paired)
            if paired
            else None
        ),
        "irrelevant_removal_stability": mean(control_pairs) if control_pairs else None,
        "citation_precision": _safe_div(citations_supported, citation_total),
        "citation_completeness": _safe_div(gold_claims_cited, gold_claims_total),
        "complete_evidence_recall": (
            mean(float(r["complete_evidence_retrieved"]) for r in retrieval_rows)
            if retrieval_rows
            else None
        ),
    }


def paired_bootstrap(
    records: Iterable[dict],
    metric: str = "paired_behavior_success",
    samples: int = 2000,
    seed: int = 17,
) -> dict[str, float]:
    """Cluster bootstrap over question-level pairs.

    Rows are resampled by item ID, preserving all conditions for each sampled
    item. This avoids treating paired interventions as independent examples.
    """

    rows = list(records)
    by_item: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_item[row["item_id"]].append(row)
    item_ids = sorted(by_item)
    if len(item_ids) < 2:
        raise ValueError("paired bootstrap requires at least two items")

    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(samples):
        sampled_rows: list[dict] = []
        for draw_index in range(len(item_ids)):
            selected = rng.choice(item_ids)
            for row in by_item[selected]:
                copy = dict(row)
                copy["item_id"] = f"{selected}__bootstrap_{draw_index}"
                sampled_rows.append(copy)
        value = compute_metrics(sampled_rows)[metric]
        if value is not None and not math.isnan(float(value)):
            values.append(float(value))
    values.sort()
    lower = values[int(0.025 * (len(values) - 1))]
    upper = values[int(0.975 * (len(values) - 1))]
    point = compute_metrics(rows)[metric]
    return {"estimate": float(point), "ci_lower": lower, "ci_upper": upper}
