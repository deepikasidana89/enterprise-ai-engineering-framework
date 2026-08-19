from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


DISCLAIMER = (
    "EARF findings indicate implementation evidence and are not certification "
    "or compliance approval."
)


def load_report(report_path: Path) -> dict[str, object]:
    with report_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("EARF report payload must be a JSON object.")
    return payload


def render_summary(payload: dict[str, object]) -> str:
    overall_score = payload.get("overall_score", "N/A")
    production_status = payload.get("production_status", "UNKNOWN")
    category_scores = payload.get("category_scores", {})
    critical_findings = payload.get("critical_findings", [])
    high_findings = payload.get("high_findings", [])

    lines: list[str] = [
        "## EARF Enterprise AI Readiness",
        f"Overall Score: {overall_score} / 100",
        f"Status: {production_status}",
        "",
        "### Category Scores",
    ]

    if isinstance(category_scores, dict) and category_scores:
        for category in sorted(category_scores.keys()):
            score = category_scores.get(category)
            lines.append(f"- {category}: {score}")
    else:
        lines.append("- None")

    critical_count = len(critical_findings) if isinstance(critical_findings, list) else 0
    high_count = len(high_findings) if isinstance(high_findings, list) else 0

    lines.extend(
        [
            "",
            f"Critical Findings: {critical_count}",
            f"High Findings: {high_count}",
            "",
            "Reports:",
            "- earf-report.json",
            "- EARF_REPORT.md",
            "",
            DISCLAIMER,
        ]
    )

    return "\n".join(lines)


def write_step_summary(summary_text: str) -> None:
    destination = os.environ.get("GITHUB_STEP_SUMMARY", "").strip()
    if not destination:
        return

    summary_path = Path(destination)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with summary_path.open("a", encoding="utf-8") as handle:
        handle.write(summary_text)
        handle.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render EARF GitHub Actions step summary")
    parser.add_argument("--report", required=True, help="Path to earf-report.json")
    args = parser.parse_args(argv)

    payload = load_report(Path(args.report))
    summary_text = render_summary(payload)

    print("EARF summary")
    print(f"Overall Score: {payload.get('overall_score', 'N/A')} / 100")
    print(f"Status: {payload.get('production_status', 'UNKNOWN')}")

    critical = payload.get("critical_findings", [])
    high = payload.get("high_findings", [])
    critical_count = len(critical) if isinstance(critical, list) else 0
    high_count = len(high) if isinstance(high, list) else 0
    print(f"Critical Findings: {critical_count}")
    print(f"High Findings: {high_count}")

    write_step_summary(summary_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
