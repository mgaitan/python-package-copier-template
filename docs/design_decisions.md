# Features and Decisions

This template is intentionally opinionated.
It is meant to capture a working baseline for modern Python projects, not to be a neutral scaffold with every choice deferred.

The original rationale is described in the blog post [My opinionated scaffolding for modern Python projects](https://mgaitan.github.io/en/posts/opinionated-python-project-scaffolding/).
This chapter translates that rationale into a feature-by-feature reference.

## Copier template, plus a wrapper

The foundation is [Copier](https://copier.readthedocs.io/), not a plain GitHub template repository.
That matters because Copier supports project updates, so conventions can evolve after the initial scaffold.

This repository also publishes a wrapper CLI as `python-package-copier-template`.
The wrapper is intentionally small:

- it detects copy vs update mode from the destination,
- it keeps the happy path short,
- it hides the extra `copier-template-extensions` setup most users do not want to remember.

When you want full control, you can always drop to raw Copier commands.

## Python packaging defaults

Generated projects assume:

- Python 3.12+,
- a `src/` layout,
- metadata centralized in `pyproject.toml`,
- [`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/) as the build backend for pure-Python packages,
- an optional CLI entrypoint implemented with [`argparse`](https://docs.python.org/3/library/argparse.html).

These defaults aim for a modern baseline without introducing unnecessary packaging complexity.
They match current packaging guidance better than older `setup.py`-centric layouts and are a good fit for libraries and small applications that do not need compiled extensions.

## Dependency management with uv

The template uses [uv](https://docs.astral.sh/uv/) for environment management, dependency resolution, and package publishing.
That decision is mostly about coherence:

- one tool for local environments and CI,
- fast installs and syncs,
- dependency groups in `pyproject.toml`,
- native support for building and publishing workflows.

Generated projects split dependencies by purpose, typically across runtime, docs, tests, and QA.
This follows the direction of [PEP 735 dependency groups](https://peps.python.org/pep-0735/) and keeps installs task-focused.

## Dependency cooldowns

The template enables `uv` dependency cooldowns by default with `[tool.uv].exclude-newer`.
The goal is not perfect supply-chain security; it is a practical delay buffer so projects do not pull the newest releases the moment they appear.

Some QA tools can still opt into fresher versions when needed.
That tradeoff keeps projects conservative by default while preserving room to adopt toolchain fixes intentionally.

## QA stack: Ruff, ty, pytest

The baseline QA toolchain is:

- [Ruff](https://docs.astral.sh/ruff/) for linting and formatting,
- [ty](https://github.com/astral-sh/ty) for type checking,
- [pytest](https://docs.pytest.org/), [pytest-cov](https://pytest-cov.readthedocs.io/), and [coverage.py](https://coverage.readthedocs.io/) for tests and coverage.

The reason is simple: this stack is fast, batteries-included, and easy to automate.
Ruff collapses what used to require several tools.
`ty` is still young, but it fits well for new codebases where adopting newer tooling is acceptable.
Pytest remains the least surprising default for most Python teams.

The generated `Makefile` exposes stable shortcuts such as `make qa` and `make test` so contributors do not need to remember long commands.

## Documentation with Sphinx and MyST

Generated projects include a `docs/` directory from day one.
That is a deliberate choice: documentation is much easier to maintain when the scaffolding already exists before the project becomes complicated.

The docs stack is:

- [Sphinx](https://www.sphinx-doc.org/),
- [MyST](https://myst-parser.readthedocs.io/) for Markdown authoring,
- GitHub Pages for hosting,
- plus a couple of extensions in generated projects for diagrams and terminal captures.

This keeps docs in the same lifecycle as code:

- authored in-repo,
- built locally with `make docs`,
- validated in CI,
- published automatically.

## GitHub automation

The template automates several repository tasks through [GitHub Actions](https://github.com/features/actions) and, when available, [GitHub CLI](https://cli.github.com/):

- CI on pushes and pull requests,
- docs previews for documentation PRs,
- releases to PyPI through [Trusted Publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/),
- scheduled template refreshes for generated projects,
- optional initial repository creation and push.

The point is to reduce the amount of “project setup work” that usually gets postponed and then repeated by hand across repositories.

## Trusted Publishing for releases

Generated projects are configured to publish to PyPI through OIDC-based Trusted Publishing rather than long-lived tokens.
That removes a class of secret-management problems from normal release automation.

It still requires a one-time manual registration in PyPI, because PyPI must know which repository and workflow are allowed to publish the project.
After that, the release flow is intentionally boring:

```bash
make bump
make release
```

## Repository ergonomics

The template also generates the boring but useful project files early:

- `LICENSE`,
- `CODE_OF_CONDUCT.md`,
- `AGENTS.md`,
- starter docs,
- Makefile targets,
- GitHub workflows.

This is less about ceremony and more about reducing setup variance.
When those pieces already exist, projects are easier to maintain consistently.

## Updating generated projects

The most distinctive feature of using Copier instead of a one-shot scaffold is updateability.
Generated projects keep a `.copier-answers.yml` file with template metadata and answers from the original questionnaire.

That enables:

- manual updates with `uvx python-package-copier-template .`,
- direct updates with `copier update`,
- automated refresh PRs through the generated workflow.

That update path is one of the main reasons to use this template at all.
It allows the scaffold to behave more like shared project infrastructure than a static starting snapshot.
