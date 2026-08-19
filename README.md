# Enterprise AI Readiness Framework (EARF)

> **Is your AI system actually ready for production?**

**EARF** is an open-source engineering framework and CLI for evaluating AI application repositories for evidence of **reliability, safety, security, evaluation, observability, privacy, governance, and operational readiness**.

Instead of asking only *“How accurate is the model?”*, EARF asks a broader engineering question:

> **Does the system around the model demonstrate the engineering practices needed to operate AI responsibly and reliably in production?**

EARF turns repository evidence into deterministic rule evaluations, severity-weighted readiness scores, and actionable reports.

Current release status: **Early Developer Release** (version `0.7.0`).

---

## 🚀 What EARF Does

EARF analyzes evidence available in an AI application's repository and helps teams:

* 🔎 **Assess** enterprise AI engineering practices
* 📊 **Score** overall and category-level readiness
* 🚨 **Identify** critical and high-severity gaps
* 🛡️ **Evaluate** reliability, safety, security, governance, and operational controls
* 📋 **Generate** console, JSON, and Markdown readiness reports
* 🧭 **Prioritize** engineering improvements before production

The goal is not to certify an AI system.

The goal is to make **AI production readiness more measurable, repeatable, and evidence-driven.**

---

## ⚡ Quick Start

Clone EARF:

```bash
git clone https://github.com/deepikasidana89/enterprise-ai-readiness-framework.git
cd enterprise-ai-readiness-framework
```

Install locally:

```bash
pip install -e .
```

## Run EARF in GitHub Actions

Minimal workflow:

```yaml
name: EARF AI Readiness

on:
	pull_request:
	push:
		branches: [main]

jobs:
	earf:
		runs-on: ubuntu-latest

		steps:
			- uses: actions/checkout@v4

			- name: Run EARF
				uses: deepikasidana89/enterprise-ai-engineering-framework@v1
```

Advanced example with optional inputs:

```yaml
name: EARF AI Readiness

on:
	pull_request:
	push:
		branches: [main]

jobs:
	earf:
		runs-on: ubuntu-latest

		steps:
			- uses: actions/checkout@v4

			- name: Run EARF
				uses: deepikasidana89/enterprise-ai-engineering-framework@v1
				with:
					path: .
					rules-path: .github/earf/rules
					fail-on-not-ready: true
```

The action generates:

- `earf-report.json`
- `EARF_REPORT.md`

EARF V1 provides engineering readiness evidence. It does not constitute certification, security assurance, or compliance approval.

Run EARF against an AI project:

```bash
earf report /path/to/your-ai-project
```

Or:

```bash
python -m earf report /path/to/your-ai-project
```

Score a repository:

```bash
earf score .
# or
python -m earf score .
```

Console report:

```bash
earf report .
# or
python -m earf report .
```

JSON report:

```bash
earf report . --format json --output earf-report.json
# or
python -m earf report . --format json --output earf-report.json
```

Markdown report:

```bash
earf report . --format markdown --output EARF_REPORT.md
# or
python -m earf report . --format markdown --output EARF_REPORT.md
```

Default report filenames:

- JSON: `earf-report.json`
- Markdown: `EARF_REPORT.md`

Console example:

Illustrative example output (values shown here are examples, not a live assessment result):

```text
EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-22T00:00:00Z
EARF Version: 0.7.0

Overall Assessment

Core Readiness: 82.0 / 100
Advanced Controls: 61.0 / 100
Automated Evaluation Coverage: 78.0%

Production Status

READY_WITH_WARNINGS
```

Report JSON schema overview:

- `repository_name`
- `generated_at`
- `earf_version`
- `overall_score`
- `core_readiness`
- `advanced_controls`
- `assessment_coverage`
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
	"earf_version": "0.7.0",
	"core_readiness": {
		"score": 82.0,
		"passed": 14,
		"failed": 2,
		"not_applicable": 5
	},
	"advanced_controls": {
		"score": 64.0,
		"passed": 4,
		"failed": 7,
		"improvement_opportunities": 7
	},
	"assessment_coverage": {
		"percentage": 73.0,
		"evaluated": 16,
		"applicable": 22
	},
	"overall_score": 74.3,
	"production_status": "READY_WITH_WARNINGS"
}
```

Markdown reports include:
- title and repository metadata
- overall assessment (core readiness, advanced controls, assessment coverage, and overall score)
- production readiness
- core controls and advanced opportunities summaries
- category table
- rule table
- summary table
- deterministic recommendations from the rule catalog

Markdown example:

```markdown
# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-22T00:00:00Z
EARF Version: 0.7.0
```

Note: EARF findings indicate the presence or absence of implementation evidence. They do not prove that a control is fully effective and do not constitute certification, compliance approval, legal advice, or security assurance.

## Scoring Semantics

- Production readiness is based primarily on applicable `core` controls.
- Advanced controls represent enterprise AI maturity beyond baseline production readiness and are reported separately.
- The existing overall score is preserved for compatibility and trend tracking.

EARF detects engineering evidence. A `PASS` indicates supported evidence was detected; it does not prove that a control is correctly or completely implemented.

### Deterministic Result States

- `PASS`: The control applies and EARF found supported implementation evidence.
- `FAIL`: The control applies but EARF did not find sufficient supported implementation evidence.
- `NOT_APPLICABLE`: EARF found sufficient deterministic evidence that the control does not apply to this repository.
- `NEEDS_SEMANTIC_REVIEW`: Deterministic evidence is insufficient to safely determine applicability or implementation. This state is surfaced for manual follow-up and is not treated as PASS/FAIL.

Category score interpretation:

- Numeric score (for example `100.0`, `63.6`, `0.0`) means the category had at least one deterministically assessed control (`PASS` or `FAIL`).
- `N/A` means the category was not scored because no controls in that category were deterministically assessed.
- `N/A` does not mean the repository failed that category.

### Automated Evaluation Coverage

Automated Evaluation Coverage represents the percentage of applicable EARF controls that were automatically resolved by deterministic checks.

- Evaluated: controls with status `PASS` or `FAIL`.
- Applicable: controls with status `PASS`, `FAIL`, `MANUAL_REVIEW`, or `ERROR`.
- Excluded from coverage: `NOT_APPLICABLE` and `DISABLED`.

`100%` means all applicable controls were automatically resolved. It does not mean 100% of system behavior or implementation quality was verified.

### Current Limitations

- EARF uses deterministic repository analysis and pattern-based source inspection.
- EARF does not perform AST-level semantic verification of implementation correctness.
- EARF does not use LLM-based repository analysis.
- Custom enterprise implementations may not always be recognized by current deterministic patterns.
- A detected evidence signal does not guarantee that the control is complete or correctly implemented.

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

### Core Readiness Thresholds
- **>= 85.0:** READY
- **>= 70.0 and < 85.0:** READY_WITH_WARNINGS
- **< 70.0:** NOT_READY

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