from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from evisuff.experiment_cli import load_env_file

PROVIDERS = (
    {
        "name": "qwen",
        "enable_env": "ENABLE_QWEN",
        "api_key_env": "QWEN_API_KEY",
        "base_url_env": "QWEN_API_BASE",
        "model_env": "QWEN_MODEL",
        "auth": "bearer",
    },
    {
        "name": "kimi",
        "enable_env": "ENABLE_KIMI",
        "api_key_env": "KIMI_API_KEY",
        "base_url_env": "KIMI_API_BASE",
        "model_env": "KIMI_MODEL",
        "auth": "bearer",
    },
    {
        "name": "openai",
        "enable_env": "ENABLE_OPENAI",
        "api_key_env": "OPENAI_API_KEY",
        "base_url_env": "OPENAI_API_BASE",
        "model_env": "OPENAI_MODEL",
        "auth": "bearer",
    },
    {
        "name": "anthropic",
        "enable_env": "ENABLE_ANTHROPIC",
        "api_key_env": "ANTHROPIC_API_KEY",
        "base_url_env": "ANTHROPIC_API_BASE",
        "model_env": "ANTHROPIC_MODEL",
        "auth": "anthropic",
    },
)


def _enabled(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in {"1", "true", "yes", "on"}


def _models_endpoint(base_url: str) -> str:
    value = base_url.rstrip("/")
    return value if value.endswith("/models") else f"{value}/models"


def fetch_model_ids(
    *,
    base_url: str,
    api_key: str,
    auth: str,
    timeout_seconds: int = 30,
) -> list[str]:
    if auth == "anthropic":
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "accept": "application/json",
        }
    else:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "accept": "application/json",
        }
    request = urllib.request.Request(
        _models_endpoint(base_url), headers=headers, method="GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("model-list response must be a JSON object")
    rows: Any = payload.get("data", payload.get("models", []))
    if not isinstance(rows, list):
        raise ValueError("model-list response has no data/models list")
    model_ids: list[str] = []
    for row in rows:
        if isinstance(row, str):
            model_ids.append(row)
        elif isinstance(row, dict):
            value = row.get("id", row.get("name"))
            if isinstance(value, str) and value:
                model_ids.append(value)
    return sorted(set(model_ids))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Best-effort listing of model IDs available to enabled providers"
    )
    parser.add_argument("--env", type=Path, default=Path(".env"))
    parser.add_argument("--provider", choices=[item["name"] for item in PROVIDERS])
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    load_env_file(args.env)

    selected = [
        item
        for item in PROVIDERS
        if (args.provider is None or item["name"] == args.provider)
        and _enabled(str(item["enable_env"]))
    ]
    if not selected:
        raise SystemExit("No matching provider is enabled in .env")

    results: list[dict[str, Any]] = []
    for provider in selected:
        name = str(provider["name"])
        base_url = os.getenv(str(provider["base_url_env"]), "").strip()
        api_key = os.getenv(str(provider["api_key_env"]), "").strip()
        configured_model = os.getenv(str(provider["model_env"]), "").strip()
        result: dict[str, Any] = {
            "provider": name,
            "configured_model": configured_model or None,
            "endpoint": _models_endpoint(base_url) if base_url else None,
            "models": [],
            "error": None,
        }
        if not base_url or not api_key or api_key.startswith("REPLACE_"):
            result["error"] = "Set a real API key and base URL in .env first"
        else:
            try:
                result["models"] = fetch_model_ids(
                    base_url=base_url,
                    api_key=api_key,
                    auth=str(provider["auth"]),
                    timeout_seconds=args.timeout_seconds,
                )
            except (RuntimeError, ValueError) as exc:
                result["error"] = str(exc)
        results.append(result)

    print(
        json.dumps(
            {
                "result_type": "provider_model_discovery_not_experiment_results",
                "providers": results,
                "api_keys_printed": False,
                "note": (
                    "Model-list support varies by provider and account. If a provider "
                    "returns an error, copy the exact model ID from its official console."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
