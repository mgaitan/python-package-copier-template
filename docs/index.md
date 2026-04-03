# python-package-copier-template

This documentation covers how to use, maintain, and evolve `python-package-copier-template`.
The project is a [Copier](https://copier.readthedocs.io/) template packaged as a small Python CLI wrapper, so the most common entrypoint is:

```bash
uvx python-package-copier-template [DESTINATION]
```

That wrapper decides whether to run `copier copy` or `copier update` by inspecting the destination directory for a Copier answers file.
If you prefer the raw Copier commands, or want the latest development version from GitHub, the details are in [Getting Started](getting_started.md).

## What this template includes

- A modern Python package baseline targeting Python 3.12+.
- Dependency and environment management with [uv](https://docs.astral.sh/uv/).
- QA defaults built around [Ruff](https://docs.astral.sh/ruff/), [ty](https://github.com/astral-sh/ty), and [pytest](https://docs.pytest.org/).
- Sphinx documentation written in Markdown with [MyST](https://myst-parser.readthedocs.io/).
- GitHub Actions workflows for CI, docs publishing, template refreshes, and PyPI releases.
- Optional GitHub repository bootstrapping with [GitHub CLI](https://cli.github.com/).
- Generated projects that remain updatable with [`copier update`](https://copier.readthedocs.io/en/stable/updating/).

The broader rationale for these choices is described in the original blog post:
[My opinionated scaffolding for modern Python projects](https://mgaitan.github.io/en/posts/opinionated-python-project-scaffolding/).

```{toctree}
:maxdepth: 2

getting_started.md
maintain_template.md
configuration.md
design_decisions.md
about_the_docs.md
```
