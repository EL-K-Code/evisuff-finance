from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .enterprise_workflow import financial_metrics


@dataclass(frozen=True)
class ModelRequest:
    request_id: str
    workflow_id: str
    condition: str
    department: str | None
    system_prompt: str
    user_prompt: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class ModelResponse:
    content: str
    parsed: dict[str, Any] | None
    input_tokens: int
    output_tokens: int
    latency_seconds: float
    raw: dict[str, Any]


class ModelBackend(Protocol):
    def generate(self, request: ModelRequest) -> ModelResponse:
        ...


def parse_json_content(content: str) -> dict[str, Any]:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("Model response must be a JSON object")
    return payload


class OpenAICompatibleBackend:
    """Minimal dependency-free backend for OpenAI-compatible chat APIs."""

    def __init__(
        self,
        *,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: int = 180,
        temperature: float = 0.0,
        max_tokens: int = 4096,
        extra_headers: dict[str, str] | None = None,
        use_json_response_format: bool = True,
        max_retries: int = 3,
        retry_backoff_seconds: float = 2.0,
        extra_body: dict[str, Any] | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_headers = dict(extra_headers or {})
        self.use_json_response_format = use_json_response_format
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds
        self.extra_body = dict(extra_body or {})

    def generate(self, request: ModelRequest) -> ModelResponse:
        endpoint = self.base_url
        if not endpoint.endswith("/chat/completions"):
            endpoint = f"{endpoint}/chat/completions"
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            **self.extra_body,
        }
        if self.use_json_response_format:
            body["response_format"] = {"type": "json_object"}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            **self.extra_headers,
        }
        http_request = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        started = time.perf_counter()
        raw: dict[str, Any] | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urllib.request.urlopen(
                    http_request, timeout=self.timeout_seconds
                ) as response:
                    loaded = json.loads(response.read().decode("utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError("Model API response must be a JSON object")
                raw = loaded
                break
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                retryable = exc.code == 429 or exc.code >= 500
                if not retryable or attempt >= self.max_retries:
                    raise RuntimeError(
                        f"Model API returned HTTP {exc.code}: {detail}"
                    ) from exc
                time.sleep(self.retry_backoff_seconds * (2**attempt))
            except urllib.error.URLError as exc:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"Model API request failed: {exc}") from exc
                time.sleep(self.retry_backoff_seconds * (2**attempt))
        if raw is None:
            raise RuntimeError("Model API failed without a response")
        latency = time.perf_counter() - started
        choices = raw.get("choices", [])
        if not choices:
            raise ValueError("Model API response has no choices")
        content = choices[0].get("message", {}).get("content", "")
        if isinstance(content, list):
            content = "".join(
                str(part.get("text", "")) if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Model API response has empty content")
        usage = raw.get("usage", {}) or {}
        parsed = parse_json_content(content)
        return ModelResponse(
            content=content,
            parsed=parsed,
            input_tokens=int(usage.get("prompt_tokens", 0) or 0),
            output_tokens=int(usage.get("completion_tokens", 0) or 0),
            latency_seconds=latency,
            raw=raw,
        )


class CommandBackend:
    """Run a local model or harness command that accepts JSON on stdin."""

    def __init__(self, command: list[str], timeout_seconds: int = 600) -> None:
        if not command:
            raise ValueError("command backend requires a non-empty command")
        self.command = command
        self.timeout_seconds = timeout_seconds

    def generate(self, request: ModelRequest) -> ModelResponse:
        # The runner keeps the full benchmark spec in private metadata for offline
        # deterministic controls. Never expose that spec to an evaluated command,
        # because it contains the gold facts and risk labels.
        safe_metadata = {
            key: value for key, value in request.metadata.items() if key != "spec"
        }
        payload = {
            "request_id": request.request_id,
            "workflow_id": request.workflow_id,
            "condition": request.condition,
            "department": request.department,
            "system_prompt": request.system_prompt,
            "user_prompt": request.user_prompt,
            "metadata": safe_metadata,
        }
        started = time.perf_counter()
        completed = subprocess.run(
            self.command,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        latency = time.perf_counter() - started
        if completed.returncode != 0:
            raise RuntimeError(
                f"Command backend failed with code {completed.returncode}: "
                f"{completed.stderr.strip()}"
            )
        envelope = json.loads(completed.stdout)
        if not isinstance(envelope, dict):
            raise ValueError("Command backend must emit a JSON object")
        content = envelope.get("content")
        parsed = envelope.get("parsed")
        if parsed is None and isinstance(content, str):
            parsed = parse_json_content(content)
        if parsed is not None and not isinstance(parsed, dict):
            raise ValueError("Command backend parsed output must be a JSON object")
        if content is None and parsed is not None:
            content = json.dumps(parsed)
        if not isinstance(content, str):
            raise ValueError("Command backend must emit content or parsed")
        return ModelResponse(
            content=content,
            parsed=parsed,
            input_tokens=int(envelope.get("input_tokens", 0) or 0),
            output_tokens=int(envelope.get("output_tokens", 0) or 0),
            latency_seconds=latency,
            raw=envelope,
        )


class DeterministicControlBackend:
    """Offline controls for CI. Never report these outputs as model results."""

    def __init__(self, mode: str = "oracle") -> None:
        if mode not in {"oracle", "stale_silo", "partial_handoff"}:
            raise ValueError(f"Unknown deterministic mode: {mode}")
        self.mode = mode

    def _version_for(self, department: str) -> str:
        if self.mode == "stale_silo" and department in {"valuation", "memo"}:
            return "v1"
        return "v2"

    def _artifact(self, spec: dict[str, Any], department: str) -> dict[str, Any]:
        version_id = self._version_for(department)
        version = spec["versions"][version_id]
        scenario = spec["required_scenario_id"]
        facts = version["facts"]
        document_id = version["document_id"]
        if department == "diligence":
            return {
                "department": "due_diligence",
                "source_version": version_id,
                "scenario_id": scenario,
                "facts": dict(facts),
                "citations": {
                    key: f"{document_id}:fact:{key}" for key in facts
                },
            }
        if department == "valuation":
            keys = (
                "price_per_share_usd",
                "primary_shares_m",
                "existing_shares_m",
                "debt_usd_m",
                "cash_usd_m",
            )
            return {
                "department": "valuation",
                "source_version": version_id,
                "scenario_id": scenario,
                "inputs": {key: facts[key] for key in keys},
                "outputs": financial_metrics(facts),
            }
        if department == "risk":
            risk_flags = list(version["risk_flags"])
            if self.mode == "partial_handoff" and risk_flags:
                risk_flags = risk_flags[:-1]
            return {
                "department": "risk",
                "source_version": version_id,
                "scenario_id": scenario,
                "risk_flags": risk_flags,
            }
        if department == "memo":
            risks = list(version["risk_flags"])
            if self.mode == "partial_handoff" and risks:
                risks = risks[:-1]
            citation_document = (
                spec["versions"]["v1"]["document_id"]
                if self.mode == "partial_handoff"
                else document_id
            )
            return {
                "department": "ecm_committee",
                "source_version": version_id,
                "scenario_id": scenario,
                "headline_metrics": financial_metrics(facts),
                "top_risks": risks,
                "citations": [
                    f"{citation_document}:summary:offering",
                    f"{citation_document}:summary:risks",
                ],
                "recommendation": "proceed_with_conditions",
            }
        raise ValueError(f"Unknown department: {department}")

    def generate(self, request: ModelRequest) -> ModelResponse:
        started = time.perf_counter()
        spec = request.metadata["spec"]
        if request.department is None:
            parsed = {
                key: self._artifact(spec, key)
                for key in ("diligence", "valuation", "risk", "memo")
            }
        else:
            parsed = self._artifact(spec, request.department)
        content = json.dumps(parsed)
        return ModelResponse(
            content=content,
            parsed=parsed,
            input_tokens=0,
            output_tokens=0,
            latency_seconds=time.perf_counter() - started,
            raw={"deterministic_control": self.mode},
        )


def backend_from_config(config: dict[str, Any]) -> ModelBackend:
    backend_type = str(config.get("type", ""))
    if backend_type == "openai_compatible":
        api_key_env = str(config.get("api_key_env", ""))
        base_url_env = str(config.get("base_url_env", ""))
        api_key = os.getenv(api_key_env) if api_key_env else config.get("api_key")
        base_url = os.getenv(base_url_env) if base_url_env else config.get("base_url")
        if not api_key:
            raise RuntimeError(f"Missing API key; set {api_key_env or 'api_key'}")
        if not base_url:
            raise RuntimeError(f"Missing base URL; set {base_url_env or 'base_url'}")
        return OpenAICompatibleBackend(
            model=str(config["model"]),
            base_url=str(base_url),
            api_key=str(api_key),
            timeout_seconds=int(config.get("timeout_seconds", 180)),
            temperature=float(config.get("temperature", 0.0)),
            max_tokens=int(config.get("max_tokens", 4096)),
            extra_headers={
                str(key): str(value)
                for key, value in dict(config.get("extra_headers", {})).items()
            },
            use_json_response_format=bool(
                config.get("use_json_response_format", True)
            ),
            max_retries=int(config.get("max_retries", 3)),
            retry_backoff_seconds=float(config.get("retry_backoff_seconds", 2.0)),
            extra_body=dict(config.get("extra_body", {})),
        )
    if backend_type == "command":
        return CommandBackend(
            [str(item) for item in config.get("command", [])],
            timeout_seconds=int(config.get("timeout_seconds", 600)),
        )
    if backend_type == "deterministic_control":
        return DeterministicControlBackend(str(config.get("mode", "oracle")))
    raise ValueError(f"Unsupported backend type: {backend_type}")
