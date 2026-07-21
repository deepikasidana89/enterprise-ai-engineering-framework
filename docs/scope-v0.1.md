# Scope v0.1 (Phase 2)

## Purpose

Phase 2 extends the Phase 1 skeleton with declarative YAML rules, loading, validation, duplicate detection, and rule catalog CLI commands. No repository scanning, evidence matching, rule evaluation execution, scoring, or reporting is implemented in this phase.

## Supported inputs

- Local filesystem path to a repository (validated but not scanned).

## Planned outputs

- In later phases: JSON/Markdown reports, scores, and findings. Phase 1 emits placeholders only.

## In-scope capabilities

- Package layout under `src/earf`
- Domain models and interfaces
- YAML rule schema and loader
- Rule validation and duplicate ID detection
- Rule catalog query methods
- CLI commands: `version`, `scan`, `rules list`, `rules validate`, `rules show`
- Unit tests for Phase 2

## Out-of-scope

- Repository scanning and evidence matching
- Rule evaluation execution
- Scoring and readiness levels
- Report generation
- LLM integrations
- External APIs or persistence

## Phase 2 limitations

- Collectors return empty evidence lists.
- Rule evaluation is unimplemented.
- Scoring and reporting are unimplemented.

## Future phases

- Phase 3: repository scanning, evidence matching, and rule engine evaluation
- Phase 4: scoring, readiness levels, and reporting
