from __future__ import annotations

import copy
import json
import time
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from tempfile import TemporaryDirectory
from typing import Any

from .enterprise_workflow import ARTIFACT_FILES, financial_metrics, read_json, score_run, write_json
from .experiment_runner import (
    DEPARTMENTS,
    CallRecord,
    _call_cost,
    _schema_for,
    _sha256_text,
    _stable_json,
    _system_prompt,
    _validate_artifact,
    build_department_prompt,
    build_generalist_prompt,
)
from .model_backends import ModelBackend, ModelRequest, ModelResponse, backend_from_config

STAGED_CONDITIONS = ("staged_isolated", "staged_generalist", "staged_multi_agent")


def _ordered_public_versions(spec: dict[str, Any]) -> list[dict[str, Any]]:
    packet = spec.get("source_packet", {})
    versions = packet.get("versions", [])
    if not isinstance(versions, list) or len(versions) < 2:
        raise ValueError("Staged evaluation requires at least two public packet versions")
    rows = [row for row in versions if isinstance(row, dict)]
    if len(rows) != len(versions):
        raise ValueError("Every source_packet version must be a JSON object")
    return sorted(rows, key=lambda row: str(row.get("as_of", "")))


def stage_spec(spec: dict[str, Any], version_id: str) -> dict[str, Any]:
    """Return a private verifier spec whose prompt-visible packet contains one stage only."""
    staged = copy.deepcopy(spec)
    public_versions = _ordered_public_versions(spec)
    selected = [row for row in public_versions if row.get("version_id") == version_id]
    if len(selected) != 1:
        raise ValueError(f"Unknown or duplicate public version: {version_id}")
    initial_version = str(public_versions[0]["version_id"])
    final_version = str(public_versions[-1]["version_id"])
    staged["required_source_version"] = version_id
    staged["_staged_initial_version"] = initial_version
    staged["_staged_final_version"] = final_version
    staged["source_packet"]["versions"] = selected
    staged["source_packet"]["chronology_rule"] = (
        f"This stage contains only version {version_id}. Use it as the authoritative "
        "state available at this point in the workflow."
    )
    return staged


def staged_version_ids(spec: dict[str, Any]) -> tuple[str, str]:
    versions = _ordered_public_versions(spec)
    first = str(versions[0]["version_id"])
    latest = str(versions[-1]["version_id"])
    if first == latest:
        raise ValueError("Initial and final staged versions must differ")
    return first, latest


class StageAwareControlBackend:
    """Offline control used only to validate the staged runner and its verifiers."""

    def __init__(self, mode: str = "oracle") -> None:
        if mode not in {"oracle", "ignore_update"}:
            raise ValueError(f"Unsupported staged deterministic mode: {mode}")
        self.mode = mode

    @staticmethod
    def _artifact(spec: dict[str, Any], department: str, version_id: str) -> dict[str, Any]:
        version = spec["versions"][version_id]
        facts = version["facts"]
        document_id = str(version["document_id"])
        scenario = str(spec["required_scenario_id"])
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
            return {
                "department": "risk",
                "source_version": version_id,
                "scenario_id": scenario,
                "risk_flags": list(version["risk_flags"]),
            }
        if department == "memo":
            return {
                "department": "ecm_committee",
                "source_version": version_id,
                "scenario_id": scenario,
                "headline_metrics": financial_metrics(facts),
                "top_risks": list(version["risk_flags"]),
                "citations": [
                    f"{document_id}:summary:offering",
                    f"{document_id}:summary:risks",
                ],
                "recommendation": "proceed_with_conditions",
            }
        raise ValueError(f"Unknown department: {department}")

    def generate(self, request: ModelRequest) -> ModelResponse:
        started = time.perf_counter()
        spec = request.metadata["spec"]
        target = str(spec["required_source_version"])
        stage = str(request.metadata.get("stage", ""))
        if self.mode == "ignore_update" and stage == "round2":
            target = str(spec["_staged_initial_version"])
        if request.department is None:
            parsed = {
                department: self._artifact(spec, department, target)
                for department in DEPARTMENTS
            }
        else:
            parsed = self._artifact(spec, request.department, target)
        content = json.dumps(parsed, sort_keys=True)
        return ModelResponse(
            content=content,
            parsed=parsed,
            input_tokens=0,
            output_tokens=0,
            latency_seconds=time.perf_counter() - started,
            raw={"staged_deterministic_control": self.mode},
        )


