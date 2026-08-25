# EARF Enterprise AI Readiness Report

Repository: ready-ai-project
Generated: 2026-08-25T02:26:20Z
EARF Version: 0.7.0
Total Evidence: 27

## Overall Assessment

| Metric | Result |
| --- | ---: |
| Core Readiness | 100.0 / 100 |
| Advanced Controls | 100.0 / 100 |
| Automated Evaluation Coverage | 100.0% (12/12) |
| Overall Score | 100.0 / 100 |

## Production Status

READY

## Why?

- 0 critical blockers
- 0 high-priority core gaps
- 11 of 11 scored core controls passed
- 0 applicable core controls require manual review

## Core Controls

| Metric | Value |
| --- | ---: |
| Passed | 11 |
| Failed | 0 |
| Manual Review | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |

## Advanced Controls

| Metric | Value |
| --- | ---: |
| Passed | 1 |
| Improvement Opportunities | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |

## Category Scores

| Category | Score | Coverage | Passed | Failed | Manual Review | Needs Semantic Review | N/A | Disabled | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Evaluation | 100.0 | 1/1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Governance | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Modeling | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Observability | 100.0 | 1/1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| Reliability | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Safety | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Security | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |

## Summary

| Metric | Value |
| --- | ---: |
| Passed | 12 |
| Failed | 0 |
| Manual Review | 0 |
| Needs Semantic Review | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 0 |
| High Failures | 0 |

## Full Rule Results

| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | core | high | PASS | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | core | high | PASS | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | core | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | core | high | PASS | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | advanced | medium | PASS | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | core | medium | PASS | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | core | medium | PASS | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | core | medium | PASS | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | core | high | PASS | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | core | high | PASS | Add post-processing or policy checks for model outputs. |
| SEC-001 | Externalized secret management evidence is present | Security | core | high | PASS | Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence. |
| SEC-002 | Tool access uses least privilege | Security | core | high | PASS | Restrict tool scopes and runtime permissions. |

## Recommendations

- None

## Critical Blockers

- None

## Top Core Gaps

- None

## Advanced Opportunities

- None

## Manual Review Required

- None

## Needs Semantic Review

- None

## Passed Controls

- PASS EVA-001: AI behavior has automated evaluations
- PASS GOV-001: AI ownership documented
- PASS GOV-002: AI purpose documented
- PASS MOD-001: Model or provider configured
- PASS MOD-002: Model version documented
- PASS OBS-001: AI interactions produce logs or telemetry
- PASS REL-001: Model calls define timeouts
- PASS REL-002: Model calls define retry or fallback
- PASS SAF-001: Input validation present
- PASS SAF-002: Output guardrails present
- PASS SEC-001: Externalized secret management evidence is present
- PASS SEC-002: Tool access uses least privilege

## Not Applicable

- None
