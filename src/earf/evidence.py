from __future__ import annotations

from typing import Iterable, List

from .models import Evidence, EvidenceType


class EvidenceRepository:
    """In-memory store for Evidence items."""

    def __init__(self) -> None:
        self._items: List[Evidence] = []

    def add(self, item: Evidence) -> None:
        self._items.append(item)

    def add_many(self, items: Iterable[Evidence]) -> None:
        self._items.extend(items)

    def all(self) -> List[Evidence]:
        return list(self._items)

    def filter_by_type(self, evidence_type: EvidenceType) -> List[Evidence]:
        return [e for e in self._items if e.evidence_type == evidence_type]

    def filter_by_source(self, source: str) -> List[Evidence]:
        return [e for e in self._items if e.source == source]

    def clear(self) -> None:
        self._items.clear()
