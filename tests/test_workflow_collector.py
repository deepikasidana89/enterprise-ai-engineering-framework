from pathlib import Path

from earf.collectors.workflow_collector import WorkflowCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_workflow_collector_collects_workflow_filenames(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci", encoding="utf-8")
    (workflows / "release.yaml").write_text("name: release", encoding="utf-8")

    collector = WorkflowCollector()
    items = collector.collect(_context(tmp_path))

    assert [item.identifier for item in items] == ["ci.yml", "release.yaml"]


def test_workflow_collector_missing_dir(tmp_path: Path) -> None:
    collector = WorkflowCollector()
    assert collector.collect(_context(tmp_path)) == []
