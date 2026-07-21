from pathlib import Path

from earf.collectors.config_collector import ConfigCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_config_collector_collects_known_configs(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'", encoding="utf-8")
    (tmp_path / ".editorconfig").write_text("root=true", encoding="utf-8")

    collector = ConfigCollector()
    items = collector.collect(_context(tmp_path))

    assert [item.identifier for item in items] == ["pyproject.toml", ".editorconfig"]


def test_config_collector_missing_files(tmp_path: Path) -> None:
    collector = ConfigCollector()
    assert collector.collect(_context(tmp_path)) == []
