# Contributing

Thank you for considering a contribution! :tada:

## Workflow
1. **Fork** & create feature branch (`feat/xyz` or `fix/xyz`).
2. Ensure `pytest` passes locally.
3. Follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.
4. Open a PR against `main`; the GitHub Actions pipeline will run tests.

## Coding standards
* Black + isort formatting (coming soon).
* Type hints where practical.
* Keep `DEBUG=True`—don't remove the dev shortcuts.

## Adding dependencies
* Pin versions in `requirements.txt`.
* Avoid heavy packages; deployment footprint matters.

## Docs
Update markdown files in `docs/` when behavior or endpoints change. 