from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CodePatternDefinition:
    identifier: str
    category: str
    description: str
    pattern: re.Pattern[str]
    extensions: tuple[str, ...]


def _compile(regex: str) -> re.Pattern[str]:
    return re.compile(regex, re.IGNORECASE)


ALL_CODE_EXTENSIONS: tuple[str, ...] = (
    ".py",
    ".java",
    ".kt",
    ".js",
    ".ts",
    ".tsx",
    ".go",
    ".cs",
)


CODE_PATTERN_REGISTRY: tuple[CodePatternDefinition, ...] = (
    # Retry and resilience
    CodePatternDefinition(
        identifier="retry_annotation",
        category="retry",
        description="Retry annotation usage detected",
        pattern=_compile(r"@\s*Retry(?:able)?\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="retry_template",
        category="retry",
        description="Spring RetryTemplate usage detected",
        pattern=_compile(r"\bRetryTemplate\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="resilience4j_retry",
        category="retry",
        description="Resilience4j retry API usage detected",
        pattern=_compile(r"io\.github\.resilience4j\.retry|\bRetry\.decorate\w*\s*\("),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="python_tenacity_retry",
        category="retry",
        description="Python tenacity retry decorator detected",
        pattern=_compile(r"@\s*(?:tenacity\.)?retry\s*\("),
        extensions=(".py",),
    ),
    # Input validation
    CodePatternDefinition(
        identifier="java_validation_annotation",
        category="input_validation",
        description="Java/Kotlin validation annotation detected",
        pattern=_compile(r"@\s*(Valid|Validated|NotNull|NotBlank)\b"),
        extensions=(".java", ".kt"),
    ),
    CodePatternDefinition(
        identifier="pydantic_model_validation",
        category="input_validation",
        description="Pydantic model validation construct detected",
        pattern=_compile(r"\bBaseModel\b|\bField\s*\(|\bfield_validator\s*\(|\bmodel_validator\s*\("),
        extensions=(".py",),
    ),
    CodePatternDefinition(
        identifier="schema_validation_library",
        category="input_validation",
        description="Schema-validation library usage detected",
        pattern=_compile(r"\bz\.object\s*\(|\bJoi\.object\s*\(|\bschema\.validate\s*\("),
        extensions=(".js", ".ts", ".tsx"),
    ),
    # Observability and tracing
    CodePatternDefinition(
        identifier="otel_tracing",
        category="observability",
        description="OpenTelemetry tracing usage detected",
        pattern=_compile(
            r"\bOpenTelemetry\b|\bio\.opentelemetry\b|\bGlobalOpenTelemetry\b|"
            r"\bstart_as_current_span\s*\(|\bstartSpan\s*\(|\bgetTracer\s*\("
        ),
        extensions=ALL_CODE_EXTENSIONS,
    ),
    # Fallback constructs
    CodePatternDefinition(
        identifier="circuit_breaker_fallback",
        category="fallback",
        description="Circuit-breaker fallback construct detected",
        pattern=_compile(r"\bfallbackMethod\s*=|@\s*CircuitBreaker\b"),
        extensions=(".java", ".kt"),
    ),
)
