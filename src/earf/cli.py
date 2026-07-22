from __future__ import annotations

from pathlib import Path
import sys
from typing import Optional

import typer

from .repository import RepositoryLoader
from . import __version__
from .exceptions import (
    InvalidRepositoryPathError,
    RuleDefinitionError,
)
from .evidence_collection import EvidenceCollectionService
from .models import EvidenceType
from .rules.evaluation_service import RuleEvaluationService
from .rules.results import RuleStatus
from .rules.catalog import RuleCatalog
from .scoring.service import ScoringService

app = typer.Typer(help="EARF CLI")
rules_app = typer.Typer(help="Rule catalog commands")
app.add_typer(rules_app, name="rules")


@app.command()
def version() -> None:
    """Show EARF version."""
    typer.echo(f"EARF {__version__}")


@app.command()
def scan(path: Path) -> None:
    """Load repository at PATH (Phase 1: scanning not implemented)."""
    try:
        loader = RepositoryLoader()
        context = loader.load(path)
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
        loader = RepositoryLoader()
        context = loader.load(path)

        service = EvidenceCollectionService()
        repository = service.collect(context)

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
    rules_path: Path = typer.Option(
        Path("rules"),
        "--rules-path",
        help="Rules file or directory",
    ),
) -> None:
    """Evaluate rules against collected evidence (Phase 4: matching only)."""
    try:
        loader = RepositoryLoader()
        context = loader.load(path)

        evidence_repository = EvidenceCollectionService().collect(context)
        catalog, _ = RuleCatalog.from_path(rules_path)
        results = RuleEvaluationService().evaluate_all(catalog, evidence_repository)

        typer.echo(f"Repository: {context.project_name}")
        typer.echo("")
        typer.echo("Rule Evaluation")
        typer.echo("")
        typer.echo("ID       Status          Title")

        rule_lookup = {rule.id: rule for rule in catalog.all()}
        for result in results:
            title = rule_lookup.get(result.rule_id)
            title_text = title.title if title is not None else ""
            status = result.status.name
            typer.echo(f"{result.rule_id:<8} {status:<15} {title_text}")
            if show_evidence and result.matched_evidence:
                matched_ids = ", ".join(e.identifier for e in result.matched_evidence)
                typer.echo(f"  matched: {matched_ids}")

        summary = {
            RuleStatus.PASS: 0,
            RuleStatus.FAIL: 0,
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
    rules_path: Path = typer.Option(
        Path("rules"),
        "--rules-path",
        help="Rules file or directory",
    ),
) -> None:
    """Calculate enterprise readiness score from rule evaluation results."""
    try:
        loader = RepositoryLoader()
        context = loader.load(path)

        evidence_repository = EvidenceCollectionService().collect(context)
        catalog, _ = RuleCatalog.from_path(rules_path)
        results = RuleEvaluationService().evaluate_all(catalog, evidence_repository)
        readiness = ScoringService().score(results, catalog)

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
        for category, value in sorted(readiness.category_scores.items()):
            typer.echo(f"{category:<15} {value:.1f}")

        typer.echo("")
        typer.echo("Summary")
        typer.echo("")
        typer.echo(f"Passed: {readiness.passed_rules}")
        typer.echo(f"Failed: {readiness.failed_rules}")
        typer.echo(f"Not Applicable: {readiness.not_applicable_rules}")
        typer.echo(f"Disabled: {readiness.disabled_rules}")
        typer.echo(f"Errors: {readiness.error_rules}")
        typer.echo(f"Critical Failures: {readiness.critical_failures}")
        typer.echo(f"High Failures: {readiness.high_failures}")
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
        # typer uses SystemExit, re-raise to preserve exit code
        raise
    return 0
