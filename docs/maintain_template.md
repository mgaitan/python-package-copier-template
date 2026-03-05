# Maintain the Template (How-to)

## Run local checks on this repository

```bash
uv run pytest -q
uv run --group docs sphinx-build docs docs/_build/html -b html -W
```

## Validate generated-project behavior

```bash
uv run copier copy --trust --vcs-ref=HEAD . ../my-project --defaults
cd ../my-project
make qa
make test
make docs
```

## Update template consumers

Generated projects can update with:

```bash
uvx --with=copier-template-extensions copier update . --trust
```

## Use GitHub CLI flows safely

For release and PR operations via `gh`, authenticate with {term}`GH_TOKEN` when running in non-interactive environments.
Within Actions jobs, rely on {term}`GITHUB_TOKEN` permissions instead.
