from pathlib import Path
import json

from typer.testing import CliRunner

from earf import __version__
from earf.cli import app


runner = CliRunner()


def _valid_rule_yaml(rule_id: str = "GOV-001") -> str:
    return f"""
rules:
  - id: {rule_id}
    title: Ownership documented
    description: Owner exists
    category: governance
    severity: high
    version: "1.0"
    enabled: true
    applicability: {{always: true}}
    rationale: Why
    recommendation: Do this
    tags: [governance]
    references: []
    evidence_requirements: {{any: []}}
    metadata: {{}}
""".strip()


def _write_rules(tmp_path: Path, filename: str = "rules.yaml", rule_id: str = "GOV-001") -> Path:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir(exist_ok=True)
    (rules_dir / filename).write_text(_valid_rule_yaml(rule_id), encoding="utf-8")
    return rules_dir


def _evaluation_rules_yaml() -> str:
    return """
rules:
  - id: GOV-001
    title: Readme exists
    description: Repository has readme
    category: governance
    severity: high
    version: "1.0"
    enabled: true
    applicability: {always: true}
    rationale: why
    recommendation: do
    tags: []
    references: []
    evidence_requirements:
      evidence_type: file
      identifiers: [README.md]
    metadata: {}

  - id: SEC-001
    title: Security file exists
    description: Repository has security file
    category: security
    severity: high
    version: "1.0"
    enabled: true
    applicability: {always: true}
    rationale: why
    recommendation: do
    tags: []
    references: []
    evidence_requirements:
      evidence_type: file
      identifiers: [SECURITY.md]
    metadata: {}
""".strip()


def _score_rules_yaml() -> str:
    return "\n".join(
        [
            "rules:",
            "  - id: GOV-001",
            "    title: Readme exists",
            "    description: Repository has readme",
            "    category: governance",
            "    severity: high",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: do",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [README.md]",
            "    metadata: {}",
            "",
            "  - id: SEC-001",
            "    title: Security file exists",
            "    description: Repository has security file",
            "    category: security",
            "    severity: medium",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: do",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [SECURITY.md]",
            "    metadata: {}",
            "",
            "  - id: REL-001",
            "    title: Dockerfile exists",
            "    description: Repository has Dockerfile",
            "    category: reliability",
            "    severity: low",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: do",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [Dockerfile]",
            "    metadata: {}",
        ]
    )


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"EARF {__version__}" in result.stdout


def test_rules_list_command(tmp_path: Path) -> None:
    rules_dir = _write_rules(tmp_path)
    result = runner.invoke(app, ["rules", "list", "--path", str(rules_dir)])
    assert result.exit_code == 0
    assert "ID  Category  Severity  Title  Enabled" in result.stdout
    assert "GOV-001" in result.stdout
    assert "1 rules loaded." in result.stdout


def test_rules_validate_command(tmp_path: Path) -> None:
    rules_dir = _write_rules(tmp_path)
    result = runner.invoke(app, ["rules", "validate", "--path", str(rules_dir)])
    assert result.exit_code == 0
    assert "Rule catalog is valid." in result.stdout
    assert "1 rules loaded from 1 files." in result.stdout


def test_rules_show_command(tmp_path: Path) -> None:
    rules_dir = _write_rules(tmp_path)
    result = runner.invoke(app, ["rules", "show", "GOV-001", "--path", str(rules_dir)])
    assert result.exit_code == 0
    assert "id: GOV-001" in result.stdout
    assert "category: governance" in result.stdout
    assert "severity: high" in result.stdout


def test_rules_custom_path(tmp_path: Path) -> None:
    custom = tmp_path / "custom-rules"
    custom.mkdir()
    (custom / "catalog.yml").write_text(_valid_rule_yaml("GOV-002"), encoding="utf-8")

    result = runner.invoke(app, ["rules", "list", "--path", str(custom)])
    assert result.exit_code == 0
    assert "GOV-002" in result.stdout


def test_rules_invalid_path() -> None:
    result = runner.invoke(app, ["rules", "validate", "--path", "no-such-path"])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Traceback" not in result.stdout


def test_rules_malformed_yaml(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "broken.yaml").write_text("rules: [", encoding="utf-8")

    result = runner.invoke(app, ["rules", "validate", "--path", str(rules_dir)])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Malformed YAML" in result.stdout
    assert "Traceback" not in result.stdout


