# Contributing

Thanks for your interest in contributing to EARF.

## How to Contribute

1. Fork the repository and create a feature branch.
2. Make focused changes with tests when behavior changes.
3. Run local checks.
4. Open a pull request with a clear summary.

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run checks before opening a PR:

```bash
pytest
ruff check .
mypy src/earf
```

## Scope and Architecture Boundaries

- Keep collectors focused on deterministic fact collection.
- Keep rule definitions declarative in YAML.
- Keep scoring logic in the scoring layer.
- Avoid unrelated refactors in contribution PRs.

## Pull Request Guidelines

- Use descriptive commit messages.
- Include tests for new behavior when practical.
- Update docs when CLI behavior or workflows change.
- Keep PRs small and reviewable.

## Code of Conduct

By participating, you agree to follow `CODE_OF_CONDUCT.md`.

## License

By contributing, you agree that contributions are provided under the MIT License.
