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
earf report /path/to/your-ai-project \
  --format markdown \
  --output EARF_REPORT.md
```

Generate JSON:

```bash
earf report /path/to/your-ai-project \
  --format json \
  --output earf-report.json
```

---

## 📊 What You Get

EARF produces an engineering-readiness assessment containing:

```text
EARF Enterprise AI Readiness Report

Repository: my-ai-project

Overall Readiness
-----------------
Score: <0-100>

Production Status:
READY
READY_WITH_WARNINGS
or
NOT_READY

Category Scores
---------------
Reliability
Safety
Security
Evaluation
Observability
Privacy
Governance
Operations

Findings
--------
Critical findings
High-severity findings
Rule-level results
Deterministic recommendations
```

EARF uses a **0–100 severity-weighted score**, but production readiness is not determined by score alone.

A critical failed control can block a `READY` result.

---

# Why EARF?

AI engineering teams already evaluate things such as:

* model quality
* retrieval quality
* latency
* cost
* hallucination rates

But production AI systems depend on much more than the model.

A system can have a highly accurate model and still be unsafe or unreliable because it lacks:

* fallback behavior
* observability
* evaluation pipelines
* access controls
* auditability
* privacy safeguards
* deployment controls
* failure handling
* governance
* operational readiness

EARF provides a structured way to evaluate these engineering signals.

```text
Model Quality
      │
      ▼
┌─────────────────────────────┐
│     AI Application          │
│                             │
│  Reliability                │
│  Safety                     │
│  Security                   │
│  Evaluation                 │
│  Observability              │
│  Privacy                    │
│  Governance                 │
│  Operations                 │
└─────────────────────────────┘
      │
      ▼
Production Readiness
```

---

# How EARF Works

EARF currently follows a deterministic assessment pipeline:

```text
AI Repository
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
Severity-Weighted Scoring
      │
      ▼
Readiness Report
```

At a high level:

### 1. Evidence Collection

EARF inspects supported repository artifacts and collects deterministic evidence.

Current evidence types include:

* `file`
* `dependency`
* `workflow`
* `configuration`

### 2. Rule Evaluation

Evidence is evaluated against declarative YAML rules.

Each rule contains metadata such as:

```yaml
id:
title:
description:
category:
severity:
evidence_requirements:
```

Rule outcomes include:

```text
PASS
FAIL
NOT_APPLICABLE
DISABLED
ERROR
```

### 3. Readiness Scoring

EARF calculates severity-weighted scores.

Default weights:

| Severity      | Weight |
| ------------- | -----: |
| Critical      |     10 |
| High          |      7 |
| Medium        |      4 |
| Low           |      2 |
| Informational |      1 |

Scores are normalized to **0–100**.

### 4. Production Readiness Gate

EARF applies explicit readiness gates:

| Condition                         | Status                |
| --------------------------------- | --------------------- |
| Any critical rule fails           | `NOT_READY`           |
| No critical failures + score ≥ 85 | `READY`               |
| No critical failures + score ≥ 70 | `READY_WITH_WARNINGS` |
| Otherwise                         | `NOT_READY`           |

This prevents a high aggregate score from hiding a critical engineering failure.

---

# 🧩 Assessment Areas

EARF is designed around the engineering concerns that determine whether AI systems can operate safely and reliably in enterprise environments.

These include:

### Reliability

Resilience, failure handling, fallbacks, and production reliability practices.

### Safety

Controls designed to reduce unsafe or unintended AI behavior.

### Security

Engineering evidence related to secure AI application design and operation.

### Evaluation

Evidence that AI behavior is systematically tested and evaluated.

### Observability

Monitoring, logging, tracing, and operational visibility.

### Privacy

Practices related to protecting sensitive information.

### Governance

Controls supporting accountability, review, and responsible operation.

### Operations

Deployment and operational practices needed to sustain production AI systems.

---

# 🏗️ Two Layers of EARF

EARF contains two complementary approaches.

## Automated Engineering Assessment

The CLI provides repository-level evidence collection, deterministic rule evaluation, scoring, and reporting.

Use this when you want a fast engineering signal from a repository.

```bash
earf report ./my-ai-project
```

## Enterprise Maturity Framework

EARF also contains a broader organizational assessment framework covering the lifecycle of enterprise AI.

The framework includes:

* Core principles
* 5-level maturity model
* 8 assessment pillars
* Assessment methodology
* Assessment templates
* Example enterprise assessment

This layer is intended for deeper architecture, engineering, governance, and organizational reviews.

---

# 🏢 Enterprise AI Maturity Model

EARF defines five maturity levels:

| Level                                | Description                                           |
| ------------------------------------ | ----------------------------------------------------- |
| **Level 1 — Initial**                | Ad-hoc practices with limited formalization           |
| **Level 2 — Managed**                | Basic processes are documented                        |
| **Level 3 — Defined**                | Practices are standardized and increasingly automated |
| **Level 4 — Quantitatively Managed** | Systems and processes are measured and optimized      |
| **Level 5 — Optimized**              | Continuous improvement and engineering innovation     |

The maturity model complements the repository-level readiness score; they represent different views of AI readiness and should not be interpreted as the same metric.

---

# 🧭 Enterprise Assessment Pillars

The broader EARF maturity framework examines eight dimensions:

1. **Business Strategy & Alignment**
2. **Data Governance & Quality**
3. **Data Architecture & Infrastructure**
4. **Model Development & Experimentation**
5. **Model Deployment & Operations**
6. **Monitoring, Observability & Maintenance**
7. **Security, Compliance & Governance**
8. **Team, Skills & Organization**

These pillars help organizations evaluate AI readiness beyond an individual code repository.

---

# 🛠️ CLI Commands

### Check version

```bash
earf version
```

### Collect evidence

```bash
earf evidence PATH
```

### Evaluate rules

```bash
earf evaluate PATH
```

Include supporting evidence:

```bash
earf evaluate PATH --show-evidence
```

### Calculate readiness score

```bash
earf score PATH
```

### Generate report

```bash
earf report PATH
```

JSON:

```bash
earf report PATH --format json
```

Markdown:

```bash
earf report PATH --format markdown
```

Save the output:

```bash
earf report PATH \
  --format markdown \
  --output EARF_REPORT.md
