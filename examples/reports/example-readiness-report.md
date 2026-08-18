# EARF Enterprise AI Readiness Report

Repository: enterprise-ai-readiness-framework
Generated: 2026-08-18T05:41:38Z
EARF Version: 0.7.0
Total Evidence: 64

## Overall Assessment

| Metric | Result |
| --- | ---: |
| Core Readiness | 61.1 / 100 |
| Advanced Controls | 0.0 / 100 |
| Assessment Coverage | 100.0% (3/3) |
| Overall Score | 61.1 / 100 |

## Production Status

NOT_READY

## Why?

- 0 critical blockers
- 1 high-priority core gaps
- 2 of 3 applicable core controls passed

## Core Controls

| Metric | Value |
| --- | ---: |
| Passed | 2 |
| Failed | 1 |
| Manual Review | 0 |
| Not Applicable | 8 |
| Disabled | 0 |
| Errors | 0 |

## Advanced Controls

| Metric | Value |
| --- | ---: |
| Passed | 0 |
| Improvement Opportunities | 0 |
| Not Applicable | 1 |
| Disabled | 0 |
| Errors | 0 |

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
| Manual Review | 0 |
| Not Applicable | 9 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 0 |
| High Failures | 1 |

## Full Rule Results

| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | core | high | NOT_APPLICABLE | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | core | high | FAIL | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | core | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | core | high | NOT_APPLICABLE | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | advanced | medium | NOT_APPLICABLE | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | core | medium | NOT_APPLICABLE | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | core | medium | NOT_APPLICABLE | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | core | medium | NOT_APPLICABLE | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | core | high | NOT_APPLICABLE | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | core | high | NOT_APPLICABLE | Add post-processing or policy checks for model outputs. |
| SEC-001 | Externalized secret management evidence is present | Security | core | high | PASS | Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence. |
| SEC-002 | Tool access uses least privilege | Security | core | high | NOT_APPLICABLE | Restrict tool scopes and runtime permissions. |

## Recommendations

- GOV-001: Document the owner and escalation path.

## Critical Blockers

- None

## Top Core Gaps

### GOV-001 - AI ownership documented

**Severity:** High

**Status:** FAIL

**Reason:** Required evidence for this control was not detected.

**Action:** Document the owner and escalation path.

**Missing evidence checks:**

- Missing requirement: evidence_type=file, identifiers=['CODEOWNERS']


## Advanced Opportunities

- None

## Passed Controls

- PASS GOV-002: AI purpose documented
- PASS SEC-001: Externalized secret management evidence is present

## Not Applicable

### EVA-001 - AI behavior has automated evaluations

**Reason:** uses_llm capability evidence was not detected.

### MOD-001 - Model or provider configured

**Reason:** Missing requirement: evidence_type=dependency, identifiers=['anthropic', 'azure-ai-inference', 'google-generativeai', 'langchain', 'langgraph', 'litellm', 'llama-index', 'openai', 'semantic-kernel', 'transformers']

### MOD-002 - Model version documented

**Reason:** Missing requirement: evidence_type=dependency, identifiers=['anthropic', 'azure-ai-inference', 'google-generativeai', 'langchain', 'langgraph', 'litellm', 'llama-index', 'openai', 'semantic-kernel', 'transformers']

### OBS-001 - AI interactions produce logs or telemetry

**Reason:** Missing requirement: evidence_type=dependency, identifiers=['anthropic', 'azure-ai-inference', 'google-generativeai', 'langchain', 'langgraph', 'litellm', 'llama-index', 'openai', 'semantic-kernel', 'transformers']

### REL-001 - Model calls define timeouts

**Reason:** uses_llm capability evidence was not detected.

### REL-002 - Model calls define retry or fallback

**Reason:** uses_llm capability evidence was not detected.

### SAF-001 - Input validation present

**Reason:** uses_llm capability evidence was not detected.

### SAF-002 - Output guardrails present

**Reason:** Missing requirement: evidence_type=dependency, identifiers=['anthropic', 'azure-ai-inference', 'google-generativeai', 'langchain', 'langgraph', 'litellm', 'llama-index', 'openai', 'semantic-kernel', 'transformers']

### SEC-002 - Tool access uses least privilege

**Reason:** Missing requirement: evidence_type=dependency, identifiers=['anthropic', 'azure-ai-inference', 'google-generativeai', 'langchain', 'langgraph', 'litellm', 'llama-index', 'openai', 'semantic-kernel', 'transformers']

