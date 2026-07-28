from __future__ import annotations

import argparse
import json
from pathlib import Path

from .real_cases import validate_index


def main() -> None:
    parser = argparse.ArgumentParser(prog="evisuff-real-cases")
    parser.add_argument("index", type=Path, help="Path to the real IPO case index")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_index(args.index)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    raise SystemExit(0 if report["valid"] else 1)


if __name__ == "__main__":
    main()
