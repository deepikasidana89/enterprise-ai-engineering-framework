from __future__ import annotations

from pathlib import Path

from earf.evidence_collection import EvidenceCollectionService
from earf.models import RepositoryContext
from earf.rules.catalog import RuleCatalog
from earf.rules.evaluation_service import RuleEvaluationService
from earf.rules.results import RuleStatus


def _rules_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "rules"


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_rel_002_passes_with_retry_code_pattern_without_retry_dependencies(tmp_path: Path) -> None:
    # Applicability requires an AI dependency, but evidence requirements for REL-002
    # are satisfied by a code pattern in this scenario.
    (tmp_path / "requirements.txt").write_text("openai>=1.0.0", encoding="utf-8")
    (tmp_path / "service.py").write_text(
        "from tenacity import retry, stop_after_attempt\n"
        "@retry(stop=stop_after_attempt(3))\n"
        "def call_model():\n"
        "    return \"ok\"\n",
        encoding="utf-8",
    )

    catalog, _ = RuleCatalog.from_path(_rules_dir())
    rule = catalog.get("REL-002")
    evidence_repo = EvidenceCollectionService().collect(_context(tmp_path))
    result = RuleEvaluationService().evaluate_all(RuleCatalog([rule]), evidence_repo)[0]

    assert result.status == RuleStatus.PASS
    assert any(item.evidence_type.value == "CODE_PATTERN" for item in result.matched_evidence)
    assert any(item.identifier == "python_tenacity_retry" for item in result.matched_evidence)
