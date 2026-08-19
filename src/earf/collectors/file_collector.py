from __future__ import annotations

from .base import EvidenceCollector
from .workspace_index import ensure_workspace_index
from ..models import Evidence, EvidenceType, RepositoryContext


class FileCollector(EvidenceCollector):
    name = "file"

    _TARGET_FILES = (
        "README.md",
        "Dockerfile",
        "docker-compose.yml",
        "CODEOWNERS",
        "LICENSE",
        "SECURITY.md",
        "CONTRIBUTING.md",
        ".env.example",
    )

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        index = ensure_workspace_index(context)

        items: list[Evidence] = []
        for filename in self._TARGET_FILES:
            matched_files = [item for item in index.by_name({filename})]
            for indexed in matched_files:
                rel_path = indexed.relative_path
                items.append(
                    Evidence(
                        evidence_type=EvidenceType.FILE,
                        source=self.name,
                        description=f"Meaningful repository file found: {filename}",
                        identifier=filename,
                        path=rel_path,
                        location=rel_path,
                        metadata={"collector": self.name},
                    )
                )
        return items


# Backward-compatible alias for existing imports.
FileEvidenceCollector = FileCollector
