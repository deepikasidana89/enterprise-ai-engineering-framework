from pathlib import Path

from earf.collectors.dependency_collector import DependencyCollector
from earf.models import RepositoryContext


def _context(path: Path) -> RepositoryContext:
    return RepositoryContext(root_path=path, project_name=path.name)


def test_dependency_collector_collects_from_requirements_and_pyproject(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        """
# comment
requests>=2.0
pydantic==2.8.0
requests>=2.0
""".strip(),
        encoding="utf-8",
    )
    (tmp_path / "pyproject.toml").write_text(
        """
[project]
dependencies = ["typer>=0.10.0", "rich>=13.0"]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff"]
""".strip(),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    items = collector.collect(_context(tmp_path))
    ids = [item.identifier for item in items]

    assert "requests" in ids
    assert "pydantic" in ids
    assert "typer" in ids
    assert "rich" in ids
    assert "pytest" in ids
    assert "ruff" in ids


def test_dependency_collector_normalizes_python_package_variants(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "\n".join(
            [
                "OpenAI==1.40.0",
                '"openai>=1.0,<2.0"',
                "langchain_openai>=0.3",
                "langchain[openai]~=0.3",
                "my-openai-helper",
                "openai-tools-internal",
            ]
        ),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    items = collector.collect(_context(tmp_path))
    ids = {item.identifier for item in items}

    assert "openai" in ids
    assert "langchain-openai" in ids
    assert "langchain" in ids
    assert "my-openai-helper" in ids
    assert "openai-tools-internal" in ids


def test_dependency_collector_collects_tool_poetry_dependencies(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        "\n".join(
            [
                "[tool.poetry]",
                "name = \"x\"",
                "version = \"0.1.0\"",
                "[tool.poetry.dependencies]",
                "python = \">=3.11\"",
                "OpenAI = \"^1.40.0\"",
                "langchain_openai = \"^0.3.0\"",
                "[tool.poetry.group.dev.dependencies]",
                "pytest = \"^8.0.0\"",
            ]
        ),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    ids = {item.identifier for item in collector.collect(_context(tmp_path))}

    assert "openai" in ids
    assert "langchain-openai" in ids
    assert "pytest" in ids


def test_dependency_collector_collects_from_setup_cfg(tmp_path: Path) -> None:
    (tmp_path / "setup.cfg").write_text(
        "\n".join(
            [
                "[metadata]",
                "name = sample",
                "[options]",
                "install_requires =",
                "    OpenAI>=1.0",
                "    langchain_openai~=0.3",
                "[options.extras_require]",
                "dev =",
                "    pytest>=8",
            ]
        ),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    ids = {item.identifier for item in collector.collect(_context(tmp_path))}

    assert "openai" in ids
    assert "langchain-openai" in ids
    assert "pytest" in ids


def test_dependency_collector_collects_from_setup_py(tmp_path: Path) -> None:
    (tmp_path / "setup.py").write_text(
        "\n".join(
            [
                "from setuptools import setup",
                "setup(",
                "    name='sample',",
                "    install_requires=['OpenAI>=1.0', 'langchain_openai>=0.3'],",
                "    extras_require={'dev': ['pytest>=8']},",
                ")",
            ]
        ),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    ids = {item.identifier for item in collector.collect(_context(tmp_path))}

    assert "openai" in ids
    assert "langchain-openai" in ids
    assert "pytest" in ids


def test_dependency_collector_collects_from_pipfile(tmp_path: Path) -> None:
    (tmp_path / "Pipfile").write_text(
        "\n".join(
            [
                "[packages]",
                "OpenAI = \"*\"",
                "langchain_openai = \"*\"",
                "[dev-packages]",
                "pytest = \"*\"",
            ]
        ),
        encoding="utf-8",
    )

    collector = DependencyCollector()
    ids = {item.identifier for item in collector.collect(_context(tmp_path))}

    assert "openai" in ids
    assert "langchain-openai" in ids
    assert "pytest" in ids


def test_dependency_collector_handles_missing_files(tmp_path: Path) -> None:
    collector = DependencyCollector()
    assert collector.collect(_context(tmp_path)) == []


def test_dependency_collector_ignores_invalid_pyproject(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project", encoding="utf-8")
    collector = DependencyCollector()
    assert collector.collect(_context(tmp_path)) == []


def test_dependency_collector_collects_from_package_json(tmp_path: Path) -> None:
        (tmp_path / "package.json").write_text(
                """
{
    "name": "sample",
    "dependencies": {
        "@aws-sdk/client-secrets-manager": "^3.0.0",
        "express": "^4.0.0"
    },
    "optionalDependencies": {
        "@google-cloud/secret-manager": "^5.0.0"
    }
}
""".strip(),
                encoding="utf-8",
        )

        collector = DependencyCollector()
        items = collector.collect(_context(tmp_path))
        ids = {item.identifier for item in items}

        assert "@aws-sdk/client-secrets-manager" in ids
        assert "@google-cloud/secret-manager" in ids
        assert "express" in ids


def test_dependency_collector_collects_from_pom_xml(tmp_path: Path) -> None:
        (tmp_path / "pom.xml").write_text(
                """
<project>
    <dependencies>
        <dependency>
            <groupId>software.amazon.awssdk</groupId>
            <artifactId>secretsmanager</artifactId>
            <version>2.25.0</version>
        </dependency>
    </dependencies>
</project>
""".strip(),
                encoding="utf-8",
        )

        collector = DependencyCollector()
        items = collector.collect(_context(tmp_path))
        ids = {item.identifier for item in items}

        assert "secretsmanager" in ids
        assert "software.amazon.awssdk:secretsmanager" in ids
