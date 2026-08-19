from __future__ import annotations

from pathlib import Path

from earf.github_action_summary import DISCLAIMER, render_summary, write_step_summary


def test_render_summary_includes_expected_fields() -> None:
    payload = {
        "overall_score": 74,
        "production_status": "READY_WITH_WARNINGS",
        "category_scores": {"reliability": 82, "governance": 76, "observability": 64},
        "critical_findings": [],
        "high_findings": [{"rule_id": "REL-001"}, {"rule_id": "REL-002"}, {"rule_id": "OBS-001"}],
    }

    summary = render_summary(payload)

    assert "## EARF Enterprise AI Readiness" in summary
    assert "Overall Score: 74 / 100" in summary
    assert "Status: READY_WITH_WARNINGS" in summary
    assert "- governance: 76" in summary
    assert "- observability: 64" in summary
    assert "- reliability: 82" in summary
    assert "Critical Findings: 0" in summary
    assert "High Findings: 3" in summary
    assert "earf-report.json" in summary
    assert "EARF_REPORT.md" in summary
    assert DISCLAIMER in summary


def test_write_step_summary_writes_to_github_summary_file(tmp_path: Path, monkeypatch) -> None:
    summary_file = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    write_step_summary("hello summary")

    assert summary_file.read_text(encoding="utf-8") == "hello summary\n"
