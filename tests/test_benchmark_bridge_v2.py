from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DESIGN_PATH = ROOT / "configs" / "benchmark_bridge_v2.json"
LOCK_PATH = ROOT / "configs" / "bridge_v2_upstream_lock.json"
FINAR_MANIFEST_PATH = ROOT / "configs" / "bridge_v2_finar_items.json"
IPO_MANIFEST_PATH = ROOT / "configs" / "bridge_v2_ipo_agent_items.json"
IPO_PROTOCOL_PATH = ROOT / "configs" / "bridge_v2_ipo_rubric_protocol.json"
BFB_MANIFEST_PATH = ROOT / "configs" / "bridge_v2_big_finance_items.json"
SUPERSESSION_PATH = ROOT / "docs" / "preregistered_v1_supersession.md"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BenchmarkBridgeV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
        cls.lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        cls.finar_manifest = json.loads(FINAR_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.ipo_manifest = json.loads(IPO_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.ipo_protocol = json.loads(IPO_PROTOCOL_PATH.read_text(encoding="utf-8"))
        cls.bfb_manifest = json.loads(BFB_MANIFEST_PATH.read_text(encoding="utf-8"))
        cls.supersession = SUPERSESSION_PATH.read_text(encoding="utf-8")

    def test_v1_is_superseded_before_official_inference(self) -> None:
        self.assertEqual(self.design["supersedes"], "evisuff-stateful-ipo-v1")
        self.assertFalse(self.design["official_v2_inference_started"])
        self.assertIn("superseded_before_official_inference", self.supersession)
        self.assertIn("Official v1 model calls completed:** `0`", self.supersession)
        self.assertIn("Official v1 workflow runs completed:** `0`", self.supersession)

    def test_four_comparison_surfaces_are_present(self) -> None:
        self.assertEqual(
            set(self.design["reference_surfaces"]),
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
        self.assertEqual(len(surfaces["ipo_finance_agent"]["one_based_question_positions"]), 12)
        self.assertEqual(surfaces["big_finance_bench"]["sample_size"], 12)
        self.assertEqual(len(surfaces["big_finance_bench"]["item_ids"]), 12)
        self.assertEqual(surfaces["evisuff_stateful_ipo"]["evaluated_model_calls"], 18)

        budget = self.design["evaluated_model_call_budget_per_model"]
        self.assertEqual(budget["total"], 54)
        self.assertEqual(sum(value for key, value in budget.items() if key != "total"), 54)

    def test_finar_source_and_exact_items_are_materialized(self) -> None:
        source_lock = self.lock["sources"]["finar_bench"]
        source = self.finar_manifest["source"]
        selection = self.finar_manifest["selection"]
        items = self.finar_manifest["items"]

        self.assertTrue(source_lock["lock_complete"])
        self.assertIsNone(source_lock["remaining_action"])
        self.assertEqual(len(source_lock["dataset_revision"]), 40)
        self.assertEqual(len(source_lock["test_file_sha256"]), 64)
        self.assertEqual(source_lock["test_file_size_bytes"], 2_386_147)
        self.assertEqual(source["record_count"], 90)
        self.assertEqual(source["task_counts"], {"fact": 540, "indicator": 540, "reasoning": 90})
        self.assertEqual(selection["counts"], {"fact": 4, "indicator": 4, "reasoning": 4})
        self.assertEqual(len(items), 12)
        self.assertEqual(len({item["task_id"] for item in items}), 12)

        selected_ids = [item["task_id"] for item in items]
        self.assertEqual(selected_ids, source_lock["selected_task_ids"])
        self.assertEqual(selected_ids, self.design["reference_surfaces"]["finar_bench"]["selected_task_ids"])
        self.assertEqual(source_lock["item_manifest_sha256"], file_sha256(FINAR_MANIFEST_PATH))
        self.assertTrue(self.design["gate_status"]["materialize_exact_finar_task_ids"])

    def test_ipo_questions_are_exact_and_protocol_is_honest(self) -> None:
        source_lock = self.lock["sources"]["ipo_finance_agent"]
        surface = self.design["reference_surfaces"]["ipo_finance_agent"]
        items = self.ipo_manifest["items"]
        positions = [item["position"] for item in items]
        question_ids = [item["question_id"] for item in items]

        self.assertEqual(self.ipo_manifest["source"]["public_question_count"], 70)
        self.assertEqual(positions, [1, 2, 5, 9, 12, 16, 18, 19, 25, 29, 35, 46])
        self.assertEqual(len(items), 12)
        self.assertEqual(len(set(question_ids)), 12)
        self.assertTrue(all(len(item["question_sha256"]) == 64 for item in items))
        self.assertTrue(source_lock["questions_materialized"])
        self.assertFalse(source_lock["static_public_rubrics_materialized"])
        self.assertTrue(source_lock["rubric_protocol_resolved"])
        self.assertFalse(source_lock["final_rubrics_materialized"])
        self.assertEqual(source_lock["item_manifest_sha256"], file_sha256(IPO_MANIFEST_PATH))
        self.assertEqual(surface["item_manifest_sha256"], file_sha256(IPO_MANIFEST_PATH))
        self.assertEqual(source_lock["rubric_protocol_sha256"], file_sha256(IPO_PROTOCOL_PATH))
        self.assertEqual(surface["rubric_protocol_sha256"], file_sha256(IPO_PROTOCOL_PATH))
        self.assertEqual(surface["selected_question_ids"], question_ids)
        self.assertTrue(self.design["gate_status"]["materialize_exact_ipo_questions"])
        self.assertTrue(self.design["gate_status"]["resolve_ipo_rubric_protocol"])
        self.assertFalse(self.design["gate_status"]["generate_review_and_freeze_ipo_rubrics"])

    def test_ipo_rubric_replication_parameters_are_frozen(self) -> None:
        protocol = self.ipo_protocol
        parameters = protocol["frozen_parameters"]
        gates = protocol["gate_status"]

        self.assertTrue(protocol["public_artifact_finding"]["questions_publicly_materialized"])
        self.assertFalse(protocol["public_artifact_finding"]["static_per_question_final_rubrics_publicly_materialized"])
        self.assertTrue(protocol["public_artifact_finding"]["rubric_pipeline_scripts_publicly_materialized"])
        self.assertEqual(parameters["rubric_construction_answer_sets"], 5)
        self.assertEqual(parameters["minimum_fact_agreement"], 2)
        self.assertEqual(parameters["maximum_enrichment_iterations"], 5)
        self.assertEqual(parameters["maximum_repair_iterations"], 5)
        self.assertEqual(parameters["temperature_for_rubric_pipeline_calls"], 0.0)
        self.assertTrue(gates["protocol_resolved"])
        self.assertFalse(gates["machine_rubrics_generated"])
        self.assertFalse(gates["human_expert_review_completed"])
        self.assertFalse(gates["final_rubrics_frozen"])
        self.assertEqual(protocol["model_calls_completed_under_this_protocol"], 0)

    def test_big_finance_items_and_weighted_rubrics_are_materialized(self) -> None:
        source_lock = self.lock["sources"]["big_finance_bench"]
        surface = self.design["reference_surfaces"]["big_finance_bench"]
        items = self.bfb_manifest["items"]
        ids = [item["id"] for item in items]

        self.assertEqual(self.bfb_manifest["source"]["public_item_count"], 50)
        self.assertEqual(len(items), 12)
        self.assertEqual(len(set(ids)), 12)
        self.assertEqual(ids, surface["item_ids"])
        self.assertEqual(ids, source_lock["selected_item_ids"])
        for item in items:
            self.assertTrue(item["query"])
            self.assertIn("reference_answer", item)
            self.assertTrue(item["rubric"])
            self.assertTrue(all("text" in row and "points" in row for row in item["rubric"]))
            self.assertGreater(sum(row["points"] for row in item["rubric"]), 0)
        self.assertTrue(source_lock["items_and_weighted_rubrics_materialized"])
        self.assertTrue(surface["weighted_rubrics_materialized"])
        self.assertEqual(source_lock["item_manifest_sha256"], file_sha256(BFB_MANIFEST_PATH))
        self.assertEqual(surface["item_manifest_sha256"], file_sha256(BFB_MANIFEST_PATH))
        self.assertTrue(self.design["gate_status"]["copy_and_hash_exact_big_finance_items_and_rubrics"])

    def test_upstream_revisions_are_pinned_and_launch_remains_locked(self) -> None:
        sources = self.lock["sources"]
        for name in ("finar_bench", "ipo_finance_agent", "big_finance_bench"):
            self.assertEqual(len(sources[name]["commit_sha"]), 40)
            self.assertTrue(sources[name]["lock_complete"])
        self.assertEqual(self.lock["status"], "all_public_items_materialized_ipo_rubric_protocol_frozen")
        self.assertFalse(self.lock["inference_allowed"])

    def test_models_judges_rubrics_and_budget_must_be_frozen(self) -> None:
        policy = self.design["model_panel_policy"]
        self.assertGreaterEqual(policy["minimum_models"], 2)
        self.assertFalse(policy["exact_model_ids_frozen"])
        self.assertTrue(self.design["judge_call_policy"]["count_separately_from_evaluated_model_calls"])
        required = set(self.design["required_pre_inference_gates"])
        self.assertTrue(
            {
                "freeze_ipo_rubric_construction_ensemble",
                "freeze_ipo_rubric_judges",
                "generate_review_and_freeze_ipo_rubrics",
                "freeze_evaluated_model_ids",
                "freeze_judge_models",
                "approve_evaluated_and_judge_call_budget",
                "create_new_registration_branch",
            }.issubset(required)
        )
        for gate in (
            "freeze_ipo_rubric_construction_ensemble",
            "freeze_ipo_rubric_judges",
            "generate_review_and_freeze_ipo_rubrics",
            "freeze_evaluated_model_ids",
            "freeze_judge_models",
            "freeze_tool_surfaces",
            "approve_evaluated_and_judge_call_budget",
            "create_new_registration_branch",
        ):
            self.assertFalse(self.design["gate_status"][gate])

    def test_cross_benchmark_metrics_are_explicit(self) -> None:
        self.assertEqual(
            set(self.design["cross_benchmark_metrics"]),
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
