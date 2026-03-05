# Getting Started (Tutorial)

This tutorial runs the template end to end from a local checkout.

## 1. Install dependencies

```bash
uv sync
```

## 2. Generate a project from current HEAD

```bash
uv run copier copy --trust --vcs-ref=HEAD . ../my-project --defaults
```

For non-interactive local smoke runs, set {term}`COPIER_TEMPLATE_DEFAULTS`.

## 3. Validate the generated project

```bash
cd ../my-project
make qa
make test
make docs
```

This confirms linting, typing, tests, and docs all run with scaffold defaults.
