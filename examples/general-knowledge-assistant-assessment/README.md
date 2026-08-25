# EARF sample assessment: General Knowledge Assistant

This directory contains a reproducible EARF assessment of the separate example project [General Knowledge Assistant](https://github.com/deepikasidana89/general-knowledge-assistant).

The project is intentionally small: it accepts a question, sends it to a language model, and prints the answer. That makes it useful for demonstrating how EARF identifies evidence around an AI application without requiring a large production codebase.

## Run the assessment yourself

From the root of the EARF repository:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
git clone https://github.com/deepikasidana89/general-knowledge-assistant.git /tmp/general-knowledge-assistant
earf report /tmp/general-knowledge-assistant --format markdown --output EARF_REPORT.md
```

The checked-in [`EARF_REPORT.md`](EARF_REPORT.md) is an example result generated from the current version of the sample project. Scores and findings can change as EARF rules, the sample project, or the assessment configuration evolve.

## What this assessment demonstrates

EARF detected evidence that the project:

- Uses a configured model/provider
- Documents the model version
- Defines a model-call timeout
- Documents the AI system's purpose

It also identified gaps that a team would normally address before production, including:

- Automated AI evaluations
- Ownership and escalation documentation
- Runtime observability
- Retry or fallback behavior
- Input validation
- Output guardrails
- Secret-management evidence
- Least-privilege access controls

The `NOT_READY` result is not a certification decision. It is an evidence-based starting point for engineering review. Repository analysis cannot prove runtime behavior or the effectiveness of a control, so findings should be validated with tests, threat modeling, telemetry, human review, and operational evidence.

## Provide feedback

If you run this assessment on the sample project or your own non-confidential AI repository, please share:

1. Which findings were accurate or inaccurate?
2. Which recommendation was most useful?
3. What evidence or framework pattern EARF missed?

Open an issue or start a discussion in the [EARF repository](https://github.com/deepikasidana89/enterprise-ai-engineering-framework). Short adopter feedback and anonymized case studies are especially welcome.
