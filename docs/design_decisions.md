# Design Decisions

This template is intentionally opinionated. The goal is not to provide a neutral skeleton, but a practical baseline that already encodes decisions usually made at project start.

## Boilerplate vs scaffolding

A `pyproject.toml` plus a package folder is enough to start coding, but real projects quickly need much more: QA conventions, CI/CD, docs, release flow, and repository automation.
The template treats those as part of project architecture, not optional extras.

That is why this repository uses Copier instead of a one-shot boilerplate approach.
With Copier, generated projects can evolve through `copier update`, so conventions can improve over time without hand-editing every repository.

## Why this toolchain

The defaults reflect the rationale described in the project blog post:
<https://mgaitan.github.io/en/posts/opinionated-python-project-scaffolding/>.

In short:

- `uv` for dependency and environment management with dependency groups.
- Ruff + Ty + pytest as the baseline QA stack.
- Sphinx + MyST for documentation as part of the same code lifecycle.
- GitHub Actions for CI, release automation, docs deploy, and template refresh.

This is a coherence decision more than a \"best tool\" claim: the stack should feel integrated and keep friction low for day-to-day work.

## Why generated projects are \"complete\" from day one

The template generates project metadata, docs skeleton, CI/CD workflows, and operational shortcuts (`Makefile`) because those are the pieces teams often postpone and later have to retrofit under pressure.
Starting with them in place reduces setup variance and improves long-term maintainability.
