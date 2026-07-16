"""Audit public IPO Finance Agent question taxonomy and rubric artifacts.

This script reads an existing local clone. It does not modify the upstream
repository and does not interpret automated quality flags as human review.
"""

from __future__ import annotations

import argparse
import collections
import csv
import json
import re
import statistics
import subprocess
from pathlib import Path


def git_json(repo: Path, path: str) -> list[dict]:
    raw = subprocess.check_output(
        ["git", "show", f"HEAD:{path}"], cwd=repo, stderr=subprocess.DEVNULL
    )
    return json.loads(raw)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    taxonomy_path = args.repo / "data" / "questions_taxonomy.csv"
    with taxonomy_path.open(encoding="utf-8") as handle:
        taxonomy = list(csv.DictReader(handle))

    rubric_versions = {}
    for path in (
        "rubric/rubrics_checked.json",
        "rubric/rubrics_checked_7thpass.json",
    ):
        rubrics = git_json(args.repo, path)
        scores = [
            x.get("quality", {}).get("overall")
            for x in rubrics
            if x.get("quality", {}).get("overall") is not None
        ]
        rubric_versions[path] = {
            "records": len(rubrics),
            "recommendations": dict(
                collections.Counter(x.get("recommendation") for x in rubrics)
            ),
            "quality_mean": statistics.mean(scores) if scores else None,
            "quality_median": statistics.median(scores) if scores else None,
            "quality_min": min(scores) if scores else None,
            "quality_below_0_8": sum(x < 0.8 for x in scores),
            "listed_issues": sum(
                len(x.get("quality", {}).get("issues", [])) for x in rubrics
            ),
            "records_with_top_level_evidence_key": sum(
                any("evidence" in key.lower() for key in x) for x in rubrics
            ),
        }

    public_result_path = "results/qwen3.7-max-public-spacex-70-20260609-134629.json"
    public_results = git_json(args.repo, public_result_path)
    answers = [x.get("answer") or "" for x in public_results]
    url_counts = [len(re.findall(r'https?://[^\s"\)]+', x)) for x in answers]

    report = {
        "result_type": "reproducible_public_repository_audit",
        "upstream_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=args.repo, text=True
        ).strip(),
        "taxonomy": {
            "questions": len(taxonomy),
            "categories": dict(
                collections.Counter(x["original_category"] for x in taxonomy)
            ),
            "domains": dict(
                collections.Counter(x["proposed_domain"] for x in taxonomy)
            ),
            "workflows": dict(
                collections.Counter(x["proposed_workflow"] for x in taxonomy)
            ),
        },
        "rubric_versions": rubric_versions,
        "answer_provenance_example": {
            "artifact": public_result_path,
            "answers": len(answers),
            "successful": sum(bool(x.get("success")) for x in public_results),
            "answers_with_url": sum(x > 0 for x in url_counts),
            "median_urls_per_answer": statistics.median(url_counts),
            "max_urls_per_answer": max(url_counts),
            "answers_with_markdown_inline_citation": sum(
                bool(re.search(r"\[[^\]]+\]\(https?://", x)) for x in answers
            ),
            "answers_with_stable_evidence_id_token": sum(
                bool(
                    re.search(
                        r"(?i)evidence[_ -]?id|chunk[_ -]?id|passage[_ -]?id", x
                    )
                )
                for x in answers
            ),
            "scope_warning": (
                "This is one public model result artifact and measures output "
                "format, not factual correctness or the entire benchmark."
            ),
        },
        "interpretation_warning": (
            "Automated quality flags are repository artifacts, not independent "
            "human validation and not a direct estimate of grading error."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
