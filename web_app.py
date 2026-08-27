from __future__ import annotations

import io
import json
import re
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import streamlit as st

from earf.pipeline import EARFPipeline
from earf.reporting import PdfReporter


MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 150 * 1024 * 1024
MAX_FILES = 10_000
USER_AGENT = "EARF-Web/1.0 (+https://github.com/deepikasidana89/enterprise-ai-engineering-framework)"
GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class RepositoryInputError(ValueError):
    pass


def parse_github_repository(value: str) -> tuple[str, str]:
    """Return (owner, repo) for an exact public github.com repository URL."""
    raw = value.strip()
    if not raw:
        raise RepositoryInputError("Enter a GitHub repository URL.")

    if "://" not in raw:
        raw = "https://" + raw

    parsed = urlparse(raw)
    if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
        raise RepositoryInputError("Use an https://github.com/owner/repository URL.")

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        raise RepositoryInputError("Enter the repository root URL, for example https://github.com/owner/repository.")

    owner, repo = parts
    if repo.endswith(".git"):
        repo = repo[:-4]

    if not GITHUB_REPO_PATTERN.fullmatch(f"{owner}/{repo}"):
        raise RepositoryInputError("The GitHub owner or repository name contains unsupported characters.")

    return owner, repo


def _request_json(url: str) -> dict[str, object]:
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read(1_000_000)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RepositoryInputError(
                "Repository not found. The hosted pilot currently supports public GitHub repositories only."
            ) from exc
        if exc.code == 403:
            raise RepositoryInputError("GitHub rate limit reached. Please try again later.") from exc
        raise RepositoryInputError(f"GitHub returned HTTP {exc.code} while validating the repository.") from exc
    except urllib.error.URLError as exc:
        raise RepositoryInputError("GitHub could not be reached. Please try again.") from exc

    try:
        result = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RepositoryInputError("GitHub returned an unexpected response.") from exc

    if not isinstance(result, dict):
        raise RepositoryInputError("GitHub returned an unexpected response.")
    return result


def get_public_repository(owner: str, repo: str) -> dict[str, object]:
    metadata = _request_json(f"https://api.github.com/repos/{owner}/{repo}")
    if bool(metadata.get("private", False)):
        raise RepositoryInputError("Private repositories are not supported by the hosted pilot.")
    if bool(metadata.get("archived", False)):
        st.info("This repository is archived. EARF can still assess the repository snapshot.")
    return metadata


def download_repository_zip(owner: str, repo: str, branch: str, destination: Path) -> Path:
    safe_branch = urllib.parse.quote(branch, safe="")
    url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{safe_branch}"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    archive = io.BytesIO()
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > MAX_DOWNLOAD_BYTES:
                raise RepositoryInputError("Repository archive is too large for the hosted pilot (50 MB limit).")

            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    raise RepositoryInputError("Repository archive is too large for the hosted pilot (50 MB limit).")
                archive.write(chunk)
    except urllib.error.HTTPError as exc:
        raise RepositoryInputError(f"GitHub could not provide the repository archive (HTTP {exc.code}).") from exc
    except urllib.error.URLError as exc:
        raise RepositoryInputError("The repository archive could not be downloaded.") from exc

    archive.seek(0)
    try:
        with zipfile.ZipFile(archive) as zip_file:
            infos = zip_file.infolist()
            if len(infos) > MAX_FILES:
                raise RepositoryInputError("Repository contains too many files for the hosted pilot.")

            extracted_size = sum(info.file_size for info in infos)
            if extracted_size > MAX_EXTRACTED_BYTES:
                raise RepositoryInputError("Repository expands beyond the hosted pilot's 150 MB scan limit.")

            destination_resolved = destination.resolve()
            for info in infos:
                member_path = (destination / info.filename).resolve()
                if destination_resolved not in member_path.parents and member_path != destination_resolved:
                    raise RepositoryInputError("Repository archive contains an unsafe path and cannot be scanned.")

            zip_file.extractall(destination)
    except zipfile.BadZipFile as exc:
        raise RepositoryInputError("GitHub returned an invalid repository archive.") from exc

    roots = [path for path in destination.iterdir() if path.is_dir()]
    if len(roots) != 1:
        raise RepositoryInputError("The downloaded repository archive has an unexpected structure.")
    return roots[0]


def generate_assessment(owner: str, repo: str) -> tuple[object, bytes]:
    metadata = get_public_repository(owner, repo)
    default_branch = str(metadata.get("default_branch") or "main")

    with tempfile.TemporaryDirectory(prefix="earf-web-") as temp_dir:
        workspace = Path(temp_dir)
        repository_path = download_repository_zip(owner, repo, default_branch, workspace / "repository")
        analysis = EARFPipeline().analyze(repository_path)
        report = analysis.readiness_report
        if report is None:
            raise RuntimeError("EARF did not produce a readiness report.")

        pdf_path = workspace / "EARF_REPORT.pdf"
        PdfReporter().write(report, pdf_path)
        pdf_bytes = pdf_path.read_bytes()
        return report, pdf_bytes


