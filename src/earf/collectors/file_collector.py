from __future__ import annotations

from .base import EvidenceCollector
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
        root = context.root_path
        items: list[Evidence] = []
        for filename in self._TARGET_FILES:
            file_path = root / filename
            if not file_path.is_file():
                continue
            rel_path = str(file_path.relative_to(root))
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