def _backend_from_staged_config(config: dict[str, Any]) -> ModelBackend:
    if str(config.get("type", "")) == "staged_deterministic_control":
        return StageAwareControlBackend(str(config.get("mode", "oracle")))
    return backend_from_config(config)


def _invoke(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    stage: str,
    department: str | None,
    user_prompt: str,
    repetition: int,
) -> tuple[dict[str, Any], CallRecord, dict[str, Any]]:
    request_id = (
        f"{spec['workflow_id']}::{system_config['system_id']}::{condition}::"
        f"{stage}::{department or 'all'}::r{repetition}"
    )
    request = ModelRequest(
        request_id=request_id,
        workflow_id=str(spec["workflow_id"]),
        condition=condition,
        department=department,
        system_prompt=_system_prompt(),
        user_prompt=user_prompt,
        metadata={"spec": spec, "repetition": repetition, "stage": stage},
    )
    started_at = time.time()
    response = backend.generate(request)
    if response.parsed is None:
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
    raw = {
        "request_id": request_id,
        "stage": stage,
        "backend_raw": response.raw,
        "content": response.content,
    }
    return response.parsed, record, raw


def _run_department_sequence(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    stage: str,
    repetition: int,
) -> tuple[dict[str, dict[str, Any]], list[CallRecord], list[dict[str, Any]]]:
    artifacts: dict[str, dict[str, Any]] = {}
    calls: list[CallRecord] = []
    raw_rows: list[dict[str, Any]] = []
    for department in DEPARTMENTS:
        handoffs: dict[str, dict[str, Any]] = {}
        if condition == "staged_multi_agent":
            if department in {"valuation", "risk"} and "diligence" in artifacts:
                handoffs = {"diligence": artifacts["diligence"]}
            elif department == "memo":
                handoffs = dict(artifacts)
        parsed, record, raw = _invoke(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            stage=stage,
            department=department,
            user_prompt=build_department_prompt(spec, department, handoffs=handoffs),
            repetition=repetition,
        )
        artifacts[department] = _validate_artifact(department, parsed)
        calls.append(record)
        raw_rows.append(raw)
    return artifacts, calls, raw_rows


def _generalist_update_prompt(
    spec: dict[str, Any],
    previous_artifacts: dict[str, dict[str, Any]],
) -> str:
    payload = {
        "task": (
            "A later authoritative filing has arrived. Audit the previous four artifacts, "
            "replace every stale value or citation, preserve still-valid information, and "
            "return a complete revised workflow state."
        ),
        "workflow_id": spec["workflow_id"],
        "required_source_version": spec["required_source_version"],
        "required_scenario_id": spec["required_scenario_id"],
        "new_authoritative_packet": spec["source_packet"],
        "previous_artifacts": previous_artifacts,
        "output_schema": {
            department: _schema_for(department) for department in DEPARTMENTS
        },
    }
    return (
        "Return one JSON object with exactly diligence, valuation, risk, and memo. "
        "Every artifact must reflect the new authoritative version. JSON only.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def _department_update_prompt(
    spec: dict[str, Any],
    department: str,
    previous_artifact: dict[str, Any],
    upstream_handoffs: dict[str, dict[str, Any]],
) -> str:
    payload = {
        "task": (
            f"Update the {department} artifact after a later authoritative filing. "
            "Remove stale claims, use the revised upstream handoffs, and preserve "
            "still-valid information without inventing values."
        ),
        "workflow_id": spec["workflow_id"],
        "required_source_version": spec["required_source_version"],
        "required_scenario_id": spec["required_scenario_id"],
        "new_authoritative_packet": spec["source_packet"],
        "previous_artifact": previous_artifact,
        "updated_upstream_handoffs": upstream_handoffs,
        "output_schema": _schema_for(department),
    }
    return (
        "Return exactly one revised JSON artifact matching output_schema. JSON only.\n\n"
        + json.dumps(payload, indent=2, ensure_ascii=False)
    )


