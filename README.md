# EARF
## Enterprise AI Readiness Framework

[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-Beta-orange.svg)]()

EARF (Enterprise AI Readiness Framework) is an open-source framework for **evaluating whether AI-powered software is ready for enterprise production**.

Unlike traditional code quality tools that focus on software correctness, EARF evaluates **AI engineering readiness** across governance, safety, security, reliability, observability, modeling, and evaluation.

EARF performs deterministic analysis of repositories to identify missing engineering practices before AI systems reach production.

---

# Why EARF?

Building an AI application involves more than selecting the right model.

Enterprise AI systems require engineering practices such as:

- Model configuration
- AI safety controls
- Input validation
- Output guardrails
- Governance documentation
- Observability
- Evaluation pipelines
- Operational reliability
- Security

Many organizations evaluate model quality but overlook engineering readiness.

EARF helps bridge that gap.

---

# Features

- Declarative rule engine
- Repository evidence collection
- Enterprise readiness scoring
- Deterministic evaluation
- Markdown reports
- JSON reports
- CLI
- GitHub Actions integration
- Extensible rule catalog
- Open architecture

---

# Readiness Categories

EARF currently evaluates repositories across:

| Category | Purpose |
|-----------|----------|
| Governance | Ownership, documentation, accountability |
| Modeling | Model configuration and versioning |
| Safety | Input validation and output guardrails |
| Reliability | Timeouts, retries, fallback strategies |
| Observability | Logging, monitoring, telemetry |
| Security | Secrets and least-privilege access |
| Evaluation | Automated AI evaluation practices |

---

# Installation

```bash
pip install earf
```

Or install from source:

```bash
git clone https://github.com/<username>/enterprise-ai-readiness-framework.git

cd enterprise-ai-readiness-framework

pip install -e .
```

---

# Quick Start

Collect repository evidence:

```bash
earf evidence .
```

Evaluate rules:

```bash
earf evaluate .
```

Calculate readiness:

```bash
earf score .
```

Generate a report:

```bash
earf report .
```

Export JSON:

```bash
earf report . --format json
```

Export Markdown:

```bash
earf report . --format markdown
```

---

# Example Output

```
Overall Readiness

78.4 / 100

Production Status

READY_WITH_WARNINGS

Category Scores

Governance       100
Security          90
Safety            75
Reliability       60
Observability     80
Evaluation        95

Passed Rules      18
Failed Rules       4
```

---

# Architecture

```
Repository
      │
      ▼
Repository Loader
      │
      ▼
Evidence Collection
      │
      ▼
Evidence Repository
      │
      ▼
Rule Evaluation
      │
      ▼
Scoring Engine
      │
      ▼
Report Builder
      │
      ▼
Readiness Report
```

The EARFPipeline orchestrates the complete analysis workflow while keeping the CLI thin and reusable across future integrations.

---

# Rule Engine

Rules are defined declaratively using YAML.

Example:

```yaml
id: GOV-001

title: AI ownership documented

category: governance

severity: high

evidence_requirements:

  any:

    - evidence_type: file

      identifiers:

        - CODEOWNERS
```

This enables new enterprise checks without changing Python code.

---

# Reports

EARF currently supports:

- Console
- JSON
- Markdown

Reports include:

- Overall readiness score
- Production status
- Category scores
- Rule evaluation summary
- Critical findings
- Recommendations

---

# SEC-001 Interpretation

SEC-001 evaluates repository evidence for externalized secret management.

It does not prove that hard-coded secrets are absent.

Use `earf evaluate . --show-evidence` to inspect which evidence triggered the result.

SEC-001 outcomes:

- PASS: strong provider/configuration evidence was detected.
- MANUAL_REVIEW: potential custom secret-management abstraction was detected, but evidence is not strong enough for definitive PASS.
- FAIL: no supported evidence of externalized secret management was detected.

Examples:

- Known provider: dependency and usage for AWS Secrets Manager, Azure Key Vault, HashiCorp Vault, GCP Secret Manager, or Kubernetes `secretKeyRef`.
- Custom implementation candidate: names such as `CredentialProvider` or `SecretManager` with supporting signals.
- Weak-only signals: a single generic environment variable access or mention of "secret" in text is not sufficient.

---

# GitHub Actions

EARF can be executed automatically during CI to generate readiness reports for pull requests and repositories.

See:

```
.github/workflows/
```

---

# Repository Structure

```
src/
tests/
docs/
examples/
rules/
```

---

# Development

Clone the repository:

```bash
git clone ...

pip install -e ".[dev]"
```

Run validation:

```bash
pytest

ruff check .

mypy src/earf
```

Build:

```bash
python -m build
```

---

# Examples

The repository includes sample projects demonstrating both production-ready and non-production-ready AI repositories.

See:

```
examples/
```

---

# Roadmap

Planned future enhancements include:

- Additional enterprise rule packs
- Expanded AI engineering coverage
- Community-contributed rules
- Additional reporting formats

---

# Contributing

Contributions are welcome.

Please read:

- CONTRIBUTING.md
- CODE_OF_CONDUCT.md

---

# License

MIT License.

---

# Citation

If EARF contributes to your research or engineering work, please cite the project once the citation information becomes available.

---

# Author

**Deepika Sidana**

Enterprise AI Engineering • Machine Learning • Distributed Systems • Responsible AI

---

## Vision

EARF aims to make **Enterprise AI Readiness** as measurable and repeatable as traditional software quality, helping engineering teams build AI systems that are not only intelligent—but also reliable, secure, governable, and production-ready.