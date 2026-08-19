from __future__ import annotations

import re

from .base import EvidenceCollector
from .workspace_index import ensure_workspace_index
from ..models import Evidence, EvidenceType, RepositoryContext


class SignalCollector(EvidenceCollector):
    """Collect generalized deterministic signals from repository-wide indexed files."""

    name = "signal"

    _CONFIG_SUFFIXES = {
        ".yaml",
        ".yml",
        ".json",
        ".toml",
        ".properties",
        ".conf",
        ".ini",
        ".xml",
        ".env.example",
    }
    _CODE_SUFFIXES = {
        ".py",
        ".java",
        ".kt",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".go",
        ".cs",
        ".rb",
        ".rs",
        ".php",
    }

    _AI_CONFIG_PATTERN = re.compile(
        r"\b(provider|model_provider|llm_provider|azure_openai|anthropic|gemini|bedrock|deployment_name|model)\b\s*[:=]\s*['\"]?([A-Za-z0-9_.:-]+)?",
        re.IGNORECASE,
    )
    _AI_IMPORT_PATTERN = re.compile(
        r"\b(from\s+(openai|anthropic|google\.generativeai|langchain|langgraph|litellm)\s+import|"
        r"import\s+(openai|anthropic|google\.generativeai|langchain|langgraph|litellm)|"
        r"require\(\s*['\"](@?openai|anthropic|@google/generative-ai|langchain|langgraph|litellm)['\"]\s*\)|"
        r"import\s+.*\s+from\s+['\"](@?openai|anthropic|@google/generative-ai|langchain|langgraph|litellm)['\"])",
        re.IGNORECASE,
    )
    _AI_RUNTIME_PATTERN = re.compile(
        r"\b(responses\.create|chat\.completions\.create|messages\.create|generate_content|invoke_model|embeddings\.create)\s*\(",
        re.IGNORECASE,
    )
    _AI_GATEWAY_PATTERN = re.compile(
        r"\b(ai_client|llm_client|model_gateway|llm_gateway|inference_client|generation_client)\b",
        re.IGNORECASE,
    )

    _OBS_RUNTIME_PATTERN = re.compile(
        r"\b(start_as_current_span|startSpan|getTracer|OpenTelemetry|TracerProvider|trace\.get_tracer)\b",
        re.IGNORECASE,
    )
    _REL_TIMEOUT_PATTERN = re.compile(r"\b(timeout|request_timeout|max_wait)\s*=", re.IGNORECASE)
    _REL_RETRY_PATTERN = re.compile(
        r"\b(retry|backoff|RetryTemplate|tenacity|CircuitBreaker|fallbackMethod)\b",
        re.IGNORECASE,
    )
    _SAF_INPUT_PATTERN = re.compile(
        r"\b(BaseModel|field_validator|model_validator|schema\.validate|Joi\.object|z\.object)\b",
        re.IGNORECASE,
    )
    _SAF_OUTPUT_PATTERN = re.compile(
        r"\b(guardrail|content_filter|moderation|policy_check|sanitize_output)\b",
        re.IGNORECASE,
    )
    _EVAL_RUNTIME_PATTERN = re.compile(
        r"\b(evaluate\(|run_evaluation\(|compute_metrics\(|assert_quality\(|score_output\()",
        re.IGNORECASE,
    )
    _WORKFLOW_LEAST_PRIV_PATTERN = re.compile(
        r"permissions\s*:\s*(?:\n\s+[A-Za-z_-]+\s*:\s*read\s*)+|permissions\s*:\s*read-all",
        re.IGNORECASE,
    )

    _AI_DOC_PATTERN = re.compile(r"\b(openai|anthropic|llm|model provider|ai gateway)\b", re.IGNORECASE)
    _AI_COMMENT_PATTERN = re.compile(r"\b(openai|anthropic|llm|ai)\b", re.IGNORECASE)

    def collect(self, context: RepositoryContext) -> list[Evidence]:
        index = ensure_workspace_index(context)

        items: list[Evidence] = []

        for indexed in index.files:
            text = indexed.text
            if not indexed.is_text or text is None:
                continue

            if indexed.suffix in self._CONFIG_SUFFIXES:
                items.extend(self._config_signals(indexed.relative_path, text))

            if indexed.is_workflow:
                least_priv_line = self._line_for(text, self._WORKFLOW_LEAST_PRIV_PATTERN)
                if least_priv_line is not None:
                    items.append(
                        self._build(
                            evidence_type=EvidenceType.CONFIGURATION,
                            identifier="sec.workflow_least_privilege",
                            description="Workflow least-privilege permissions configuration detected",
                            rel_path=indexed.relative_path,
                            line=least_priv_line,
                            strength="MODERATE",
                            capability="security",
                        )
                    )

            if indexed.suffix in self._CODE_SUFFIXES and not indexed.is_test_like:
                items.extend(self._code_signals(indexed.relative_path, text))

            if indexed.is_documentation and self._AI_DOC_PATTERN.search(text):
                items.append(
                    self._build(
                        evidence_type=EvidenceType.DOCUMENTATION,
                        identifier="ai.documentation_mention",
                        description="AI-related mention in documentation",
                        rel_path=indexed.relative_path,
                        line=self._line_for(text, self._AI_DOC_PATTERN),
                        strength="WEAK",
                        capability="uses_ai",
                    )
                )

            for line_no, line_text in self._iter_comment_lines(indexed.relative_path, text):
                if self._AI_COMMENT_PATTERN.search(line_text):
                    items.append(
                        self._build(
                            evidence_type=EvidenceType.COMMENT,
                            identifier="ai.comment_mention",
                            description="AI-related mention in comment",
                            rel_path=indexed.relative_path,
                            line=line_no,
                            strength="WEAK",
                            capability="uses_ai",
                        )
                    )
                    break

            filename_lower = indexed.relative_path.lower()
            if "evaluation" in filename_lower:
                items.append(
                    self._build(
                        evidence_type=EvidenceType.FILENAME,
                        identifier="evaluation.filename_hint",
                        description="Evaluation-related filename detected",
                        rel_path=indexed.relative_path,
                        line=1,
                        strength="WEAK",
                        capability="evaluation",
                    )
                )

        return self._dedupe(items)

    def _config_signals(self, rel_path: str, text: str) -> list[Evidence]:
        items: list[Evidence] = []
        for match in self._AI_CONFIG_PATTERN.finditer(text):
            key = match.group(1).lower()
            value = (match.group(2) or "").lower()
            line = text.count("\n", 0, match.start()) + 1
            identifier = "ai.provider_config" if key != "model" else "ai.model_config"
            items.append(
                self._build(
                    evidence_type=EvidenceType.CONFIGURATION,
                    identifier=identifier,
                    description="AI provider/model configuration key detected",
                    rel_path=rel_path,
                    line=line,
                    strength="MODERATE",
                    capability="uses_ai",
                    metadata={"config_key": key, "value_hint": self._safe_value_hint(value)},
                )
            )
        return items

    def _code_signals(self, rel_path: str, text: str) -> list[Evidence]:
        items: list[Evidence] = []

        import_line = self._line_for(text, self._AI_IMPORT_PATTERN)
        if import_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPORT,
                    identifier="ai.provider_import",
                    description="AI provider/framework import detected",
                    rel_path=rel_path,
                    line=import_line,
                    strength="MODERATE",
                    capability="uses_ai",
                )
            )

        runtime_line = self._line_for(text, self._AI_RUNTIME_PATTERN)
        if runtime_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.RUNTIME_CALL,
                    identifier="ai.runtime_call",
                    description="AI runtime API invocation detected",
                    rel_path=rel_path,
                    line=runtime_line,
                    strength="STRONG",
                    capability="uses_ai",
                )
            )

        gateway_line = self._line_for(text, self._AI_GATEWAY_PATTERN)
        if gateway_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="ai.gateway_usage",
                    description="Internal AI gateway usage detected",
                    rel_path=rel_path,
                    line=gateway_line,
                    strength="MODERATE",
                    capability="uses_ai",
                )
            )

        obs_line = self._line_for(text, self._OBS_RUNTIME_PATTERN)
        if obs_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="obs.telemetry_runtime",
                    description="Telemetry/tracing implementation detected",
                    rel_path=rel_path,
                    line=obs_line,
                    strength="STRONG",
                    capability="observability",
                )
            )

        timeout_line = self._line_for(text, self._REL_TIMEOUT_PATTERN)
        if timeout_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="rel.timeout_runtime",
                    description="Timeout configuration in implementation detected",
                    rel_path=rel_path,
                    line=timeout_line,
                    strength="MODERATE",
                    capability="reliability",
                )
            )

        retry_line = self._line_for(text, self._REL_RETRY_PATTERN)
        if retry_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="rel.retry_runtime",
                    description="Retry/fallback implementation detected",
                    rel_path=rel_path,
                    line=retry_line,
                    strength="STRONG",
                    capability="reliability",
                )
            )

        input_line = self._line_for(text, self._SAF_INPUT_PATTERN)
        if input_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="saf.input_validation_runtime",
                    description="Input validation implementation detected",
                    rel_path=rel_path,
                    line=input_line,
                    strength="STRONG",
                    capability="safety",
                )
            )

        output_line = self._line_for(text, self._SAF_OUTPUT_PATTERN)
        if output_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.IMPLEMENTATION,
                    identifier="saf.output_guardrail_runtime",
                    description="Output guardrail implementation detected",
                    rel_path=rel_path,
                    line=output_line,
                    strength="STRONG",
                    capability="safety",
                )
            )

        eval_line = self._line_for(text, self._EVAL_RUNTIME_PATTERN)
        if eval_line is not None:
            items.append(
                self._build(
                    evidence_type=EvidenceType.TEST,
                    identifier="eva.runtime_evaluation",
                    description="Evaluation execution/metric computation detected",
                    rel_path=rel_path,
                    line=eval_line,
                    strength="STRONG",
                    capability="evaluation",
                )
            )

        return items

    def _iter_comment_lines(self, rel_path: str, text: str) -> list[tuple[int, str]]:
        suffix = rel_path.rsplit(".", 1)[-1].lower() if "." in rel_path else ""
        comment_markers = ["#"] if suffix == "py" else ["//", "#"]

        lines: list[tuple[int, str]] = []
        for index, line in enumerate(text.splitlines(), start=1):
            stripped = line.strip()
            if any(stripped.startswith(marker) for marker in comment_markers):
                lines.append((index, stripped))
        return lines

    def _line_for(self, content: str, pattern: re.Pattern[str]) -> int | None:
        match = pattern.search(content)
        if match is None:
            return None
        return content.count("\n", 0, match.start()) + 1

    def _safe_value_hint(self, value: str) -> str:
        if not value:
            return "unknown"
        token = value.strip().lower()
        if any(secret_marker in token for secret_marker in ("key", "token", "secret", "password")):
            return "redacted"
        return token[:40]

    def _build(
        self,
        *,
        evidence_type: EvidenceType,
        identifier: str,
        description: str,
        rel_path: str,
        line: int | None,
        strength: str,
        capability: str,
        metadata: dict[str, object] | None = None,
    ) -> Evidence:
        location = rel_path if line is None else f"{rel_path}:{line}"
        payload: dict[str, object] = {
            "collector": self.name,
            "line": line,
            "strength": strength,
            "capability": capability,
        }
        if metadata:
            payload.update(metadata)

        return Evidence(
            evidence_type=evidence_type,
            source=self.name,
            description=description,
            identifier=identifier,
            path=rel_path,
            location=location,
            metadata=payload,
        )

    def _dedupe(self, items: list[Evidence]) -> list[Evidence]:
        seen: set[tuple[str, str, str | None]] = set()
        result: list[Evidence] = []
        for item in items:
            key = (item.evidence_type.value, item.identifier, item.location)
            if key in seen:
                continue
            seen.add(key)
            result.append(item)
        return sorted(result, key=lambda item: (item.identifier, item.path or "", item.location or ""))
