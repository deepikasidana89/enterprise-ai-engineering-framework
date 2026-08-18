from __future__ import annotations

from pathlib import Path

from earf.collectors.code_pattern_collector import CodePatternCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_code_pattern_java_retry_annotation_detected(tmp_path: Path) -> None:
    (tmp_path / "Service.java").write_text(
        "@Retry(name = \"modelProvider\")\n"
        "public class Service {}\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert any(item.identifier == "retry_annotation" for item in items)


def test_code_pattern_python_tenacity_detected(tmp_path: Path) -> None:
    (tmp_path / "service.py").write_text(
        "@retry(stop=stop_after_attempt(3))\n"
        "def call_model():\n"
        "    pass\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert any(item.identifier == "python_tenacity_retry" for item in items)


def test_code_pattern_generic_retry_word_not_matched(tmp_path: Path) -> None:
    (tmp_path / "Service.java").write_text(
        "String message = \"retry the request later\";\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert all(item.identifier not in {"retry_annotation", "retry_template", "resilience4j_retry", "python_tenacity_retry"} for item in items)


def test_code_pattern_comment_does_not_count(tmp_path: Path) -> None:
    (tmp_path / "Service.java").write_text(
        "// TODO add @Retry here\n"
        "public class Service {}\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert all(item.identifier != "retry_annotation" for item in items)


def test_code_pattern_java_validation_detected(tmp_path: Path) -> None:
    (tmp_path / "Controller.java").write_text(
        "public class Controller {\n"
        "  public void create(@Valid Request request) {}\n"
        "}\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert any(item.identifier == "java_validation_annotation" for item in items)


def test_code_pattern_pydantic_detected(tmp_path: Path) -> None:
    (tmp_path / "models.py").write_text(
        "from pydantic import BaseModel\n"
        "class Request(BaseModel):\n"
        "    prompt: str\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert any(item.identifier == "pydantic_model_validation" for item in items)


def test_code_pattern_opentelemetry_detected(tmp_path: Path) -> None:
    (tmp_path / "Tracing.java").write_text(
        "Tracer tracer = GlobalOpenTelemetry.getTracer(\"ai-service\");\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert any(item.identifier == "otel_tracing" for item in items)


def test_code_pattern_ignored_directory_not_scanned(tmp_path: Path) -> None:
    node_modules = tmp_path / "node_modules"
    node_modules.mkdir()
    (node_modules / "lib.js").write_text("@Retry(name='x')", encoding="utf-8")

    items = CodePatternCollector().collect(_context(tmp_path))

    assert items == []


def test_code_pattern_test_directory_not_scanned_by_default(tmp_path: Path) -> None:
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "service.py").write_text(
        "@retry(stop=stop_after_attempt(3))\n"
        "def call_model():\n"
        "    pass\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))

    assert items == []


def test_code_pattern_large_or_binary_file_skipped(tmp_path: Path) -> None:
    # Larger than collector max and includes a binary byte.
    oversized = tmp_path / "service.py"
    oversized.write_bytes(b"\x00" + b"a" * 1_100_000)

    items = CodePatternCollector().collect(_context(tmp_path))

    assert items == []


def test_code_pattern_evidence_contains_provenance(tmp_path: Path) -> None:
    (tmp_path / "Service.java").write_text(
        "@Retry(name = \"provider\")\n"
        "public class Service {}\n",
        encoding="utf-8",
    )

    items = CodePatternCollector().collect(_context(tmp_path))
    match = next(item for item in items if item.identifier == "retry_annotation")

    assert match.path == "Service.java"
    assert match.location is not None and match.location.startswith("Service.java:")
    assert match.metadata.get("pattern_id") == "retry_annotation"
