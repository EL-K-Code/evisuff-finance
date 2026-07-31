from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"
FALLBACK_MODELS = (
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
)
EXCLUDED_TERMS = ("image", "tts", "audio", "live")


def fetch_models(base_url: str, api_key: str, timeout_seconds: int = 60) -> list[str]:
    endpoint = f"{base_url.rstrip('/')}/models"
    request = urllib.request.Request(
        endpoint,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini model discovery returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Gemini model discovery failed: {exc}") from exc

    rows = payload.get("data", payload.get("models", [])) if isinstance(payload, dict) else []
    available: list[str] = []
    for item in rows if isinstance(rows, list) else []:
        if not isinstance(item, dict):
            continue
        value = item.get("id", item.get("name"))
        if isinstance(value, str) and value:
            available.append(value.removeprefix("models/"))
    return sorted(set(available))


def select_model(available: list[str], preferred: str = "") -> str:
    normalized = preferred.strip().removeprefix("models/")
    priorities = (normalized, *FALLBACK_MODELS)
    for model in priorities:
        if model and model in available:
            return model
    for model in available:
        if (
            model.startswith("gemini-")
            and "flash" in model
            and all(term not in model for term in EXCLUDED_TERMS)
        ):
            return model
    preview = ", ".join(available[:20]) or "<empty model list>"
    raise ValueError(f"No compatible Gemini Flash model found. Available IDs: {preview}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Select an available Gemini Flash model")
    parser.add_argument("--preferred", default="")
    parser.add_argument(
        "--base-url",
        default=os.getenv("GEMINI_API_BASE", DEFAULT_BASE_URL),
    )
    parser.add_argument("--timeout-seconds", type=int, default=60)
    args = parser.parse_args()

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("GEMINI_API_KEY is not set")
    try:
        available = fetch_models(args.base_url, api_key, args.timeout_seconds)
        print(select_model(available, args.preferred))
    except (RuntimeError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
