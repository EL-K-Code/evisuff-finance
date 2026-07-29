from __future__ import annotations

import json
import unittest
from pathlib import Path

from evisuff.enterprise_workflow import (
    financial_metrics,
    score_memo,
    score_risk,
    score_valuation,
)


ROOT = Path(__file__).resolve().parents[1]
CASE_ROOT = ROOT / "data" / "ipo_real_cases"
CASE_PATHS = (
    CASE_ROOT / "reddit_2024" / "spec.json",
    CASE_ROOT / "rubrik_2024" / "spec.json",
    CASE_ROOT / "coreweave_2025" / "spec.json",
)


def load_spec(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class WorkflowScoringContractTests(unittest.TestCase):
    def test_public_risk_ids_match_scored_risk_flags(self) -> None:
        for path in CASE_PATHS:
            spec = load_spec(path)
            gold_versions = spec["versions"]
            for packet_version in spec["source_packet"]["versions"]:
                version_id = packet_version["version_id"]
                public_ids = [
                    item["risk_id"]
                    for item in packet_version["evidence"]
                    if item["evidence_id"].startswith("risk_")
                ]
                self.assertEqual(len(public_ids), len(set(public_ids)), path)
                self.assertEqual(
                    set(public_ids),
                    set(gold_versions[version_id]["risk_flags"]),
                    f"Public risk ontology differs from scored labels in {path} {version_id}",
                )

    def test_reporting_scale_rounding_is_accepted_for_derived_metrics(self) -> None:
        spec = load_spec(CASE_PATHS[0])
        version_id = spec["required_source_version"]
        facts = spec["versions"][version_id]["facts"]
        expected = financial_metrics(facts)
        rounded = dict(expected)
        rounded["gross_proceeds_usd_m"] += 0.005
        rounded["dilution_pct"] += 0.005

        valuation = {
            "source_version": version_id,
            "scenario_id": spec["required_scenario_id"],
            "inputs": dict(facts),
            "outputs": rounded,
        }
        valuation_score = score_valuation(spec, valuation)
        self.assertTrue(all(check.passed for check in valuation_score.checks))

        memo = {
            "source_version": version_id,
            "scenario_id": spec["required_scenario_id"],
            "headline_metrics": rounded,
            "top_risks": list(spec["versions"][version_id]["risk_flags"]),
            "citations": [
                f"{spec['versions'][version_id]['document_id']}:summary:offering"
            ],
            "recommendation": "proceed_with_conditions",
        }
        memo_score = score_memo(spec, memo)
        self.assertTrue(all(check.passed for check in memo_score.checks))

    def test_material_metric_error_still_fails(self) -> None:
        spec = load_spec(CASE_PATHS[0])
        version_id = spec["required_source_version"]
        facts = spec["versions"][version_id]["facts"]
        outputs = financial_metrics(facts)
        outputs["dilution_pct"] += 0.02
        artifact = {
            "source_version": version_id,
            "scenario_id": spec["required_scenario_id"],
            "inputs": dict(facts),
            "outputs": outputs,
        }
        score = score_valuation(spec, artifact)
        check = next(
            item for item in score.checks if item.check_id == "valuation.output.dilution_pct"
        )
        self.assertFalse(check.passed)

    def test_unsupported_risk_is_a_critical_failure(self) -> None:
        spec = load_spec(CASE_PATHS[0])
        version_id = spec["required_source_version"]
        artifact = {
            "source_version": version_id,
            "scenario_id": spec["required_scenario_id"],
            "risk_flags": [
                *spec["versions"][version_id]["risk_flags"],
                "unsupported_invented_risk",
            ],
        }
        score = score_risk(spec, artifact)
        check = next(item for item in score.checks if item.check_id == "risk.no_unsupported")
        self.assertFalse(check.passed)
        self.assertTrue(check.critical)


if __name__ == "__main__":
    unittest.main()
