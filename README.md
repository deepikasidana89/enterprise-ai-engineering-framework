# Enterprise AI Readiness Framework (EARF)

## What EARF Is

EARF is an open-source Python framework and CLI for deterministic repository-based AI readiness assessment. It collects concrete evidence from a repository, evaluates YAML-defined rules, computes weighted readiness scores, and generates reports.

## Why It Exists

Teams shipping AI systems often need a repeatable way to assess readiness across governance, security, safety, reliability, observability, evaluation, and model configuration. EARF provides a transparent, evidence-driven baseline that can run locally and in CI.

## Current Capabilities

- Repository loading and validation
- Deterministic evidence collection
- Declarative YAML rule catalog
- Rule evaluation against collected evidence
- Severity-weighted scoring
- End-to-end `EARFPipeline`
- Reporting in console, JSON, and Markdown formats
- Built-in rules shipped with the package

## Installation

```bash
python -m pip install earf
```

For local development in this repository:

```bash
python -m pip install -e ".[dev]"
```

## Quick Start

Run a full report against the current repository:

```bash
earf report .
```

## Evidence Command

Collect and summarize evidence only:

```bash
earf evidence .
```

## Evaluate Command

Evaluate rules against evidence:

```bash
earf evaluate .
```

Show matched evidence per rule:

```bash
earf evaluate . --show-evidence
```

## Score Command

Calculate weighted readiness score:

```bash
earf score .
```

## Report Command

Generate console report:

```bash
earf report .
```

## JSON Export

Write JSON report:

```bash
earf report . --format json --output earf-report.json
```

## Markdown Export

Write Markdown report:

```bash
earf report . --format markdown --output EARF_REPORT.md
```

## GitHub Actions Usage

This repository includes two workflows:

- `.github/workflows/ci.yml`: matrix CI on Python 3.11, 3.12, and 3.13 running tests, linting, type checks, build, and `twine check`
- `.github/workflows/earf-scan.yml`: informational pull request/manual EARF Markdown scan with report artifact upload

## Rule Categories

The built-in catalog covers:

- governance
- security
- safety
- reliability
- observability
- evaluation
- modeling

## Architecture

High-level execution flow:

1. Repository path is validated and loaded.
2. Evidence collectors emit deterministic facts into an `EvidenceRepository`.
3. YAML rules are loaded into a `RuleCatalog`.
4. Rules are evaluated to `RuleResult` entries.
5. Scoring computes overall/category readiness.
6. Report builder/writer emits console, JSON, or Markdown output.

## Example Repositories

- `examples/ready-ai-project`: minimal evidence expected to satisfy several rules
- `examples/not-ready-ai-project`: minimal repository intentionally missing evidence and expected to fail several rules

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pytest
ruff check .
mypy src/earf
```

## Release Status

Current package version: `0.7.0`.

Status: public beta preparation in progress.

## Limitations

- Deterministic repository evidence only (no LLM analysis)
- No secret scanning engine beyond declared evidence indicators
- No SARIF export
- No REST API or dashboard
- Readiness is rule-catalog dependent and should be interpreted with engineering judgment

## Contributing

See `CONTRIBUTING.md` for contribution workflow and development expectations.

## License

MIT License. See `LICENSE`.
