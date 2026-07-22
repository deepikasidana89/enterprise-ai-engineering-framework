# Changelog

## Unreleased

- Phase 1: Project skeleton and core domain models (initial commit)
- Phase 2: Declarative YAML rule definitions and validation
- Added YAML rule loading with deterministic ordering and duplicate rule detection
- Added rule catalog and CLI commands: rules list, rules validate, rules show
- Added initial 12-rule catalog under top-level rules directory
- Added tests for rule model validation, YAML loader, rule catalog, and rules CLI
- Phase 3: Evidence collection framework
- Added FileCollector, DependencyCollector, WorkflowCollector, and ConfigCollector
- Added EvidenceCollectionService with exact deduplication into EvidenceRepository
- Added CLI command: evidence PATH
- Added tests for collectors, evidence service, evidence repository, and evidence CLI
- Phase 4: Evidence-to-rule matching
- Added RuleStatus and rule-scoring-independent RuleResult model for evaluation outcomes
- Added RuleEvaluator with deterministic support for direct requirements and any/all operators
- Added RuleEvaluationService to evaluate full catalogs in deterministic rule-id order
- Added CLI command: evaluate PATH with optional --show-evidence
- Added tests for evaluator logic, evaluation service ordering, repository query helpers, and evaluate CLI output
