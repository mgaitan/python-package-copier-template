# Working with This Template

You are assisting on a Copier-based Python project template. Keep changes minimal and automation-friendly.

Repo: https://github.com/mgaitan/python-package-copier-template
Copier docs: https://copier.readthedocs.io/en/stable/

## Purpose
- Scaffold a basic Python package with `uv`, CLI entrypoint, tests, docs, CI/CD (GitHub Actions), and optional PyPI publishing.
- Supports optional GitHub repo creation via the `gh` CLI and an early PyPI name check.

## Quick Facts for Agents
- Template entrypoint: `copier.yml` (prompts, defaults, tasks).
- Jinja helpers: see `extensions.py` (slugify, PyPI check/suggestion, gh username/availability).
- Project skeleton lives under `project/`.
- CI: `project/.github/workflows/ci.yml.jinja` (lint/tests).
- CD: `project/.github/workflows/cd.yml.jinja` (PyPI publish on release; docs publish on release or manual dispatch).
- Makefile: `project/Makefile.jinja` (install, test, qa, docs, etc.).

## Running the Template Locally
- Create a project: `uv run copier copy --trust  --vcs-ref=HEAD . ../my-project`
  - To skip gh repo creation: `--data gh_repo_create=skip`
  - To force a PyPI name: set `python_package_distribution_name` and confirm if prompted.
- Generated project uses `uv sync` for deps; `make qa` for lint/type; `make test` for tests.

## Editing Notes
- Prefer `apply_patch` for edits; avoid touching user changes you didn't make.
- Do not auto-commit/auto-push unless requested.
- Network calls are limited to what the template already does (e.g., PyPI HEAD check).
