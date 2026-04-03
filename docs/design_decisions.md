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

The dependency groups also use `include-group` to compose higher-level groups from narrower ones instead of repeating the same tools across sections.
That gives generated projects a small inheritance-style structure:

```{mermaid}
flowchart TD
    lint["lint"] --> qa["qa"]
    test["test"] --> dev["dev"]
    qa --> dev
    docs["docs"] -. optional local install .-> run_docs["uv run --group docs ..."]
    test -. focused install .-> run_test["uv run --group test pytest"]
    dev -. default dev environment .-> run_dev["uv run ..."]
```

In the generated `pyproject.toml`, that looks like this:

```toml
[dependency-groups]
test = [
    "pytest>=9.0.1",
    "pytest-freezer>=0.4.9",
    "pytest-mock>=3.15.0",
    "pytest-cov>=7.0.0",
]
lint = ["ruff"]
qa = [
    { include-group = "lint" },
    "ty>=0.0.27",
]
docs = [
    "myst-parser>=3.0.0",
    "sphinx>=8.2",
    "sphinx-book-theme>=1.1.0",
    "sphinxcontrib-mermaid>=1.0.0",
    "richterm[sphinx]>=0.1.0",
]
dev = [
    { include-group = "test" },
    { include-group = "qa" },
    "ipdb",
    "ipython",
]
```

This keeps each group focused:

- `test` contains only what is needed to run tests,
- `qa` layers type-checking on top of linting,
- `dev` gives contributors the broadest working set without duplicating `test` and `qa`.

Simon Willison called out this exact pattern in [Dependency groups and uv run](https://til.simonwillison.net/uv/dependency-groups#bonus-tip-defining-dev-in-terms-of-other-dependency-groups), noting that he learned it from `python-package-copier-template`.

:::{note}
We learn from Simon's writing all the time, so it felt especially meaningful to give something back for once. Seeing this project teach him one small trick was a real point of pride and gratitude. 🙏
:::

## Dependency cooldowns

The template enables `uv` dependency cooldowns by default with `[tool.uv].exclude-newer`.
The goal is not perfect supply-chain security; it is a practical delay buffer so projects do not pull the newest releases the moment they appear.

Some QA tools can still opt into fresher versions when needed.
That tradeoff keeps projects conservative by default while preserving room to adopt toolchain fixes intentionally.

## Ruff for linting and formatting

[Ruff](https://docs.astral.sh/ruff/) is the linting and formatting baseline.
The main value here is consolidation: a single fast tool can cover what used to require multiple linters and formatters, which makes local feedback and CI simpler.

## ty for type checking

[ty](https://github.com/astral-sh/ty) is the default type checker.
That is an intentionally modern choice rather than the most conservative one.
For a fresh template, the tradeoff is acceptable: the tool is fast, improving quickly, and a good fit for projects that want explicit types without a lot of ceremony.

## pytest for tests

[pytest](https://docs.pytest.org/) remains the default testing framework, together with [pytest-cov](https://pytest-cov.readthedocs.io/) and [coverage.py](https://coverage.readthedocs.io/).
It is still the least surprising default for most Python teams, and it keeps the generated test suite straightforward to extend.

## prek for orchestration and hooks

[prek](https://github.com/j178/prek) is included as an optional layer for QA orchestration and git hook management.
The template does not hard-require it to exist everywhere, but when it is available it gives generated projects a convenient way to install hooks and run the whole QA suite consistently.

The generated `Makefile` exposes stable shortcuts such as `make qa` and `make test` so contributors do not need to remember long commands.

## Documentation with Sphinx and MyST

Generated projects include a `docs/` directory from day one.
That is a deliberate choice: documentation is much easier to maintain when the scaffolding already exists before the project becomes complicated.

The docs stack is:

- [Sphinx](https://www.sphinx-doc.org/),
- [MyST](https://myst-parser.readthedocs.io/) for Markdown authoring,
- [sphinx-book-theme](https://sphinx-book-theme.readthedocs.io/) for the generated site theme,
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

## Demo repository

The template is exercised continuously against [mgaitan/yet-another-demo](https://github.com/mgaitan/yet-another-demo), a public repository generated from this scaffold.
That demo is useful for three different reasons:

- it shows what the scaffold looks like after rendering,
- it gives a realistic target for smoke-testing updates,
- it helps keep the template honest by forcing changes to work in a generated project, not only in the template repository itself.

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

## Agent-facing guidance

The generated `AGENTS.md` is part of the scaffold on purpose.
As code agents become a normal part of day-to-day maintenance, repositories benefit from having explicit local instructions for editing style, release habits, documentation expectations, and operational constraints.

This turns agent guidance into project infrastructure instead of ad-hoc chat context.

## Updating generated projects

The most distinctive feature of using Copier instead of a one-shot scaffold is updateability.
Generated projects keep a `.copier-answers.yml` file with template metadata and answers from the original questionnaire.

That enables:

- manual updates with `uvx python-package-copier-template .`,
- direct updates with `copier update`,
- automated refresh PRs through the generated workflow.

That update path is one of the main reasons to use this template at all.
It allows the scaffold to behave more like shared project infrastructure than a static starting snapshot.
