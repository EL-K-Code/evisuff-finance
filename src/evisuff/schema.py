from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any


@dataclass(frozen=True)
class EvidenceUnit:
    evidence_id: str
    document_id: str
    section: str
    text: str
    source_url: str | None = None
    published_at: str | None = None
    is_distractor: bool = False

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "EvidenceUnit":
        return cls(**value)

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.evidence_id.strip():
            errors.append("evidence_id is empty")
        if not self.document_id.strip():
            errors.append(f"{self.evidence_id}: document_id is empty")
        if not self.text.strip():
            errors.append(f"{self.evidence_id}: text is empty")
        if self.published_at:
            try:
                date.fromisoformat(self.published_at)
            except ValueError:
                errors.append(
                    f"{self.evidence_id}: published_at must be ISO YYYY-MM-DD"
                )
        return errors


@dataclass(frozen=True)
class BenchmarkItem:
    item_id: str
    question: str
    gold_answer: str
    atomic_claims: dict[str, str]
    evidence: tuple[EvidenceUnit, ...]
    minimal_evidence_sets: tuple[tuple[str, ...], ...]
    category: str
    document_ids: tuple[str, ...]
    cutoff_date: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "BenchmarkItem":
        return cls(
            item_id=value["item_id"],
            question=value["question"],
            gold_answer=value["gold_answer"],
            atomic_claims=dict(value["atomic_claims"]),
            evidence=tuple(EvidenceUnit.from_dict(x) for x in value["evidence"]),
            minimal_evidence_sets=tuple(
                tuple(x) for x in value["minimal_evidence_sets"]
            ),
            category=value["category"],
            document_ids=tuple(value["document_ids"]),
            cutoff_date=value.get("cutoff_date"),
            metadata=dict(value.get("metadata", {})),
        )

    @property
    def evidence_ids(self) -> set[str]:
        return {x.evidence_id for x in self.evidence}

    @property
    def distractor_ids(self) -> set[str]:
        return {x.evidence_id for x in self.evidence if x.is_distractor}

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.item_id.strip():
            errors.append("item_id is empty")
        if not self.question.strip():
            errors.append(f"{self.item_id}: question is empty")
        if not self.atomic_claims:
            errors.append(f"{self.item_id}: atomic_claims is empty")
        ids = [x.evidence_id for x in self.evidence]
        if len(ids) != len(set(ids)):
            errors.append(f"{self.item_id}: evidence IDs are not unique")
        for unit in self.evidence:
            errors.extend(unit.validate())
        if not self.minimal_evidence_sets:
            errors.append(f"{self.item_id}: no minimal evidence set")
        for index, evidence_set in enumerate(self.minimal_evidence_sets):
            if not evidence_set:
                errors.append(f"{self.item_id}: minimal set {index} is empty")
            missing = set(evidence_set) - self.evidence_ids
            if missing:
                errors.append(
                    f"{self.item_id}: minimal set {index} references missing IDs "
                    f"{sorted(missing)}"
                )
        sets = [set(x) for x in self.minimal_evidence_sets]
        for i, left in enumerate(sets):
            for j, right in enumerate(sets):
                if i != j and left > right:
                    errors.append(
                        f"{self.item_id}: set {i} is not minimal because it "
                        f"strictly contains set {j}"
                    )
        if self.cutoff_date:
            try:
                date.fromisoformat(self.cutoff_date)
            except ValueError:
                errors.append(f"{self.item_id}: cutoff_date must be ISO YYYY-MM-DD")
        return errors

