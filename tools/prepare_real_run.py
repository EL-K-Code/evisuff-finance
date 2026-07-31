from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

PROVIDERS = (
    {
        "name": "qwen",
        "backend_type": "openai_compatible",
        "enable_env": "ENABLE_QWEN",
        "api_key_env": "QWEN_API_KEY",
        "base_url_env": "QWEN_API_BASE",
        "model_env": "QWEN_MODEL",
        "input_price_env": "QWEN_INPUT_PRICE_USD_PER_MTOK",
        "output_price_env": "QWEN_OUTPUT_PRICE_USD_PER_MTOK",
    },
    {
        "name": "kimi",
        "backend_type": "openai_compatible",
        "enable_env": "ENABLE_KIMI",
        "api_key_env": "KIMI_API_KEY",
        "base_url_env": "KIMI_API_BASE",
        "model_env": "KIMI_MODEL",
        "input_price_env": "KIMI_INPUT_PRICE_USD_PER_MTOK",
        "output_price_env": "KIMI_OUTPUT_PRICE_USD_PER_MTOK",
    },
    {
        "name": "openai",
        "backend_type": "openai_compatible",
        "enable_env": "ENABLE_OPENAI",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_API_BASE",
        "model_env": "OPENAI_MODEL",
        "input_price_env": "OPENAI_INPUT_PRICE_USD_PER_MTOK",
        "output_price_env": "OPENAI_OUTPUT_PRICE_USD_PER_MTOK",
    },
    {
        "name": "anthropic",
        "backend_type": "anthropic",
        "enable_env": "ENABLE_ANTHROPIC",
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url_env": "ANTHROPIC_API_BASE",
        "model_env": "ANTHROPIC_MODEL",
        "input_price_env": "ANTHROPIC_INPUT_PRICE_USD_PER_MTOK",
        "output_price_env": "ANTHROPIC_OUTPUT_PRICE_USD_PER_MTOK",
    },
)
CASES = (
    "../data/ipo_real_cases/reddit_2024/spec.json",
    "../data/ipo_real_cases/rubrik_2024/spec.json",
    "../data/ipo_real_cases/coreweave_2025/spec.json",
)
CONDITIONS = ("isolated", "generalist", "multi_agent")
CALLS_PER_CASE = 4 + 1 + 4


def load_env(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Copy sample.env to .env and fill the enabled providers."
        )
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Invalid .env line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        if not key:
            raise ValueError(f"Invalid .env line {line_number}: empty key")
        os.environ.setdefault(key, value)


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("REPLACE_"):
        raise ValueError(f"Missing or placeholder value for {name}")
    return value


def _price(name: str) -> float:
    value = os.getenv(name, "0").strip() or "0"
    parsed = float(value)
    if parsed < 0:
        raise ValueError(f"{name} must be non-negative")
    return parsed


def build_config(repetitions: int) -> tuple[dict[str, Any], list[str]]:
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    systems: list[dict[str, Any]] = []
    warnings: list[str] = []
    for provider in PROVIDERS:
        if not _enabled(str(provider["enable_env"])):
            continue
        model = _required(str(provider["model_env"]))
        _required(str(provider["api_key_env"]))
        _required(str(provider["base_url_env"]))
        input_price = _price(str(provider["input_price_env"]))
        output_price = _price(str(provider["output_price_env"]))
        if input_price == 0 or output_price == 0:
            warnings.append(
                f"{provider['name']}: token pricing is zero; cost estimates will be incomplete"
            )
        backend: dict[str, Any] = {
            "type": provider["backend_type"],
            "model_env": provider["model_env"],
            "base_url_env": provider["base_url_env"],
            "api_key_env": provider["api_key_env"],
            "temperature": 0.0,
            "max_tokens": 4096,
            "timeout_seconds": 300,
            "max_retries": 3,
        }
        if provider["backend_type"] == "openai_compatible":
            backend["use_json_response_format"] = True
        systems.append(
            {
                "system_id": f"{provider['name']}::{model}",
                "enabled": True,
                "backend": backend,
                "pricing_usd_per_million_tokens": {
                    "input": input_price,
                    "output": output_price,
                },
            }
        )
    if not systems:
        raise ValueError("No provider enabled in .env")
    config = {
        "experiment_id": "ipo-workflow-frontier-models-v1",
        "cases": list(CASES),
        "conditions": list(CONDITIONS),
        "repetitions": repetitions,
        "output_root": "../results/ipo_empirical",
        "systems": systems,
    }
    return config, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a secret-free local configuration for the real IPO experiment"
    )
    parser.add_argument("--env", type=Path, default=Path(".env"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("configs/ipo_empirical.local.json"),
    )
    parser.add_argument("--repetitions", type=int)
    args = parser.parse_args()
    load_env(args.env)
    repetitions = args.repetitions or int(os.getenv("EVISUFF_REPETITIONS", "3"))
    config, warnings = build_config(repetitions)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    systems = len(config["systems"])
    calls_per_system = len(CASES) * repetitions * CALLS_PER_CASE
    summary = {
        "config": str(args.output),
        "systems": [item["system_id"] for item in config["systems"]],
        "cases": len(CASES),
        "conditions": list(CONDITIONS),
        "repetitions": repetitions,
        "calls_per_system": calls_per_system,
        "planned_calls_total": systems * calls_per_system,
        "warnings": warnings,
        "secrets_written_to_config": False,
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
