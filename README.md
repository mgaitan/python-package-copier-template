# Modern Python package template

[![Copier](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/copier-org/copier/master/img/badge/badge-grayscale-inverted-border-purple.json)](https://github.com/copier-org/copier)
[![CI](https://github.com/mgaitan/python-package-copier-template/actions/workflows/ci.yml/badge.svg)](https://github.com/mgaitan/python-package-copier-template/actions/workflows/ci.yml)


A [Copier](https://github.com/copier-org/copier) template
for modern Python projects. 

Demo repo generated from this template: [mgaitan/yet-another-demo](https://github.com/mgaitan/yet-another-demo)

## Features

- 🐍 Modern Python package (3.12+)
- 📦 Build and dependency management with [uv](https://docs.astral.sh/uv/), split by groups (dev/qa/docs)
- 🧹 Linting and formatting via [Ruff](https://docs.astral.sh/ruff/) with a broad set of rules enabled
- ✅ Type checking via [ty](https://github.com/astral-sh/ty)
- 🧪 Tests with [pytest](https://docs.pytest.org/en/stable/), [coverage.py](https://coverage.readthedocs.io/en/latest/) and extensions
- 📚 Docs with [Sphinx](https://www.sphinx-doc.org/en/master/), [MyST](https://myst-parser.readthedocs.io/en/stable/) and a few extensions, deployed to [GitHub Pages](https://pages.github.com/)
- 🏗️ Use of [GitHub CLI](https://cli.github.com/) for autotic project creation 
- ⚙️ CI workflow on [GitHub Actions](https://github.com/features/actions)
- 🚀 Automated releases to PyPI via [Trusted Publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/)
- 🧠 Sensible defaults via introspection to minimize answers during the initial setup
- 🛠️ Makefile with shortcuts for common tasks
- 📄 Generation of generic docs such as `LICENSE`, `CODE_OF_CONDUCT`, etc.
- 🤖 Heavily curated [AGENTS.md](https://agents.md/)
- 🌀 Initial setup of the development environment and git repo
- ♻️ Projects updatable with [`copier update`](https://copier.readthedocs.io/en/stable/updating/)

Please read [my blog post](https://mgaitan.github.io/en/posts/opinionated-python-project-scaffolding/) to learn about the details of the decisions I made and the alternatives I considered.

## Quick setup and usage

Start a new project with this template:

```bash
uvx --with=copier-template-extensions copier copy --trust "gh:mgaitan/python-package-copier-template" /path/to/your/new/project
```

To upgrade an existing project created from this template to the latest version, run:

```bash
uvx copier update .
```

This will fetch the latest template version and guide you through updating your project, preserving your customizations whenever possible.

To test a development version of the template, clone the repository and run:

```bash
uv sync
uv run copier copy --trust  --vcs-ref=HEAD . /path/to/your/test/project
```

If you create the GitHub repository via the `gh` CLI prompt, the template will attempt to enable GitHub Pages (using the Actions build type) so documentation deployments succeed. If Pages is unavailable (for example, with some private repositories or account policies), the docs workflow will keep failing until Pages is allowed.


To publish a release of your project to PyPI, you need to [register the project with trusted published](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).  Read more about how this workflow works [here](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

Then

```
$ make bump    # optional
$ make release
```


### Acknowledgement

This project template started as a fork of [pawamoy/copier-uv](https://github.com/pawamoy/copier-uv). Then I simplified and changed it to fit my needs.
