# EARF sample assessment: Ready AI Project

This directory contains a reproducible EARF assessment of the minimal [`ready-ai-project`](../ready-ai-project/) example included in this repository.

It is the positive counterpart to the [General Knowledge Assistant assessment](../general-knowledge-assistant-assessment/). Together, the two examples show how repository evidence can produce different readiness outcomes.

## Run the assessment yourself

From the root of the EARF repository:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e .
earf report examples/ready-ai-project --format markdown --output EARF_REPORT.md
```

The checked-in [`EARF_REPORT.md`](EARF_REPORT.md) is an example result generated from the current EARF rules and this fixture.

## Result

This assessment produces:

- Core readiness: **100.0 / 100**
- Overall score: **100.0 / 100**
- Production status: **READY**
- Deterministically failed core controls: **0**

The fixture includes evidence for ownership, purpose, security artifacts, CI workflow presence, and common AI-related configuration patterns.

## Important interpretation

`READY` means EARF did not identify a deterministically failed core control in this example. It does **not** mean that the project is certified, secure, reliable in production, or ready for deployment without further review.

This sample also contains controls requiring semantic or manual review. Teams should combine EARF with runtime tests, threat modeling, telemetry, human review, and operational evidence before making a production decision.

## Compare the results

- [General Knowledge Assistant: NOT_READY](../general-knowledge-assistant-assessment/)
- [Ready AI Project: READY](README.md)

If you find a result inaccurate or discover evidence that EARF misses, please open an issue with a minimal reproduction or add a positive/negative fixture.
