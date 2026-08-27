from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any
import urllib.error
import urllib.parse
import urllib.request


@dataclass(frozen=True)
class AdoptionConfig:
    token: str
    repository: str
    branch: str = "main"
    hash_salt: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.repository and self.hash_salt)


class AdoptionStoreError(RuntimeError):
    pass


class GitHubAdoptionStore:
    """Persist small adoption-evidence records to a private GitHub repository.

    The hosted EARF app stores the normalized public GitHub repository URL plus a
    salted SHA-256 fingerprint for unique/repeat-assessment analytics. Repository
    source code and generated PDF reports are never stored in the evidence repo.
    """

    def __init__(self, config: AdoptionConfig) -> None:
        if not config.enabled:
            raise AdoptionStoreError("Adoption evidence storage is not configured.")
        if "/" not in config.repository:
            raise AdoptionStoreError("Evidence repository must be in owner/name format.")
        self._config = config

    @staticmethod
    def new_assessment_id() -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        return f"EARF-{timestamp}-{random_part}"

    @staticmethod
    def normalized_repository_url(owner: str, repo: str) -> str:
        return f"https://github.com/{owner.strip()}/{repo.strip()}"

    def repository_fingerprint(self, owner: str, repo: str) -> str:
        normalized = f"{owner.strip().lower()}/{repo.strip().lower()}"
        digest = hashlib.sha256(
            f"{self._config.hash_salt}:{normalized}".encode("utf-8")
        ).hexdigest()
        return digest

    def record_assessment(
        self,
        *,
        assessment_id: str,
        owner: str,
        repo: str,
        earf_version: str,
        production_status: str,
        core_readiness: float,
        advanced_controls: float,
        automated_coverage: float,
        optional_profile: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        fingerprint = self.repository_fingerprint(owner, repo)
        repository_url = self.normalized_repository_url(owner, repo)
        repo_state_path = f"evidence/repositories/{fingerprint}.json"
        repo_state, repo_state_sha = self._read_json(repo_state_path)

        previous_count = int(repo_state.get("assessment_count", 0)) if repo_state else 0
        assessment_count = previous_count + 1
        repeat_assessment = previous_count > 0

        updated_repo_state = {
            "repository_url": repository_url,
            "repository_public": True,
            "repository_fingerprint": fingerprint,
            "assessment_count": assessment_count,
            "first_assessed_at": (
                repo_state.get("first_assessed_at") if repo_state else self._timestamp(now)
            ),
            "last_assessed_at": self._timestamp(now),
            "last_assessment_id": assessment_id,
        }
        self._write_json(
            repo_state_path,
            updated_repo_state,
            message=f"Track EARF repository assessment {assessment_id}",
            sha=repo_state_sha,
        )

        profile = {
            key: value.strip()
            for key, value in (optional_profile or {}).items()
            if isinstance(value, str) and value.strip()
        }
        record: dict[str, Any] = {
            "assessment_id": assessment_id,
            "assessed_at": self._timestamp(now),
            "repository_url": repository_url,
            "repository_public": True,
            "repository_fingerprint": fingerprint,
            "repeat_assessment": repeat_assessment,
            "repository_assessment_number": assessment_count,
            "assessment_completed": True,
            "pdf_generated": True,
            "pdf_downloaded": False,
            "earf_version": earf_version,
            "production_status": production_status,
            "core_readiness": round(core_readiness, 1),
            "advanced_controls": round(advanced_controls, 1),
            "automated_coverage": round(automated_coverage, 1),
            "optional_profile_shared": bool(profile),
        }
        if profile:
            record["optional_profile"] = profile

        path = self._assessment_path(assessment_id, now)
        self._write_json(
            path,
            record,
            message=f"Record EARF assessment {assessment_id}",
        )
        return record

    def record_pdf_download(self, assessment_id: str) -> None:
        path = self._find_assessment_path(assessment_id)
        if path is None:
            return
        record, sha = self._read_json(path)
        if not record or not sha or bool(record.get("pdf_downloaded")):
            return
        record["pdf_downloaded"] = True
        record["pdf_downloaded_at"] = self._timestamp(datetime.now(timezone.utc))
        self._write_json(
            path,
            record,
            message=f"Record EARF PDF download {assessment_id}",
            sha=sha,
        )

    def record_feedback(
        self,
        *,
        assessment_id: str,
        useful_rating: int,
        new_consideration: str,
        likely_to_act: str,
        would_use_again: str,
        comment: str = "",
    ) -> None:
        now = datetime.now(timezone.utc)
        feedback = {
            "assessment_id": assessment_id,
            "submitted_at": self._timestamp(now),
            "useful_rating": int(useful_rating),
            "identified_new_consideration": new_consideration,
            "likely_to_act": likely_to_act,
            "would_use_again": would_use_again,
            "comment": comment.strip(),
        }
        path = f"evidence/feedback/{now:%Y/%m}/{assessment_id}.json"
        existing, existing_sha = self._read_json(path)
        self._write_json(
            path,
            feedback,
            message=f"Record EARF feedback {assessment_id}",
            sha=existing_sha if existing else None,
        )

    def _assessment_path(self, assessment_id: str, when: datetime) -> str:
        return f"evidence/assessments/{when:%Y/%m}/{assessment_id}.json"

    def _find_assessment_path(self, assessment_id: str) -> str | None:
        parts = assessment_id.split("-")
        if len(parts) < 3 or len(parts[1]) != 8 or not parts[1].isdigit():
            return None
        year = parts[1][:4]
        month = parts[1][4:6]
        return f"evidence/assessments/{year}/{month}/{assessment_id}.json"

    @staticmethod
    def _timestamp(value: datetime) -> str:
        return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    def _api_url(self, path: str) -> str:
        owner, repo = self._config.repository.split("/", 1)
        encoded_path = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
        return f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}"

    def _request(self, request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = response.read(2_000_000)
        except urllib.error.HTTPError as exc:
            body = exc.read(4000).decode("utf-8", errors="replace")
            raise AdoptionStoreError(
                f"Evidence store request failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise AdoptionStoreError("Evidence store could not reach GitHub.") from exc

        if not payload:
            return {}
        try:
            parsed = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise AdoptionStoreError("Evidence store returned an unexpected response.") from exc
        return parsed if isinstance(parsed, dict) else {}

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._config.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "EARF-Adoption-Evidence/1.0",
        }

    def _read_json(self, path: str) -> tuple[dict[str, Any], str | None]:
        request = urllib.request.Request(self._api_url(path), headers=self._headers())
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                payload = response.read(2_000_000)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {}, None
            body = exc.read(4000).decode("utf-8", errors="replace")
            raise AdoptionStoreError(
                f"Evidence store read failed with HTTP {exc.code}: {body}"
            ) from exc
        except urllib.error.URLError as exc:
            raise AdoptionStoreError("Evidence store could not reach GitHub.") from exc

        try:
            response_json = json.loads(payload.decode("utf-8"))
            encoded = str(response_json.get("content", "")).replace("\n", "")
            decoded = base64.b64decode(encoded).decode("utf-8")
            record = json.loads(decoded)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise AdoptionStoreError("Evidence store contains an invalid record.") from exc
        return (record if isinstance(record, dict) else {}), str(response_json.get("sha") or "") or None

    def _write_json(
        self,
        path: str,
        record: dict[str, Any],
        *,
        message: str,
        sha: str | None = None,
    ) -> None:
        content = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        body: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": self._config.branch,
        }
        if sha:
            body["sha"] = sha
        request = urllib.request.Request(
            self._api_url(path),
            data=json.dumps(body).encode("utf-8"),
            headers={**self._headers(), "Content-Type": "application/json"},
            method="PUT",
        )
        self._request(request)
