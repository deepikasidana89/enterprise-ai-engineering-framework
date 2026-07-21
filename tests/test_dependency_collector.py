from pathlib import Path

from earf.collectors.dependency_collector import DependencyCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_dependency_collector_collects_from_requirements_and_pyproject(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        """
# comment
requests>=2.0
pydantic==2.8.0
requests>=2.0
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["typer>=0.10.0", "rich>=13.0"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff"]
""".strip(),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    items = collector.collect(_context(tmp_path))
    ids = [item.identifier for item in items]

    assert "requests" in ids
    assert "pydantic" in ids
    assert "typer" in ids
    assert "rich" in ids
    assert "pytest" in ids
    assert "ruff" in ids


def test_dependency_collector_handles_missing_files(tmp_path: Path) -> None:
    collector = DependencyCollector()
    assert collector.collect(_context(tmp_path)) == []


def test_dependency_collector_ignores_invalid_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project", encoding="utf-8")
    collector = DependencyCollector()
    assert collector.collect(_context(tmp_path)) == []