def _status_icon(status: str) -> str:
    if status == "READY":
        return "✅"
    if status == "READY_WITH_WARNINGS":
        return "⚠️"
    return "🚧"


def render_report(report: object, pdf_bytes: bytes, owner: str, repo: str) -> None:
    score = report.readiness_score
    status = score.production_readiness.value
    coverage = score.assessment_coverage

    st.success("Assessment complete")
    st.subheader(f"{owner}/{repo}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Core readiness", f"{score.core_readiness_score:.1f}/100")
    col2.metric("Advanced controls", f"{score.advanced_controls_score:.1f}/100")
    col3.metric("Automated coverage", f"{coverage.percentage:.1f}%")

    st.markdown(f"### {_status_icon(status)} Production status: `{status}`")

    category_rows: list[dict[str, object]] = []
    for category, detail in sorted(score.category_details.items()):
        tracked = (
            detail.passed_rules
            + detail.failed_rules
            + detail.manual_review_rules
            + detail.needs_semantic_review_rules
            + detail.not_applicable_rules
            + detail.disabled_rules
            + detail.error_rules
        )
        category_rows.append(
            {
                "Category": category.replace("_", " ").title(),
                "Score": round(detail.score, 1) if detail.score is not None else None,
                "Passed": detail.passed_rules,
                "Failed": detail.failed_rules,
                "Coverage": f"{detail.passed_rules + detail.failed_rules}/{tracked}",
            }
        )

    if category_rows:
        st.markdown("#### Category scores")
        st.dataframe(category_rows, use_container_width=True, hide_index=True)

    core_gaps = list(report.metadata.get("core_gaps", []))
    if core_gaps:
        st.markdown("#### Priority findings")
        for finding in core_gaps[:8]:
            severity = str(finding.get("severity", ""))
            rule_id = str(finding.get("rule_id", ""))
            title = str(finding.get("title", "Finding"))
            recommendation = str(finding.get("recommendation", "")).strip()
            with st.expander(f"{severity} · {rule_id} · {title}"):
                if recommendation:
                    st.write(recommendation)
                else:
                    st.write("Review this finding with the responsible engineering team.")

    st.download_button(
        "Download full PDF report",
        data=pdf_bytes,
        file_name=f"EARF_REPORT_{repo}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )

    st.caption(
        "EARF reports repository evidence, not certification. Validate important findings with the responsible engineers and combine them with runtime and operational evidence."
    )


def main() -> None:
    st.set_page_config(
        page_title="EARF AI Readiness Assessment",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        .block-container {max-width: 1000px; padding-top: 2.5rem; padding-bottom: 3rem;}
        .earf-hero {padding: 1.4rem 1.6rem; border: 1px solid #dbe4ec; border-radius: 18px; background: #f7fafc; margin-bottom: 1.2rem;}
        .earf-hero h1 {margin: 0 0 .35rem 0; font-size: 2.1rem;}
        .earf-hero p {margin: 0; color: #536273; font-size: 1.02rem;}
        </style>
        <div class="earf-hero">
          <h1>EARF AI Readiness Assessment</h1>
          <p>Paste a public GitHub repository and receive an evidence-based engineering readiness assessment with a downloadable PDF report.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(
        "Hosted pilot: public GitHub repositories only. EARF downloads a temporary snapshot for the assessment and does not intentionally retain the repository after the request finishes."
    )

    repo_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository",
        help="Use the repository root URL. Private repositories are not supported by the hosted pilot.",
    )
    authorized = st.checkbox(
        "I confirm that I am authorized to submit this repository for assessment."
    )

    submitted = st.button(
        "Generate readiness assessment",
        type="primary",
        use_container_width=True,
        disabled=not authorized,
    )

    if submitted:
        try:
            owner, repo = parse_github_repository(repo_url)
            with st.spinner("Downloading the repository snapshot and running EARF..."):
                report, pdf_bytes = generate_assessment(owner, repo)
            render_report(report, pdf_bytes, owner, repo)
        except RepositoryInputError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("EARF could not complete this assessment. Please verify the repository and try again.")
            with st.expander("Technical details"):
                st.code(f"{type(exc).__name__}: {exc}")

    st.divider()
    st.caption(
        "Enterprise AI Readiness Framework (EARF) · Open-source, evidence-driven production-readiness assessment"
    )


if __name__ == "__main__":
    main()
