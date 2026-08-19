from __future__ import annotations

from .base import EvidenceCollector
from .workspace_index import ensure_workspace_index
from ..models import Evidence, EvidenceType, RepositoryContext


class ConfigCollector(EvidenceCollector):
    name = "configuration"

    _CONFIG_FILES = (
        "ruff.toml",
        "pyproject.toml",
        "pytest.ini",
        "mypy.ini",
        ".pre-commit-config.yaml",
        ".editorconfig",
    )
    _CONFIG_SUFFIXES = {
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".properties",
        ".conf",
        ".ini",
        ".xml",
        ".env.example",
    }

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        index = ensure_workspace_index(context)

        items: list[Evidence] = []
        seen_paths: set[str] = set()

        for filename in self._CONFIG_FILES:
            for indexed in index.by_name({filename}):
                rel_path = indexed.relative_path
                seen_paths.add(rel_path)
                items.append(
                    Evidence(
                        evidence_type=EvidenceType.CONFIGURATION,
                        source=self.name,
                        description=f"Configuration file found: {filename}",
                        identifier=filename,
                        path=rel_path,
                        location=rel_path,
                        metadata={"collector": self.name},
                    )
                )

        for indexed in index.files:
            filename = indexed.path.name
            if filename not in self._CONFIG_FILES and indexed.suffix not in self._CONFIG_SUFFIXES:
                continue
            rel_path = indexed.relative_path
            if rel_path in seen_paths:
                continue
            items.append(
                Evidence(
                    evidence_type=EvidenceType.CONFIGURATION,
                    source=self.name,
                    description=f"Configuration file found: {filename}",
                    identifier=filename,
                    path=rel_path,
                    location=rel_path,
                    metadata={"collector": self.name},
                )
            )

        return items


# Backward-compatible alias for existing imports.
ConfigurationEvidenceCollector = ConfigCollector
