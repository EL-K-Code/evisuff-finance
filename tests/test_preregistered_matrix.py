from __future__ import annotations

import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "configs" / "preregistered_matrix_v1.json"
MANIFEST_PATH = ROOT / "configs" / "preregistered_freeze_manifest_v1.json"


class PreregisteredMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
        cls.manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_freeze_identity_is_consistent(self) -> None:
        self.assertEqual(self.plan["preregistration_id"], "evisuff-stateful-ipo-v1")
        self.assertEqual(
            self.plan["preregistration_id"], self.manifest["preregistration_id"]
        )
        self.assertEqual(
            self.plan["benchmark_commit_sha"], self.manifest["frozen_commit_sha"]
        )
        self.assertEqual(
            self.plan["frozen_reference_branch"],
            self.manifest["frozen_reference_branch"],
        )
        self.assertEqual(len(self.plan["benchmark_commit_sha"]), 40)
        self.assertTrue(self.manifest["critical_blobs"])
        for blob_sha in self.manifest["critical_blobs"].values():
            self.assertEqual(len(blob_sha), 40)

    def test_design_has_three_cases_conditions_and_repetitions(self) -> None:
        self.assertEqual(set(self.plan["cases"]), {"reddit", "coreweave", "rubrik"})
        self.assertEqual(
            self.plan["conditions"],
            ["staged_generalist", "staged_isolated", "staged_multi_agent"],
        )
        self.assertEqual(self.plan["repetitions_per_cell"], 3)
        self.assertEqual(self.plan["planned_workflow_runs"], 27)

    def test_call_budget_is_exact(self) -> None:
        calls = self.plan["calls_per_condition"]
        self.assertEqual(calls["staged_generalist"], 2)
        self.assertEqual(calls["staged_isolated"], 8)
        self.assertEqual(calls["staged_multi_agent"], 8)
        calls_per_case = sum(calls.values())
        self.assertEqual(calls_per_case, 18)
        self.assertEqual(3 * 3 * calls_per_case, 162)
        self.assertEqual(self.plan["planned_model_calls"], 162)
        self.assertEqual(
            sum(block["planned_calls"] for block in self.plan["execution_blocks"]),
            162,
        )

    def test_execution_blocks_are_unique_balanced_and_quota_safe(self) -> None:
        blocks = self.plan["execution_blocks"]
        self.assertEqual(len(blocks), 6)
        self.assertEqual(len({block["block_id"] for block in blocks}), 6)
        self.assertTrue(all(block["planned_calls"] <= 36 for block in blocks))

        cases_by_repetition: dict[int, list[str]] = defaultdict(list)
        calls_by_repetition: Counter[int] = Counter()
        orders_by_repetition: dict[int, tuple[str, ...]] = {}
        for block in blocks:
            repetition = int(block["repetition"])
            cases_by_repetition[repetition].extend(block["case_order"])
            calls_by_repetition[repetition] += int(block["planned_calls"])
            order = tuple(block["condition_order"])
            previous = orders_by_repetition.setdefault(repetition, order)
            self.assertEqual(previous, order)
            self.assertEqual(
                block["planned_calls"],
                len(block["case_order"]) * sum(self.plan["calls_per_condition"].values()),
            )

        for repetition in (1, 2, 3):
            self.assertEqual(
                Counter(cases_by_repetition[repetition]),
                Counter({"reddit": 1, "coreweave": 1, "rubrik": 1}),
            )
            self.assertEqual(calls_by_repetition[repetition], 54)

        expected_rotations = {
            1: (
                "staged_generalist",
                "staged_isolated",
                "staged_multi_agent",
            ),
            2: (
                "staged_isolated",
                "staged_multi_agent",
                "staged_generalist",
            ),
            3: (
                "staged_multi_agent",
                "staged_generalist",
                "staged_isolated",
            ),
        }
        self.assertEqual(orders_by_repetition, expected_rotations)

    def test_no_hidden_retries_and_pilots_are_excluded(self) -> None:
        policy = self.plan["model_policy"]
        self.assertEqual(policy["api_max_retries"], 0)
        self.assertEqual(policy["hidden_benchmark_retries"], 0)
        self.assertFalse(policy["allow_model_fallback"])
        self.assertTrue(self.plan["execution_rules"]["pilot_runs_are_excluded"])
        self.assertEqual(
            self.plan["output_root"], "../results/preregistered_runs"
        )
        self.assertTrue(
            self.manifest["pilot_results_excluded_from_preregistered_analysis"]
        )

    def test_primary_endpoint_and_failure_rules_are_frozen(self) -> None:
        self.assertEqual(
            self.plan["primary_endpoint"], "strict_enterprise_success_v2"
        )
        rules = self.plan["execution_rules"]
        self.assertEqual(
            rules["provider_failure_before_model_output"],
            "non_evaluable_and_repeat_same_cell_next_window",
        )
        self.assertEqual(
            rules["model_schema_or_format_failure"],
            "strict_enterprise_failure_no_replacement_call",
        )
        self.assertEqual(
            rules["partial_model_workflow_failure"],
            "strict_enterprise_failure_no_replacement_call",
        )


if __name__ == "__main__":
    unittest.main()