def test_rules_duplicate_ids(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "one.yaml").write_text(_valid_rule_yaml("GOV-001"), encoding="utf-8")
    (rules_dir / "two.yaml").write_text(_valid_rule_yaml("GOV-001"), encoding="utf-8")

    result = runner.invoke(app, ["rules", "validate", "--path", str(rules_dir)])
    assert result.exit_code != 0
    assert "Duplicate rule id" in result.stdout
    assert "Traceback" not in result.stdout


def test_rules_unknown_id(tmp_path: Path) -> None:
    rules_dir = _write_rules(tmp_path)
    result = runner.invoke(app, ["rules", "show", "GOV-999", "--path", str(rules_dir)])
    assert result.exit_code != 0
    assert "Rule not found" in result.stdout
    assert "Traceback" not in result.stdout


def test_rules_non_zero_exit_on_error(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "invalid.yaml").write_text("rules: {}", encoding="utf-8")

    result = runner.invoke(app, ["rules", "list", "--path", str(rules_dir)])
    assert result.exit_code != 0
    assert "Error:" in result.stdout


def test_scan_valid(tmp_path: Path) -> None:
    d = tmp_path / "proj"
    d.mkdir()
    result = runner.invoke(app, ["scan", str(d)])
    assert result.exit_code == 0
    assert "Repository loaded successfully." in result.stdout
    assert "Project: proj" in result.stdout
    assert f"Path: {d.resolve()}" in result.stdout
    assert "Repository scanning is not implemented in Phase 1." in result.stdout


def test_scan_invalid() -> None:
    result = runner.invoke(app, ["scan", "no-such-path"])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Traceback" not in result.stdout


