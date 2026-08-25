# EARF Enterprise AI Readiness Report

Repository: general-knowledge-assistant
Generated: 2026-08-25T02:00:26Z
EARF Version: 0.7.0
Total Evidence: 9

## Overall Assessment

| Metric | Result |
| --- | ---: |
| Core Readiness | 23.1 / 100 |
| Advanced Controls | 100.0 / 100 |
| Automated Evaluation Coverage | 100.0% (12/12) |
| Overall Score | 27.5 / 100 |

## Production Status

NOT_READY

## Why?

- 0 critical blockers
- 6 high-priority core gaps
- 3 of 11 scored core controls passed
- 0 applicable core controls require manual review

## Core Controls

| Metric | Value |
| --- | ---: |
| Passed | 3 |
| Failed | 8 |
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
| Evaluation | 0.0 | 1/1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Governance | 36.4 | 2/2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| Modeling | 100.0 | 2/2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| Observability | 0.0 | 1/1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Reliability | 50.0 | 2/2 | 1 | 1 | 0 | 0 | 0 | 0 | 0 |
| Safety | 0.0 | 2/2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| Security | 0.0 | 2/2 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |

## Summary

| Metric | Value |
| --- | ---: |
| Passed | 4 |
| Failed | 8 |
| Manual Review | 0 |
| Needs Semantic Review | 0 |
| Not Applicable | 0 |
| Disabled | 0 |
| Errors | 0 |
| Critical Failures | 0 |
| High Failures | 6 |

## Full Rule Results

| Rule ID | Title | Category | Tier | Severity | Status | Recommendation |
| --- | --- | --- | --- | --- | --- | --- |
| EVA-001 | AI behavior has automated evaluations | Evaluation | core | high | FAIL | Add repeatable AI evaluation tests to CI workflows. |
| GOV-001 | AI ownership documented | Governance | core | high | FAIL | Document the owner and escalation path. |
| GOV-002 | AI purpose documented | Governance | core | medium | PASS | Add documentation describing intended use and boundaries. |
| MOD-001 | Model or provider configured | Modeling | core | high | PASS | Add explicit model/provider configuration settings. |
| MOD-002 | Model version documented | Modeling | advanced | medium | PASS | Document model versions and update procedures. |
| OBS-001 | AI interactions produce logs or telemetry | Observability | core | medium | FAIL | Add structured logs and telemetry for AI interactions. |
| REL-001 | Model calls define timeouts | Reliability | core | medium | PASS | Set timeout values for all model calls. |
| REL-002 | Model calls define retry or fallback | Reliability | core | medium | FAIL | Implement bounded retries or alternate provider fallback. |
| SAF-001 | Input validation present | Safety | core | high | FAIL | Add validation and sanitization checks for AI inputs. |
| SAF-002 | Output guardrails present | Safety | core | high | FAIL | Add post-processing or policy checks for model outputs. |
| SEC-001 | Externalized secret management evidence is present | Security | core | high | FAIL | Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence. |
| SEC-002 | Tool access uses least privilege | Security | core | high | FAIL | Restrict tool scopes and runtime permissions. |

## Recommendations

- EVA-001: Add repeatable AI evaluation tests to CI workflows.
- GOV-001: Document the owner and escalation path.
- OBS-001: Add structured logs and telemetry for AI interactions.
- REL-002: Implement bounded retries or alternate provider fallback.
- SAF-001: Add validation and sanitization checks for AI inputs.
- SAF-002: Add post-processing or policy checks for model outputs.
- SEC-001: Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence.
- SEC-002: Restrict tool scopes and runtime permissions.

## Critical Blockers

- None

## Top Core Gaps

### EVA-001 - AI behavior has automated evaluations

**Severity:** High

**Status:** FAIL

**Reason:** Automated AI evaluation evidence was not detected.

**Action:** Add repeatable AI evaluation tests to CI workflows.

**Missing evidence checks:**

- Missing requirement: evidence_type=workflow
- Missing requirement: evidence_type=test, identifiers=['eva.runtime_evaluation'], source=signal

### GOV-001 - AI ownership documented

**Severity:** High

**Status:** FAIL

**Reason:** Required evidence for this control was not detected.

**Action:** Document the owner and escalation path.

**Missing evidence checks:**

- Missing requirement: evidence_type=file, identifiers=['CODEOWNERS']

### OBS-001 - AI interactions produce logs or telemetry

**Severity:** Medium

**Status:** FAIL

