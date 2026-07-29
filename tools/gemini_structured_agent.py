from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

FACT_FIELDS = (
    "price_per_share_usd",
    "primary_shares_m",
    "existing_shares_m",
    "debt_usd_m",
    "cash_usd_m",
)
METRIC_FIELDS = (
    "gross_proceeds_usd_m",
    "post_money_equity_value_usd_m",
    "net_debt_usd_m",
    "dilution_pct",
)
DEPARTMENTS = ("diligence", "valuation", "risk", "memo")


def closed_object(
    properties: dict[str, Any], required: tuple[str, ...] | list[str]
) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": list(required),
        "additionalProperties": False,
    }


def department_schemas() -> dict[str, dict[str, Any]]:
    numeric_facts = {key: {"type": "number"} for key in FACT_FIELDS}
    metrics = {key: {"type": "number"} for key in METRIC_FIELDS}
    citations = {key: {"type": "string"} for key in FACT_FIELDS}

    diligence = closed_object(
        {
            "department": {"type": "string", "enum": ["due_diligence"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "facts": closed_object(numeric_facts, FACT_FIELDS),
            "citations": closed_object(citations, FACT_FIELDS),
        },
        ("department", "source_version", "scenario_id", "facts", "citations"),
    )
    valuation = closed_object(
        {
            "department": {"type": "string", "enum": ["valuation"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "inputs": closed_object(numeric_facts, FACT_FIELDS),
            "outputs": closed_object(metrics, METRIC_FIELDS),
        },
        ("department", "source_version", "scenario_id", "inputs", "outputs"),
    )
    risk = closed_object(
        {
            "department": {"type": "string", "enum": ["risk"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "risk_flags": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        ("department", "source_version", "scenario_id", "risk_flags"),
    )
    memo = closed_object(
        {
            "department": {"type": "string", "enum": ["ecm_committee"]},
            "source_version": {"type": "string"},
            "scenario_id": {"type": "string"},
            "headline_metrics": closed_object(metrics, METRIC_FIELDS),
            "top_risks": {
                "type": "array",
                "items": {"type": "string"},
            },
            "citations": {
                "type": "array",
                "items": {"type": "string"},
            },
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
    return {
        "diligence": diligence,
        "valuation": valuation,
        "risk": risk,
        "memo": memo,
    }


def response_schema(department: str | None) -> dict[str, Any]:
    schemas = department_schemas()
    if department is None:
        return closed_object(
            {name: schemas[name] for name in DEPARTMENTS},
            DEPARTMENTS,
        )
    if department not in schemas:
        raise ValueError(f"Unsupported department: {department}")
    return schemas[department]


def response_format(department: str | None) -> dict[str, Any]:
    name = "ipo_workflow_artifacts" if department is None else f"ipo_{department}_artifact"
    return {
        "type": "json_schema",
        "json_schema": {
            "name": name,
            "strict": True,
            "schema": response_schema(department),
        },
    }


def _request_json(
    endpoint: str,
    headers: dict[str, str],
    body: dict[str, Any],
    *,
    timeout_seconds: int = 300,
    max_retries: int = 5,
    retry_backoff_seconds: float = 3.0,
) -> dict[str, Any]:
    encoded = json.dumps(body).encode("utf-8")
    started = time.perf_counter()
    for attempt in range(max_retries + 1):
        request = urllib.request.Request(
            endpoint,
            data=encoded,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Gemini API response must be a JSON object")
            payload["_latency_seconds"] = time.perf_counter() - started
            return payload
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt >= max_retries:
                raise RuntimeError(f"Gemini API returned HTTP {exc.code}: {detail}") from exc
            time.sleep(retry_backoff_seconds * (2**attempt))
        except urllib.error.URLError as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"Gemini API request failed: {exc}") from exc
            time.sleep(retry_backoff_seconds * (2**attempt))
    raise RuntimeError("Gemini API failed without a response")


def _extract_content(raw: dict[str, Any]) -> str:
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise ValueError("Gemini response has no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("Gemini response choice must be an object")
    message = first.get("message", {})
    if not isinstance(message, dict):
        raise ValueError("Gemini response message must be an object")
    content: Any = message.get("content", "")
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part)
            for part in content
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Gemini response has empty content")
    return content


def run_agent(request_payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "").strip().removeprefix("models/")
    base_url = os.getenv(
        "GEMINI_API_BASE",
        "https://generativelanguage.googleapis.com/v1beta/openai",
    ).rstrip("/")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")
    if not model:
        raise RuntimeError("Missing GEMINI_MODEL")

    department_value = request_payload.get("department")
    department = str(department_value) if department_value is not None else None
    system_prompt = request_payload.get("system_prompt")
    user_prompt = request_payload.get("user_prompt")
    if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
        raise ValueError("Command request must contain string prompts")

    raw = _request_json(
        f"{base_url}/chat/completions",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "max_tokens": 4096,
            "reasoning_effort": "low",
            "response_format": response_format(department),
        },
    )
    content = _extract_content(raw)
    parsed = json.loads(content)
    if not isinstance(parsed, dict):
        raise ValueError("Gemini structured response must be a JSON object")

    usage = raw.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    choices = raw.get("choices", [])
    finish_reason = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason")
    return {
        "content": content,
        "parsed": parsed,
        "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "output_tokens": int(usage.get("completion_tokens", 0) or 0),
        "provider_metadata": {
            "model": raw.get("model", model),
            "response_id": raw.get("id"),
            "finish_reason": finish_reason,
            "latency_seconds": round(float(raw.get("_latency_seconds", 0.0)), 6),
            "department_schema": department or "generalist",
        },
    }


def self_test() -> None:
    schemas = department_schemas()
    assert set(schemas) == set(DEPARTMENTS)
    assert set(response_schema(None)["required"]) == set(DEPARTMENTS)
    for name, schema in schemas.items():
        assert schema["additionalProperties"] is False
        assert schema["type"] == "object"
        assert response_format(name)["json_schema"]["strict"] is True


def main() -> None:
    parser = argparse.ArgumentParser(description="Gemini structured-output command agent")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("Gemini structured-agent schema self-test passed.")
        return

    try:
        request_payload = json.load(sys.stdin)
        if not isinstance(request_payload, dict):
            raise ValueError("Command input must be a JSON object")
        result = run_agent(request_payload)
        json.dump(result, sys.stdout, ensure_ascii=False)
        sys.stdout.write("\n")
    except Exception as exc:  # noqa: BLE001 - command backend reports stderr safely
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