def test_scan_file_path_invalid(tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("hi")
    result = runner.invoke(app, ["scan", str(f)])
    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Path is not a directory" in result.stdout
    assert "Traceback" not in result.stdout


def test_evidence_command_summary(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("typer>=0.10", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='x'\ndependencies=['rich>=13']",
        encoding="utf-8",
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: ci", encoding="utf-8")

    result = runner.invoke(app, ["evidence", str(tmp_path)])

    assert result.exit_code == 0
    assert "Repository loaded successfully" in result.stdout
    assert "Evidence Summary" in result.stdout
    assert "Files: 1" in result.stdout
    assert "Dependencies: 2" in result.stdout
    assert "Workflows: 1" in result.stdout
    assert "Configurations: 1" in result.stdout
    assert "Total Evidence: 5" in result.stdout


def _report_rules_yaml() -> str:
    return "\n".join(
        [
            "rules:",
            "  - id: GOV-001",
            "    title: Ownership documented",
            "    description: Repository has owner file",
            "    category: governance",
            "    severity: high",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: Add CODEOWNERS or OWNERS.",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [CODEOWNERS]",
            "    metadata: {}",
            "",
            "  - id: SAF-001",
            "    title: Input validation present",
            "    description: Repository validates inputs",
            "    category: safety",
            "    severity: critical",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: Implement input validation.",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [SECURITY.md]",
            "    metadata: {}",
            "",
            "  - id: REL-001",
            "    title: Timeouts defined",
            "    description: Repository defines timeouts",
            "    category: reliability",
            "    severity: high",
            "    version: \"1.0\"",
            "    enabled: true",
            "    applicability: {always: true}",
            "    rationale: why",
            "    recommendation: Add timeouts.",
            "    tags: []",
            "    references: []",
            "    evidence_requirements:",
            "      evidence_type: file",
            "      identifiers: [Dockerfile]",
            "    metadata: {}",
        ]
    )


def test_evidence_command_empty_repository(tmp_path: Path) -> None:
    result = runner.invoke(app, ["evidence", str(tmp_path)])

    assert result.exit_code == 0
    assert "Files: 0" in result.stdout
    assert "Dependencies: 0" in result.stdout
    assert "Workflows: 0" in result.stdout
    assert "Configurations: 0" in result.stdout
    assert "Total Evidence: 0" in result.stdout


def test_evidence_command_invalid_path() -> None:
    result = runner.invoke(app, ["evidence", "no-such-path"])

    assert result.exit_code != 0
    assert "Error:" in result.stdout
    assert "Traceback" not in result.stdout


def test_evaluate_command_summary(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_evaluation_rules_yaml(), encoding="utf-8")

    result = runner.invoke(
        app,
        ["evaluate", str(tmp_path), "--rules-path", str(rules_dir)],
    )

    assert result.exit_code == 0
    assert "Rule Evaluation" in result.stdout
    assert "GOV-001" in result.stdout
    assert "SEC-001" in result.stdout
    assert "Passed: 1" in result.stdout
    assert "Failed: 1" in result.stdout
    assert "Total: 2" in result.stdout


def test_evaluate_command_show_evidence(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_evaluation_rules_yaml(), encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "evaluate",
            str(tmp_path),
            "--rules-path",
            str(rules_dir),
            "--show-evidence",
        ],
    )

    assert result.exit_code == 0
    assert "matched: README.md (README.md)" in result.stdout


def test_score_command_hundred_percent_repository(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("security", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.11", encoding="utf-8")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_score_rules_yaml(), encoding="utf-8")

    result = runner.invoke(app, ["score", str(tmp_path), "--rules-path", str(rules_dir)])

    assert result.exit_code == 0
    assert "Overall Readiness" in result.stdout
    assert "100.0 / 100" in result.stdout
    assert "Production Status" in result.stdout
    assert "READY" in result.stdout
    assert "Passed: 3" in result.stdout
    assert "Failed: 0" in result.stdout
    assert "Critical Failures: 0" in result.stdout


def test_score_command_zero_percent_repository(tmp_path: Path) -> None:
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_score_rules_yaml(), encoding="utf-8")

    result = runner.invoke(app, ["score", str(tmp_path), "--rules-path", str(rules_dir)])

    assert result.exit_code == 0
    assert "0.0 / 100" in result.stdout
    assert "NOT_READY" in result.stdout
    assert "Passed: 0" in result.stdout
    assert "Failed: 3" in result.stdout


def test_score_command_mixed_repository(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    (tmp_path / "SECURITY.md").write_text("security", encoding="utf-8")

    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_score_rules_yaml(), encoding="utf-8")

    result = runner.invoke(app, ["score", str(tmp_path), "--rules-path", str(rules_dir)])

    assert result.exit_code == 0
    assert "84.6 / 100" in result.stdout
    assert "READY_WITH_WARNINGS" in result.stdout
    assert "Passed: 2" in result.stdout
    assert "Failed: 1" in result.stdout


def test_report_command_console_output(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_report_rules_yaml(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["report", str(tmp_path), "--rules-path", str(rules_dir)])

    assert result.exit_code == 0
    assert "EARF Enterprise AI Readiness Report" in result.stdout
    assert "Overall Assessment" in result.stdout
    assert "Core Readiness:" in result.stdout
    assert "Automated Evaluation Coverage:" in result.stdout
    assert "Production Status" in result.stdout
    assert "Why?" in result.stdout
    assert "Critical Blockers" in result.stdout
    assert "SAF-001" in result.stdout
    assert "Top Core Gaps" in result.stdout
    assert "Advanced Opportunities" in result.stdout
    assert "Passed Controls" in result.stdout


def test_report_command_json_writes_file(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_report_rules_yaml(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["report", str(tmp_path), "--rules-path", str(rules_dir), "--format", "json"],
    )

    assert result.exit_code == 0
    output_path = tmp_path / "earf-report.json"
    assert output_path.is_file()
    assert "Report written to: earf-report.json" in result.stdout
    parsed = json.loads(output_path.read_text(encoding="utf-8"))
    assert parsed["repository_name"] == tmp_path.name


def test_report_command_markdown_writes_file(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_report_rules_yaml(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        ["report", str(tmp_path), "--rules-path", str(rules_dir), "--format", "markdown"],
    )

    assert result.exit_code == 0
    output_path = tmp_path / "EARF_REPORT.md"
    assert output_path.is_file()
    assert "Report written to: EARF_REPORT.md" in result.stdout


def test_report_command_custom_output_path(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_report_rules_yaml(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    output_path = tmp_path / "custom-report.json"

    result = runner.invoke(
        app,
        [
            "report",
            str(tmp_path),
            "--rules-path",
            str(rules_dir),
            "--format",
            "json",
            "--output",
            str(output_path),
        ],
    )

    assert result.exit_code == 0
    assert output_path.is_file()
    assert f"Report written to: {output_path}" in result.stdout


def test_report_command_rejects_output_with_console(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("readme", encoding="utf-8")
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()
    (rules_dir / "rules.yaml").write_text(_report_rules_yaml(), encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(
        app,
        [
            "report",
            str(tmp_path),
            "--rules-path",
            str(rules_dir),
            "--format",
            "console",
            "--output",
            "report.txt",
        ],
    )

    assert result.exit_code != 0
    assert "--output is not supported with console format" in result.stdout
