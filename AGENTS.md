# Working with This Template

You are assisting on a Copier-based Python project template. Keep changes minimal and automation-friendly.

Repo: https://github.com/mgaitan/python-package-copier-template
Copier docs: https://copier.readthedocs.io/en/stable/

## Purpose
- Scaffold a basic Python package with `uv`, CLI entrypoint, tests, docs, CI/CD (GitHub Actions), and optional PyPI publishing.
- Supports optional GitHub repo creation via the `gh` CLI and an early PyPI name check.

## Quick Facts for Agents
- Template entrypoint: `copier.yml` (prompts, defaults, tasks).
- Jinja helpers: see `python_package_copier_template/extensions.py` (slugify, PyPI check/suggestion, gh username/availability).
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
- Never auto-commit/auto-push unless requested.
- Network calls are limited to what the template already does (e.g., PyPI HEAD check).

## Python preferences

- Modern and idiomatic practices that emphasize clarity and predictable behavior. Examples of modern features:
   - Pathlib for file operations
   - Data model methods (like __len__, __add__, etc.)
   - Stdlib or pydantic dataclasses
   - Advanced itertools
   - Pattern matching
   - walrus operator
   - enums subclasses (StrEnum, IntEnum, IntFlag)
- Dependency changes use `uv add` or `uv remove`
- Docstrings in Markdown ("myst") format, expressing intentions rather than implementation details.
  Make references to other code if appropriate. Eg: "See also `{py:func}`other_module.helper_function`.".
- Explicit and robust type annotations using built-in generics (`list`, `dict`, etc.), union types with `|`, etc.
- Prefer flat code: use early returns, guard clauses, fixtures over context managers on tests, etc.
- Never hallucinate APIs or behaviours. If uncertain, inspect the code and/or check online documentation (ensure it's the correct version declared by uv.lock) or ask the developer
