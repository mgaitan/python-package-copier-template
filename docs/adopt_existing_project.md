# Adopt the Template in an Existing Project

This guide is for the case where you already have a Python project, but it was not originally generated from `python-package-copier-template`.

The important constraint is this:

- `copier update` only works naturally after a project is already linked to the template through `.copier-answers.yml`.

So the first adoption is not a normal update.
The practical way to do it, especially with code agents, is:

1. render a fresh project from the template using metadata that matches the existing repository,
2. compare that rendered scaffold against the real project,
3. let the agent apply the template pieces incrementally,
4. create and keep `.copier-answers.yml`,
5. from then on, use normal template updates.

## Recommended migration strategy

For non-trivial repositories, do not try to “force” the template onto the project in one destructive pass.
Instead, use a bootstrap PR that introduces the template structure in controlled steps.

That gives you:

- smaller diffs,
- easier review,
- fewer merge conflicts,
- a clear checkpoint after which `copier update` becomes viable.

## Automated workflow with a code agent

The agent-friendly workflow looks like this.

### 1. Work on a dedicated branch

Create a migration branch in the existing project:

```bash
git checkout -b chore/adopt-python-package-copier-template
```

### 2. Render the template into a temporary directory

Render a clean scaffold with metadata that matches the existing project as closely as possible.

Example:

```bash
uvx --with=copier-template-extensions copier copy --trust \
  --data project_name="My Project" \
  --data project_description="My existing Python project" \
  --data author_fullname="Your Name" \
  --data author_email="you@example.com" \
  --data author_username="your-github-user" \
  --data gh_repo_create=skip \
  --data python_package_distribution_name="my-project" \
  --data python_package_import_name="my_project" \
  --data python_package_command_line_name="my-project" \
  --data repository_name="my-project" \
  --data copyright_license="BSD-3-Clause" \
  "gh:mgaitan/python-package-copier-template" \
  /tmp/my-project-template
```

For repeatability, it is usually better to keep those answers in a small YAML file and pass `--data-file` instead of a long command line.

### 3. Ask the agent to reconcile the rendered scaffold with the real repository

The agent should treat `/tmp/my-project-template` as the desired baseline and the existing repository as the target to migrate.

The useful instruction is not “replace my project with the template”.
The useful instruction is:

- preserve project-specific code and behavior,
- adopt template files and conventions where they fit,
- flag conflicts instead of bulldozing them,
- create `.copier-answers.yml`,
- leave the repo in a state where future `copier update` runs are plausible.

Good areas for the first automated pass:

- `pyproject.toml`
- `Makefile`
- `docs/`
- `.github/workflows/`
- `AGENTS.md`
- QA configuration such as Ruff, Ty, pytest, or `prek`

Areas that usually need more care:

- package layout changes
- existing CI/CD conventions
- release automation
- docs IA if the project already has substantial documentation

### 4. Review the migration in slices

A good agent-driven migration PR is easier to review if it is grouped by concern:

- packaging and dependency management
- QA and local developer workflow
- CI/CD
- docs
- agent guidance

If the repository is large, it is often worth doing this as multiple PRs instead of one.

### 5. Commit the template metadata

The project must keep `.copier-answers.yml`.
That file is what connects the repository to the template for future updates.

Without it, you have only copied files from the template; you have not actually adopted the template lifecycle.

### 6. Validate the migrated repository

Before calling the migration done, run the generated lifecycle commands that now matter:

```bash
uv sync
make qa
make test
make docs
```

If your repository already has equivalent commands, keep the ones that make sense, but the point is the same: confirm that the adopted structure is internally consistent.

### 7. Start using normal template updates

Once the project contains `.copier-answers.yml` and the initial migration is merged, future maintenance becomes much simpler:

```bash
uvx python-package-copier-template .
```

Or directly with Copier:

```bash
uvx --with=copier-template-extensions copier update --trust .
```

## What a code agent should optimize for

When you ask an agent to perform this adoption, the brief should emphasize:

- keep the existing project working,
- prefer additive changes before structural rewrites,
- do not delete domain-specific code just because the scaffold does not contain it,
- preserve existing package names and repository identity,
- stage risky refactors separately from template adoption,
- keep `.copier-answers.yml` accurate.

In other words, the agent should treat the template as the target baseline, not as permission to erase project-specific decisions blindly.

## Suggested agent prompt

You can adapt this prompt to your preferred coding agent:

```text
I have an existing Python repository that was not created from python-package-copier-template.

I rendered the template into /tmp/my-project-template using metadata that matches this project.

Your task is to adopt the template into the current repository with minimal disruption:

- compare the current repository against /tmp/my-project-template
- bring over template structure, tooling, docs, workflows, and AGENTS.md where appropriate
- preserve project-specific source code and behavior
- do not overwrite non-template code blindly
- create or preserve .copier-answers.yml so future copier updates are possible
- surface conflicts explicitly instead of guessing
- validate the result with the repository's normal checks

Prefer small, reviewable commits grouped by concern.
```

## When not to automate the whole thing

If the existing repository differs heavily from the template in package layout, release process, or documentation architecture, full automation may cost more than it saves.

In that situation, the best hybrid approach is:

1. use the template render as the reference implementation,
2. let the agent port low-risk files and conventions automatically,
3. keep structural decisions under explicit human review.

That still gives you most of the benefit while avoiding a giant migration PR full of accidental regressions.
