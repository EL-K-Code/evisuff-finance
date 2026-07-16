import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from evisuff.cli import command_build_conditions, command_score
from evisuff.interventions import (
    build_conditions,
    complete_evidence_retrieved,
    minimal_hitting_set,
)
from evisuff.io import read_items
from evisuff.metrics import compute_metrics, paired_bootstrap
from evisuff.io import write_jsonl
from evisuff.predictions import validate_prediction_records


DATA = Path(__file__).parents[1] / "data" / "example_annotations.jsonl"


class EviSuffTests(unittest.TestCase):
    def test_example_annotations_validate(self):
        items = read_items(DATA)
        self.assertEqual(len(items), 3)
        self.assertTrue(all(not item.validate() for item in items))

    def test_hitting_set_breaks_alternative_minimal_sets(self):
        result = minimal_hitting_set((("e1", "e2"), ("e3",)))
        self.assertEqual(len(result), 2)
        self.assertTrue(set(result) & {"e1", "e2"})
        self.assertIn("e3", result)

    def test_intervention_answerability(self):
        item = read_items(DATA)[0]
        conditions = {x.condition: x for x in build_conditions(item)}
        self.assertTrue(conditions["full"].expected_answerable)
        self.assertFalse(conditions["necessary_removal"].expected_answerable)
        self.assertIn(
            set(conditions["necessary_removal"].removed_evidence_ids),
            ({"e1"}, {"e2"}),
        )
        self.assertTrue(conditions["irrelevant_removal"].expected_answerable)

    def test_complete_evidence_retrieval_requires_whole_set(self):
        minimal_sets = (("e1", "e2"), ("e3",))
        self.assertFalse(complete_evidence_retrieved({"e1"}, minimal_sets))
        self.assertTrue(complete_evidence_retrieved({"e1", "e2"}, minimal_sets))
        self.assertTrue(complete_evidence_retrieved({"e3"}, minimal_sets))

    def test_paired_metrics(self):
        rows = []
        for item_id in ("a", "b", "c"):
            rows.extend(
                [
                    {
                        "item_id": item_id,
                        "condition": "full",
                        "model": "m",
                        "run_id": "0",
                        "expected_answerable": True,
                        "correct": True,
                        "abstained": False,
                        "p_answerable": 0.9,
                    },
                    {
                        "item_id": item_id,
                        "condition": "necessary_removal",
                        "model": "m",
                        "run_id": "0",
                        "expected_answerable": False,
                        "correct": False,
                        "abstained": True,
                        "p_answerable": 0.1,
                    },
                ]
            )
        metrics = compute_metrics(rows)
        self.assertEqual(metrics["paired_behavior_success"], 1.0)
        self.assertEqual(metrics["unsupported_persistence_rate"], 0.0)
        self.assertEqual(metrics["counterfactual_abstention_shift"], 1.0)
        ci = paired_bootstrap(rows, samples=50)
        self.assertEqual(ci["estimate"], 1.0)
        self.assertEqual(ci["ci_lower"], 1.0)

    def test_empty_predictions_rejected(self):
        with self.assertRaises(ValueError):
            compute_metrics([])

    def test_prediction_manifest_validation(self):
        errors = validate_prediction_records(
            [
                {
                    "item_id": "item",
                    "condition": "necessary_removal",
                    "model": "model",
                    "expected_answerable": True,
                    "correct": False,
                    "abstained": False,
                    "p_answerable": 1.2,
                }
            ]
        )
        self.assertTrue(any("expected_answerable" in error for error in errors))
        self.assertTrue(any("p_answerable" in error for error in errors))

    def test_build_conditions_and_score_cli_commands(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            conditions_path = root / "conditions.jsonl"
            self.assertEqual(command_build_conditions(DATA, conditions_path), 0)
            self.assertTrue(conditions_path.exists())

            rows = []
            for item_id in ("a", "b"):
                rows.extend(
                    [
                        {
                            "item_id": item_id,
                            "condition": "full",
                            "model": "model-a",
                            "run_id": "0",
                            "expected_answerable": True,
                            "correct": True,
                            "abstained": False,
                            "p_answerable": 0.9,
                        },
                        {
                            "item_id": item_id,
                            "condition": "necessary_removal",
                            "model": "model-a",
                            "run_id": "0",
                            "expected_answerable": False,
                            "correct": False,
                            "abstained": True,
                            "p_answerable": 0.1,
                        },
                    ]
                )
            predictions_path = root / "predictions.jsonl"
            output_path = root / "metrics.json"
            write_jsonl(predictions_path, rows)
            self.assertEqual(command_score(predictions_path, output_path, 50, 17), 0)
            self.assertTrue(output_path.exists())


if __name__ == "__main__":
    unittest.main()
