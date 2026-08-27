# EARF Adoption Evidence

The hosted EARF pilot can record privacy-first adoption evidence without storing submitted source code or generated PDF reports.

## What is recorded

For a completed assessment, EARF can retain:

- a random assessment ID
- UTC timestamp
- a salted SHA-256 fingerprint of the normalized GitHub owner/repository name
- whether that repository fingerprint has been assessed before
- assessment number for that repository fingerprint
- EARF version
- production status
- core readiness score
- advanced controls score
- automated evaluation coverage
- assessment completion
- PDF download event
- optional 30-second feedback
- optional name, role, organization/university, and email only when the user chooses to provide them

EARF does **not** store the repository URL, repository source code, or generated PDF report in the adoption evidence store.

## Why evidence is not stored in a local Excel file

Streamlit Community Cloud app storage is not designed as a durable shared evidence database. A single workbook also creates write-collision problems when multiple users submit assessments at the same time.

Instead, EARF writes one small JSON record per assessment to a private GitHub repository. This provides durable, timestamped records without requiring a database. The records can later be exported into a formatted Excel evidence workbook for analysis or an evidence archive.

## Recommended evidence repository

Use a private repository such as:

`deepikasidana89/earf-adoption-pilot`

Keep the evidence repository private because optional participants may choose to provide identifying information or feedback.

## Streamlit secrets

The hosted app only enables persistent evidence capture when all required secrets are configured in Streamlit Community Cloud.

Add these secrets in the app's Streamlit settings:

```toml
ADOPTION_GITHUB_TOKEN = "<fine-grained-token>"
ADOPTION_EVIDENCE_REPO = "deepikasidana89/earf-adoption-pilot"
ADOPTION_EVIDENCE_BRANCH = "main"
ADOPTION_HASH_SALT = "<long-random-secret>"
```

Use a fine-grained GitHub token restricted to the private evidence repository with only the repository contents permission required to create/update evidence files. Do not commit the token or hash salt to either repository.

The hash salt should be a long random value. Keeping it secret makes it substantially harder for someone with only the evidence records to reverse common public repository names by guessing them and recomputing hashes.

## Evidence layout

The private evidence repository will contain records similar to:

```text
evidence/
  assessments/
    2026/
      08/
        EARF-20260827-A1B2C3D4.json
  feedback/
    2026/
      08/
        EARF-20260827-A1B2C3D4.json
  repositories/
    <salted-repository-fingerprint>.json
```

The repository fingerprint record stores only the fingerprint, first/last assessment timestamps, assessment count, and latest assessment ID. This supports repeat-assessment metrics without retaining the repository URL.

## Exporting to Excel

Do not treat the private JSON records as the presentation layer. Periodically export them to a dated Excel workbook with summary metrics such as:

- completed assessments
- unique repository fingerprints
- repeat assessments
- PDF downloads
- feedback response rate
- average usefulness rating
- percentage reporting a new readiness consideration
- percentage likely to act on recommendations
- percentage willing to use EARF again
- voluntarily identified organizations/universities

Keep dated exports in the private adoption evidence repository or another approved evidence archive.
