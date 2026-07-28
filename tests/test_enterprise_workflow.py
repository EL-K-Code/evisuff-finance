from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evisuff.enterprise_workflow import generate_synthetic_baselines, run_synthetic_pilot, score_run


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "data" / "ipo_workflow_pilot" / "spec.json"


class EnterpriseWorkflowTests(unittest.TestCase):
    def test_coordinated_control_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs = generate_synthetic_baselines(SPEC, Path(tmp))
            coordinated = next(path for path in runs if path.name == "coordinated_team")
            report = score_run(SPEC, coordinated)
            self.assertEqual(report.component_score, 1.0)
            self.assertEqual(report.coordination_score, 1.0)
            self.assertEqual(report.workflow_score, 1.0)
            self.assertTrue(report.enterprise_success)

    def test_siloed_departments_expose_composition_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs = generate_synthetic_baselines(SPEC, Path(tmp))
            siloed = next(path for path in runs if path.name == "siloed_benchmark_winners")
            report = score_run(SPEC, siloed)
            self.assertEqual(report.component_score, 1.0)
            self.assertLess(report.coordination_score, 1.0)
            self.assertGreater(report.composition_gap, 0.0)
            self.assertFalse(report.enterprise_success)

    def test_partial_handoff_fails_risk_and_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            runs = generate_synthetic_baselines(SPEC, Path(tmp))
            partial = next(path for path in runs if path.name == "partial_handoff")
            report = score_run(SPEC, partial)
            failed = {check.check_id for check in report.local_checks + report.coordination_checks if not check.passed}
            self.assertIn("risk.coverage", failed)
            self.assertIn("memo.risks", failed)
            self.assertIn("memo.citations", failed)
            self.assertIn("latest_provenance.memo", failed)
            self.assertFalse(report.enterprise_success)

    def test_full_pilot_writes_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "pilot.json"
            result = run_synthetic_pilot(SPEC, root / "runs", output)
            self.assertTrue(output.exists())
            self.assertEqual(len(result["systems"]), 3)
            loaded = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(loaded["pilot"], "ipo_multi_department_composition")


if __name__ == "__main__":
    unittest.main()