```

### Explore the rule catalog

```bash
earf rules list
```

Validate rules:

```bash
earf rules validate
```

Inspect an individual rule:

```bash
earf rules show RULE_ID
```

---

# 📁 Repository Structure

```text
enterprise-ai-engineering-framework/
│
├── src/                  # EARF implementation
├── rules/                # Declarative readiness rules
├── tests/                # Automated tests
├── framework/            # Enterprise maturity framework
├── examples/             # Example assessments
├── docs/                 # Documentation
│
├── pyproject.toml
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

---

# 📚 Framework Documentation

For a deeper enterprise assessment:

* [Core Principles](framework/core-principles.md)
* [Maturity Model](framework/maturity-model.md)
* [Assessment Pillars](framework/pillars.md)
* [Scoring Methodology](framework/scoring.md)
* [Getting Started](framework/getting-started.md)
* [Assessment Template](framework/assessment-template.md)

Example:

* [MidCorp Financial Services Assessment](examples/example-assessment-midcorp.md)

---

# 🚧 Current Status

**Current release: `0.1.0-dev` — Early Developer Release**

EARF currently includes:

* ✅ Package architecture
* ✅ CLI
* ✅ Domain models
* ✅ Declarative YAML rule catalog
* ✅ Rule loading and validation
* ✅ Deterministic evidence collection
* ✅ Evidence-to-rule evaluation
* ✅ Severity-weighted scoring
* ✅ Production readiness gates
* ✅ Console reporting
* ✅ JSON reporting
* ✅ Markdown reporting

EARF is actively evolving.

Current limitations include:

* Repository analysis is deterministic and metadata-driven
* No AST-based code analysis
* No semantic/embedding-based analysis
* No LLM-assisted analysis
* No RAG-based analysis
* No secret or prompt vulnerability detection
* No SARIF export
* No native GitHub Actions integration

These capabilities may be explored in future releases.

---

# 🗺️ Roadmap

Potential areas of development include:

### Deeper Repository Analysis

* Additional evidence collectors
* Pattern-based analysis
* AST-aware inspection
* Expanded AI engineering controls

### CI/CD Integration

```text
Pull Request
     ↓
EARF Assessment
     ↓
Readiness Gate
     ↓
Report
```

### Expanded Reporting

* SARIF
* HTML dashboards
* Trend analysis
* Comparison between releases

### Optional Intelligent Analysis

Future versions may explore optional LLM-assisted analysis for controls that cannot be reliably evaluated using deterministic repository evidence alone.

Deterministic evaluation should remain the foundation wherever possible.

---

# 🔬 Project Philosophy

EARF is built around several principles.

### Evidence over claims

Production readiness should be supported by observable engineering evidence.

### Deterministic before probabilistic

Controls that can be evaluated deterministically should not require an LLM.

### Critical risks should not disappear inside averages

A high aggregate score should not override a critical failed control.

### AI readiness is a system property

Model accuracy alone does not determine whether an AI application is ready for enterprise production.

---

# 🤝 Contributing

EARF is open source and community feedback is welcome.

Useful ways to contribute include:

* ⭐ Star the repository if you find the project useful
* 🍴 Fork EARF and experiment with it
* 🧪 Run EARF against an AI project
* 🐛 Report false positives or false negatives
* 📝 Propose new readiness rules
* 🔧 Improve evidence collectors
* 📊 Suggest improvements to scoring
* 💡 Share enterprise AI engineering practices that EARF should evaluate

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

If EARF misses an important production AI control, **open an issue and challenge the framework.**

That feedback is particularly valuable.

---

# ⚠️ Important Disclaimer

EARF evaluates the **presence or absence of engineering evidence** that can be detected by its supported assessment mechanisms.

A `PASS` does **not** prove that a control is correctly implemented or effective.

EARF is not:

* a security certification
* a compliance certification
* a substitute for penetration testing
* a substitute for architecture review
* a substitute for model evaluation
* legal advice
* regulatory approval

EARF should be used as one engineering signal within a broader AI assurance process.

---

# 🌟 Help Improve EARF

EARF is an early open-source project, and real-world feedback will shape where it goes next.

Try it against an AI repository:

```bash
earf report ./your-ai-project
```

Then tell us:

**What did EARF catch?**

**What did it miss?**

**Which enterprise AI controls should be added?**

If you find the project useful, consider giving it a ⭐ — it helps more AI engineers discover and improve the framework.

---

## License

MIT License

---

**EARF — because production-ready AI requires more than a good model.**
