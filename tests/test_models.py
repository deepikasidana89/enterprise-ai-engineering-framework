from pathlib import Path

import pytest

from earf.models import (
    ScanStatus,
    Severity,
    EvidenceType,
    RepositoryFile,
    RepositoryContext,
    Evidence,
    RuleResult,
)


def test_enums_values() -> None:
    assert ScanStatus.PASS.value == "PASS"
    assert Severity.CRITICAL.value == "CRITICAL"
    assert EvidenceType.FILE.value == "FILE"


def test_repository_file_and_context_defaults(tmp_path: Path) -> None:
    rf = RepositoryFile(path=tmp_path / "x", relative_path=Path("x"), extension=".md", size_bytes=10)
    ctx = RepositoryContext(root_path=tmp_path, project_name="proj")
    assert rf.size_bytes == 10
    assert ctx.project_name == "proj"


def test_rule_result_confidence_validation() -> None:
    # Valid confidence
    r = RuleResult(rule_id="r1", status=ScanStatus.PASS, confidence=0.5)
    assert r.confidence == 0.5

    # Invalid confidence
    with pytest.raises(ValueError):
        RuleResult(rule_id="r2", status=ScanStatus.FAIL, confidence=1.5)


def test_metadata_accepts_complex_values() -> None:
    metadata = {
        "name": "sample",
        "enabled": True,
        "count": 3,
        "score": 0.8,
        "tags": ["ai", "security"],
        "config": {"timeout": 30},
    }

    ctx = RepositoryContext(root_path=Path("/tmp"), project_name="proj", metadata=metadata)
    assert ctx.metadata["name"] == "sample"
    assert ctx.metadata["enabled"] is True
    assert ctx.metadata["count"] == 3
    assert ctx.metadata["score"] == 0.8
    assert ctx.metadata["tags"] == ["ai", "security"]
    assert ctx.metadata["config"] == {"timeout": 30}

    evidence = Evidence(
        evidence_type=EvidenceType.FILE,
        source="src",
        description="desc",
        metadata=metadata,
    )
    assert evidence.metadata["tags"] == ["ai", "security"]


def test_package_version_is_defined() -> None:
    import earf

    assert earf.__version__
