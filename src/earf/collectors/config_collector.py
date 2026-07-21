from __future__ import annotations

from .base import EvidenceCollector
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

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        root = context.root_path
        items: list[Evidence] = []

        for filename in self._CONFIG_FILES:
            config_path = root / filename
            if not config_path.is_file():
                continue

            rel_path = str(config_path.relative_to(root))
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
