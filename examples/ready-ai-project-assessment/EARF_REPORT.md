# EARF Enterprise AI Readiness Report

Repository: ready-ai-project
Generated: 2026-08-25T02:16:02Z
EARF Version: 0.7.0
Total Evidence: 13

## Overall Assessment

| Metric | Result |
| --- | ---: |
| Core Readiness | 100.0 / 100 |
| Advanced Controls | 0.0 / 100 |
| Automated Evaluation Coverage | 100.0% (3/3) |
| Overall Score | 100.0 / 100 |

## Production Status

READY

## Why?

- 0 critical blockers
- 0 high-priority core gaps
- 3 of 3 scored core controls passed
- 0 applicable core controls require manual review

## Core Controls

| Metric | Value |
| --- | ---: |
| Passed | 3 |
| Failed | 0 |
| Manual Review | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |

## Advanced Controls

| Metric | Value |
| --- | ---: |
| Passed | 0 |
| Improvement Opportunities | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |

## Category Scores

| Category | Score | Coverage | Passed | Failed | Manual Review | Needs Semantic Review | N/A | Disabled | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Evaluation | N/A | 0/1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| Governance | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Modeling | N/A | 0/2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| Observability | N/A | 0/1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| Reliability | N/A | 0/2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| Safety | N/A | 0/2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |
| Security | 100.0 | 1/2 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |

## Summary

| Metric | Value |
| --- | ---: |
| Passed | 3 |
| Failed | 0 |
| Manual Review | 0 |
| Needs Semantic Review | 9 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 0 |
| High Failures | 0 |

## Full Rule Results

| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | core | high | NEEDS_SEMANTIC_REVIEW | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | core | high | PASS | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | core | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | core | high | NEEDS_SEMANTIC_REVIEW | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | advanced | medium | NEEDS_SEMANTIC_REVIEW | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | core | medium | NEEDS_SEMANTIC_REVIEW | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | core | medium | NEEDS_SEMANTIC_REVIEW | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | core | medium | NEEDS_SEMANTIC_REVIEW | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | core | high | NEEDS_SEMANTIC_REVIEW | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | core | high | NEEDS_SEMANTIC_REVIEW | Add post-processing or policy checks for model outputs. |
| SEC-001 | Externalized secret management evidence is present | Security | core | high | PASS | Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence. |
| SEC-002 | Tool access uses least privilege | Security | core | high | NEEDS_SEMANTIC_REVIEW | Restrict tool scopes and runtime permissions. |

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

### EVA-001 - AI behavior has automated evaluations

**Severity:** High

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Add repeatable AI evaluation tests to CI workflows.

### MOD-001 - Model or provider configured

**Severity:** High

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Add explicit model/provider configuration settings.

### MOD-002 - Model version documented

**Severity:** Medium

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Document model versions and update procedures.

### OBS-001 - AI interactions produce logs or telemetry

**Severity:** Medium

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Add structured logs and telemetry for AI interactions.

### REL-001 - Model calls define timeouts

**Severity:** Medium

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Set timeout values for all model calls.

### REL-002 - Model calls define retry or fallback

**Severity:** Medium

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Implement bounded retries or alternate provider fallback.

### SAF-001 - Input validation present

**Severity:** High

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Add validation and sanitization checks for AI inputs.

### SAF-002 - Output guardrails present

**Severity:** High

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Add post-processing or policy checks for model outputs.

### SEC-002 - Tool access uses least privilege

**Severity:** High

**Status:** NEEDS_SEMANTIC_REVIEW

**Reason:** Deterministic applicability is inconclusive.

**Review:** Restrict tool scopes and runtime permissions.


## Passed Controls

- PASS GOV-001: AI ownership documented
- PASS GOV-002: AI purpose documented
- PASS SEC-001: Externalized secret management evidence is present

## Not Applicable

- None
