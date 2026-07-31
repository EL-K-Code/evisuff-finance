from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

REQUIRED_FACTS = (
    "price_per_share_usd",
    "primary_shares_m",
    "existing_shares_m",
    "debt_usd_m",
    "cash_usd_m",
)
REQUIRED_DEPARTMENTS = (
    "due_diligence",
    "valuation",
    "risk",
    "ecm_committee",
)
SEC_ARCHIVE_HOST = "www.sec.gov"
SEC_ARCHIVE_PREFIX = "/Archives/edgar/data/"


@dataclass(frozen=True)
class CaseValidation:
    case_id: str
    workflow_id: str
    issuer: str
    ticker: str
    source_versions: int
    documents: int
    evidence_items: int
    changed_facts: list[str]
    changed_risks: list[str]
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["valid"] = self.valid
        return payload


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return payload


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid_sec_archive_url(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and parsed.hostname == SEC_ARCHIVE_HOST
        and parsed.path.startswith(SEC_ARCHIVE_PREFIX)
    )


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _validate_gold_version(
    case_id: str,
    version_id: str,
    payload: Any,
    errors: list[str],
) -> None:
    prefix = f"{case_id}.versions.{version_id}"
    if not isinstance(payload, dict):
        errors.append(f"{prefix} must be an object")
        return
    document_id = payload.get("document_id")
    if not isinstance(document_id, str) or not document_id.strip():
        errors.append(f"{prefix}.document_id must be a non-empty string")
    facts = payload.get("facts")
    if not isinstance(facts, dict):
        errors.append(f"{prefix}.facts must be an object")
    else:
        missing = sorted(set(REQUIRED_FACTS) - set(facts))
        extra = sorted(set(facts) - set(REQUIRED_FACTS))
        if missing:
            errors.append(f"{prefix}.facts missing {missing}")
        if extra:
            errors.append(f"{prefix}.facts has unsupported keys {extra}")
        for fact_name in REQUIRED_FACTS:
            value = facts.get(fact_name)
            if not _is_number(value):
                errors.append(f"{prefix}.facts.{fact_name} must be numeric")
            elif float(value) < 0:
                errors.append(f"{prefix}.facts.{fact_name} must be non-negative")
    risks = payload.get("risk_flags")
    if not isinstance(risks, list) or not risks:
        errors.append(f"{prefix}.risk_flags must be a non-empty list")
    elif any(not isinstance(item, str) or not item.strip() for item in risks):
        errors.append(f"{prefix}.risk_flags must contain non-empty strings")
    elif len(risks) != len(set(risks)):
        errors.append(f"{prefix}.risk_flags contains duplicates")


