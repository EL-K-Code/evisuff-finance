from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

ARTIFACT_FILES = {
    "diligence": "diligence.json",
    "valuation": "valuation.json",
    "risk": "risk.json",
    "memo": "memo.json",
}

# Source facts and direct fact handoffs remain effectively exact. Derived
# metrics use reporting-scale tolerances because model outputs may round monetary
# values expressed in USD millions and percentages without changing the economic
# conclusion. These tolerances must be reported with empirical results.
FACT_TOLERANCE = 1e-6
METRIC_TOLERANCES = {
    "gross_proceeds_usd_m": 0.01,
    "post_money_equity_value_usd_m": 0.01,
    "net_debt_usd_m": 0.01,
    "dilution_pct": 0.01,
}


@dataclass(frozen=True)
class Check:
    check_id: str
    scope: str
    passed: bool
    critical: bool
    message: str


@dataclass(frozen=True)
class ArtifactScore:
    artifact: str
    score: float
    checks: list[Check]


@dataclass(frozen=True)
class WorkflowReport:
    workflow_id: str
    system_id: str
    component_score: float
    coordination_score: float
    workflow_score: float
    composition_gap: float
    enterprise_success: bool
    artifact_scores: dict[str, float]
    local_checks: list[Check]
    coordination_checks: list[Check]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["result_type"] = "synthetic_workflow_software_validation_not_model_results"
        return payload


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _close(actual: Any, expected: float, tolerance: float = FACT_TOLERANCE) -> bool:
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


def _metric_close(metric_name: str, actual: Any, expected: float) -> bool:
    tolerance = METRIC_TOLERANCES.get(metric_name, FACT_TOLERANCE)
    return _close(actual, expected, tolerance=tolerance)


def _score(checks: Iterable[Check]) -> float:
    rows = list(checks)
    return 1.0 if not rows else sum(row.passed for row in rows) / len(rows)


def _version(spec: dict[str, Any], version_id: str) -> dict[str, Any]:
    versions = spec.get("versions", {})
    if version_id not in versions:
        raise ValueError(f"Unknown source_version: {version_id}")
    version = versions[version_id]
    if not isinstance(version, dict):
        raise ValueError(f"Invalid version payload: {version_id}")
    return version


def financial_metrics(facts: dict[str, Any]) -> dict[str, float]:
    price = float(facts["price_per_share_usd"])
    primary = float(facts["primary_shares_m"])
    existing = float(facts["existing_shares_m"])
    debt = float(facts["debt_usd_m"])
    cash = float(facts["cash_usd_m"])
    post_money_shares = existing + primary
    return {
        "gross_proceeds_usd_m": price * primary,
        "post_money_equity_value_usd_m": price * post_money_shares,
        "net_debt_usd_m": debt - cash,
        "dilution_pct": 100.0 * primary / post_money_shares,
    }


