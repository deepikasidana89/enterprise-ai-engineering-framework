from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

import typer

from . import __version__
from .exceptions import InvalidRepositoryPathError, RuleDefinitionError
from .models import EvidenceType
from .pipeline import EARFPipeline
from .reporting import ReportWriter
from .repository import RepositoryLoader
from .rules.catalog import RuleCatalog
from .rules.results import RuleStatus

app = typer.Typer(help="EARF CLI")
rules_app = typer.Typer(help="Rule catalog commands")
app.add_typer(rules_app, name="rules")


def _pipeline(rules_path: Path | None = None) -> EARFPipeline:
    return EARFPipeline(rules_path=rules_path)


@app.command()
def version() -> None:
    """Show EARF version."""
    typer.echo(f"EARF {__version__}")


@app.command()
def scan(path: Path) -> None:
    """Load repository at PATH (Phase 1: scanning not implemented)."""
    try:
        context = RepositoryLoader().load(path)
        typer.echo("Repository loaded successfully.")
        typer.echo("")
        typer.echo(f"Project: {context.project_name}")
        typer.echo(f"Path: {context.root_path}")
        typer.echo("")
        typer.echo("Repository scanning is not implemented in Phase 1.")
        raise typer.Exit(code=0)
    except InvalidRepositoryPathError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def evidence(path: Path) -> None:
    """Collect repository evidence (Phase 3: collection only)."""
    try:
        analysis = _pipeline().analyze(path)
        context = analysis.repository_context
        repository = analysis.evidence_repository

        file_count = len(repository.filter_by_type(EvidenceType.FILE))
        dependency_count = len(repository.filter_by_type(EvidenceType.DEPENDENCY))
        workflow_count = len(repository.filter_by_type(EvidenceType.WORKFLOW))
        config_count = len(repository.filter_by_type(EvidenceType.CONFIGURATION))

        typer.echo("Repository loaded successfully")
        typer.echo("")
        typer.echo(f"Project: {context.project_name}")
        typer.echo(f"Path: {context.root_path}")
        typer.echo("")
        typer.echo("Evidence Summary")
        typer.echo("")
        typer.echo(f"Files: {file_count}")
        typer.echo(f"Dependencies: {dependency_count}")
        typer.echo(f"Workflows: {workflow_count}")
        typer.echo(f"Configurations: {config_count}")
        typer.echo("")
        typer.echo(f"Total Evidence: {repository.count()}")
    except InvalidRepositoryPathError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def evaluate(
    path: Path,
    show_evidence: bool = typer.Option(
        False,
        "--show-evidence",
        help="Show matched evidence identifiers per rule",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        help="Explain applicability and evidence decisions for each rule",
    ),
    rules_path: Path | None = typer.Option(
        None,
        "--rules-path",
        help="Rules file or directory",
    ),
) -> None:
    """Evaluate rules against collected evidence (Phase 4: matching only)."""
    try:
        analysis = _pipeline(rules_path).analyze(path)
        context = analysis.repository_context
        catalog = analysis.rule_catalog
        results = analysis.rule_results

        typer.echo(f"Repository: {context.project_name}")
        typer.echo("")
        typer.echo("Rule Evaluation")
        typer.echo("")
        typer.echo("ID       Status          Title")

        rule_lookup = {rule.id: rule for rule in catalog.all()}
        for result in results:
            title = rule_lookup.get(result.rule_id)
            title_text = title.title if title is not None else ""
            typer.echo(f"{result.rule_id:<8} {result.status.name:<15} {title_text}")
            if show_evidence and result.matched_evidence:
                rendered: list[str] = []
                for item in result.matched_evidence:
                    if item.location:
                        rendered.append(f"{item.identifier} ({item.location})")
                    elif item.path:
                        rendered.append(f"{item.identifier} ({item.path})")
                    else:
                        rendered.append(item.identifier)
                matched_ids = ", ".join(rendered)
                typer.echo(f"  matched: {matched_ids}")

            if explain:
                applicability_reason = str(result.metadata.get("applicability_reason", "")).strip()
                uncertain_reasons = result.metadata.get("applicability_uncertain_reasons", [])
                if result.status == RuleStatus.NOT_APPLICABLE:
                    typer.echo(f"  applicability: FALSE - {applicability_reason or 'No applicability evidence detected.'}")
                elif result.status == RuleStatus.NEEDS_SEMANTIC_REVIEW:
                    typer.echo(
                        f"  applicability: UNCERTAIN - {applicability_reason or 'Deterministic applicability is inconclusive.'}"
                    )
                    if isinstance(uncertain_reasons, list):
                        for reason in uncertain_reasons:
                            typer.echo(f"    uncertain_reason: {reason}")
                else:
                    typer.echo("  applicability: TRUE")

                if result.missing_requirements:
                    typer.echo("  missing_requirements:")
                    for requirement in result.missing_requirements:
                        typer.echo(f"    - {requirement}")

        summary = {
            RuleStatus.PASS: 0,
            RuleStatus.FAIL: 0,
            RuleStatus.MANUAL_REVIEW: 0,
            RuleStatus.NEEDS_SEMANTIC_REVIEW: 0,
            RuleStatus.NOT_APPLICABLE: 0,
            RuleStatus.DISABLED: 0,
            RuleStatus.ERROR: 0,
        }
        for result in results:
            summary[result.status] += 1

        typer.echo("")
        typer.echo("Summary")
        typer.echo("")
        typer.echo(f"Passed: {summary[RuleStatus.PASS]}")
        typer.echo(f"Failed: {summary[RuleStatus.FAIL]}")
        typer.echo(f"Manual Review: {summary[RuleStatus.MANUAL_REVIEW]}")
        typer.echo(f"Needs Semantic Review: {summary[RuleStatus.NEEDS_SEMANTIC_REVIEW]}")
        typer.echo(f"Not Applicable: {summary[RuleStatus.NOT_APPLICABLE]}")
        typer.echo(f"Disabled: {summary[RuleStatus.DISABLED]}")
        typer.echo(f"Errors: {summary[RuleStatus.ERROR]}")
        typer.echo(f"Total: {len(results)}")
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def score(
    path: Path,
    rules_path: Path | None = typer.Option(
        None,
        "--rules-path",
        help="Rules file or directory",
    ),
) -> None:
    """Calculate enterprise readiness score from rule evaluation results."""
    try:
        analysis = _pipeline(rules_path).analyze(path)
        context = analysis.repository_context
        readiness = analysis.readiness_score

        typer.echo(f"Repository: {context.project_name}")
        typer.echo("")
        typer.echo("Overall Readiness")
        typer.echo("")
        typer.echo(f"{readiness.overall_score:.1f} / 100")
        typer.echo("")
        typer.echo("Production Status")
        typer.echo("")
        typer.echo(readiness.production_readiness.value)
        typer.echo("")
        typer.echo("Category Scores")
        typer.echo("")
        typer.echo("Category          Score   Coverage")
        for category in readiness.category_ranking():
            detail = readiness.category_details.get(category)
            if detail is None:
                continue
            scored = detail.passed_rules + detail.failed_rules
            tracked = (
                detail.passed_rules
                + detail.failed_rules
                + detail.manual_review_rules
                + detail.needs_semantic_review_rules
                + detail.not_applicable_rules
                + detail.disabled_rules
                + detail.error_rules
            )
            value = readiness.category_scores.get(category)
            score_text = f"{value:>5.1f}" if value is not None else "  N/A"
            typer.echo(f"{category.title():<16}{score_text}   {scored}/{tracked}")

        typer.echo("")
        typer.echo("Summary")
        typer.echo("")
        typer.echo(f"Passed: {readiness.passed_rules}")
        typer.echo(f"Failed: {readiness.failed_rules}")
        typer.echo(f"Needs Semantic Review: {readiness.needs_semantic_review_rules}")
        typer.echo(f"Not Applicable: {readiness.not_applicable_rules}")
        typer.echo(f"Disabled: {readiness.disabled_rules}")
        typer.echo(f"Errors: {readiness.error_rules}")
        typer.echo(f"Critical Failures: {readiness.critical_failures}")
        typer.echo(f"High Failures: {readiness.high_failures}")
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def report(
    path: Path,
    output_format: str = typer.Option("console", "--format", help="Report output format"),
    output: Path | None = typer.Option(None, "--output", help="Output file for json or markdown reports"),
    rules_path: Path | None = typer.Option(
        None,
        "--rules-path",
        help="Rules file or directory",
    ),
) -> None:
    """Generate an enterprise AI readiness report."""
    try:
        analysis = _pipeline(rules_path).analyze(path)
        report_model = analysis.readiness_report
        assert report_model is not None
        writer = ReportWriter()

        selected_format = output_format.strip().lower()
        if selected_format == "console":
            if output is not None:
                typer.echo("Error: --output is not supported with console format")
                raise typer.Exit(code=2)
            typer.echo(writer.render_console(report_model))
        elif selected_format == "json":
            output_path = output or Path("earf-report.json")
            written = writer.write_json(report_model, output_path)
            typer.echo(f"Report written to: {written}")
        elif selected_format == "markdown":
            output_path = output or Path("EARF_REPORT.md")
            written = writer.write_markdown(report_model, output_path)
            typer.echo(f"Report written to: {written}")
        else:
            typer.echo(f"Error: unsupported format {output_format!r}")
            raise typer.Exit(code=2)
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


