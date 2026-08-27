# EARF Web Assessment

EARF includes a Streamlit web interface that lets a user paste a **public GitHub repository URL**, run an EARF assessment without cloning the repository locally, review key readiness results in the browser, and download the full PDF report.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[web]"
streamlit run web_app.py
```

## Hosted pilot behavior

The first hosted version intentionally supports public GitHub repositories only.

The app:

1. Accepts only `https://github.com/owner/repository` repository-root URLs.
2. Checks repository metadata through GitHub's public API.
3. Downloads the default-branch archive into a temporary directory.
4. Enforces archive, extracted-size, and file-count limits.
5. Runs the existing EARF analysis pipeline against the temporary snapshot.
6. Shows readiness metrics and priority findings in the browser.
7. Generates the same polished EARF PDF assessment used by the CLI.
8. Returns the PDF through a download button.
9. Removes the temporary workspace when the assessment request completes.

EARF does not intentionally persist submitted repository source code in the web application.

## Deploy free on Streamlit Community Cloud

1. Sign in to Streamlit Community Cloud with GitHub.
2. Choose **Create app** / **Deploy an app**.
3. Select `deepikasidana89/enterprise-ai-engineering-framework`.
4. Select branch `main`.
5. Set the app entrypoint to `web_app.py`.
6. Choose an available app URL, for example `earf-assessment.streamlit.app`.
7. Deploy.

The repository includes `requirements.txt` for Community Cloud installation and `.streamlit/config.toml` for the basic app configuration.

After deployment, add the actual hosted URL to the main README as the **Try EARF Online** link.

## Security and privacy boundaries

The hosted pilot is not intended for confidential, proprietary, or private repositories. Users must confirm that they are authorized to submit the repository.

Do not add a text box for personal access tokens. Private-repository support should be implemented later using an approved GitHub authentication/application flow and an appropriate production hosting/security model.

The web assessment remains an engineering evidence review, not a certification, compliance approval, or security assurance.
