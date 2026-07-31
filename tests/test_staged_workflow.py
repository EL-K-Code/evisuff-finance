from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evisuff.staged_workflow import (
    run_staged_experiment,
    run_staged_one,
    stage_spec,
    staged_version_ids,
)


ROOT = Path(__file__).resolve().parents[1]
REDDIT = ROOT / "data" / "ipo_real_cases" / "reddit_2024" / "spec.json"


def system(mode: str = "oracle") -> dict:
    return {
        "system_id": f"staged-control-{mode}",
        "backend": {
            "type": "staged_deterministic_control",
            "mode": mode,
        },
        "pricing_usd_per_million_tokens": {
            "input": 0.0,
            "output": 0.0,
        },
    }


class StagedWorkflowTests(unittest.TestCase):
    def test_each_stage_exposes_only_one_public_version(self) -> None:
        spec = json.loads(REDDIT.read_text(encoding="utf-8"))
        initial, final = staged_version_ids(spec)
        for version_id in (initial, final):
            staged = stage_spec(spec, version_id)
            visible = staged["source_packet"]["versions"]
            self.assertEqual(len(visible), 1)
            self.assertEqual(visible[0]["version_id"], version_id)
            self.assertEqual(staged["required_source_version"], version_id)
            self.assertNotIn("facts", visible[0])
            self.assertNotIn("risk_flags", visible[0])

    def test_staged_generalist_uses_two_calls_and_updates_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = run_staged_one(
                spec_path=REDDIT,
                output_root=Path(temporary),
                system_config=system(),
                condition="staged_generalist",
                repetition=0,
                overwrite=True,
            )
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["call_count"], 2)
        self.assertTrue(report["round1_enterprise_success"])
        self.assertTrue(report["enterprise_success"])
        self.assertTrue(report["update_success"])
        self.assertEqual(report["stale_artifacts_after_update"], [])

    def test_staged_isolated_uses_eight_calls_without_shared_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = run_staged_one(
                spec_path=REDDIT,
                output_root=Path(temporary),
                system_config=system(),
                condition="staged_isolated",
                repetition=0,
                overwrite=True,
            )
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["call_count"], 8)
        self.assertTrue(report["enterprise_success"])
        self.assertTrue(report["update_success"])

    def test_staged_multi_agent_uses_eight_calls_and_updates_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = run_staged_one(
                spec_path=REDDIT,
                output_root=Path(temporary),
                system_config=system(),
                condition="staged_multi_agent",
                repetition=0,
                overwrite=True,
            )
        self.assertEqual(report["status"], "completed")
        self.assertEqual(report["call_count"], 8)
        self.assertTrue(report["round1_enterprise_success"])
        self.assertTrue(report["enterprise_success"])
        self.assertTrue(report["update_success"])
        self.assertEqual(report["changed_artifact_count"], 4)

    def test_ignore_update_control_is_detected_as_stale(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = run_staged_one(
                spec_path=REDDIT,
                output_root=Path(temporary),
                system_config=system("ignore_update"),
                condition="staged_generalist",
                repetition=0,
                overwrite=True,
            )
        self.assertEqual(report["status"], "completed")
        self.assertFalse(report["enterprise_success"])
        self.assertFalse(report["update_success"])
        self.assertEqual(
            set(report["stale_artifacts_after_update"]),
            {"diligence", "valuation", "risk", "memo"},
        )

    def test_offline_matrix_separates_oracle_and_stale_controls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config = {
                "experiment_id": "staged-test",
                "cases": [str(REDDIT)],
                "conditions": [
                    "staged_isolated",
                    "staged_generalist",
                    "staged_multi_agent",
                ],
                "repetitions": 1,
                "output_root": str(root / "results"),
                "systems": [system(), system("ignore_update")],
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            summary = run_staged_experiment(config_path, overwrite=True)

        self.assertEqual(len(summary["reports"]), 6)
        oracle = [
            report
            for report in summary["reports"]
            if report["system_id"] == "staged-control-oracle"
        ]
        stale = [
            report
            for report in summary["reports"]
            if report["system_id"] == "staged-control-ignore_update"
        ]
        self.assertTrue(all(report["update_success"] for report in oracle))
        self.assertTrue(all(not report["update_success"] for report in stale))


if __name__ == "__main__":
    unittest.main()