def validate_case(case_entry: dict[str, Any], index_path: Path) -> CaseValidation:
    case_id = str(case_entry.get("case_id", ""))
    relative_spec = case_entry.get("spec")
    errors: list[str] = []
    if not case_id:
        errors.append("index case_id is required")
    if not isinstance(relative_spec, str) or not relative_spec:
        errors.append(f"{case_id or '<unknown>'}.spec must be a path string")
        spec_path = index_path.parent / "__missing__"
        spec: dict[str, Any] = {}
    else:
        spec_path = (index_path.parent / relative_spec).resolve()
        try:
            spec = _read_json(spec_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{case_id}.spec could not be read: {exc}")
            spec = {}

    workflow_id = str(spec.get("workflow_id", ""))
    issuer = str(spec.get("issuer", ""))
    ticker = str(spec.get("ticker", ""))
    for field, value in (
        ("workflow_id", workflow_id),
        ("issuer", issuer),
        ("ticker", ticker),
        ("cik", str(spec.get("cik", ""))),
        ("annotation_status", str(spec.get("annotation_status", ""))),
    ):
        if not value:
            errors.append(f"{case_id}.{field} is required")

    if case_entry.get("issuer") != issuer:
        errors.append(f"{case_id}.issuer differs between index and spec")
    if case_entry.get("ticker") != ticker:
        errors.append(f"{case_id}.ticker differs between index and spec")
    if case_entry.get("annotation_status") != spec.get("annotation_status"):
        errors.append(f"{case_id}.annotation_status differs between index and spec")

    departments = spec.get("departments")
    if departments != list(REQUIRED_DEPARTMENTS):
        errors.append(
            f"{case_id}.departments must equal {list(REQUIRED_DEPARTMENTS)}"
        )

    allowed_scenarios = spec.get("allowed_scenarios")
    required_scenario = spec.get("required_scenario_id")
    if not isinstance(allowed_scenarios, list) or required_scenario not in allowed_scenarios:
        errors.append(f"{case_id}.required_scenario_id must be allowed")

    gold_versions = spec.get("versions")
    if not isinstance(gold_versions, dict) or len(gold_versions) < 2:
        errors.append(f"{case_id}.versions must contain at least two gold versions")
        gold_versions = {}
    for version_id, payload in gold_versions.items():
        _validate_gold_version(case_id, str(version_id), payload, errors)

    required_version = spec.get("required_source_version")
    if required_version not in gold_versions:
        errors.append(f"{case_id}.required_source_version is not in versions")

    packet = spec.get("source_packet")
    packet_versions: list[Any] = []
    if not isinstance(packet, dict):
        errors.append(f"{case_id}.source_packet must be an object")
    else:
        if packet.get("packet_type") != "official_sec_evidence_packet":
            errors.append(f"{case_id}.source_packet.packet_type is invalid")
        if packet.get("issuer") != issuer:
            errors.append(f"{case_id}.source_packet.issuer differs from spec")
        if "facts" in packet or "risk_flags" in packet:
            errors.append(f"{case_id}.source_packet must not expose gold labels")
        required_facts = packet.get("required_facts")
        if required_facts != list(REQUIRED_FACTS):
            errors.append(
                f"{case_id}.source_packet.required_facts must equal {list(REQUIRED_FACTS)}"
            )
        packet_versions = packet.get("versions", [])
        if not isinstance(packet_versions, list) or len(packet_versions) < 2:
            errors.append(f"{case_id}.source_packet.versions must contain at least two entries")
            packet_versions = []

    document_count = 0
    evidence_count = 0
    packet_dates: dict[str, date] = {}
    packet_version_ids: set[str] = set()
    for position, packet_version in enumerate(packet_versions):
        prefix = f"{case_id}.source_packet.versions[{position}]"
        if not isinstance(packet_version, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if "facts" in packet_version or "risk_flags" in packet_version:
            errors.append(f"{prefix} must not expose gold labels")
        version_id = packet_version.get("version_id")
        if not isinstance(version_id, str) or not version_id:
            errors.append(f"{prefix}.version_id is required")
            continue
        if version_id in packet_version_ids:
            errors.append(f"{case_id}.source_packet has duplicate version {version_id}")
        packet_version_ids.add(version_id)
        if version_id not in gold_versions:
            errors.append(f"{prefix}.version_id has no matching gold version")
        else:
            expected_document_id = gold_versions[version_id].get("document_id")
            if packet_version.get("document_id") != expected_document_id:
                errors.append(f"{prefix}.document_id differs from gold version")
        parsed_date = _parse_date(packet_version.get("as_of"))
        if parsed_date is None:
            errors.append(f"{prefix}.as_of must be ISO date YYYY-MM-DD")
        else:
            packet_dates[version_id] = parsed_date

        documents = packet_version.get("documents")
        if not isinstance(documents, list) or not documents:
            errors.append(f"{prefix}.documents must be a non-empty list")
        else:
            document_count += len(documents)
            for doc_position, document in enumerate(documents):
                doc_prefix = f"{prefix}.documents[{doc_position}]"
                if not isinstance(document, dict):
                    errors.append(f"{doc_prefix} must be an object")
                    continue
                if not _valid_sec_archive_url(document.get("url")):
                    errors.append(f"{doc_prefix}.url must be an official SEC archive URL")
                for key in ("form_type", "accession"):
                    if not isinstance(document.get(key), str) or not document.get(key):
                        errors.append(f"{doc_prefix}.{key} is required")

        evidence = packet_version.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{prefix}.evidence must be a non-empty list")
        else:
            evidence_count += len(evidence)
            evidence_ids: list[str] = []
            for evidence_position, item in enumerate(evidence):
                item_prefix = f"{prefix}.evidence[{evidence_position}]"
                if not isinstance(item, dict):
                    errors.append(f"{item_prefix} must be an object")
                    continue
                evidence_id = item.get("evidence_id")
                text = item.get("text")
                if not isinstance(evidence_id, str) or not evidence_id:
                    errors.append(f"{item_prefix}.evidence_id is required")
                else:
                    evidence_ids.append(evidence_id)
                if not isinstance(text, str) or not text.strip():
                    errors.append(f"{item_prefix}.text is required")
            if len(evidence_ids) != len(set(evidence_ids)):
                errors.append(f"{prefix}.evidence contains duplicate evidence_id values")

    if packet_version_ids != set(gold_versions):
        errors.append(f"{case_id}.source_packet and gold versions must align exactly")
    if required_version in packet_dates and packet_dates:
        if packet_dates[required_version] != max(packet_dates.values()):
            errors.append(f"{case_id}.required_source_version must be the latest packet date")

    changed_facts: list[str] = []
    changed_risks: list[str] = []
    if len(gold_versions) >= 2:
        ordered = sorted(
            gold_versions,
            key=lambda item: packet_dates.get(str(item), date.min),
        )
        first = gold_versions[ordered[0]]
        last = gold_versions[ordered[-1]]
        first_facts = first.get("facts", {}) if isinstance(first, dict) else {}
        last_facts = last.get("facts", {}) if isinstance(last, dict) else {}
        changed_facts = [
            key for key in REQUIRED_FACTS if first_facts.get(key) != last_facts.get(key)
        ]
        first_risks = set(first.get("risk_flags", [])) if isinstance(first, dict) else set()
        last_risks = set(last.get("risk_flags", [])) if isinstance(last, dict) else set()
        changed_risks = sorted(first_risks.symmetric_difference(last_risks))
        if not changed_facts and not changed_risks:
            errors.append(f"{case_id} has no version-sensitive target")

    return CaseValidation(
        case_id=case_id,
        workflow_id=workflow_id,
        issuer=issuer,
        ticker=ticker,
        source_versions=len(packet_versions),
        documents=document_count,
        evidence_items=evidence_count,
        changed_facts=changed_facts,
        changed_risks=changed_risks,
        errors=errors,
    )


def validate_index(index_path: Path) -> dict[str, Any]:
    index_path = index_path.resolve()
    index = _read_json(index_path)
    cases = index.get("cases")
    top_errors: list[str] = []
    if not isinstance(index.get("dataset_id"), str) or not index.get("dataset_id"):
        top_errors.append("dataset_id is required")
    if not isinstance(cases, list) or not cases:
        top_errors.append("cases must be a non-empty list")
        cases = []

    reports: list[CaseValidation] = []
    for position, entry in enumerate(cases):
        if not isinstance(entry, dict):
            top_errors.append(f"cases[{position}] must be an object")
            continue
        reports.append(validate_case(entry, index_path))

    case_ids = [report.case_id for report in reports]
    workflow_ids = [report.workflow_id for report in reports]
    if len(case_ids) != len(set(case_ids)):
        top_errors.append("case_id values must be unique")
    if len(workflow_ids) != len(set(workflow_ids)):
        top_errors.append("workflow_id values must be unique")

    errors = top_errors + [error for report in reports for error in report.errors]
    return {
        "result_type": "real_ipo_case_validation_not_model_results",
        "dataset_id": index.get("dataset_id"),
        "valid": not errors,
        "case_count": len(reports),
        "document_count": sum(report.documents for report in reports),
        "evidence_item_count": sum(report.evidence_items for report in reports),
        "errors": errors,
        "cases": [report.to_dict() for report in reports],
    }
