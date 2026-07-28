from __future__ import annotations

import argparse
import json
from pathlib import Path

from .enterprise_workflow import read_json
from .experiment_runner import run_experiment, run_one


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff-experiment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run the empirical matrix across cases, systems, and workflow conditions",
    )
    run.add_argument("config", type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--overwrite", action="store_true")

    one = subparsers.add_parser("run-one", help="Run one case/system/condition")
    one.add_argument("config", type=Path)
    one.add_argument("--case-index", type=int, default=0)
    one.add_argument("--system-index", type=int, default=0)
    one.add_argument(
        "--condition",
        choices=("isolated", "generalist", "multi_agent"),
        required=True,
    )
    one.add_argument("--repetition", type=int, default=0)
    one.add_argument("--output-root", type=Path, required=True)
    one.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.command == "run":
        summary = run_experiment(
            args.config,
            output_override=args.output_root,
            overwrite=args.overwrite,
        )
        print(json.dumps(summary, indent=2))
        return

    config = read_json(args.config)
    base = args.config.parent.resolve()
    case_value = Path(config["cases"][args.case_index])
    case_path = case_value if case_value.is_absolute() else (base / case_value).resolve()
    system = dict(config["systems"][args.system_index])
    report = run_one(
        spec_path=case_path,
        output_root=args.output_root,
        system_config=system,
        condition=args.condition,
        repetition=args.repetition,
        overwrite=args.overwrite,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
