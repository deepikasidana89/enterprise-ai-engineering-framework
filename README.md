# Enterprise AI Readiness Framework (EARF)

> EARF is an open-source assessment framework designed to inspect AI application repositories for evidence of enterprise engineering practices across reliability, safety, evaluation, observability, privacy, governance, and operations.

Current Status:
In-Progress

Current Version:
0.1.0-dev

Completed:
✓ Package architecture
✓ CLI
✓ Domain models
✓ Declarative YAML rule catalog
✓ Rule loading and validation
✓ Evidence collection framework
✓ Deterministic evidence-to-rule matching

Not yet implemented:

- Full repository scanning and pattern matching
- Scoring
- Reporting
- LLM analysis

## Vision

Enterprise AI is evolving rapidly, but organizations often lack a structured approach to determine whether an AI solution is truly ready for production.

The Enterprise AI Readiness Framework (EARF) aims to provide engineering leaders and practitioners with a practical framework to assess AI systems across the complete lifecycle—from business strategy and architecture to governance, operations, and continuous improvement.

## Goals

- Define what "production-ready Enterprise AI" means.
- Establish a practical AI maturity model.
- Provide objective readiness assessments.
- Share engineering best practices for Enterprise AI.
- Help organizations build trustworthy, scalable, and responsible AI systems.

## Current Status

✅ Version 1.0 – Core framework complete and ready for use.

## Repository Structure

### Core Framework (`/framework`)
- **[Core Principles](framework/core-principles.md)** – Foundational beliefs about production-ready AI
- **[Maturity Model](framework/maturity-model.md)** – 5-level maturity progression
- **[Assessment Pillars](framework/pillars.md)** – 8 key dimensions of AI readiness
- **[Scoring Methodology](framework/scoring.md)** – How to measure and interpret readiness
- **[Getting Started](framework/getting-started.md)** – Step-by-step guide to using EARF
- **[Assessment Template](framework/assessment-template.md)** – Comprehensive assessment form

### Examples (`/examples`)
- **[MidCorp Financial Services](examples/example-assessment-midcorp.md)** – Detailed example assessment with findings and roadmap

### Supporting Materials
- `/research` – Reference papers and industry research
- `/articles` – Supporting articles and blog posts
- `/images` – Diagrams and visual assets
- `/tools` – Assessment automation tools (coming soon)

## Quick Start

### For Newcomers
1. Read [Core Principles](framework/core-principles.md) (15 min)
2. Review [Maturity Model](framework/maturity-model.md) (30 min)
3. Study [Assessment Pillars](framework/pillars.md) (30 min)
4. Review example assessment (30 min)
5. **Total: ~2 hours to understand the framework**

### To Conduct Your First Assessment
1. Follow [Getting Started](framework/getting-started.md) guide
2. Use [Assessment Template](framework/assessment-template.md)
3. Allocate 4-6 weeks for comprehensive assessment
4. Plan improvement roadmap based on findings

## CLI (Phase 6)

EARF currently supports:

- `earf version` — show EARF version
- `earf scan PATH` — validate repository path and show placeholder message
- `earf evidence PATH` — collect deterministic repository evidence only
- `earf evaluate PATH [--show-evidence]` — evaluate rules against collected evidence
- `earf score PATH [--rules-path PATH]` — calculate weighted readiness score from `RuleResult` values
- `earf report PATH [--rules-path PATH] [--format console|json|markdown] [--output PATH]` — generate a readiness report
- `earf rules list [--path PATH]` — list loaded rules
- `earf rules validate [--path PATH]` — validate YAML rule catalog
- `earf rules show RULE_ID [--path PATH]` — show one rule definition

`python -m earf` supports the same commands.

Default rules path is top-level `rules/`.

Rule YAML requirements:

- Top-level `rules` key containing a list
- Required per-rule fields: `id`, `title`, `description`, `category`, `severity`
- Rule ID format: `^[A-Z]{3}-\d{3}$`
- Supported severities: `critical`, `high`, `medium`, `low`, `info`

Phase 4.5+ evaluation and scoring scope:

