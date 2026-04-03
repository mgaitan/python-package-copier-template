# Getting Started

This project is, first and foremost, a [Copier](https://copier.readthedocs.io/) template.
What makes it nicer to consume is that it is also published as a Python package with a tiny wrapper CLI:

```bash
uvx python-package-copier-template [DESTINATION]
```

That wrapper exists so you do not need to remember the `copier copy` and `copier update` incantations every time.
It checks the destination directory:

- If there is no `.copier-answers.yml` or `.copier-answers.yaml`, it creates a project.
- If there is a Copier answers file, it updates the project in place.

You can inspect the published wrapper version with:

```bash
uvx python-package-copier-template --version
```

If you want to use the latest development version from GitHub instead of the latest published release:

```bash
uvx git+https://github.com/mgaitan/python-package-copier-template [DESTINATION]
```

And to inspect that development wrapper version:

```bash
uvx git+https://github.com/mgaitan/python-package-copier-template -- --version
```

## Create a new project with the wrapper

The most convenient path is:

```bash
uvx python-package-copier-template /path/to/your/new/project
```

That will run Copier in copy mode with sensible defaults and prompt you for the remaining project metadata.

The capture below shows a real wrapper-driven project creation during the docs build.
Under the hood it runs non-interactively with defaults in a temporary directory, while displaying the normal command a user would type:

```{richterm} sh -lc 'tmp="$(mktemp -d)"; COPIER_TEMPLATE_DEFAULTS=1 uv run python-package-copier-template "$tmp/demo-project"'
:shown-command: uvx python-package-copier-template /path/to/your/new/project
```

After generation:

```bash
cd /path/to/your/new/project
uv sync
make qa
make test
make docs
```

That gives you a ready-to-work baseline with dependencies, QA, tests, and documentation.
Use `make docs-open` if you want to open the generated HTML locally.

## Update an existing project with the wrapper

For a project already created from this template, run the same wrapper from inside the repository:

```bash
cd /path/to/existing/project
uvx python-package-copier-template .
```

Because the project contains `.copier-answers.yml`, the wrapper switches to update mode automatically.
The update process uses Copier metadata from that file to track the source template and the version previously applied.

Generated projects also include a scheduled `template-update.yml` workflow that can open a PR with template refreshes.
That is useful for gradual adoption, but the local wrapper command is still the primary manual update path.

## Use Copier directly

If you prefer to avoid the wrapper, the equivalent explicit commands are:

Create a new project:

```bash
uvx --with=copier-template-extensions copier copy --trust "gh:mgaitan/python-package-copier-template" /path/to/your/new/project
```

Update an existing project:

```bash
cd /path/to/existing/project
uvx --with=copier-template-extensions copier update --trust .
```

This repository uses a couple of Jinja extensions, so `copier-template-extensions` must be available when you run Copier directly.
The wrapper handles that for you, which is the main reason it exists.

## Work against the local repository

If you are developing the template itself and want to test the current checkout instead of a published release:

```bash
uv sync
uv run copier copy --trust --vcs-ref=HEAD . /path/to/your/test/project
```

That uses the local repository as the template source and resolves updates against the current `HEAD`.

## GitHub and publishing notes

If you choose GitHub repository creation during the questionnaire and have `gh` available, the template can bootstrap the repository for you.
For public repositories, it also tries to enable GitHub Pages so the generated docs workflow can publish without extra manual setup.

For PyPI publishing in generated projects, the release workflow is based on [Trusted Publishing](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
That still requires one manual registration step in PyPI for the project and workflow identity.
