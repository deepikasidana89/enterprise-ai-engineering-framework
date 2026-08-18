from __future__ import annotations

import json

from .collectors.base import EvidenceCollector
from .collectors.config_collector import ConfigCollector
from .collectors.dependency_collector import DependencyCollector
from .collectors.file_collector import FileCollector
from .collectors.secret_management_collector import SecretManagementCollector
from .collectors.workflow_collector import WorkflowCollector
from .evidence import EvidenceRepository
from .models import Evidence, RepositoryContext


class EvidenceCollectionService:
    def __init__(self, collectors: list[EvidenceCollector] | None = None) -> None:
        self._collectors = collectors or [
            FileCollector(),
            DependencyCollector(),
            WorkflowCollector(),
            ConfigCollector(),
            SecretManagementCollector(),
        ]

    def collect(
        self,
        context: RepositoryContext,
        repository: EvidenceRepository | None = None,
    ) -> EvidenceRepository:
        repo = repository or EvidenceRepository()

        merged: list[Evidence] = []
        for collector in self._collectors:
            merged.extend(collector.collect(context))

        unique = self._deduplicate(merged)
        repo.add_many(unique)
        return repo

    def _deduplicate(self, evidence_items: list[Evidence]) -> list[Evidence]:
        seen: set[str] = set()
        result: list[Evidence] = []

        for item in evidence_items:
            key = self._fingerprint(item)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)

        return result

    @staticmethod
    def _fingerprint(item: Evidence) -> str:
        metadata_key = json.dumps(item.metadata, sort_keys=True, separators=(",", ":"))
        return "|".join(
            [
                item.evidence_type.value,
                item.source,
                item.description,
                item.identifier,
                item.path or "",
                item.location or "",
                metadata_key,
                str(item.confidence),
                item.timestamp or "",
            ]
        )
