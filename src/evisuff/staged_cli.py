from __future__ import annotations

import argparse
import json
from pathlib import Path

from .enterprise_workflow import read_json
from .experiment_cli import load_env_file
from .staged_workflow import (
    STAGED_CONDITIONS,
    run_staged_experiment,
    run_staged_one,
)


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff-staged")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run the two-round filing-amendment matrix",
    )
    run.add_argument("config", type=Path)
    run.add_argument("--env-file", type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--overwrite", action="store_true")

    one = subparsers.add_parser(
        "run-one",
        help="Run one case/system/two-round condition",
    )
    one.add_argument("config", type=Path)
    one.add_argument("--env-file", type=Path)
    one.add_argument("--case-index", type=int, default=0)
    one.add_argument("--system-index", type=int, default=0)
    one.add_argument(
        "--condition",
        choices=STAGED_CONDITIONS,
        required=True,
    )
    one.add_argument("--repetition", type=int, default=0)
    one.add_argument("--output-root", type=Path, required=True)
    one.add_argument("--overwrite", action="store_true")

    args = parser.parse_args()
    if args.env_file:
        load_env_file(args.env_file)

    if args.command == "run":
        summary = run_staged_experiment(
            args.config,
            output_override=args.output_root,
            overwrite=args.overwrite,
        )
        print(json.dumps(summary, indent=2))
        return

    config = read_json(args.config)
    base = args.config.parent.resolve()
    case_value = Path(config["cases"][args.case_index])
    case_path = (
        case_value if case_value.is_absolute() else (base / case_value).resolve()
    )
    system = dict(config["systems"][args.system_index])
    report = run_staged_one(
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
