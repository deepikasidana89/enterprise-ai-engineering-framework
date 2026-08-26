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
    """Load repository at PATH."""
    try:
        context = RepositoryLoader().load(path)
        typer.echo("Repository loaded successfully.")
        typer.echo(f"Project: {context.project_name}")
        typer.echo(f"Path: {context.root_path}")
    except InvalidRepositoryPathError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def evidence(path: Path) -> None:
    """Collect repository evidence."""
    try:
        analysis = _pipeline().analyze(path)
        repository = analysis.evidence_repository
        typer.echo(f"Project: {analysis.repository_context.project_name}")
        typer.echo(f"Files: {len(repository.filter_by_type(EvidenceType.FILE))}")
        typer.echo(f"Dependencies: {len(repository.filter_by_type(EvidenceType.DEPENDENCY))}")
        typer.echo(f"Workflows: {len(repository.filter_by_type(EvidenceType.WORKFLOW))}")
        typer.echo(f"Configurations: {len(repository.filter_by_type(EvidenceType.CONFIGURATION))}")
        typer.echo(f"Total Evidence: {repository.count()}")
    except InvalidRepositoryPathError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def evaluate(
    path: Path,
    show_evidence: bool = typer.Option(False, "--show-evidence", help="Show matched evidence identifiers per rule"),
    explain: bool = typer.Option(False, "--explain", help="Explain applicability and evidence decisions for each rule"),
    rules_path: Path | None = typer.Option(None, "--rules-path", help="Rules file or directory"),
) -> None:
    """Evaluate rules against collected evidence."""
    try:
        analysis = _pipeline(rules_path).analyze(path)
        rule_lookup = {rule.id: rule for rule in analysis.rule_catalog.all()}
        typer.echo(f"Repository: {analysis.repository_context.project_name}\n")
        typer.echo("Rule Evaluation\n")
        typer.echo("ID       Status          Title")
        for result in analysis.rule_results:
            rule = rule_lookup.get(result.rule_id)
            typer.echo(f"{result.rule_id:<8} {result.status.name:<15} {rule.title if rule else ''}")
            if show_evidence and result.matched_evidence:
                typer.echo("  matched: " + ", ".join(item.identifier for item in result.matched_evidence))
            if explain:
                if result.status == RuleStatus.NOT_APPLICABLE:
                    typer.echo("  applicability: FALSE")
                elif result.status == RuleStatus.NEEDS_SEMANTIC_REVIEW:
                    typer.echo("  applicability: UNCERTAIN")
                else:
                    typer.echo("  applicability: TRUE")
                if result.missing_requirements:
                    typer.echo("  missing_requirements:")
                    for requirement in result.missing_requirements:
                        typer.echo(f"    - {requirement}")
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def score(path: Path, rules_path: Path | None = typer.Option(None, "--rules-path", help="Rules file or directory")) -> None:
    """Calculate enterprise readiness score."""
    try:
        analysis = _pipeline(rules_path).analyze(path)
        readiness = analysis.readiness_score
        typer.echo(f"Repository: {analysis.repository_context.project_name}\n")
        typer.echo(f"Overall Readiness\n\n{readiness.overall_score:.1f} / 100\n")
        typer.echo(f"Production Status\n\n{readiness.production_readiness.value}\n")
        typer.echo("Category Scores\n")
        for category in readiness.category_ranking():
            detail = readiness.category_details.get(category)
            if detail is not None:
                value = readiness.category_scores.get(category)
                typer.echo(f"{category.title():<16}{f'{value:.1f}' if value is not None else 'N/A'}")
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@app.command()
def report(
    path: Path,
    output_format: str = typer.Option("console", "--format", help="Report output format: console, json, markdown, or pdf"),
    output: Path | None = typer.Option(None, "--output", help="Output file for json, markdown, or PDF reports"),
    rules_path: Path | None = typer.Option(None, "--rules-path", help="Rules file or directory"),
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
            written = writer.write_json(report_model, output or Path("earf-report.json"))
            typer.echo(f"Report written to: {written}")
        elif selected_format == "markdown":
            written = writer.write_markdown(report_model, output or Path("EARF_REPORT.md"))
            typer.echo(f"Report written to: {written}")
        elif selected_format == "pdf":
            written = writer.write_pdf(report_model, output or Path("EARF_REPORT.pdf"))
            typer.echo(f"PDF report written to: {written}")
        else:
            typer.echo(f"Error: unsupported format {output_format!r}. Use console, json, markdown, or pdf.")
            raise typer.Exit(code=2)
    except (InvalidRepositoryPathError, RuleDefinitionError) as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


def _load_rule_catalog(path: Path) -> tuple[RuleCatalog, int]:
    return RuleCatalog.from_path(path)


@rules_app.command("list")
def rules_list(path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")) -> None:
    try:
        catalog, _ = _load_rule_catalog(path)
        typer.echo("ID  Category  Severity  Title  Enabled")
        for rule in catalog.all():
            typer.echo(f"{rule.id}  {rule.category}  {rule.severity.name.lower()}  {rule.title}  {rule.enabled}")
        typer.echo(f"\n{len(catalog.all())} rules loaded.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("validate")
def rules_validate(path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")) -> None:
    try:
        catalog, file_count = _load_rule_catalog(path)
        typer.echo("Rule catalog is valid.")
        typer.echo(f"{len(catalog.all())} rules loaded from {file_count} files.")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


@rules_app.command("show")
def rules_show(rule_id: str, path: Path = typer.Option(Path("rules"), "--path", help="Rules file or directory")) -> None:
    try:
        catalog, _ = _load_rule_catalog(path)
        rule = catalog.get(rule_id)
        for key in ("id", "title", "description", "category", "severity", "version", "enabled", "applicability", "rationale", "recommendation", "tags", "references", "evidence_requirements", "metadata"):
            value = getattr(rule, key)
            if key == "severity":
                value = value.name.lower()
            typer.echo(f"{key}: {value}")
    except RuleDefinitionError as exc:
        typer.echo(f"Error: {exc}")
        raise typer.Exit(code=2)


def main(argv: Optional[list[str]] | None = None) -> int:
    try:
        app(argv or sys.argv[1:])
    except SystemExit:
        raise
    return 0
