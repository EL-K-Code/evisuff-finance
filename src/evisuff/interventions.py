from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations

from .schema import BenchmarkItem, EvidenceUnit


@dataclass(frozen=True)
class Condition:
    item_id: str
    condition: str
    expected_answerable: bool
    evidence: tuple[EvidenceUnit, ...]
    removed_evidence_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        value = asdict(self)
        value["evidence"] = [asdict(x) for x in self.evidence]
        return value


def minimal_hitting_set(minimal_sets: tuple[tuple[str, ...], ...]) -> tuple[str, ...]:
    """Return the lexicographically first smallest set breaking every MSES.

    A removal intervention is only guaranteed to make a question unanswerable
    if it intersects every known minimal sufficient evidence set.
    """

    sets = [set(x) for x in minimal_sets]
    if not sets or any(not x for x in sets):
        raise ValueError("minimal evidence sets must be non-empty")
    universe = sorted(set().union(*sets))
    for size in range(1, len(universe) + 1):
        for candidate in combinations(universe, size):
            if all(set(candidate) & evidence_set for evidence_set in sets):
                return tuple(candidate)
    raise RuntimeError("no hitting set found")


def _without(item: BenchmarkItem, removed: set[str]) -> tuple[EvidenceUnit, ...]:
    return tuple(x for x in item.evidence if x.evidence_id not in removed)


def build_conditions(item: BenchmarkItem) -> list[Condition]:
    errors = item.validate()
    if errors:
        raise ValueError("; ".join(errors))

    primary_gold = set(item.minimal_evidence_sets[0])
    necessary = set(minimal_hitting_set(item.minimal_evidence_sets))
    conditions = [
        Condition(
            item_id=item.item_id,
            condition="full",
            expected_answerable=True,
            evidence=item.evidence,
        ),
        Condition(
            item_id=item.item_id,
            condition="gold_only",
            expected_answerable=True,
            evidence=tuple(
                x for x in item.evidence if x.evidence_id in primary_gold
            ),
            removed_evidence_ids=tuple(sorted(item.evidence_ids - primary_gold)),
        ),
        Condition(
            item_id=item.item_id,
            condition="necessary_removal",
            expected_answerable=False,
            evidence=_without(item, necessary),
            removed_evidence_ids=tuple(sorted(necessary)),
        ),
    ]

    if item.distractor_ids:
        distractor = {sorted(item.distractor_ids)[0]}
        conditions.append(
            Condition(
                item_id=item.item_id,
                condition="irrelevant_removal",
                expected_answerable=True,
                evidence=_without(item, distractor),
                removed_evidence_ids=tuple(distractor),
            )
        )
    return conditions


def complete_evidence_retrieved(
    retrieved_ids: set[str], minimal_sets: tuple[tuple[str, ...], ...]
) -> bool:
    """True when at least one complete minimal evidence set was retrieved."""

    return any(set(evidence_set) <= retrieved_ids for evidence_set in minimal_sets)

