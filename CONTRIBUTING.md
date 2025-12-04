# Contributing

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

## Environment setup

Install [uv](https://github.com/astral-sh/uv) following the
[official instructions](https://docs.astral.sh/uv/getting-started/installation/).
Copier does not need to be installed globally; we'll run it through uv.

Then clone the repository and install the local environment:

```bash
git clone https://github.com/mgaitan/python-package-copier-template
cd python-package-copier-template
uv sync
```

## Running tests

To run the tests, first generate a sample project locally and then run its test suite:

```bash
uv run copier copy --trust --vcs-ref=HEAD . /tmp/template-test --defaults
cd /tmp/template-test
uv run --group lint ruff check
uv run --group test pytest
uv run --group qa ty check
uv build
make docs
```

## Serving docs

Documentation for this template is served by building the sample project's docs
with `make docs` as shown above.
