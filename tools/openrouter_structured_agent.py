from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from typing import Any

try:
    from tools.gemini_structured_agent import response_format, response_schema
except ModuleNotFoundError:  # Direct execution from tools/
    from gemini_structured_agent import response_format, response_schema


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
                raise ValueError("OpenRouter response must be a JSON object")
            payload["_latency_seconds"] = time.perf_counter() - started
            return payload
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            retryable = exc.code == 429 or exc.code >= 500
            if not retryable or attempt >= max_retries:
                raise RuntimeError(
                    f"OpenRouter API returned HTTP {exc.code}: {detail}"
                ) from exc
            time.sleep(retry_backoff_seconds * (2**attempt))
        except urllib.error.URLError as exc:
            if attempt >= max_retries:
                raise RuntimeError(f"OpenRouter API request failed: {exc}") from exc
            time.sleep(retry_backoff_seconds * (2**attempt))
    raise RuntimeError("OpenRouter API failed without a response")


def _extract_content(raw: dict[str, Any]) -> str:
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        raise ValueError("OpenRouter response has no choices")
    first = choices[0]
    if not isinstance(first, dict):
        raise ValueError("OpenRouter response choice must be an object")
    message = first.get("message", {})
    if not isinstance(message, dict):
        raise ValueError("OpenRouter response message must be an object")
    content: Any = message.get("content", "")
    if isinstance(content, list):
        content = "".join(
            str(part.get("text", "")) if isinstance(part, dict) else str(part)
            for part in content
        )
    if not isinstance(content, str) or not content.strip():
        raise ValueError("OpenRouter response has empty content")
    return content


def _candidate_texts(content: str) -> list[str]:
    text = content.strip()
    candidates = [text]

    harmony_marker = "<|channel|>final<|message|>"
    if harmony_marker in text:
        candidates.insert(0, text.split(harmony_marker, 1)[1].strip())

    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates.extend(block.strip() for block in fenced if block.strip())

    decoder = json.JSONDecoder()
    for source in list(candidates):
        for match in re.finditer(r"\{", source):
            try:
                _, end = decoder.raw_decode(source[match.start() :])
            except json.JSONDecodeError:
                continue
            candidates.append(source[match.start() : match.start() + end])

    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = candidate.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(normalized)
    return unique


def _parse_structured_content(content: str, department: str | None) -> dict[str, Any]:
    expected_keys = set(response_schema(department)["required"])
    parse_errors: list[str] = []
    for candidate in _candidate_texts(content):
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            parse_errors.append(str(exc))
            continue
        if not isinstance(parsed, dict):
            continue
        if expected_keys.issubset(parsed):
            return parsed
    detail = parse_errors[-1] if parse_errors else "no JSON object candidate found"
    raise ValueError(f"OpenRouter response did not contain the required JSON object: {detail}")


def _retry_budget() -> int:
    raw = os.getenv("OPENROUTER_MAX_RETRIES", "5").strip()
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError("OPENROUTER_MAX_RETRIES must be an integer") from exc
    if value < 0 or value > 10:
        raise ValueError("OPENROUTER_MAX_RETRIES must be between 0 and 10")
    return value


def run_agent(request_payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    model = os.getenv(
        "OPENROUTER_MODEL", "openai/gpt-oss-20b:free"
    ).strip()
    base_url = os.getenv(
        "OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"
    ).rstrip("/")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY")
    if not model:
        raise RuntimeError("Missing OPENROUTER_MODEL")
    max_retries = _retry_budget()

    department_value = request_payload.get("department")
    department = str(department_value) if department_value is not None else None
    system_prompt = request_payload.get("system_prompt")
    user_prompt = request_payload.get("user_prompt")
    if not isinstance(system_prompt, str) or not isinstance(user_prompt, str):
        raise ValueError("Command request must contain string prompts")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": os.getenv(
            "OPENROUTER_HTTP_REFERER", "https://github.com/EL-K-Code/evisuff-finance"
        ),
        "X-Title": os.getenv("OPENROUTER_APP_TITLE", "EviSuff Finance"),
    }
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.0,
        "max_tokens": 4096,
        "response_format": response_format(department),
        "provider": {
            "require_parameters": True,
            "allow_fallbacks": True,
        },
    }
    raw = _request_json(
        f"{base_url}/chat/completions",
        headers,
        body,
        max_retries=max_retries,
    )
    content = _extract_content(raw)
    parsed = _parse_structured_content(content, department)

    usage = raw.get("usage", {})
    if not isinstance(usage, dict):
        usage = {}
    choices = raw.get("choices", [])
    finish_reason = None
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        finish_reason = choices[0].get("finish_reason")
    return {
        "content": json.dumps(parsed, ensure_ascii=False),
        "parsed": parsed,
        "input_tokens": int(usage.get("prompt_tokens", 0) or 0),
        "output_tokens": int(usage.get("completion_tokens", 0) or 0),
        "provider_metadata": {
            "provider": "openrouter",
            "requested_model": model,
            "model": raw.get("model", model),
            "response_id": raw.get("id"),
            "finish_reason": finish_reason,
            "latency_seconds": round(float(raw.get("_latency_seconds", 0.0)), 6),
            "department_schema": department or "generalist",
            "max_retries": max_retries,
        },
    }


def self_test() -> None:
    assert response_format(None)["type"] == "json_schema"
    assert response_format("risk")["json_schema"]["strict"] is True
    sample = {
        "department": "risk",
        "source_version": "v2",
        "scenario_id": "base_case",
        "risk_flags": ["example"],
    }
    fenced = "```json\n" + json.dumps(sample) + "\n```"
    assert _parse_structured_content(fenced, "risk") == sample


def main() -> None:
    parser = argparse.ArgumentParser(
        description="OpenRouter structured-output command agent"
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print("OpenRouter structured-agent schema self-test passed.")
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
