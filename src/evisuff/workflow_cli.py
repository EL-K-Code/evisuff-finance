from __future__ import annotations

import argparse
import json
from pathlib import Path

from .enterprise_workflow import run_synthetic_pilot, score_run, write_json


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff-workflow")
    subparsers = parser.add_subparsers(dest="command", required=True)

    score = subparsers.add_parser("score-run", help="Score one multi-department workflow run")
    score.add_argument("spec", type=Path)
    score.add_argument("run_dir", type=Path)
    score.add_argument("--output", type=Path, required=True)

    pilot = subparsers.add_parser("synthetic-pilot", help="Generate and score deterministic software-validation baselines")
    pilot.add_argument("spec", type=Path)
    pilot.add_argument("--runs-dir", type=Path, default=Path("results/ipo_pilot_runs"))
    pilot.add_argument("--output", type=Path, default=Path("results/ipo_workflow_pilot.json"))

    args = parser.parse_args()
    if args.command == "score-run":
        report = score_run(args.spec, args.run_dir).to_dict()
        write_json(args.output, report)
        print(json.dumps(report, indent=2))
        return
    report = run_synthetic_pilot(args.spec, args.runs_dir, args.output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
