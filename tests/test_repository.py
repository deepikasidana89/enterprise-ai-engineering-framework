from pathlib import Path

import pytest

from earf.repository import RepositoryLoader
from earf.evidence import EvidenceRepository
from earf.models import Evidence, EvidenceType


def test_repository_loader_valid(tmp_path: Path) -> None:
    d = tmp_path / "proj"
    d.mkdir()
    loader = RepositoryLoader()
    ctx = loader.load(d)
    assert ctx.project_name == "proj"


def test_repository_loader_invalid_path(tmp_path: Path) -> None:
    loader = RepositoryLoader()
    with pytest.raises(Exception):
        loader.load(tmp_path / "nope")


def test_repository_loader_file_instead_of_dir(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("hi")
    loader = RepositoryLoader()
    with pytest.raises(Exception):
        loader.load(f)


def test_evidence_repository_add_and_filter() -> None:
    repo = EvidenceRepository()
    e1 = Evidence(evidence_type=EvidenceType.FILE, source="sc1", description="d1")
    e2 = Evidence(evidence_type=EvidenceType.DEPENDENCY, source="sc2", description="d2")
    repo.add(e1)
    repo.add_many([e2])
    all_items = repo.all()
    assert len(all_items) == 2
    files = repo.filter_by_type(EvidenceType.FILE)
    assert files[0].source == "sc1"
    by_source = repo.filter_by_source("sc2")
    assert by_source and by_source[0].description == "d2"


def test_evidence_repository_clear() -> None:
    repo = EvidenceRepository()
    e1 = Evidence(evidence_type=EvidenceType.FILE, source="sc1", description="d1")
    repo.add(e1)
    assert repo.all()
    repo.clear()
    assert repo.all() == []
