# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-07-30T04:36:20Z
EARF Version: 0.7.0
Total Evidence: 16

## Overall Readiness

66.7 / 100

## Production Status

NOT_READY

## Category Scores

| Category | Score |
| --- | ---: |
| Evaluation | 0.0 |
| Governance | 36.4 |
| Modeling | 0.0 |
| Observability | 0.0 |
| Reliability | 0.0 |
| Safety | 0.0 |
| Security | 100.0 |

## Summary

| Metric | Value |
| --- | ---: |
| Passed | 2 |
| Failed | 1 |
| Not Applicable | 9 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 0 |
| High Failures | 1 |

## Critical Findings

- None

## High Findings

- GOV-001: AI ownership documented

## Full Rule Results

| Rule ID | Title | Category | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | high | NOT_APPLICABLE | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | high | FAIL | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | high | NOT_APPLICABLE | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | medium | NOT_APPLICABLE | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | medium | NOT_APPLICABLE | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | medium | NOT_APPLICABLE | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | medium | NOT_APPLICABLE | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | high | NOT_APPLICABLE | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | high | NOT_APPLICABLE | Add post-processing or policy checks for model outputs. |
| SEC-001 | Secrets are not hard-coded | Security | critical | PASS | Move secrets to environment variables or secret managers. |
| SEC-002 | Tool access uses least privilege | Security | high | NOT_APPLICABLE | Restrict tool scopes and runtime permissions. |

## Recommendations

- GOV-001: Document the owner and escalation path.
