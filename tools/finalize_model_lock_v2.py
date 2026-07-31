from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "configs" / "bridge_v2_model_panel_candidate.json"
PROTOCOL_PATH = ROOT / "configs" / "bridge_v2_ipo_rubric_protocol.json"
DESIGN_PATH = ROOT / "configs" / "benchmark_bridge_v2.json"
LOCK_PATH = ROOT / "configs" / "bridge_v2_upstream_lock.json"
TEST_PATH = ROOT / "tests" / "test_benchmark_bridge_v2.py"


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    design = json.loads(DESIGN_PATH.read_text(encoding="utf-8"))
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))

    route = {
        "base_url": "https://openrouter.ai/api/v1",
        "provider_policy": {
            "only": ["openai"],
            "allow_fallbacks": False,
            "require_parameters": True,
            "data_collection": "deny",
        },
        "transport_note": (
            "OpenRouter transport pinned to OpenAI-hosted endpoints; "
            "no alternate provider fallback is allowed."
        ),
    }
    exact_models = {
        "frontier_anchor": "openai/gpt-5.6-terra",
        "cost_control": "openai/gpt-5.6-luna",
        "rubric_induction_and_audit": "openai/gpt-5.6-luna",
        "final_evaluation": "openai/gpt-5.6-sol",
        "open_weight_engineering_control": "openai/gpt-oss-20b",
    }

    for model in plan["evaluated_models"]:
        role = model["role"]
        model.update(
            {
                "provider": "openrouter",
                "model_id": exact_models[role],
                "transport": route,
                "access_verified": True,
                "frozen": True,
            }
        )
    for role, judge in plan["judge_candidates"].items():
        judge.update(
            {
                "provider": "openrouter",
                "model_id": exact_models[role],
                "transport": route,
                "access_verified": True,
                "status": "frozen_before_rubric_generation_and_evaluation",
                "frozen": True,
            }
        )
    plan.update(
        {
            "status": "exact_openrouter_routes_frozen_funding_required",
            "transport_lock": route,
            "exact_model_ids": exact_models,
            "model_ids_frozen": True,
            "judge_ids_frozen": True,
            "funding_ready": False,
            "funding_gate": {
                "current_key_is_free_tier": True,
                "paid_model_calls_authorized": False,
                "required_action": (
                    "Add OpenRouter credits or configure OPENAI_API_KEY before "
                    "rubric generation or evaluated-model inference."
                ),
            },
            "inference_allowed": False,
        }
    )

    protocol["rubric_judge"] = {
        "provider": "openrouter",
        "model_id": exact_models["rubric_induction_and_audit"],
        "reasoning_effort": "medium",
        "temperature": 0.0,
        "transport": route,
        "frozen_before_generation": True,
    }
    protocol["gate_status"]["rubric_construction_ensemble_frozen"] = True
    protocol["gate_status"]["rubric_judges_frozen"] = True
    protocol["status"] = (
        "public_answer_ensemble_and_rubric_judge_frozen_final_rubrics_pending"
    )
    write_json(PROTOCOL_PATH, protocol)
    protocol_sha = hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest()

    design["status"] = (
        "public_objects_and_exact_model_routes_frozen_"
        "funding_and_ipo_rubrics_pending"
    )
    policy = design["model_panel_policy"]
    policy.update(
        {
            "exact_model_ids_frozen": True,
            "selected_evaluated_models": [
                exact_models["frontier_anchor"],
                exact_models["cost_control"],
            ],
            "selected_judges": {
                "ipo_rubric": exact_models["rubric_induction_and_audit"],
                "final_evaluation": exact_models["final_evaluation"],
            },
            "transport": route,
            "funding_ready": False,
        }
    )
    design["reference_surfaces"]["ipo_finance_agent"][
        "rubric_protocol_sha256"
    ] = protocol_sha
    gates = design["gate_status"]
    for gate in (
        "freeze_ipo_rubric_construction_ensemble",
        "freeze_ipo_rubric_judges",
        "freeze_evaluated_model_ids",
        "freeze_judge_models",
    ):
        gates[gate] = True
    for gate in (
        "generate_review_and_freeze_ipo_rubrics",
        "freeze_tool_surfaces",
        "approve_evaluated_and_judge_call_budget",
        "create_new_registration_branch",
    ):
        gates[gate] = False

    lock["status"] = (
        "exact_model_and_judge_routes_frozen_funding_and_final_rubrics_pending"
    )
    lock["sources"]["ipo_finance_agent"][
        "rubric_protocol_sha256"
    ] = protocol_sha
    lock["model_panel"] = {
        "path": "configs/bridge_v2_model_panel_candidate.json",
        "evaluated_models": [
            exact_models["frontier_anchor"],
            exact_models["cost_control"],
        ],
        "judges": [
            exact_models["rubric_induction_and_audit"],
            exact_models["final_evaluation"],
        ],
        "transport": route,
        "model_ids_frozen": True,
        "funding_ready": False,
    }
    completed_labels = {
        "freeze IPO rubric-construction ensemble IDs",
        "freeze IPO rubric judge IDs",
        "freeze evaluated model IDs",
        "freeze evaluation judge models",
    }
    lock["remaining_non_source_gates"] = [
        gate
        for gate in lock["remaining_non_source_gates"]
        if gate not in completed_labels
    ]
    funding_label = "fund OpenRouter paid-model budget or configure direct OpenAI key"
    if funding_label not in lock["remaining_non_source_gates"]:
        lock["remaining_non_source_gates"].insert(0, funding_label)
    lock["inference_allowed"] = False

    text = TEST_PATH.read_text(encoding="utf-8")
    text = text.replace(
        'self.assertEqual(self.lock["status"], '
        '"all_public_items_materialized_ipo_rubric_protocol_frozen")',
        'self.assertEqual(self.lock["status"], '
        '"exact_model_and_judge_routes_frozen_funding_and_final_rubrics_pending")',
    )
    text = text.replace(
        'self.assertFalse(policy["exact_model_ids_frozen"])',
        'self.assertTrue(policy["exact_model_ids_frozen"])',
    )
    old_loop = '''        for gate in (
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
'''
    new_loop = '''        for gate in (
            "freeze_ipo_rubric_construction_ensemble",
            "freeze_ipo_rubric_judges",
            "freeze_evaluated_model_ids",
            "freeze_judge_models",
        ):
            self.assertTrue(self.design["gate_status"][gate])
        for gate in (
            "generate_review_and_freeze_ipo_rubrics",
            "freeze_tool_surfaces",
            "approve_evaluated_and_judge_call_budget",
            "create_new_registration_branch",
        ):
            self.assertFalse(self.design["gate_status"][gate])
'''
    if old_loop not in text and new_loop not in text:
        raise RuntimeError("Expected gate assertion block was not found")
    text = text.replace(old_loop, new_loop)

    marker = "    def test_cross_benchmark_metrics_are_explicit(self) -> None:\n"
    addition = '''    def test_exact_model_routes_and_public_ipo_ensemble_are_frozen(self) -> None:
        policy = self.design["model_panel_policy"]
        self.assertEqual(
            policy["selected_evaluated_models"],
            ["openai/gpt-5.6-terra", "openai/gpt-5.6-luna"],
        )
        self.assertEqual(
            policy["selected_judges"]["final_evaluation"],
            "openai/gpt-5.6-sol",
        )
        self.assertEqual(
            policy["transport"]["provider_policy"]["only"], ["openai"]
        )
        self.assertFalse(
            policy["transport"]["provider_policy"]["allow_fallbacks"]
        )
        self.assertFalse(policy["funding_ready"])
        self.assertTrue(
            self.design["gate_status"]["freeze_ipo_rubric_construction_ensemble"]
        )
        self.assertTrue(
            self.design["gate_status"]["freeze_ipo_rubric_judges"]
        )
        self.assertFalse(self.lock["inference_allowed"])

'''
    if "test_exact_model_routes_and_public_ipo_ensemble_are_frozen" not in text:
        text = text.replace(marker, addition + marker)

    write_json(PLAN_PATH, plan)
    write_json(DESIGN_PATH, design)
    write_json(LOCK_PATH, lock)
    TEST_PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
