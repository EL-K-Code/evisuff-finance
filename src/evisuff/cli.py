from __future__ import annotations

import argparse
import json
from pathlib import Path

from .interventions import build_conditions
from .io import read_items, read_jsonl, write_json, write_jsonl
from .metrics import compute_metrics, paired_bootstrap
from .predictions import validate_prediction_records


def _synthetic_predictions(items_path: Path) -> list[dict]:
    rows: list[dict] = []
    for item in read_items(items_path):
        for condition in build_conditions(item):
            for model in ("evidence_sensitive", "relevance_only"):
                if model == "evidence_sensitive":
                    abstained = not condition.expected_answerable
                    correct = condition.expected_answerable
                    p_answerable = 0.93 if condition.expected_answerable else 0.12
                else:
                    abstained = False
                    correct = condition.expected_answerable
                    p_answerable = 0.88 if condition.expected_answerable else 0.79
                evidence_count = len(condition.evidence)
                rows.append(
                    {
                        "item_id": item.item_id,
                        "condition": condition.condition,
                        "model": model,
                        "run_id": "synthetic-0",
                        "expected_answerable": condition.expected_answerable,
                        "correct": correct,
                        "abstained": abstained,
                        "p_answerable": p_answerable,
                        "citations_total": 0 if abstained else min(2, evidence_count),
                        "citations_supported": 0 if abstained else min(2, evidence_count),
                        "gold_claims_total": len(item.atomic_claims),
                        "gold_claims_cited": 0 if abstained else len(item.atomic_claims),
                        "complete_evidence_retrieved": condition.expected_answerable,
                    }
                )
    return rows


def command_validate(path: Path) -> int:
    errors: list[str] = []
    items = read_items(path)
    for item in items:
        errors.extend(item.validate())
        if not item.validate():
            build_conditions(item)
    print(json.dumps({"items": len(items), "errors": errors}, indent=2))
    return int(bool(errors))


def command_build_conditions(path: Path, output: Path) -> int:
    """Materialize paired contexts from validated benchmark annotations."""

    items = read_items(path)
    errors: list[str] = []
    conditions: list[dict] = []
    for item in items:
        item_errors = item.validate()
        errors.extend(item_errors)
        if not item_errors:
            conditions.extend(condition.to_dict() for condition in build_conditions(item))
    if errors:
        print(json.dumps({"items": len(items), "errors": errors}, indent=2))
        return 1
    write_jsonl(output, conditions)
    print(
        json.dumps(
            {
                "items": len(items),
                "conditions": len(conditions),
                "output": str(output),
            },
            indent=2,
        )
    )
    return 0


def command_score(predictions_path: Path, output: Path, samples: int, seed: int) -> int:
    """Score a validated prediction manifest, grouped by model identifier."""

    rows = read_jsonl(predictions_path)
    errors = validate_prediction_records(rows)
    if errors:
        print(json.dumps({"records": len(rows), "errors": errors}, indent=2))
        return 1

    by_model: dict[str, dict] = {}
    for model in sorted({str(row["model"]) for row in rows}):
        model_rows = [row for row in rows if str(row["model"]) == model]
        item_ids = {str(row["item_id"]) for row in model_rows}
        report: dict[str, object] = {"metrics": compute_metrics(model_rows)}
        if len(item_ids) >= 2:
            report["paired_behavior_bootstrap"] = paired_bootstrap(
                model_rows, samples=samples, seed=seed
            )
        else:
            report["paired_behavior_bootstrap"] = None
        by_model[model] = report

    result = {
        "result_type": "model_prediction_metrics_require_external_answer_and_citation_validation",
        "source": str(predictions_path),
        "models": by_model,
    }
    write_json(output, result)
    print(json.dumps(result, indent=2))
    return 0


def command_smoke(output: Path) -> int:
    root = Path(__file__).resolve().parents[2]
    items_path = root / "data" / "example_annotations.jsonl"
    rows = _synthetic_predictions(items_path)
    by_model = {}
    for model in sorted({x["model"] for x in rows}):
        model_rows = [x for x in rows if x["model"] == model]
        by_model[model] = {
            "metrics": compute_metrics(model_rows),
            "paired_behavior_bootstrap": paired_bootstrap(
                model_rows, samples=500, seed=17
            ),
        }
    report = {
        "result_type": "synthetic_software_smoke_test_not_research_results",
        "models": by_model,
    }
    write_json(output, report)
    print(json.dumps(report, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate")
    validate.add_argument("path", type=Path)
    build = subparsers.add_parser("build-conditions")
    build.add_argument("path", type=Path)
    build.add_argument("--output", type=Path, required=True)
    smoke = subparsers.add_parser("smoke")
    smoke.add_argument("--output", type=Path, default=Path("results/smoke_metrics.json"))
    score = subparsers.add_parser("score")
    score.add_argument("predictions", type=Path)
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--bootstrap-samples", type=int, default=2000)
    score.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    if args.command == "validate":
        raise SystemExit(command_validate(args.path))
    if args.command == "build-conditions":
        raise SystemExit(command_build_conditions(args.path, args.output))
    if args.command == "score":
        raise SystemExit(
            command_score(
                args.predictions,
                args.output,
                args.bootstrap_samples,
                args.seed,
            )
        )
    raise SystemExit(command_smoke(args.output))


if __name__ == "__main__":
    main()
