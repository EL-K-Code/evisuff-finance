from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "configs" / "benchmark_bridge_v2.json"
LOCK_PATH = ROOT / "configs" / "bridge_v2_upstream_lock.json"
SUPERSESSION_PATH = ROOT / "docs" / "preregistered_v1_supersession.md"


class BenchmarkBridgeV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        cls.supersession = SUPERSESSION_PATH.read_text(encoding="utf-8")

    def test_v1_is_superseded_before_official_inference(self) -> None:
        self.assertEqual(self.design["supersedes"], "evisuff-stateful-ipo-v1")
        self.assertFalse(self.design["official_v2_inference_started"])
        self.assertIn("superseded_before_official_inference", self.supersession)
        self.assertIn("Official v1 model calls completed:** `0`", self.supersession)
        self.assertIn("Official v1 workflow runs completed:** `0`", self.supersession)

    def test_four_comparison_surfaces_are_present(self) -> None:
        surfaces = self.design["reference_surfaces"]
        self.assertEqual(
            set(surfaces),
            {
                "finar_bench",
                "ipo_finance_agent",
                "big_finance_bench",
                "evisuff_stateful_ipo",
            },
        )

    def test_bridge_item_counts_and_evaluated_model_budget(self) -> None:
        surfaces = self.design["reference_surfaces"]
        self.assertEqual(surfaces["finar_bench"]["sample_size"], 12)
        self.assertEqual(sum(surfaces["finar_bench"]["task_type_counts"].values()), 12)
        self.assertEqual(surfaces["ipo_finance_agent"]["sample_size"], 12)
        self.assertEqual(
            len(surfaces["ipo_finance_agent"]["one_based_question_positions"]), 12
        )
        self.assertEqual(surfaces["big_finance_bench"]["sample_size"], 12)
        self.assertEqual(len(surfaces["big_finance_bench"]["item_ids"]), 12)
        self.assertEqual(len(set(surfaces["big_finance_bench"]["item_ids"])), 12)
        self.assertEqual(surfaces["evisuff_stateful_ipo"]["evaluated_model_calls"], 18)

        budget = self.design["evaluated_model_call_budget_per_model"]
        self.assertEqual(budget["finar_bench"], 12)
        self.assertEqual(budget["ipo_finance_agent"], 12)
        self.assertEqual(budget["big_finance_bench"], 12)
        self.assertEqual(budget["evisuff_stateful_ipo"], 18)
        self.assertEqual(budget["total"], 54)
        self.assertEqual(sum(value for key, value in budget.items() if key != "total"), 54)

    def test_external_item_choices_are_exact_and_stable(self) -> None:
        ipo_positions = self.design["reference_surfaces"]["ipo_finance_agent"][
            "one_based_question_positions"
        ]
        self.assertEqual(
            ipo_positions,
            [1, 2, 5, 9, 12, 16, 18, 19, 25, 29, 35, 46],
        )

        bfb_ids = self.design["reference_surfaces"]["big_finance_bench"]["item_ids"]
        self.assertEqual(
            bfb_ids,
            [
                "bf-0a8c20169a",
                "bf-0e2b33b21b",
                "bf-14e00db503",
                "bf-20474b5540",
                "bf-2c01534176",
                "bf-36d4a10aa8",
                "bf-37f81aef9b",
                "bf-39bacf8580",
                "bf-50f29af2ed",
                "bf-51844d71db",
                "bf-55f33faa82",
                "bf-5b4cd39939",
            ],
        )

    def test_upstream_revisions_are_pinned_and_launch_remains_locked(self) -> None:
        sources = self.lock["sources"]
        for name in ("finar_bench", "ipo_finance_agent", "big_finance_bench"):
            self.assertEqual(len(sources[name]["commit_sha"]), 40)
        self.assertEqual(len(sources["ipo_finance_agent"]["git_blob_sha"]), 40)
        self.assertEqual(len(sources["big_finance_bench"]["git_blob_sha"]), 40)
        self.assertFalse(sources["finar_bench"]["lock_complete"])
        self.assertIsNone(sources["finar_bench"]["test_file_hash"])
        self.assertFalse(self.lock["inference_allowed"])

    def test_models_judges_and_budget_must_be_frozen_before_inference(self) -> None:
        policy = self.design["model_panel_policy"]
        self.assertGreaterEqual(policy["minimum_models"], 2)
        self.assertFalse(policy["exact_model_ids_frozen"])
        self.assertTrue(
            self.design["judge_call_policy"][
                "count_separately_from_evaluated_model_calls"
            ]
        )
        gates = set(self.design["required_pre_inference_gates"])
        self.assertTrue(
            {
                "materialize_exact_finar_task_ids",
                "freeze_evaluated_model_ids",
                "freeze_judge_models",
                "approve_evaluated_and_judge_call_budget",
                "create_new_registration_branch",
            }.issubset(gates)
        )

    def test_cross_benchmark_metrics_are_explicit(self) -> None:
        metrics = self.design["cross_benchmark_metrics"]
        self.assertEqual(
            set(metrics),
            {
                "reference_competence",
                "benchmark_to_workflow_gap",
                "composition_retention",
                "amendment_delta",
                "coordination_validity_gap",
            },
        )


if __name__ == "__main__":
    unittest.main()
