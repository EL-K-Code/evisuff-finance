from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from .enterprise_workflow import ARTIFACT_FILES, read_json, score_run, write_json
from .model_backends import ModelBackend, ModelRequest, ModelResponse, backend_from_config

DEPARTMENTS = ("diligence", "valuation", "risk", "memo")
CONDITIONS = ("isolated", "generalist", "multi_agent")


@dataclass(frozen=True)
class CallRecord:
    request_id: str
    department: str | None
    started_at_unix: float
    latency_seconds: float
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    response_sha256: str


def _stable_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _source_packet(spec: dict[str, Any]) -> dict[str, Any]:
    if "source_packet" in spec:
        packet = spec["source_packet"]
        if not isinstance(packet, dict):
            raise ValueError("source_packet must be a JSON object")
        return packet
    return {
        "issuer": spec.get("issuer"),
        "required_source_version": spec["required_source_version"],
        "versions": spec["versions"],
    }


def _schema_for(department: str) -> dict[str, Any]:
    schemas = {
        "diligence": {
            "department": "due_diligence",
            "source_version": "latest filing version id",
            "scenario_id": "shared scenario id",
            "facts": {"required_fact_name": "number"},
            "citations": {"required_fact_name": "DOCUMENT_ID:location"},
        },
        "valuation": {
            "department": "valuation",
            "source_version": "filing version id used",
            "scenario_id": "shared scenario id",
            "inputs": {
                "price_per_share_usd": "number",
                "primary_shares_m": "number",
                "existing_shares_m": "number",
                "debt_usd_m": "number",
                "cash_usd_m": "number",
            },
            "outputs": {
                "gross_proceeds_usd_m": "number",
                "post_money_equity_value_usd_m": "number",
                "net_debt_usd_m": "number",
                "dilution_pct": "number",
            },
        },
        "risk": {
            "department": "risk",
            "source_version": "filing version id used",
            "scenario_id": "shared scenario id",
            "risk_flags": ["material risk identifiers"],
        },
        "memo": {
            "department": "ecm_committee",
            "source_version": "filing version id used",
            "scenario_id": "shared scenario id",
            "headline_metrics": {
                "gross_proceeds_usd_m": "number",
                "post_money_equity_value_usd_m": "number",
                "net_debt_usd_m": "number",
                "dilution_pct": "number",
            },
            "top_risks": ["material risk identifiers"],
            "citations": ["DOCUMENT_ID:location"],
            "recommendation": "proceed | proceed_with_conditions | do_not_proceed",
        },
    }
    return schemas[department]


def _department_instruction(department: str) -> str:
    instructions = {
        "diligence": (
            "Act as the IPO due-diligence department. Extract every required fact "
            "from the most authoritative filing version and attach source-version citations."
        ),
        "valuation": (
            "Act as the valuation department. Use the supplied evidence and handoff, "
            "calculate all requested metrics, and do not silently substitute stale inputs."
        ),
        "risk": (
            "Act as the risk department. Identify every material risk in the latest "
            "authoritative filing and avoid unsupported additions."
        ),
        "memo": (
            "Act as the ECM committee. Reconcile the work of all departments into one "
            "coherent recommendation. Metrics, risks, source version, and citations must agree."
        ),
    }
    return instructions[department]


def _system_prompt() -> str:
    return (
        "You are an auditable financial-workflow agent. Return JSON only. "
        "Never invent missing values. Prefer the latest authoritative filing. "
        "Preserve exact units and source-version identifiers."
    )


