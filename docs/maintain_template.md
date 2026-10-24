# Maintain the Template

This guide separates two different maintenance flows that are easy to mix up:

- maintaining a project generated from the template,
- maintaining the template package itself.

## Maintain a generated project

Inside an existing generated project, update from the latest template:

```bash
uvx --with=copier-template-extensions copier update . --trust
```

If you prefer the package wrapper behavior (copy vs update autodetected), run `uvx python-package-copier-template .` from the project directory as shown in [Getting Started](getting_started.md).

The generated project also includes an optional scheduled workflow (`template-update.yml`) that opens PRs with template refreshes.

### Customize the security policy

Generated projects receive a `SECURITY.md` with a private reporting contact taken
from `author_fullname` and `author_email`. Review that contact and the supported
versions before publishing the project. By default, only the latest published
release receives security fixes; before the first release, the default branch
is supported.

Customize the policy if your project needs a different support scope or reporting
route. Template updates preserve an existing `SECURITY.md`, including these
customizations. Existing projects receive the policy on their next template update.

### Enable Dependabot on GitHub

New repositories created by the template automatically enable Dependabot alerts,
the dependency graph, and security updates after the initial push. Copies made
with GitHub creation skipped do not change GitHub settings.

Existing projects receive the Dependabot configuration on update, but GitHub
settings change only when explicitly requested:

```bash
uvx python-package-copier-template --configure-dependabot .
```

With Copier directly, answer yes to `gh_dependabot_configure`, or run:

```bash
uvx --with=copier-template-extensions copier update --trust --defaults --data gh_dependabot_configure=true .
```

This opt-in is not saved for subsequent updates. Scheduled template refreshes
therefore leave GitHub settings alone.

To configure GitHub separately or retry a failed setup, run `make dependabot`
inside the generated project or this template repository. This command uses
`gh repo view` to resolve the current repository, as does update setup; you can also pass an explicit
repository to `sh .github/configure-dependabot.sh OWNER/REPO`.
Repeated runs use idempotent `PUT` requests and preserve enabled settings.

Authenticate `gh` with repository admin access. Fine-grained tokens require
repository **Administration: write**; organization policies may restrict these
settings. Setup errors include a retry instruction; automatic creation warns and
continues, while explicit update setup and `make dependabot` fail visibly.
See [GitHub's repository API](https://docs.github.com/en/rest/repos/repos#enable-vulnerability-alerts).

Commit and push `.github/dependabot.yml` to the default branch to activate
scheduled version updates. See [Configuration](configuration.md) for
the schedule and grouping policy.

### Protect main on GitHub

New GitHub repositories created by the template receive `main` protection after
the initial push. Reusing an existing GitHub repository or updating a project
does not change its protection unless explicitly requested:

```bash
uvx python-package-copier-template --configure-main-protection .
```

With Copier directly, answer yes to `gh_main_protection_configure`, or run:

```bash
uvx --with=copier-template-extensions copier update --trust --defaults --data gh_main_protection_configure=true .
```

This choice is not saved, so later and scheduled updates do not reconfigure
GitHub. Skipping GitHub repository creation also skips automatic protection.
After adopting the template in an existing repository, or to retry setup, run:

```bash
make protect-main
```

This target is available in both generated projects and this template repository.
Like update setup, it resolves the current repository with `gh repo view` rather
than saved template metadata. Alternatively, pass an explicit repository to
`sh .github/configure-main-protection.sh OWNER/REPO`.

The command idempotently manages a single branch ruleset, preserving other
protections. See [Configuration](configuration.md) for the policy.
All changes to `main`, including releases, go through a PR: continue using
`make release-pr`, review the version and release notes in the PR, then merge it
to publish to PyPI and create the GitHub release.

Authenticate `gh` with repository admin access; fine-grained tokens need
**Administration: write**. GitHub supports rulesets on public repositories with
Free plans, but private repositories require an eligible paid plan. Organization
policies may impose further restrictions. Automatic setup warns and continues
if protection cannot be configured; explicit updates and `make protect-main`
fail visibly. See [GitHub's rulesets documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
and [rulesets API](https://docs.github.com/en/rest/repos/rules).

### Enable the LLM documentation index

New projects generate `llms.txt` with the HTML documentation. Existing projects
preserve their `docs/**` files during template updates, so adopt this feature
manually if `docs/conf.py` does not already enable it.

Add the documentation dependency:

```bash
uv add --group docs 'sphinx-llms-txt>=0.7.1'
```

Add `"sphinx_llms_txt"` to `extensions` in `docs/conf.py`, then configure:

```python
llms_txt_uri_template = "_sources/{docname}{suffix}{sourcelink_suffix}"
```

Run `make docs` and check `docs/_build/html/llms.txt`. Relative source URLs work
under both the canonical site path and PR previews.

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

## Maintain the demo release flow

Releases of this repository publish to PyPI and then refresh `mgaitan/yet-another-demo` from the newly released template.
That automation depends on the GitHub Actions secret {term}`DEMO_REPO_TOKEN`.

## Notes on GitHub authentication

For non-interactive `gh` operations in scripts, use {term}`GH_TOKEN`.
Within GitHub Actions workflows, use {term}`GITHUB_TOKEN` with explicit permissions.
