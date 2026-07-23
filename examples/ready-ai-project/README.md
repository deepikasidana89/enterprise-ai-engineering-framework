# Ready AI Project (Example)

This minimal repository demonstrates the kind of deterministic evidence that allows EARF to pass several rules without adding application complexity.

## What It Demonstrates

- Ownership and project purpose documentation (`CODEOWNERS`, `README.md`)
- Security baseline artifacts (`SECURITY.md`, `.env.example`)
- CI workflow presence (`.github/workflows/ci.yml`)
- Common AI dependencies in `pyproject.toml` that satisfy modeling, safety, reliability, and observability checks

## Expected EARF Status

Expected overall status: `READY` or `READY_WITH_WARNINGS` (depending on catalog/weights in use).

## Scan Command

Run from the repository root:

```bash
earf report examples/ready-ai-project
```
