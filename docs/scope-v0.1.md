# Scope v0.1 (Phase 1)

## Purpose

Phase 1 creates a clean, extensible Python package skeleton with clearly defined interfaces for repository loading, evidence collection, rule evaluation, scoring, and reporting. No real analysis or rule evaluation is implemented in this phase.

## Supported inputs

- Local filesystem path to a repository (validated but not scanned).

## Planned outputs

- In later phases: JSON/Markdown reports, scores, and findings. Phase 1 emits placeholders only.

## In-scope capabilities

- Package layout under `src/earf`
- Domain models and interfaces
- CLI commands: `version`, `scan`, `rules`
- Unit tests for Phase 1

## Out-of-scope

- Rule definitions and matching
- Real scanning or pattern matching
- LLM integrations
- External APIs or persistence

## Phase 1 limitations

- Collectors return empty evidence lists.
- Rule loading and evaluation are unimplemented.

## Future phases

- Phase 2: declarative rule loader, rule definitions, basic rules, simple scoring
- Phase 3: real collectors, scoring strategies, reporters, CI/CD packaging
