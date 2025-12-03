# Modern Python package template

A [Copier](https://github.com/copier-org/copier) template
for modern Python projects. 

## Features

- [uv](https://github.com/astral-sh/uv) setup, with pre-defined `pyproject.toml`.
- Pre-configured tools for code formatting, quality analysis and testing (including [ty](https://github.com/astral-sh/ty) via `uv run ty check`).
- GitHub Actions for publishing to PyPI using [pypa/gh-action-pypi-publish](https://github.com/pypa/gh-action-pypi-publish).
- Tests run with [pytest](https://github.com/pytest-dev/pytest) and plugins, with [coverage](https://github.com/nedbat/coveragepy) support
- Documentation built with [sphinx](https://github.com/sphinx-doc/sphinx) and [myst-parser](https://github.com/executablebooks/myst-parser)
- Support for GitHub workflows.
- Choice the license (BSD-3-Clause, MIT, Apache-2.0).

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


To publish a release of your project to PyPI, you need to [configure trusted published](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)

Then

```
$ make bump    # optional
$ make release
```


### Acknowledgement

This project template started as a fork of [pawamoy/copier-uv](https://github.com/pawamoy/copier-uv). Then I simplified and changed it to fit my needs.
