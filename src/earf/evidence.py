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

    def find_by_type(self, evidence_type: EvidenceType) -> List[Evidence]:
        return self.filter_by_type(evidence_type)

    def find_by_identifier(self, identifier: str) -> List[Evidence]:
        token = identifier.strip()
        return [e for e in self._items if e.identifier.strip() == token]

    def find(
        self,
        evidence_type: EvidenceType | None = None,
        identifier: str | None = None,
        source: str | None = None,
        path: str | None = None,
    ) -> List[Evidence]:
        items = self._items
        if evidence_type is not None:
            items = [e for e in items if e.evidence_type == evidence_type]
        if identifier is not None:
            token = identifier.strip()
            items = [e for e in items if e.identifier.strip() == token]
        if source is not None:
            source_token = source.strip().lower()
            items = [e for e in items if e.source.strip().lower() == source_token]
        if path is not None:
            path_token = path.strip().replace("\\", "/")
            items = [e for e in items if (e.path or "").strip().replace("\\", "/") == path_token]
        return list(items)

    def count(self) -> int:
        return len(self._items)

    def clear(self) -> None:
        self._items.clear()
