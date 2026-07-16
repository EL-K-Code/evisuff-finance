from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .schema import BenchmarkItem


def read_jsonl(path: str | Path) -> list[dict]:
    rows: list[dict] = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as error:
                    raise ValueError(f"invalid JSON on line {line_number}: {error}")
    return rows


def read_items(path: str | Path) -> list[BenchmarkItem]:
    return [BenchmarkItem.from_dict(x) for x in read_jsonl(path)]


def write_json(path: str | Path, value: dict | list) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: str | Path, values: Iterable[dict]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for value in values:
            handle.write(json.dumps(value, sort_keys=True) + "\n")