def _load_rule_catalog(path: Path) -> tuple[RuleCatalog, int]:
    catalog, file_count = RuleCatalog.from_path(path)
    return catalog, file_count


@rules_app.command("list")
def rules_list(
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")
) -> None:
    """List all loaded rules."""
    try:
        catalog, _ = _load_rule_catalog(path)
        rules = catalog.all()
        typer.echo("ID  Category  Severity  Title  Enabled")
        for rule in rules:
            typer.echo(
                f"{rule.id}  {rule.category}  {rule.severity.name.lower()}  {rule.title}  {rule.enabled}"
            )
        typer.echo("")
        typer.echo(f"{len(rules)} rules loaded.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("validate")
def rules_validate(
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")
) -> None:
    """Validate rule catalog."""
    try:
        catalog, file_count = _load_rule_catalog(path)
        typer.echo("Rule catalog is valid.")
        typer.echo(f"{len(catalog.all())} rules loaded from {file_count} files.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("show")
def rules_show(
    rule_id: str,
    path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory"),
) -> None:
    """Show one rule by ID."""
    try:
        catalog, _ = _load_rule_catalog(path)
        rule = catalog.get(rule_id)
        typer.echo(f"id: {rule.id}")
        typer.echo(f"title: {rule.title}")
        typer.echo(f"description: {rule.description}")
        typer.echo(f"category: {rule.category}")
        typer.echo(f"severity: {rule.severity.name.lower()}")
        typer.echo(f"version: {rule.version}")
        typer.echo(f"enabled: {rule.enabled}")
        typer.echo(f"applicability: {rule.applicability}")
        typer.echo(f"rationale: {rule.rationale}")
        typer.echo(f"recommendation: {rule.recommendation}")
        typer.echo(f"tags: {rule.tags}")
        typer.echo(f"references: {rule.references}")
        typer.echo(f"evidence_requirements: {rule.evidence_requirements}")
        typer.echo(f"metadata: {rule.metadata}")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


def main(argv: Optional[list[str]] | None = None) -> int:
    try:
        app(argv or sys.argv[1:])
    except SystemExit:
        raise
    return 0