def _run_round1(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    repetition: int,
) -> tuple[dict[str, dict[str, Any]], list[CallRecord], list[dict[str, Any]]]:
    if condition in {"staged_isolated", "staged_multi_agent"}:
        return _run_department_sequence(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            stage="round1",
            repetition=repetition,
        )
    parsed, record, raw = _invoke(
        backend=backend,
        system_config=system_config,
        spec=spec,
        condition=condition,
        stage="round1",
        department=None,
        user_prompt=build_generalist_prompt(spec),
        repetition=repetition,
    )
    artifacts = {
        department: _validate_artifact(department, parsed[department])
        for department in DEPARTMENTS
    }
    return artifacts, [record], [raw]


def _run_round2(
    *,
    backend: ModelBackend,
    system_config: dict[str, Any],
    spec: dict[str, Any],
    condition: str,
    previous_artifacts: dict[str, dict[str, Any]],
    repetition: int,
) -> tuple[dict[str, dict[str, Any]], list[CallRecord], list[dict[str, Any]]]:
    if condition == "staged_generalist":
        parsed, record, raw = _invoke(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            stage="round2",
            department=None,
            user_prompt=_generalist_update_prompt(spec, previous_artifacts),
            repetition=repetition,
        )
        artifacts = {
            department: _validate_artifact(department, parsed[department])
            for department in DEPARTMENTS
        }
        return artifacts, [record], [raw]

    artifacts: dict[str, dict[str, Any]] = {}
    calls: list[CallRecord] = []
    raw_rows: list[dict[str, Any]] = []
    for department in DEPARTMENTS:
        upstream: dict[str, dict[str, Any]] = {}
        if condition == "staged_multi_agent":
            if department in {"valuation", "risk"}:
                upstream = {"diligence": artifacts["diligence"]}
            elif department == "memo":
                upstream = dict(artifacts)
        parsed, record, raw = _invoke(
            backend=backend,
            system_config=system_config,
            spec=spec,
            condition=condition,
            stage="round2",
            department=department,
            user_prompt=_department_update_prompt(
                spec,
                department,
                previous_artifacts[department],
                upstream,
            ),
            repetition=repetition,
        )
        artifacts[department] = _validate_artifact(department, parsed)
        calls.append(record)
        raw_rows.append(raw)
    return artifacts, calls, raw_rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=False))
            handle.write("\n")


def _score_with_spec(spec: dict[str, Any], run_dir: Path) -> dict[str, Any]:
    with TemporaryDirectory() as temporary:
        path = Path(temporary) / "spec.json"
        write_json(path, spec)
        return score_run(path, run_dir).to_dict()


def _artifact_change_map(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, bool]:
    return {
        department: _stable_json(before[department]) != _stable_json(after[department])
        for department in DEPARTMENTS
    }


def _run_id(system_id: str, condition: str, repetition: int) -> str:
    return f"{system_id}__{condition}__r{repetition:02d}"


