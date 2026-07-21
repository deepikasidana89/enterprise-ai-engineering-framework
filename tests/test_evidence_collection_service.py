from pathlib import Path

from earf.collectors.base import EvidenceCollector
from earf.evidence import EvidenceRepository
from earf.evidence_collection import EvidenceCollectionService
from earf.models import Evidence, EvidenceType, RepositoryContext


class DuplicateCollector(EvidenceCollector):
    name = "dup"

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        return [
            Evidence(
                evidence_type=EvidenceType.FILE,
                source="file",
                description="same",
                identifier="README.md",
                path="README.md",
                location="README.md",
            ),
            Evidence(
                evidence_type=EvidenceType.FILE,
                source="file",
                description="same",
                identifier="README.md",
                path="README.md",
                location="README.md",
            ),
        ]


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_evidence_collection_service_runs_collectors_and_deduplicates(tmp_path: Path) -> None:
    service = EvidenceCollectionService(collectors=[DuplicateCollector()])
    repo = service.collect(_context(tmp_path))
    assert repo.count() == 1


def test_evidence_collection_service_uses_existing_repository(tmp_path: Path) -> None:
    service = EvidenceCollectionService(collectors=[DuplicateCollector()])
    repository = EvidenceRepository()
    result = service.collect(_context(tmp_path), repository=repository)
    assert result is repository
    assert result.count() == 1


def test_evidence_collection_service_default_collectors(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("x", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("typer>=0.10", encoding="utf-8")
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname = 'x'\ndependencies = ['rich>=13']",
        encoding="utf-8",
    )

    service = EvidenceCollectionService()
    repo = service.collect(_context(tmp_path))

    assert repo.filter_by_type(EvidenceType.FILE)
    assert repo.filter_by_type(EvidenceType.DEPENDENCY)
    assert repo.filter_by_type(EvidenceType.WORKFLOW)
    assert repo.filter_by_type(EvidenceType.CONFIGURATION)
