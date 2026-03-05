# Getting Started

This tutorial is for someone who wants to start a new Python project using this template package.
The default entrypoint is the package CLI wrapper, not a local clone.

Run:

```bash
uvx git+https://github.com/mgaitan/python-package-copier-template [DESTINATION]
```

If `DESTINATION` does not contain a Copier answers file, it creates a new project.
If `DESTINATION` already has `.copier-answers.yml` (or `.yaml`), the same command performs an update.

To check which wrapper version you are using:

```bash
uvx git+https://github.com/mgaitan/python-package-copier-template -- --version
```

After project generation, move into the new directory and run the standard lifecycle:

```bash
uv sync
make qa
make test
make docs
```

That gives you a fully working baseline with dependencies, QA, tests, and documentation.
