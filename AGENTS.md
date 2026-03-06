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
- Package docs for this repository live under `docs/` and follow Diataxis.
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
- For `gh pr` interactions, prefer `--body-file` with a temporary file created under `/tmp/`.
- For documentation edits, keep Diataxis separation clear and maintain the env var glossary in `docs/configuration.md` (refer via `{term}` in docs chapters).
- Always work via pull requests from `main` unless explicitly told otherwise.
- Never propose or attempt direct commits to `main`.
- For each new task, create an isolated branch + git worktree and perform all edits there.
- Prefer `make task-start TASK=<task-name>` to create the worktree from `origin/main`.
- Use `make task-list` to locate active task worktrees if a session is interrupted.

## Starting a New Task

Agents MUST create an isolated git worktree.

1. Preferred: run `make task-start TASK=<task-name>` from the main repository directory.
2. Manual fallback:
   - `git fetch origin`
   - `git worktree add .worktrees/<task-name> -b <branch-name> origin/main`
   - `cd .worktrees/<task-name>`
3. Do all work inside that worktree directory.
4. Keep `.agent-task-context.md` in the task worktree so interrupted sessions can recover the right branch/path.

Agents must never:

- Run `git checkout` in the main working directory to switch active task branches.
- Modify files outside their task worktree unless explicitly asked.
- Reuse a worktree that belongs to another task.

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
- Validate type safety with `uv run ty check` after relevant code changes.
- Prefer flat code: use early returns, guard clauses, fixtures over context managers on tests, etc.
- Never hallucinate APIs or behaviours. If uncertain, inspect the code and/or check online documentation (ensure it's the correct version declared by uv.lock) or ask the developer
