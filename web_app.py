from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import quote, urlparse

REPO_ROOT = Path(__file__).resolve().parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

import streamlit as st

from earf.__about__ import __version__
from earf.adoption import AdoptionConfig, AdoptionStoreError, GitHubAdoptionStore
from earf.pipeline import EARFPipeline
from earf.reporting import PdfReporter

MAX_DOWNLOAD_BYTES = 50 * 1024 * 1024
MAX_EXTRACTED_BYTES = 150 * 1024 * 1024
MAX_FILES = 10_000
USER_AGENT = "EARF-Web/1.1 (+https://github.com/deepikasidana89/enterprise-ai-engineering-framework)"
GITHUB_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


class RepositoryInputError(ValueError):
    pass


def parse_github_repository(value: str) -> tuple[str, str]:
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
    request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read(1_000_000)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RepositoryInputError("Repository not found. The hosted pilot currently supports public GitHub repositories only.") from exc
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
    safe_branch = quote(branch, safe="")
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
        return report, pdf_path.read_bytes()


def _status_icon(status: str) -> str:
    if status == "READY":
        return "✅"
    if status == "READY_WITH_WARNINGS":
        return "⚠️"
    return "🚧"


def get_adoption_store() -> GitHubAdoptionStore | None:
    try:
        config = AdoptionConfig(
            token=str(st.secrets.get("ADOPTION_GITHUB_TOKEN", "")),
            repository=str(st.secrets.get("ADOPTION_EVIDENCE_REPO", "")),
            branch=str(st.secrets.get("ADOPTION_EVIDENCE_BRANCH", "main")),
            hash_salt=str(st.secrets.get("ADOPTION_HASH_SALT", "")),
        )
    except Exception:
        return None
    if not config.enabled:
        return None
    try:
        return GitHubAdoptionStore(config)
    except AdoptionStoreError:
        return None


def render_optional_profile() -> dict[str, str]:
    with st.expander("Want to tell us about yourself? (Optional)", expanded=False):
        st.caption("You can use EARF without sharing personal information. Sharing this is completely optional and helps us understand the engineering communities using EARF.")
        col1, col2 = st.columns(2)
        name = col1.text_input("Name (optional)", key="profile_name")
        role = col2.text_input("Role (optional)", key="profile_role")
        organization = col1.text_input("Organization / university (optional)", key="profile_org")
        email = col2.text_input(
            "Email (optional)",
            key="profile_email",
            help="Share only if you are open to being contacted about EARF research, feedback, or future pilot opportunities.",
        )
    return {"name": name, "role": role, "organization": organization, "email": email}


def render_privacy_details() -> None:
    with st.expander("Privacy & Pilot Data", expanded=False):
        st.markdown(
            """
**What EARF retains**
- The submitted **public GitHub repository URL**.
- A unique assessment ID and timestamp.
- A repository fingerprint used for unique/repeat-assessment counting.
- EARF version and assessment metrics.
- Assessment completion and PDF-download activity.
- Optional feedback you choose to submit.
- Optional name, role, organization/university, and email only if you provide them.

**What EARF does not retain**
- Repository source code after the assessment finishes.
- The generated PDF report after processing.
- Credentials, private repository contents, or private GitHub access.

**Why this data is retained**
The retained metadata is used to understand EARF adoption, measure repeat usage, improve the framework, and document pilot outcomes.

**Storage**
Pilot evidence is stored in a private evidence repository rather than in the public EARF repository.

**Removal requests**
If you voluntarily share personal information or want an assessment record removed, contact the EARF maintainer and provide the assessment ID shown after your assessment.
"""
        )


def render_feedback(assessment_id: str, store: GitHubAdoptionStore | None) -> None:
    st.divider()
    st.markdown("### Help improve EARF - 30 seconds")
    st.caption("Optional. Your feedback helps improve the accuracy and usefulness of future assessments.")
    with st.form(f"feedback-{assessment_id}"):
        useful = st.slider("How useful was this assessment?", min_value=1, max_value=5, value=4)
        new_consideration = st.radio("Did EARF identify a production-readiness consideration you had not previously considered?", ["Yes", "No"], horizontal=True)
        likely_to_act = st.radio("Are you likely to act on one or more EARF recommendations?", ["Yes", "Maybe", "No"], horizontal=True)
        use_again = st.radio("Would you use EARF again?", ["Yes", "Maybe", "No"], horizontal=True)
        comment = st.text_area("Anything EARF got particularly right or wrong? (Optional)", max_chars=1000)
        submitted = st.form_submit_button("Share feedback")
    if submitted:
        if store is None:
            st.warning("Thanks for the feedback. Evidence storage is not configured yet, so this response could not be retained.")
            return
        try:
            store.record_feedback(
                assessment_id=assessment_id,
                useful_rating=useful,
                new_consideration=new_consideration,
                likely_to_act=likely_to_act,
                would_use_again=use_again,
                comment=comment,
            )
            st.success("Thank you. Your feedback has been recorded.")
        except AdoptionStoreError:
            st.warning("Thank you. EARF could not save the feedback right now; the assessment itself is unaffected.")


