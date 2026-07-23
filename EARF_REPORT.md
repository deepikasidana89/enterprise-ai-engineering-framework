# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-23T15:45:09Z
EARF Version: 0.1.0.dev0
Total Evidence: 9

## Overall Readiness

11.1 / 100

## Production Status

NOT_READY

## Category Scores

| Category | Score |
| --- | ---: |
| Evaluation | 0.0 |
| Governance | 36.4 |
| Modeling | 36.4 |
| Observability | 0.0 |
| Reliability | 0.0 |
| Safety | 0.0 |
| Security | 0.0 |

## Summary

| Metric | Value |
| --- | ---: |
| Passed | 2 |
| Failed | 10 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 1 |
| High Failures | 6 |

## Critical Findings

- SEC-001: Secrets are not hard-coded

## High Findings

- EVA-001: AI behavior has automated evaluations
- GOV-001: AI ownership documented
- MOD-001: Model or provider configured
- SAF-001: Input validation present
- SAF-002: Output guardrails present
- SEC-002: Tool access uses least privilege

## Full Rule Results

| Rule ID | Title | Category | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | high | FAIL | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | high | FAIL | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | high | FAIL | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | medium | PASS | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | medium | FAIL | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | medium | FAIL | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | medium | FAIL | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | high | FAIL | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | high | FAIL | Add post-processing or policy checks for model outputs. |
| SEC-001 | Secrets are not hard-coded | Security | critical | FAIL | Move secrets to environment variables or secret managers. |
| SEC-002 | Tool access uses least privilege | Security | high | FAIL | Restrict tool scopes and runtime permissions. |

## Recommendations

- EVA-001: Add repeatable AI evaluation tests to CI workflows.
- GOV-001: Document the owner and escalation path.
- MOD-001: Add explicit model/provider configuration settings.
- OBS-001: Add structured logs and telemetry for AI interactions.
- REL-001: Set timeout values for all model calls.
- REL-002: Implement bounded retries or alternate provider fallback.
- SAF-001: Add validation and sanitization checks for AI inputs.
- SAF-002: Add post-processing or policy checks for model outputs.
- SEC-001: Move secrets to environment variables or secret managers.
- SEC-002: Restrict tool scopes and runtime permissions.
