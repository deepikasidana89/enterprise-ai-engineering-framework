from pathlib import Path

from earf.collectors.file_collector import FileCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_file_collector_collects_meaningful_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")
    (tmp_path / "src.py").write_text("print('x')", encoding="utf-8")

    collector = FileCollector()
    items = collector.collect(_context(tmp_path))

    assert [item.identifier for item in items] == ["README.md", "Dockerfile"]
    assert all(item.source == "file" for item in items)


def test_file_collector_handles_empty_repository(tmp_path: Path) -> None:
    collector = FileCollector()
    assert collector.collect(_context(tmp_path)) == []
