# Features and Decisions

This template makes explicit choices for a working baseline for modern Python projects.

The original rationale is described in the blog post [My opinionated scaffolding for modern Python projects](https://mgaitan.github.io/en/posts/opinionated-python-project-scaffolding/).
This chapter translates that rationale into a feature-by-feature reference.

## Copier template, plus a wrapper

The foundation is [Copier](https://copier.readthedocs.io/).
Copier treats the generated project as a maintained instance of the template:
it records the template version and the answers used during generation, then
uses that information to apply later template updates. This gives the project
a clear lifecycle from the initial scaffold through subsequent improvements,
while leaving conflicts visible for the project maintainer to review.

This repository also publishes a wrapper CLI as `python-package-copier-template`.
The wrapper is intentionally small:

- it detects copy vs update mode from the destination,
- it keeps the happy path short,
- it hides the extra `copier-template-extensions` setup most users do not want to remember.

When you want full control, you can always drop to raw Copier commands.

## Python packaging defaults

Generated projects assume:

- Python 3.12 or newer; CI currently tests Python 3.12 through 3.15,
- the exact Python version used to run Copier is recorded in `.python-version`,
- a `src/` layout,
- metadata centralized in `pyproject.toml`,
- [`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/) as the build backend for pure-Python packages,
- an optional CLI entrypoint implemented with [`argparse`](https://docs.python.org/3/library/argparse.html).

These defaults provide a modern baseline with a small packaging surface.
They fit libraries and small applications that do not need compiled extensions.

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

The configuration includes [Ruff's default rules](https://docs.astral.sh/ruff/default-rules/)
and selects every rule in each listed family. Ruff's default selection is
limited to `E4`, `E7`, `E9`, and `F`; selecting `E`, `W`, and `F` therefore
activates the complete families containing those defaults. The table lists the
complete selection. The remaining families and rule are additional checks.

| Selector | Documentation | Scope |
| --- | --- | --- |
| [`E`, `W`](https://docs.astral.sh/ruff/rules/#pycodestyle-e-w) | pycodestyle | Includes default `E4`, `E7`, and `E9`, plus the complete families; catches style and syntax-adjacent issues. |
| [`F`](https://docs.astral.sh/ruff/rules/#pyflakes-f) | Pyflakes | Includes the default family; finds undefined names and other likely errors. |
| [`I`](https://docs.astral.sh/ruff/rules/#isort-i) | isort | Sorts and groups imports. |
| [`C90`](https://docs.astral.sh/ruff/rules/#mccabe-c90) | McCabe | Flags functions above complexity 10, Ruff's default threshold. |
| [`A`](https://docs.astral.sh/ruff/rules/#flake8-builtins-a) | flake8-builtins | Prevents shadowing Python built-ins. |
| [`ANN`](https://docs.astral.sh/ruff/rules/#flake8-annotations-ann) | flake8-annotations | Checks function annotations. |
| [`UP`](https://docs.astral.sh/ruff/rules/#pyupgrade-up) | pyupgrade | Encourages modern Python syntax. |
| [`RUF`](https://docs.astral.sh/ruff/rules/#ruff-specific-rules-ruf) | Ruff-specific | Applies Ruff-specific correctness and style checks. |
| [`T10`](https://docs.astral.sh/ruff/rules/#flake8-debugger-t10) | flake8-debugger | Finds debugger calls. |
| [`ISC`](https://docs.astral.sh/ruff/rules/#flake8-implicit-str-concat-isc) | flake8-implicit-str-concat | Detects implicit string concatenation. |
| [`SIM`](https://docs.astral.sh/ruff/rules/#flake8-simplify-sim) | flake8-simplify | Suggests simpler control flow. |
| [`ASYNC`](https://docs.astral.sh/ruff/rules/#flake8-async-async) | flake8-async | Checks async code for common problems. |
| [`ERA`](https://docs.astral.sh/ruff/rules/#eradicate-era) | eradicate | Finds commented-out code. |
| [`TRY`](https://docs.astral.sh/ruff/rules/#tryceratops-try) | tryceratops | Checks exception handling practices. |
| [`YTT`](https://docs.astral.sh/ruff/rules/#flake8-2020-ytt) | flake8-2020 | Finds Python-version compatibility traps. |
| [`BLE`](https://docs.astral.sh/ruff/rules/#flake8-blind-except-ble) | flake8-blind-except | Flags overly broad exception handling. |
| [`B`](https://docs.astral.sh/ruff/rules/#flake8-bugbear-b) | flake8-bugbear | Finds likely bugs and design problems. |
| [`EXE`](https://docs.astral.sh/ruff/rules/#flake8-executable-exe) | flake8-executable | Checks executable files and shebangs. |
| [`FA`](https://docs.astral.sh/ruff/rules/#flake8-future-annotations-fa) | flake8-future-annotations | Checks safe use of future annotations. |
| [`C4`](https://docs.astral.sh/ruff/rules/#flake8-comprehensions-c4) | flake8-comprehensions | Simplifies unnecessary comprehensions. |
| [`DTZ`](https://docs.astral.sh/ruff/rules/#flake8-datetimez-dtz) | flake8-datetimez | Requires explicit timezone handling. |
| [`FBT`](https://docs.astral.sh/ruff/rules/#flake8-boolean-trap-fbt) | flake8-boolean-trap | Flags ambiguous boolean arguments. |
| [`INT`](https://docs.astral.sh/ruff/rules/#flake8-gettext-int) | flake8-gettext | Checks gettext usage. |
| [`LOG`, `G`](https://docs.astral.sh/ruff/rules/#flake8-logging-log) | flake8-logging | Checks logging calls and format strings. |
| [`S`](https://docs.astral.sh/ruff/rules/#flake8-bandit-s) | flake8-bandit | Finds common security issues. |
| [`SLF`](https://docs.astral.sh/ruff/rules/#flake8-self-slf) | flake8-self | Restricts access to private members across classes. |
| [`FLY`](https://docs.astral.sh/ruff/rules/#flynt-fly) | flynt | Simplifies string formatting. |
| [`N`](https://docs.astral.sh/ruff/rules/#pep8-naming-n) | pep8-naming | Checks naming conventions. |
| [`PIE`](https://docs.astral.sh/ruff/rules/#flake8-pie-pie) | flake8-pie | Finds unnecessary or error-prone code. |
| [`PYI`](https://docs.astral.sh/ruff/rules/#flake8-pyi-pyi) | flake8-pyi | Checks type stub files. |
| [`PT`](https://docs.astral.sh/ruff/rules/#flake8-pytest-style-pt) | flake8-pytest-style | Checks pytest conventions. |
| [`TC`](https://docs.astral.sh/ruff/rules/#flake8-type-checking-tc) | flake8-type-checking | Organizes type-checking imports. |
| [`PTH`](https://docs.astral.sh/ruff/rules/#flake8-use-pathlib-pth) | flake8-use-pathlib | Encourages pathlib APIs. |
| [`PERF`](https://docs.astral.sh/ruff/rules/#perflint-perf) | Perflint | Finds avoidable performance issues. |
| [`D`](https://docs.astral.sh/ruff/rules/#pydocstyle-d) | pydocstyle | Checks docstring conventions. |
| [`PGH`](https://docs.astral.sh/ruff/rules/#pygrep-hooks-pgh) | pygrep-hooks | Checks fragile code patterns. |
| [`PL`](https://docs.astral.sh/ruff/rules/#pylint-pl) | Pylint | Adds broader code-quality checks. |
| [`FURB`](https://docs.astral.sh/ruff/rules/#refurb-furb) | refurb | Suggests modern Python improvements. |
| [`RET`](https://docs.astral.sh/ruff/rules/#flake8-return-ret) | flake8-return | Checks return statements. |
| [`TID252`](https://docs.astral.sh/ruff/rules/relative-imports/) | flake8-tidy-imports | Requires absolute imports. |

A regression test protects the required selectors in both this package and the
generated project template.

Specific per-file ignores remain narrow. Test modules skip `ANN` and `D`, and
also allow the security patterns `S101`, `S108`, `S603`, and `S607` that are
common in test fixtures. `docs/conf.py` skips `A` and `D100` because it is a
Sphinx configuration module. The incompatible pydocstyle pairs `D203`/`D211`
and `D212`/`D213` are resolved explicitly in favor of `D211` and `D212`.

## ty for type checking

[ty](https://github.com/astral-sh/ty) is the default type checker.
This is a modern choice: the tool is fast, improving quickly, and a good fit
for projects that want explicit types with little ceremony.
The generated package includes a `py.typed` marker, which declares that its
inline annotations are intended to be consumed by type checkers downstream.
`ty check` runs as part of the QA group and as a Prek hook, checking the
package source and reporting type errors before they reach CI.

## pytest for tests

[pytest](https://docs.pytest.org/) remains the default testing framework, together with [pytest-cov](https://pytest-cov.readthedocs.io/) and [coverage.py](https://coverage.readthedocs.io/).
It is still the least surprising default for most Python teams, and it keeps the generated test suite straightforward to extend.

## prek for orchestration and hooks

[prek](https://github.com/j178/prek) is included as an optional layer for QA orchestration and git hook management.
The template does not hard-require it to exist everywhere, but when it is available it gives generated projects a convenient way to install hooks and run the whole QA suite consistently.

The generated `Makefile` exposes stable shortcuts such as `make qa` and `make test`.

The configured checks are:

| Group | Checks |
| --- | --- |
| File hygiene | `trailing-whitespace`, `end-of-file-fixer`, `mixed-line-ending`, `check-added-large-files` |
| Names and links | `check-case-conflict`, `check-illegal-windows-names`, `check-symlinks`, `destroyed-symlinks`, `check-vcs-permalinks` |
| File formats | `check-json`, `check-yaml`, `check-toml`, `check-xml` |
| Repository safety | `check-merge-conflict`, `detect-private-key`, `no-commit-to-branch` for `main` |
| Executables | `check-executables-have-shebangs`, `check-shebang-scripts-are-executable` |
| Python QA | `ruff check --fix`, `ruff format`, `ty check` |

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

The canonical generated-project example is [mgaitan/yet-another-demo](https://github.com/mgaitan/yet-another-demo). Use experiment branches there when validating changes against a real repository created from this scaffold.
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

## Release attestations

Release workflows sign every wheel and source distribution without storing a
long-lived signing key. GitHub Actions exchanges its OIDC identity for a
short-lived Sigstore certificate, and the resulting signed statement binds the
artifact digest to the workflow that produced it.

`astral-sh/attest-action` creates
[PEP 740](https://peps.python.org/pep-0740/) publish attestations, which
`uv publish` uploads with the distributions to PyPI.

Verify a published wheel or source distribution by passing its PyPI file URL:

```bash
uvx pypi-attestations verify pypi \
  --repository https://github.com/mgaitan/python-package-copier-template \
  https://files.pythonhosted.org/path/to/distribution.whl
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