def render_report(report: object, pdf_bytes: bytes, owner: str, repo: str, assessment_id: str, store: GitHubAdoptionStore | None) -> None:
    score = report.readiness_score
    status = score.production_readiness.value
    coverage = score.assessment_coverage
    st.success("Assessment complete")
    st.caption(f"Assessment ID: `{assessment_id}`")
    st.subheader(f"{owner}/{repo}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Core readiness", f"{score.core_readiness_score:.1f}/100")
    col2.metric("Advanced controls", f"{score.advanced_controls_score:.1f}/100")
    col3.metric("Automated coverage", f"{coverage.percentage:.1f}%")
    st.markdown(f"### {_status_icon(status)} Production status: `{status}`")

    category_rows: list[dict[str, object]] = []
    for category, detail in sorted(score.category_details.items()):
        tracked = detail.passed_rules + detail.failed_rules + detail.manual_review_rules + detail.needs_semantic_review_rules + detail.not_applicable_rules + detail.disabled_rules + detail.error_rules
        category_rows.append({
            "Category": category.replace("_", " ").title(),
            "Score": round(detail.score, 1) if detail.score is not None else None,
            "Passed": detail.passed_rules,
            "Failed": detail.failed_rules,
            "Coverage": f"{detail.passed_rules + detail.failed_rules}/{tracked}",
        })
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
                st.write(recommendation or "Review this finding with the responsible engineering team.")

    downloaded = st.download_button(
        "Download full PDF report",
        data=pdf_bytes,
        file_name=f"EARF_REPORT_{repo}.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )
    if downloaded and store is not None and not st.session_state.get(f"download-recorded-{assessment_id}"):
        try:
            store.record_pdf_download(assessment_id)
            st.session_state[f"download-recorded-{assessment_id}"] = True
        except AdoptionStoreError:
            pass

    st.caption("EARF reports repository evidence, not certification. Validate important findings with the responsible engineers and combine them with runtime and operational evidence.")
    render_feedback(assessment_id, store)


def main() -> None:
    st.set_page_config(page_title="EARF AI Readiness Assessment", page_icon="🧭", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
        .block-container {max-width: 1000px; padding-top: 2.5rem; padding-bottom: 3rem;}
        .earf-hero {padding: 1.4rem 1.6rem; border: 1px solid #dbe4ec; border-radius: 18px; background: #f7fafc; margin-bottom: 1.2rem;}
        .earf-hero h1 {margin: 0 0 .35rem 0; font-size: 2.1rem;}
        .earf-hero p {margin: 0; color: #536273; font-size: 1.02rem;}
        </style>
        <div class="earf-hero"><h1>EARF AI Readiness Assessment</h1><p>Paste a public GitHub repository and receive an evidence-based engineering readiness assessment with a downloadable PDF report.</p></div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Hosted pilot: public GitHub repositories only. EARF downloads a temporary snapshot for the assessment. Repository source code and generated PDF reports are not retained after processing.")
    repo_url = st.text_input(
        "GitHub repository URL",
        placeholder="https://github.com/owner/repository",
        help="Use the repository root URL. Private repositories are not supported by the hosted pilot.",
    )
    authorized = st.checkbox(
        "I confirm that I am authorized to submit this public repository for assessment and understand that EARF will retain the public repository URL and assessment metadata for adoption measurement and framework improvement."
    )
    profile = render_optional_profile()
    st.caption("Privacy: EARF retains the submitted public GitHub repository URL and limited assessment/adoption metadata. Repository source code and generated PDF reports are not retained. Personal information is collected only if you voluntarily provide it.")
    render_privacy_details()

    submitted = st.button("Generate readiness assessment", type="primary", use_container_width=True, disabled=not authorized)
    store = get_adoption_store()

    if submitted:
        try:
            owner, repo = parse_github_repository(repo_url)
            with st.spinner("Downloading the repository snapshot and running EARF..."):
                report, pdf_bytes = generate_assessment(owner, repo)
            assessment_id = GitHubAdoptionStore.new_assessment_id()
            if store is not None:
                try:
                    score = report.readiness_score
                    store.record_assessment(
                        assessment_id=assessment_id,
                        owner=owner,
                        repo=repo,
                        earf_version=__version__,
                        production_status=score.production_readiness.value,
                        core_readiness=score.core_readiness_score,
                        advanced_controls=score.advanced_controls_score,
                        automated_coverage=score.assessment_coverage.percentage,
                        optional_profile=profile,
                    )
                except AdoptionStoreError:
                    st.warning("The assessment completed, but adoption evidence could not be saved. Your report is still available below.")
            st.session_state["latest_result"] = (report, pdf_bytes, owner, repo, assessment_id)
        except RepositoryInputError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error("EARF could not complete this assessment. Please verify the repository and try again.")
            with st.expander("Technical details"):
                st.code(f"{type(exc).__name__}: {exc}")

    latest = st.session_state.get("latest_result")
    if latest:
        render_report(*latest, store)

    st.divider()
    st.caption("Enterprise AI Readiness Framework (EARF) · Open-source, evidence-driven production-readiness assessment")


if __name__ == "__main__":
    main()
