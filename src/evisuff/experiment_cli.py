from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .enterprise_workflow import read_json
from .experiment_runner import run_experiment, run_one


def load_env_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Environment file not found: {path}")
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"Invalid environment line {line_number} in {path}: expected KEY=VALUE"
            )
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if not key:
            raise ValueError(f"Invalid environment line {line_number}: empty key")
        os.environ.setdefault(key, value)


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff-experiment")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run the empirical matrix across cases, systems, and workflow conditions",
    )
    run.add_argument("config", type=Path)
    run.add_argument("--env-file", type=Path)
    run.add_argument("--output-root", type=Path)
    run.add_argument("--overwrite", action="store_true")

    one = subparsers.add_parser("run-one", help="Run one case/system/condition")
    one.add_argument("config", type=Path)
    one.add_argument("--env-file", type=Path)
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
    if args.env_file:
        load_env_file(args.env_file)

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