- Collectors gather only deterministic repository evidence into an in-memory `EvidenceRepository`.
- Rule evaluation is deterministic and based only on evidence metadata requirements.
- Supported collector-emitted evidence types are: `file`, `dependency`, `workflow`, and `configuration`.
- Rule catalog `evidence_requirements` must reference only these emitted evidence types and exact emitted identifiers.
- Status values are: `PASS`, `FAIL`, `NOT_APPLICABLE`, `DISABLED`, `ERROR`.
- Scoring consumes only `RuleResult` + `RuleDefinition` metadata (severity/category) and does not inspect repositories directly.
- Default severity weights are: critical=10, high=7, medium=4, low=2, informational=1.
- `NOT_APPLICABLE` and `DISABLED` are excluded from score denominator.
- `ERROR` contributes zero earned weight and remains in denominator.
- Overall and category scores are normalized to 0-100 and rounded to one decimal.
- Production readiness gates:
	- `NOT_READY` if any critical rule fails
	- `READY` if no critical failures and overall score >= 85
	- `READY_WITH_WARNINGS` if no critical failures and overall score >= 70
	- `NOT_READY` otherwise
- Report generation and export are limited to console, JSON, and Markdown output.
- No SARIF export, GitHub Action integration, or LLM support is included.
- No LLM, RAG, embedding, regex scanning, AST analysis, or secret/prompt detection is included.

Evaluation pipeline:

Repository
	↓
EvidenceCollectionService
	↓
EvidenceRepository
	↓
RuleEvaluationService
	↓
RuleResult

Scoring philosophy:

- Severity-weighted scoring rewards controls based on business risk impact.
- Category scores expose uneven maturity across governance, security, safety, reliability, and other loaded categories.
- Production readiness is a strict gate, not just a percentile; critical failures block a `READY` decision.

Example:

```bash
python -m earf score .
```

Report generation:

```bash
python -m earf report .
python -m earf report . --format json
python -m earf report . --format markdown
python -m earf report . --format json --output report.json
python -m earf report . --format markdown --output report.md
```

Default report filenames:

- JSON: `earf-report.json`
- Markdown: `EARF_REPORT.md`

Console example:

```text
EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-22T00:00:00Z
EARF Version: 0.1.0-dev

Overall Readiness

11.1 / 100
```

Report JSON schema overview:

- `repository_name`
- `generated_at`
- `earf_version`
- `overall_score`
- `production_status`
- `total_evidence`
- `metadata`
- `category_scores`
- `rule_results`
- `summary`
- `critical_findings`
- `high_findings`
- `recommendations`

JSON example:

```json
{
	"repository_name": "enterprise-ai-readiness-framework",
	"generated_at": "2026-07-22T00:00:00Z",
	"earf_version": "0.1.0-dev",
	"overall_score": 11.1,
	"production_status": "NOT_READY"
}
```

Markdown reports include:

- title and repository metadata
- overall score and production readiness
- category table
- rule table
- summary table
- deterministic recommendations from the rule catalog

Markdown example:

```markdown
# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-22T00:00:00Z
EARF Version: 0.1.0-dev
```

Note: EARF findings indicate the presence or absence of implementation evidence. They do not prove that a control is fully effective and do not constitute certification, compliance approval, legal advice, or security assurance.

## Key Concepts

### The 5 Maturity Levels
- **Level 1: Initial** - Ad-hoc, no formal processes
- **Level 2: Managed** - Basic processes documented
- **Level 3: Defined** - Standardized and automated
- **Level 4: Quantitatively Managed** - Measured and optimized
- **Level 5: Optimized** - Continuous improvement, innovation

### The 8 Assessment Pillars
1. Business Strategy & Alignment
2. Data Governance & Quality
3. Data Architecture & Infrastructure
4. Model Development & Experimentation
5. Model Deployment & Operations
6. Monitoring, Observability & Maintenance
7. Security, Compliance & Governance
8. Team, Skills & Organization

### Overall Readiness Thresholds
- **1.0-1.5:** Not production-ready
- **1.6-2.5:** Minimal readiness (limited production use)
- **2.6-3.5:** Production-ready (standard practices)
- **3.6-4.5:** Highly production-ready (continuous optimization)
- **4.6-5.0:** Exceptional readiness (industry best practices)

## Using This Framework

### For Organizations
- Assess current AI readiness objectively
- Identify gaps and improvement opportunities
- Prioritize investments in AI infrastructure
- Plan realistic maturity progression

### For Teams
- Establish common language for AI readiness
- Set clear standards and expectations
- Guide technical decision-making
- Support hiring and skills development

### For Leaders
- Make data-driven investment decisions
- Balance risk and innovation
- Track progress over time
- Benchmark against industry standards

## Contributing

We welcome contributions from the community. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:
- Reporting issues
- Suggesting improvements
- Submitting assessments
- Sharing best practices

## License

This framework is shared under the [MIT License](LICENSE).