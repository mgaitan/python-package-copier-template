# Design Decisions (Explanation)

This chapter captures the template's opinionated defaults and why they exist.

## Tooling baseline

- `uv` is the package/dependency workflow to reduce setup variance.
- QA defaults are strict enough for early signal: Ruff, Ty, pytest, and docs warnings-as-errors.
- Docs and release automation are first-class repository concerns.

## Scaffolding strategy

- Generate a complete but minimal project skeleton.
- Keep opinionated defaults explicit and editable in template files.
- Support updateability via Copier while preserving local project customization.

## Governance decisions

- Prefer automation over manual checklist steps for CI/CD.
- Keep generated docs immediately useful for users and contributors.
- Treat documentation architecture as part of project architecture.