**Reason:** AI observability or tracing evidence was not detected.

**Action:** Add structured logs and telemetry for AI interactions.

**Missing evidence checks:**

- Missing requirement: evidence_type=implementation, identifiers=['obs.telemetry_runtime'], source=signal
- Missing requirement: evidence_type=code_pattern, identifiers=['otel_tracing']

### REL-002 - Model calls define retry or fallback

**Severity:** Medium

**Status:** FAIL

**Reason:** Retry or resilience implementation evidence was not detected.

**Action:** Implement bounded retries or alternate provider fallback.

**Missing evidence checks:**

- Missing requirement: evidence_type=implementation, identifiers=['rel.retry_runtime'], source=signal
- Missing requirement: evidence_type=code_pattern, identifiers=['circuit_breaker_fallback', 'python_tenacity_retry', 'resilience4j_retry', 'retry_annotation', 'retry_template']

### SAF-001 - Input validation present

**Severity:** High

**Status:** FAIL

**Reason:** Input validation evidence was not detected.

**Action:** Add validation and sanitization checks for AI inputs.

**Missing evidence checks:**

- Missing requirement: evidence_type=implementation, identifiers=['saf.input_validation_runtime'], source=signal
- Missing requirement: evidence_type=code_pattern, identifiers=['java_validation_annotation', 'pydantic_model_validation', 'schema_validation_library']

### SAF-002 - Output guardrails present

**Severity:** High

**Status:** FAIL

**Reason:** Output guardrail evidence was not detected.

**Action:** Add post-processing or policy checks for model outputs.

**Missing evidence checks:**

- Missing requirement: evidence_type=implementation, identifiers=['saf.output_guardrail_runtime'], source=signal

### SEC-001 - Externalized secret management evidence is present

**Severity:** High

**Status:** FAIL

**Reason:** No supported evidence of externalized secret management was detected.

**Action:** Integrate a supported secret manager or documented internal secret-management abstraction with implementation evidence.

**Missing evidence checks:**

- Missing requirement: evidence_type=dependency, identifiers=['@aws-sdk/client-secrets-manager', '@azure/keyvault-secrets', '@google-cloud/secret-manager', 'aws-secretsmanager-caching', 'azure-keyvault-secrets', 'boto3', 'com.amazonaws:aws-java-sdk-secretsmanager', 'com.bettercloud:vault-java-driver', 'google-cloud-secret-manager', 'hvac', 'secretsmanager', 'software.amazon.awssdk:secretsmanager']
- Missing requirement: evidence_type=configuration, identifiers=['sec.externalized_secret.aws_usage', 'sec.externalized_secret.azure_usage', 'sec.externalized_secret.gcp_usage', 'sec.externalized_secret.kubernetes_secret_ref', 'sec.externalized_secret.vault_usage'], source=secret_management
- Missing requirement: evidence_type=configuration, identifiers=['sec.externalized_secret.aws_usage', 'sec.externalized_secret.azure_usage', 'sec.externalized_secret.gcp_usage', 'sec.externalized_secret.kubernetes_secret_ref', 'sec.externalized_secret.vault_usage'], source=secret_management
- Missing requirement: evidence_type=file, identifiers=['.env.example']
- Missing requirement: evidence_type=file, identifiers=['SECURITY.md']
- Missing requirement: evidence_type=configuration, identifiers=['sec.externalized_secret.custom_abstraction'], source=secret_management
- Missing requirement: evidence_type=configuration, identifiers=['sec.externalized_secret.sensitive_env_access'], source=secret_management
- Missing requirement: evidence_type=configuration, identifiers=['sec.externalized_secret.custom_abstraction'], source=secret_management
- Missing requirement: evidence_type=file, identifiers=['SECURITY.md']

### SEC-002 - Tool access uses least privilege

**Severity:** High

**Status:** FAIL

**Reason:** Least-privilege access control evidence was not detected.

**Action:** Restrict tool scopes and runtime permissions.

**Missing evidence checks:**

- Missing requirement: evidence_type=file, identifiers=['CODEOWNERS']
- Missing requirement: evidence_type=configuration, identifiers=['sec.workflow_least_privilege'], source=signal


## Advanced Opportunities

- None

## Manual Review Required

- None

## Needs Semantic Review

- None

## Passed Controls

- PASS GOV-002: AI purpose documented
- PASS MOD-001: Model or provider configured
- PASS MOD-002: Model version documented
- PASS REL-001: Model calls define timeouts

## Not Applicable

- None
