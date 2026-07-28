from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from evisuff.real_cases import validate_index


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "ipo_real_cases" / "index.json"


class RealCaseValidationTests(unittest.TestCase):
    def test_all_public_cases_validate(self) -> None:
        report = validate_index(INDEX)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["case_count"], 3)
        self.assertGreaterEqual(report["document_count"], 7)
        self.assertGreaterEqual(report["evidence_item_count"], 50)

    def test_every_case_has_a_version_sensitive_target(self) -> None:
        report = validate_index(INDEX)
        for case in report["cases"]:
            self.assertTrue(case["changed_facts"] or case["changed_risks"], case)

    def test_gold_labels_are_not_allowed_inside_source_packet_versions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            spec = json.loads(
                (ROOT / "data" / "ipo_real_cases" / "reddit_2024" / "spec.json").read_text(
                    encoding="utf-8"
                )
            )
            spec["source_packet"]["versions"][0]["facts"] = {
                "price_per_share_usd": 32.5
            }
            (root / "spec.json").write_text(json.dumps(spec), encoding="utf-8")
            index = {
                "dataset_id": "leak-test",
                "cases": [
                    {
                        "case_id": "reddit_2024",
                        "spec": "spec.json",
                        "issuer": "Reddit, Inc.",
                        "ticker": "RDDT",
                        "annotation_status": spec["annotation_status"],
                    }
                ],
            }
            (root / "index.json").write_text(json.dumps(index), encoding="utf-8")
            report = validate_index(root / "index.json")
            self.assertFalse(report["valid"])
            self.assertTrue(
                any("must not expose gold labels" in item for item in report["errors"])
            )


if __name__ == "__main__":
    unittest.main()