def run_staged_one(
    *,
    spec_path: Path,
    output_root: Path,
    system_config: dict[str, Any],
    condition: str,
    repetition: int,
    overwrite: bool = False,
) -> dict[str, Any]:
    if condition not in STAGED_CONDITIONS:
        raise ValueError(f"Unsupported staged condition: {condition}")
    full_spec = read_json(spec_path)
    initial_version, final_version = staged_version_ids(full_spec)
    initial_spec = stage_spec(full_spec, initial_version)
    final_spec = stage_spec(full_spec, final_version)
    system_id = str(system_config["system_id"])
    run_id = _run_id(system_id, condition, repetition)
    run_dir = output_root / str(full_spec["workflow_id"]) / run_id
    score_path = run_dir / "score.json"
    if score_path.exists() and not overwrite:
        return read_json(score_path)

    run_dir.mkdir(parents=True, exist_ok=True)
    backend = _backend_from_staged_config(dict(system_config["backend"]))
    calls: list[CallRecord] = []
    raw_rows: list[dict[str, Any]] = []
    started = time.time()
    status = "completed"
    error: str | None = None

    try:
        round1, calls1, raw1 = _run_round1(
            backend=backend,
            system_config=system_config,
            spec=initial_spec,
            condition=condition,
            repetition=repetition,
        )
        round1_dir = run_dir / "round1"
        for department, artifact in round1.items():
            write_json(round1_dir / ARTIFACT_FILES[department], artifact)
        round1_score = _score_with_spec(initial_spec, round1_dir)

        final, calls2, raw2 = _run_round2(
            backend=backend,
            system_config=system_config,
            spec=final_spec,
            condition=condition,
            previous_artifacts=round1,
            repetition=repetition,
        )
        for department, artifact in final.items():
            write_json(run_dir / ARTIFACT_FILES[department], artifact)
        final_score = _score_with_spec(final_spec, run_dir)

        calls = calls1 + calls2
        raw_rows = raw1 + raw2
        change_map = _artifact_change_map(round1, final)
        stale = [
            department
            for department, artifact in final.items()
            if artifact.get("source_version") != final_version
        ]
        report = {
            **final_score,
            "result_type": (
                "staged_deterministic_control_not_model_results"
                if str(system_config["backend"].get("type"))
                == "staged_deterministic_control"
                else "staged_model_workflow_result_requires_verifier_and_human_review"
            ),
            "initial_version": initial_version,
            "final_version": final_version,
            "round1_workflow_score": round1_score["workflow_score"],
            "round1_enterprise_success": round1_score["enterprise_success"],
            "artifact_changed_after_update": change_map,
            "changed_artifact_count": sum(change_map.values()),
            "stale_artifacts_after_update": stale,
            "update_success": bool(final_score["enterprise_success"]) and not stale,
        }
    except Exception as exc:  # noqa: BLE001 - preserve failed experiment runs
        status = "failed"
        error = f"{type(exc).__name__}: {exc}"
        report = {
            "result_type": "failed_staged_workflow_run",
            "workflow_id": str(full_spec["workflow_id"]),
            "system_id": system_id,
            "component_score": 0.0,
            "coordination_score": 0.0,
            "workflow_score": 0.0,
            "composition_gap": 0.0,
            "enterprise_success": False,
            "update_success": False,
            "error": error,
        }

    total_cost = sum(call.estimated_cost_usd for call in calls)
    total_input = sum(call.input_tokens for call in calls)
    total_output = sum(call.output_tokens for call in calls)
    metadata = {
        "experiment_run_id": run_id,
        "workflow_id": str(full_spec["workflow_id"]),
        "system_id": system_id,
        "condition": condition,
        "repetition": repetition,
        "status": status,
        "error": error,
        "started_at_unix": started,
        "completed_at_unix": time.time(),
        "calls": [asdict(call) for call in calls],
        "call_count": len(calls),
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "estimated_cost_usd": round(total_cost, 8),
        "spec_sha256": _sha256_text(_stable_json(full_spec)),
    }
    report.update(
        {
            "experiment_run_id": run_id,
            "system_id": system_id,
            "condition": condition,
            "repetition": repetition,
            "status": status,
            "error": error,
            "call_count": len(calls),
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "estimated_cost_usd": round(total_cost, 8),
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
    rows: list[dict[str, Any]] = []
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
                "enterprise_success_rate": round(
                    sum(bool(item["enterprise_success"]) for item in completed)
                    / denominator,
                    6,
                )
                if denominator
                else 0.0,
                "update_success_rate": round(
                    sum(bool(item.get("update_success")) for item in completed)
                    / denominator,
                    6,
                )
                if denominator
                else 0.0,
                "mean_calls": round(
                    mean(int(item.get("call_count", 0)) for item in completed), 3
                )
                if completed
                else 0.0,
                "estimated_cost_usd": round(
                    sum(float(item.get("estimated_cost_usd", 0.0)) for item in items),
                    8,
                ),
            }
        )
    return {"groups": rows}


def _resolve_path(base: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base / path).resolve()


def run_staged_experiment(
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
        else _resolve_path(base, config.get("output_root", "../results/staged"))
    )
    cases = [_resolve_path(base, item) for item in config["cases"]]
    conditions = [
        str(item) for item in config.get("conditions", STAGED_CONDITIONS)
    ]
    repetitions = int(config.get("repetitions", 1))
    systems = [dict(item) for item in config["systems"] if item.get("enabled", True)]

    reports: list[dict[str, Any]] = []
    for spec_path in cases:
        for system_config in systems:
            for condition in conditions:
                for repetition in range(repetitions):
                    reports.append(
                        run_staged_one(
                            spec_path=spec_path,
                            output_root=output_root,
                            system_config=system_config,
                            condition=condition,
                            repetition=repetition,
                            overwrite=overwrite,
                        )
                    )
    summary = {
        "result_type": "staged_amendment_experiment_summary",
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
