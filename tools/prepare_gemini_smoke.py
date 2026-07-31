from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


NUMERIC_FACTS = (
    "price_per_share_usd",
    "primary_shares_m",
    "existing_shares_m",
    "debt_usd_m",
    "cash_usd_m",
)
METRICS = (
    "gross_proceeds_usd_m",
    "post_money_equity_value_usd_m",
    "net_debt_usd_m",
    "dilution_pct",
)


def closed_object(properties: dict[str, Any], required: tuple[str, ...]) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


def workflow_schema() -> dict[str, Any]:
    numeric_facts = {key: {"type": "number"} for key in NUMERIC_FACTS}
    metrics = {key: {"type": "number"} for key in METRICS}
    citations = {key: {"type": "string"} for key in NUMERIC_FACTS}

    diligence = closed_object(
        {
            "department": {"type": "string", "enum": ["due_diligence"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "facts": closed_object(numeric_facts, NUMERIC_FACTS),
            "citations": closed_object(citations, NUMERIC_FACTS),
        },
        ("department", "source_version", "scenario_id", "facts", "citations"),
    )
    valuation = closed_object(
        {
            "department": {"type": "string", "enum": ["valuation"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "inputs": closed_object(numeric_facts, NUMERIC_FACTS),
            "outputs": closed_object(metrics, METRICS),
        },
        ("department", "source_version", "scenario_id", "inputs", "outputs"),
    )
    risk = closed_object(
        {
            "department": {"type": "string", "enum": ["risk"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "risk_flags": {"type": "array", "items": {"type": "string"}},
        },
        ("department", "source_version", "scenario_id", "risk_flags"),
    )
    memo = closed_object(
        {
            "department": {"type": "string", "enum": ["ecm_committee"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "headline_metrics": closed_object(metrics, METRICS),
            "top_risks": {"type": "array", "items": {"type": "string"}},
            "citations": {"type": "array", "items": {"type": "string"}},
            "recommendation": {
                "type": "string",
                "enum": ["proceed", "proceed_with_conditions", "do_not_proceed"],
            },
        },
        (
            "department",
            "source_version",
            "scenario_id",
            "headline_metrics",
            "top_risks",
            "citations",
            "recommendation",
        ),
    )
    return closed_object(
        {
            "diligence": diligence,
            "valuation": valuation,
            "risk": risk,
            "memo": memo,
        },
        ("diligence", "valuation", "risk", "memo"),
    )


def build_config(model: str) -> dict[str, Any]:
    if not model.strip():
        raise ValueError("Gemini model identifier is required")
    return {
        "experiment_id": "gemini-ipo-workflow-smoke-v1",
        "cases": ["../data/ipo_real_cases/reddit_2024/spec.json"],
        "conditions": ["generalist"],
        "repetitions": 1,
        "output_root": "../results/provider_smoke",
        "systems": [
            {
                "system_id": f"gemini-{model}",
                "enabled": True,
                "backend": {
                    "type": "openai_compatible",
                    "model_env": "GEMINI_MODEL",
                    "base_url_env": "GEMINI_API_BASE",
                    "api_key_env": "GEMINI_API_KEY",
                    "temperature": 0.0,
                    "max_tokens": 4096,
                    "timeout_seconds": 300,
                    "max_retries": 3,
                    "use_json_response_format": False,
                    "extra_body": {
                        "reasoning_effort": "low",
                        "response_format": {
                            "type": "json_schema",
                            "json_schema": {
                                "name": "ipo_workflow_artifacts",
                                "strict": True,
                                "schema": workflow_schema(),
                            },
                        },
                    },
                },
                "pricing_usd_per_million_tokens": {
                    "input": 0.0,
                    "output": 0.0,
                },
            }
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a secret-free Gemini smoke-test configuration"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("configs/gemini_smoke.local.json"),
    )
    parser.add_argument("--model", default=os.getenv("GEMINI_MODEL", ""))
    args = parser.parse_args()

    config = build_config(args.model.strip())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "config": str(args.output),
                "model": args.model.strip(),
                "planned_calls": 1,
                "secrets_written_to_config": False,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
