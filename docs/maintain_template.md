# Maintain the Template

This guide separates two different maintenance flows that are easy to mix up:

- maintaining a project generated from the template,
- maintaining the template package itself.

## Maintain a generated project

Inside an existing generated project, update from the latest template:

```bash
uvx --with=copier-template-extensions copier update . --trust
```

If you prefer the package wrapper behavior (copy vs update autodetected), run the `uvx git+...` command from [Getting Started](getting_started.md) in the project directory.

The generated project also includes an optional scheduled workflow (`template-update.yml`) that opens PRs with template refreshes.

## Maintain this repository (the template package)

When editing `python-package-copier-template` itself, use local checks:

```bash
make qa
```

For docs-only work:

```bash
make docs
make docs-open
```

For a full smoke flow against a generated project:

```bash
make smoke
```

That runs Copier from current `HEAD`, then executes QA in the generated project.

## Notes on GitHub authentication

For non-interactive `gh` operations in scripts, use {term}`GH_TOKEN`.
Within GitHub Actions workflows, use {term}`GITHUB_TOKEN` with explicit permissions.
