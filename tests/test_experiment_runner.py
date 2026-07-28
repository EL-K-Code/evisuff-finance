from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evisuff.experiment_runner import run_experiment
from evisuff.model_backends import parse_json_content


class ExperimentRunnerTests(unittest.TestCase):
    def _write_fixture(self, root: Path) -> Path:
        spec = {
            "workflow_id": "test-ipo-v1",
            "issuer": "Test Issuer",
            "required_source_version": "v2",
            "required_scenario_id": "base_case",
            "allowed_scenarios": ["base_case"],
            "versions": {
                "v1": {
                    "document_id": "TEST-S1-001",
                    "facts": {
                        "price_per_share_usd": 10.0,
                        "primary_shares_m": 10.0,
                        "existing_shares_m": 90.0,
                        "debt_usd_m": 50.0,
                        "cash_usd_m": 20.0
                    },
                    "risk_flags": ["customer_concentration"]
                },
                "v2": {
                    "document_id": "TEST-S1A-002",
                    "facts": {
                        "price_per_share_usd": 12.0,
                        "primary_shares_m": 12.0,
                        "existing_shares_m": 90.0,
                        "debt_usd_m": 50.0,
                        "cash_usd_m": 20.0
                    },
                    "risk_flags": [
                        "customer_concentration",
                        "regulatory_investigation"
                    ]
                }
            }
        }
        spec_path = root / "spec.json"
        spec_path.write_text(json.dumps(spec), encoding="utf-8")
        return spec_path

    def test_json_code_fence_is_parsed(self) -> None:
        payload = parse_json_content("```json\n{\"ok\": true}\n```")
        self.assertEqual(payload, {"ok": True})

    def test_oracle_runs_all_three_conditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            config = {
                "experiment_id": "oracle-matrix",
                "cases": ["spec.json"],
                "conditions": ["isolated", "generalist", "multi_agent"],
                "repetitions": 1,
                "output_root": "results",
                "systems": [
                    {
                        "system_id": "oracle-control",
                        "backend": {
                            "type": "deterministic_control",
                            "mode": "oracle"
                        }
                    }
                ]
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            summary = run_experiment(config_path)
            self.assertEqual(len(summary["reports"]), 3)
            self.assertTrue(all(row["enterprise_success"] for row in summary["reports"]))
            self.assertTrue(
                all(row["workflow_score"] == 1.0 for row in summary["reports"])
            )
            self.assertTrue((root / "results" / "experiment_summary.json").exists())

    def test_stale_silo_fails_enterprise_even_when_runs_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._write_fixture(root)
            config = {
                "experiment_id": "stale-control",
                "cases": ["spec.json"],
                "conditions": ["isolated"],
                "repetitions": 1,
                "output_root": "results",
                "systems": [
                    {
                        "system_id": "stale-control",
                        "backend": {
                            "type": "deterministic_control",
                            "mode": "stale_silo"
                        }
                    }
                ]
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            summary = run_experiment(config_path)
            report = summary["reports"][0]
            self.assertEqual(report["status"], "completed")
            self.assertFalse(report["enterprise_success"])
            self.assertGreater(report["composition_gap"], 0.0)


if __name__ == "__main__":
    unittest.main()