def load_run(run_dir: Path) -> dict[str, dict[str, Any]]:
    missing = [name for name in ARTIFACT_FILES.values() if not (run_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing workflow artifacts in {run_dir}: {missing}")
    return {
        key: read_json(run_dir / filename)
        for key, filename in ARTIFACT_FILES.items()
    }


def _citation_matches(citation: Any, document_id: str) -> bool:
    return isinstance(citation, str) and citation.startswith(f"{document_id}:")


def score_diligence(
    spec: dict[str, Any], artifact: dict[str, Any]
) -> ArtifactScore:
    version_id = str(artifact.get("source_version", ""))
    version = _version(spec, version_id)
    facts = version["facts"]
    document_id = str(version["document_id"])
    output_facts = artifact.get("facts", {})
    citations = artifact.get("citations", {})
    checks: list[Check] = []
    for key, expected in facts.items():
        checks.append(
            Check(
                f"diligence.fact.{key}",
                "diligence",
                _close(output_facts.get(key), expected),
                True,
                f"Fact {key} matches declared source version",
            )
        )
        checks.append(
            Check(
                f"diligence.citation.{key}",
                "diligence",
                _citation_matches(citations.get(key), document_id),
                True,
                f"Citation {key} points to declared filing",
            )
        )
    return ArtifactScore("diligence", _score(checks), checks)


def score_valuation(
    spec: dict[str, Any], artifact: dict[str, Any]
) -> ArtifactScore:
    version_id = str(artifact.get("source_version", ""))
    version = _version(spec, version_id)
    facts = version["facts"]
    expected = financial_metrics(facts)
    inputs = artifact.get("inputs", {})
    outputs = artifact.get("outputs", {})
    checks: list[Check] = []
    for key in (
        "price_per_share_usd",
        "primary_shares_m",
        "existing_shares_m",
        "debt_usd_m",
        "cash_usd_m",
    ):
        checks.append(
            Check(
                f"valuation.input.{key}",
                "valuation",
                _close(inputs.get(key), facts[key]),
                True,
                f"Valuation input {key} matches declared source version",
            )
        )
    for key, value in expected.items():
        checks.append(
            Check(
                f"valuation.output.{key}",
                "valuation",
                _metric_close(key, outputs.get(key), value),
                True,
                f"Valuation output {key} is internally correct within its reporting tolerance",
            )
        )
    checks.append(
        Check(
            "valuation.scenario",
            "valuation",
            artifact.get("scenario_id") in spec["allowed_scenarios"],
            True,
            "Scenario is allowed",
        )
    )
    return ArtifactScore("valuation", _score(checks), checks)


def score_risk(spec: dict[str, Any], artifact: dict[str, Any]) -> ArtifactScore:
    version_id = str(artifact.get("source_version", ""))
    version = _version(spec, version_id)
    expected = set(version["risk_flags"])
    actual = set(artifact.get("risk_flags", []))
    checks = [
        Check(
            "risk.coverage",
            "risk",
            expected.issubset(actual),
            True,
            "All risks in declared source version are covered",
        ),
        Check(
            "risk.no_unsupported",
            "risk",
            actual.issubset(expected),
            True,
            "No unsupported risk is introduced",
        ),
        Check(
            "risk.scenario",
            "risk",
            artifact.get("scenario_id") in spec["allowed_scenarios"],
            True,
            "Scenario is allowed",
        ),
    ]
    return ArtifactScore("risk", _score(checks), checks)


def score_memo(spec: dict[str, Any], artifact: dict[str, Any]) -> ArtifactScore:
    version_id = str(artifact.get("source_version", ""))
    version = _version(spec, version_id)
    expected_metrics = financial_metrics(version["facts"])
    metrics = artifact.get("headline_metrics", {})
    risks = set(artifact.get("top_risks", []))
    expected_risks = set(version["risk_flags"])
    document_id = str(version["document_id"])
    citations = artifact.get("citations", [])
    checks: list[Check] = []
    for key, expected in expected_metrics.items():
        checks.append(
            Check(
                f"memo.metric.{key}",
                "memo",
                _metric_close(key, metrics.get(key), expected),
                True,
                f"Memo metric {key} is correct for declared version within its reporting tolerance",
            )
        )
    checks.extend(
        [
            Check(
                "memo.risks",
                "memo",
                expected_risks.issubset(risks),
                True,
                "Memo contains all material risks for declared version",
            ),
            Check(
                "memo.citations",
                "memo",
                bool(citations)
                and all(_citation_matches(item, document_id) for item in citations),
                True,
                "Memo citations point to declared filing",
            ),
            Check(
                "memo.recommendation",
                "memo",
                artifact.get("recommendation")
                in {"proceed", "proceed_with_conditions", "do_not_proceed"},
                False,
                "Memo has a valid recommendation",
            ),
            Check(
                "memo.scenario",
                "memo",
                artifact.get("scenario_id") in spec["allowed_scenarios"],
                True,
                "Scenario is allowed",
            ),
        ]
    )
    return ArtifactScore("memo", _score(checks), checks)


def coordination_checks(
    spec: dict[str, Any], artifacts: dict[str, dict[str, Any]]
) -> list[Check]:
    required_version = str(spec["required_source_version"])
    required_scenario = str(spec["required_scenario_id"])
    checks: list[Check] = []
    for name, artifact in artifacts.items():
        checks.append(
            Check(
                f"freshness.{name}",
                "coordination",
                artifact.get("source_version") == required_version,
                True,
                f"{name} uses the required latest filing",
            )
        )
        checks.append(
            Check(
                f"scenario.{name}",
                "coordination",
                artifact.get("scenario_id") == required_scenario,
                True,
                f"{name} uses the shared scenario",
            )
        )

    diligence_facts = artifacts["diligence"].get("facts", {})
    valuation_inputs = artifacts["valuation"].get("inputs", {})
    for key in (
        "price_per_share_usd",
        "primary_shares_m",
        "existing_shares_m",
        "debt_usd_m",
        "cash_usd_m",
    ):
        checks.append(
            Check(
                f"handoff.diligence_to_valuation.{key}",
                "coordination",
                _close(diligence_facts.get(key), valuation_inputs.get(key)),
                True,
                f"Valuation consumes diligence fact {key}",
            )
        )

    valuation_outputs = artifacts["valuation"].get("outputs", {})
    memo_metrics = artifacts["memo"].get("headline_metrics", {})
    for key in (
        "gross_proceeds_usd_m",
        "post_money_equity_value_usd_m",
        "net_debt_usd_m",
        "dilution_pct",
    ):
        checks.append(
            Check(
                f"handoff.valuation_to_memo.{key}",
                "coordination",
                _metric_close(key, valuation_outputs.get(key), memo_metrics.get(key)),
                True,
                f"Memo reuses valuation output {key} within its reporting tolerance",
            )
        )

    risk_flags = set(artifacts["risk"].get("risk_flags", []))
    memo_risks = set(artifacts["memo"].get("top_risks", []))
    checks.append(
        Check(
            "handoff.risk_to_memo",
            "coordination",
            risk_flags.issubset(memo_risks),
            True,
            "Memo carries forward all risk-team findings",
        )
    )

    latest_document = str(_version(spec, required_version)["document_id"])
    memo_citations = artifacts["memo"].get("citations", [])
    checks.append(
        Check(
            "latest_provenance.memo",
            "coordination",
            bool(memo_citations)
            and all(
                _citation_matches(item, latest_document) for item in memo_citations
            ),
            True,
            "Final memo cites only the latest authoritative filing",
        )
    )
    return checks


def score_run(spec_path: Path, run_dir: Path) -> WorkflowReport:
    spec = read_json(spec_path)
    artifacts = load_run(run_dir)
    local = {
        "diligence": score_diligence(spec, artifacts["diligence"]),
        "valuation": score_valuation(spec, artifacts["valuation"]),
        "risk": score_risk(spec, artifacts["risk"]),
        "memo": score_memo(spec, artifacts["memo"]),
    }
    local_checks = [check for item in local.values() for check in item.checks]
    coord_checks = coordination_checks(spec, artifacts)
    component_score = mean(item.score for item in local.values())
    coordination_score = _score(coord_checks)
    workflow_score = 0.6 * component_score + 0.4 * coordination_score
    enterprise_success = all(
        check.passed for check in local_checks + coord_checks if check.critical
    )
    return WorkflowReport(
        workflow_id=str(spec["workflow_id"]),
        system_id=run_dir.name,
        component_score=round(component_score, 6),
        coordination_score=round(coordination_score, 6),
        workflow_score=round(workflow_score, 6),
        composition_gap=round(component_score - workflow_score, 6),
        enterprise_success=enterprise_success,
        artifact_scores={key: round(value.score, 6) for key, value in local.items()},
        local_checks=local_checks,
        coordination_checks=coord_checks,
    )


def _artifact_bundle(
    spec: dict[str, Any],
    versions: dict[str, str],
    *,
    omit_new_risk: bool = False,
    stale_memo_citation: bool = False,
) -> dict[str, dict[str, Any]]:
    scenario = str(spec["required_scenario_id"])
    diligence_version = _version(spec, versions["diligence"])
    valuation_version = _version(spec, versions["valuation"])
    risk_version = _version(spec, versions["risk"])
    memo_version = _version(spec, versions["memo"])

    diligence_facts = dict(diligence_version["facts"])
    diligence = {
        "department": "due_diligence",
        "source_version": versions["diligence"],
        "scenario_id": scenario,
        "facts": diligence_facts,
        "citations": {
            key: f"{diligence_version['document_id']}:fact:{key}"
            for key in diligence_facts
        },
    }

    valuation_facts = dict(valuation_version["facts"])
    valuation = {
        "department": "valuation",
        "source_version": versions["valuation"],
        "scenario_id": scenario,
        "inputs": {
            key: valuation_facts[key]
            for key in (
                "price_per_share_usd",
                "primary_shares_m",
                "existing_shares_m",
                "debt_usd_m",
                "cash_usd_m",
            )
        },
        "outputs": financial_metrics(valuation_facts),
    }

    risks = list(risk_version["risk_flags"])
    if omit_new_risk and risks:
        risks = risks[:-1]
    risk = {
        "department": "risk",
        "source_version": versions["risk"],
        "scenario_id": scenario,
        "risk_flags": risks,
    }

    memo_risks = list(memo_version["risk_flags"])
    if omit_new_risk and memo_risks:
        memo_risks = memo_risks[:-1]
    memo_document = (
        _version(spec, "v1")["document_id"]
        if stale_memo_citation
        else memo_version["document_id"]
    )
    memo = {
        "department": "ecm_committee",
        "source_version": versions["memo"],
        "scenario_id": scenario,
        "headline_metrics": financial_metrics(memo_version["facts"]),
        "top_risks": memo_risks,
        "citations": [
            f"{memo_document}:summary:offering",
            f"{memo_document}:summary:risks",
        ],
        "recommendation": "proceed_with_conditions",
    }
    return {
        "diligence": diligence,
        "valuation": valuation,
        "risk": risk,
        "memo": memo,
    }


def generate_synthetic_baselines(
    spec_path: Path, output_root: Path
) -> list[Path]:
    spec = read_json(spec_path)
    systems = {
        "coordinated_team": _artifact_bundle(
            spec, {key: "v2" for key in ARTIFACT_FILES}
        ),
        "siloed_benchmark_winners": _artifact_bundle(
            spec,
            {
                "diligence": "v2",
                "valuation": "v1",
                "risk": "v2",
                "memo": "v1",
            },
        ),
        "partial_handoff": _artifact_bundle(
            spec,
            {key: "v2" for key in ARTIFACT_FILES},
            omit_new_risk=True,
            stale_memo_citation=True,
        ),
    }
    run_dirs: list[Path] = []
    for system_id, artifacts in systems.items():
        run_dir = output_root / system_id
        run_dir.mkdir(parents=True, exist_ok=True)
        for key, payload in artifacts.items():
            write_json(run_dir / ARTIFACT_FILES[key], payload)
        run_dirs.append(run_dir)
    return run_dirs


def run_synthetic_pilot(
    spec_path: Path, output_root: Path, report_path: Path
) -> dict[str, Any]:
    run_dirs = generate_synthetic_baselines(spec_path, output_root)
    detailed_reports = [score_run(spec_path, run_dir) for run_dir in run_dirs]
    reports = []
    for report in detailed_reports:
        failed = [
            check.check_id
            for check in report.local_checks + report.coordination_checks
            if not check.passed
        ]
        reports.append(
            {
                "system_id": report.system_id,
                "component_score": report.component_score,
                "coordination_score": report.coordination_score,
                "workflow_score": report.workflow_score,
                "composition_gap": report.composition_gap,
                "enterprise_success": report.enterprise_success,
                "artifact_scores": report.artifact_scores,
                "failed_checks": failed,
            }
        )
    summary = {
        "result_type": "synthetic_workflow_software_validation_not_model_results",
        "pilot": "ipo_multi_department_composition",
        "workflow_id": str(read_json(spec_path)["workflow_id"]),
        "systems": reports,
        "interpretation": {
            "coordinated_team": "Oracle-like consistency control.",
            "siloed_benchmark_winners": (
                "Each department is internally correct for its declared filing, "
                "but versions do not compose into a current enterprise state."
            ),
            "partial_handoff": (
                "Latest filing is used, but a risk and provenance handoff are incomplete."
            ),
        },
    }
    write_json(report_path, summary)
    return summary
