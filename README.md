# Enterprise AI Readiness Framework (EARF)

> **Is your AI system actually ready for production?**

**EARF** is an open-source engineering framework and CLI for evaluating AI application repositories for evidence of **reliability, safety, security, evaluation, observability, privacy, governance, and operational readiness**.

Instead of asking only *“How accurate is the model?”*, EARF asks a broader engineering question:

> **Does the system around the model demonstrate the engineering practices needed to operate AI responsibly and reliably in production?**

EARF turns repository evidence into deterministic rule evaluations, severity-weighted readiness scores, and actionable reports.

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
git clone https://github.com/deepikasidana89/enterprise-ai-engineering-framework.git
cd enterprise-ai-engineering-framework
```

Install locally:

```bash
pip install -e .
```

Run EARF against an AI project:

```bash
earf report /path/to/your-ai-project
```

Or:

```bash
python -m earf report /path/to/your-ai-project
```

Generate a Markdown report:

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
	"earf_version": "0.1.0-dev",
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
	"overall_score": 11.1,
	"production_status": "NOT_READY"
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
EARF Version: 0.1.0-dev
```

Note: EARF findings indicate the presence or absence of implementation evidence. They do not prove that a control is fully effective and do not constitute certification, compliance approval, legal advice, or security assurance.

## Scoring Semantics

- Production readiness is based primarily on applicable `core` controls.
- Advanced controls represent enterprise AI maturity beyond baseline production readiness and are reported separately.
- The existing overall score is preserved for compatibility and trend tracking.

### Assessment Coverage

Assessment Coverage represents the percentage of applicable EARF controls that completed automated evaluation.

- Evaluated: controls with status `PASS`, `FAIL`, or `MANUAL_REVIEW`.
- Applicable: controls with status `PASS`, `FAIL`, `MANUAL_REVIEW`, or `ERROR`.
- Excluded from coverage: `NOT_APPLICABLE` and `DISABLED`.

Assessment Coverage does not represent the percentage of an application's implementation inspected or verified.

EARF detects engineering evidence. A `PASS` indicates supported evidence was detected; it does not prove that a control is correctly or completely implemented.

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