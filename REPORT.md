# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated at: 2026-07-22T02:52:35Z

## Overall Readiness

11.1 / 100

## Production Readiness

NOT_READY

## Category Scores

| Category | Score |
| --- | ---: |
| Governance | 36.4 |
| Modeling | 36.4 |
| Evaluation | 0.0 |
| Observability | 0.0 |
| Reliability | 0.0 |
| Safety | 0.0 |
| Security | 0.0 |

## Rule Table

| Rule | Category | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- |
| EVA-001 | evaluation | high | FAIL | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | governance | high | FAIL | Document the owner and escalation path. |
| GOV-002 | governance | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | modeling | high | FAIL | Add explicit model/provider configuration settings. |
| MOD-002 | modeling | medium | PASS | Document model versions and update procedures. |
| OBS-001 | observability | medium | FAIL | Add structured logs and telemetry for AI interactions. |
| REL-001 | reliability | medium | FAIL | Set timeout values for all model calls. |
| REL-002 | reliability | medium | FAIL | Implement bounded retries or alternate provider fallback. |
| SAF-001 | safety | high | FAIL | Add validation and sanitization checks for AI inputs. |
| SAF-002 | safety | high | FAIL | Add post-processing or policy checks for model outputs. |
| SEC-001 | security | critical | FAIL | Move secrets to environment variables or secret managers. |
| SEC-002 | security | high | FAIL | Restrict tool scopes and runtime permissions. |

## Summary

| Status | Count |
| --- | ---: |
| PASS | 2 |
| FAIL | 10 |
| NOT APPLICABLE | 0 |
| DISABLED | 0 |
| ERROR | 0 |

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

## Critical Findings

- SEC-001

## High Findings

- EVA-001
- GOV-001
- MOD-001
- SAF-001
- SAF-002
- SEC-002
