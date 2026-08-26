# PDF Readiness Reports

EARF can generate a polished PDF assessment suitable for sharing with engineers, pilot participants, and technical reviewers.

## Generate a PDF

```bash
earf report /path/to/your-ai-project --format pdf --output EARF_REPORT.pdf
```

If `--output` is omitted, EARF writes `EARF_REPORT.pdf` in the current directory.

## What the PDF contains

The PDF uses the same readiness analysis and scoring model as the console, JSON, and Markdown reports. It adds a presentation layer with:

- Executive readiness dashboard
- Core readiness, advanced controls, and automated coverage
- Production status
- Category score table
- Critical blockers and prioritized core gaps
- Advanced opportunities
- Manual and semantic review items
- Recommended next actions
- Passed controls
- Assessment limitations and interpretation guidance

The PDF is intentionally an engineering assessment, not a certification. Findings should be reviewed with the engineers responsible for the assessed system.

## GitHub Action

The EARF composite GitHub Action now generates all three shareable artifacts:

- `earf-report.json`
- `EARF_REPORT.md`
- `EARF_REPORT.pdf`

The PDF is useful for pilot reviews and stakeholder conversations, while JSON remains the machine-readable source for automation.