def build_department_prompt(
    spec: dict[str, Any],
    department: str,
    *,
    handoffs: dict[str, dict[str, Any]] | None = None,
) -> str:
    payload = {
        "task": _department_instruction(department),
        "workflow_id": spec["workflow_id"],
        "required_source_version": spec["required_source_version"],
        "required_scenario_id": spec["required_scenario_id"],
        "source_packet": _source_packet(spec),
        "upstream_handoffs": handoffs or {},
        "output_schema": _schema_for(department),
    }
    return (
        "Complete this department task. The output must be one JSON object matching "
        "output_schema exactly.\n\n" + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def build_generalist_prompt(spec: dict[str, Any]) -> str:
    payload = {
        "task": (
            "Complete the full IPO workflow as one generalist. Produce all four department "
            "artifacts and reconcile them before returning."
        ),
        "workflow_id": spec["workflow_id"],
        "required_source_version": spec["required_source_version"],
        "required_scenario_id": spec["required_scenario_id"],
        "source_packet": _source_packet(spec),
        "output_schema": {department: _schema_for(department) for department in DEPARTMENTS},
    }
    return (
        "Return one JSON object with exactly the keys diligence, valuation, risk, and memo. "
        "Each value must match its schema.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def _validate_artifact(department: str, artifact: Any) -> dict[str, Any]:
    if not isinstance(artifact, dict):
        raise ValueError(f"{department} output must be a JSON object")
    required = {
        "diligence": {"source_version", "scenario_id", "facts", "citations"},
        "valuation": {"source_version", "scenario_id", "inputs", "outputs"},
        "risk": {"source_version", "scenario_id", "risk_flags"},
        "memo": {
            "source_version",
            "scenario_id",
            "headline_metrics",
            "top_risks",
            "citations",
            "recommendation",
        },
    }[department]
    missing = sorted(required - set(artifact))
    if missing:
        raise ValueError(f"{department} output missing fields: {missing}")
    return artifact


def _call_cost(response: ModelResponse, system_config: dict[str, Any]) -> float:
    pricing = dict(system_config.get("pricing_usd_per_million_tokens", {}))
    input_price = float(pricing.get("input", 0.0))
    output_price = float(pricing.get("output", 0.0))
    return (
        response.input_tokens * input_price
        + response.output_tokens * output_price
    ) / 1_000_000.0


def _invoke(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    department: str | None,
    user_prompt: str,
    repetition: int,
) -> tuple[dict[str, Any], CallRecord, dict[str, Any]]:
    request_id = (
        f"{spec['workflow_id']}::{system_config['system_id']}::{condition}::"
        f"{department or 'all'}::r{repetition}"
    )
    request = ModelRequest(
        request_id=request_id,
        workflow_id=str(spec["workflow_id"]),
        condition=condition,
        department=department,
        system_prompt=_system_prompt(),
        user_prompt=user_prompt,
        metadata={"spec": spec, "repetition": repetition},
    )
    started_at = time.time()
    response = backend.generate(request)
    parsed = response.parsed
    if parsed is None:
        raise ValueError(f"{request_id} returned no parsed JSON")
    record = CallRecord(
        request_id=request_id,
        department=department,
        started_at_unix=started_at,
        latency_seconds=round(response.latency_seconds, 6),
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        estimated_cost_usd=round(_call_cost(response, system_config), 8),
        response_sha256=_sha256_text(response.content),
    )
    raw_summary = {
        "request_id": request_id,
        "backend_raw": response.raw,
        "content": response.content,
    }
    return parsed, record, raw_summary


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def _run_condition(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    repetition: int,
) -> tuple[dict[str, dict[str, Any]], list[CallRecord], list[dict[str, Any]]]:
    calls: list[CallRecord] = []
    raw_rows: list[dict[str, Any]] = []
    artifacts: dict[str, dict[str, Any]] = {}

    if condition == "generalist":
        parsed, record, raw = _invoke(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            department=None,
            user_prompt=build_generalist_prompt(spec),
            repetition=repetition,
        )
        calls.append(record)
        raw_rows.append(raw)
        for department in DEPARTMENTS:
            if department not in parsed:
                raise ValueError(f"Generalist output missing department: {department}")
            artifacts[department] = _validate_artifact(department, parsed[department])
        return artifacts, calls, raw_rows

    for department in DEPARTMENTS:
        handoffs: dict[str, dict[str, Any]] = {}
        if condition == "multi_agent":
            if department == "valuation" and "diligence" in artifacts:
                handoffs = {"diligence": artifacts["diligence"]}
            elif department == "risk" and "diligence" in artifacts:
                handoffs = {"diligence": artifacts["diligence"]}
            elif department == "memo":
                handoffs = dict(artifacts)
        parsed, record, raw = _invoke(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            department=department,
            user_prompt=build_department_prompt(spec, department, handoffs=handoffs),
            repetition=repetition,
        )
        artifacts[department] = _validate_artifact(department, parsed)
        calls.append(record)
        raw_rows.append(raw)
    return artifacts, calls, raw_rows


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def _run_id(system_id: str, condition: str, repetition: int) -> str:
    return f"{system_id}__{condition}__r{repetition:02d}"


def run_one(
    *,
    spec_path: Path,
    output_root: Path,
    system_config: dict[str, Any],
    condition: str,
    repetition: int,
    overwrite: bool = False,
) -> dict[str, Any]:
    if condition not in CONDITIONS:
        raise ValueError(f"Unknown condition: {condition}")
    spec = read_json(spec_path)
    system_id = str(system_config["system_id"])
    run_id = _run_id(system_id, condition, repetition)
    run_dir = output_root / str(spec["workflow_id"]) / run_id
    score_path = run_dir / "score.json"
    if score_path.exists() and not overwrite:
        return read_json(score_path)

    run_dir.mkdir(parents=True, exist_ok=True)
    backend = backend_from_config(dict(system_config["backend"]))
    status = "completed"
    error: str | None = None
    calls: list[CallRecord] = []
    raw_rows: list[dict[str, Any]] = []
    started = time.time()
    try:
        artifacts, calls, raw_rows = _run_condition(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            repetition=repetition,
        )
        for department, artifact in artifacts.items():
            write_json(run_dir / ARTIFACT_FILES[department], artifact)
        report = score_run(spec_path, run_dir).to_dict()
        report["system_id"] = system_id
        report["result_type"] = (
            "deterministic_control_not_model_results"
            if str(system_config["backend"].get("type")) == "deterministic_control"
            else "model_workflow_result_requires_verifier_and_human_review"
        )
    except Exception as exc:  # noqa: BLE001 - preserve failed experiment runs
        status = "failed"
        error = f"{type(exc).__name__}: {exc}"
        report = {
            "result_type": "failed_workflow_run",
            "workflow_id": str(spec["workflow_id"]),
            "system_id": system_id,
            "component_score": 0.0,
            "coordination_score": 0.0,
            "workflow_score": 0.0,
            "composition_gap": 0.0,
            "enterprise_success": False,
            "artifact_scores": {},
            "error": error,
        }

    total_cost = sum(call.estimated_cost_usd for call in calls)
    total_input = sum(call.input_tokens for call in calls)
    total_output = sum(call.output_tokens for call in calls)
    metadata = {
        "experiment_run_id": run_id,
        "workflow_id": str(spec["workflow_id"]),
        "system_id": system_id,
        "condition": condition,
        "repetition": repetition,
        "status": status,
        "error": error,
        "started_at_unix": started,
        "completed_at_unix": time.time(),
        "calls": [asdict(call) for call in calls],
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "estimated_cost_usd": round(total_cost, 8),
        "spec_sha256": _sha256_text(_stable_json(spec)),
        "system_config": {
            "system_id": system_id,
            "backend_type": system_config["backend"].get("type"),
            "model": system_config["backend"].get("model"),
        },
    }
    report.update(
        {
            "experiment_run_id": run_id,
            "condition": condition,
            "repetition": repetition,
            "status": status,
            "estimated_cost_usd": round(total_cost, 8),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
        }
    )
    write_json(run_dir / "run_metadata.json", metadata)
    write_json(score_path, report)
    _write_jsonl(run_dir / "trajectory.jsonl", raw_rows)
    return report


def _aggregate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for report in reports:
        key = (str(report["system_id"]), str(report["condition"]))
        groups.setdefault(key, []).append(report)
    rows = []
    for (system_id, condition), items in sorted(groups.items()):
        completed = [item for item in items if item.get("status") == "completed"]
        denominator = len(items)
        rows.append(
            {
                "system_id": system_id,
                "condition": condition,
                "runs": denominator,
                "completed_runs": len(completed),
                "workflow_score_mean": round(
                    mean(float(item["workflow_score"]) for item in completed), 6
                )
                if completed
                else 0.0,
                "component_score_mean": round(
                    mean(float(item["component_score"]) for item in completed), 6
                )
                if completed
                else 0.0,
                "coordination_score_mean": round(
                    mean(float(item["coordination_score"]) for item in completed), 6
                )
                if completed
                else 0.0,
                "composition_gap_mean": round(
                    mean(float(item["composition_gap"]) for item in completed), 6
                )
                if completed
                else 0.0,
                "enterprise_success_rate": round(
                    sum(bool(item["enterprise_success"]) for item in completed) / denominator,
                    6,
                )
                if denominator
                else 0.0,
                "estimated_cost_usd": round(
                    sum(float(item.get("estimated_cost_usd", 0.0)) for item in items),
                    8,
                ),
                "input_tokens": sum(int(item.get("total_input_tokens", 0)) for item in items),
                "output_tokens": sum(int(item.get("total_output_tokens", 0)) for item in items),
            }
        )
    return {"groups": rows}


def run_experiment(
    config_path: Path,
    *,
    output_override: Path | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    config = read_json(config_path)
    base = config_path.parent.resolve()
    output_root = (
        output_override.resolve()
        if output_override is not None
        else _resolve_path(base, config.get("output_root", "../results/empirical"))
    )
    cases = [_resolve_path(base, item) for item in config["cases"]]
    conditions = [str(item) for item in config.get("conditions", CONDITIONS)]
    repetitions = int(config.get("repetitions", 1))
    systems = [dict(item) for item in config["systems"] if item.get("enabled", True)]

    reports: list[dict[str, Any]] = []
    for spec_path in cases:
        for system_config in systems:
            for condition in conditions:
                for repetition in range(repetitions):
                    reports.append(
                        run_one(
                            spec_path=spec_path,
                            output_root=output_root,
                            system_config=system_config,
                            condition=condition,
                            repetition=repetition,
                            overwrite=overwrite,
                        )
                    )

    summary = {
        "result_type": (
            "experiment_summary_may_include_deterministic_controls_and_model_results"
        ),
        "experiment_id": str(config["experiment_id"]),
        "config_path": str(config_path),
        "output_root": str(output_root),
        "cases": [str(path) for path in cases],
        "conditions": conditions,
        "repetitions": repetitions,
        "reports": reports,
        **_aggregate(reports),
    }
    write_json(output_root / "experiment_summary.json", summary)
    return summary
