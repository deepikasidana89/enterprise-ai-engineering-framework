# EARF Release Checklist

Use this checklist before publishing a public release.

## Repository and Metadata

- [ ] Confirm final GitHub repository URL (README, pyproject, CITATION, docs)
- [ ] Review package metadata (name, description, classifiers, Python versions)
- [ ] Confirm release version is correct everywhere

## Quality Gates

- [ ] Run `pytest`
- [ ] Run `ruff check .`
- [ ] Run `mypy src/earf`
- [ ] Build artifacts with `python -m build`
- [ ] Validate artifacts with `python -m twine check dist/*`

## Installation Validation

- [ ] Create a clean virtual environment
- [ ] Install wheel from `dist/*.whl`
- [ ] Verify CLI commands (`earf --help`, `earf evidence`, `earf evaluate`, `earf score`, `earf report`)

## GitHub Release Steps

- [ ] Confirm repository visibility setting is ready for public beta
- [ ] Create GitHub release with changelog notes and version tag

## PyPI Publication

- [ ] Upload to TestPyPI and validate install/run
- [ ] Upload to PyPI production

## Communication

- [ ] Prepare public announcement summary
- [ ] Include scope, known limitations, and contribution links
