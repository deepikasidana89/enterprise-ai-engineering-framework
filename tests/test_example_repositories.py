from __future__ import annotations

from pathlib import Path

from earf.pipeline import EARFPipeline
from earf.scoring.models import ProductionReadiness


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def test_ready_example_passes_critical_rules() -> None:
    analysis = EARFPipeline().analyze(_project_root() / "examples" / "ready-ai-project")

    assert analysis.readiness_score.critical_failures == 0
    assert analysis.readiness_score.passed_rules >= 8
    assert analysis.readiness_score.production_readiness in {
        ProductionReadiness.READY,
        ProductionReadiness.READY_WITH_WARNINGS,
    }


def test_not_ready_example_fails_readiness() -> None:
    analysis = EARFPipeline().analyze(_project_root() / "examples" / "not-ready-ai-project")

    assert analysis.readiness_score.production_readiness == ProductionReadiness.NOT_READY
    assert analysis.readiness_score.failed_rules >= 5
    assert analysis.readiness_score.critical_failures >= 1
