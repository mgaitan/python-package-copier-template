# Configuration

```{glossary}
COPIER_TEMPLATE_DEFAULTS
  Environment variable consumed by the package CLI wrapper.
  When set to `1`, `python-package-copier-template` runs copy mode with defaults.

GH_TOKEN
  Token used by the GitHub CLI (`gh`) for authenticated operations in scripts or CI.
  Prefer this for non-interactive `gh` usage.

GITHUB_TOKEN
  Ephemeral token automatically provided by GitHub Actions.
  Its effective permissions are controlled by workflow/job `permissions` blocks.

UV_MALWARE_CHECK
  Enables uv's preview lockfile scan against malicious-package advisories from OSV.
  Make targets and GitHub Actions set it to `1`, causing syncs to stop when a locked dependency matches a known malware advisory.

DEMO_REPO_TOKEN
  Repository secret used by this template repository's release workflow to push updates to the demo repository `mgaitan/yet-another-demo`.
  Use a fine-grained token with `Contents: Read and write` on that repository.
```

## Template Choices

`copyright_license` controls generated package license metadata, the `LICENSE`
file, and license badges. Public repositories default to `BSD-3-Clause`;
explicitly private repositories default to `none`, which omits license metadata
and does not generate a `LICENSE` file. Local copies that skip GitHub repository
creation keep the licensed `BSD-3-Clause` default.

`gh_dependabot_configure` enables Dependabot alerts, the dependency graph, and
security updates through `gh` during a template update. It defaults to `false`
and is excluded from the answers file so each update requires a fresh opt-in.
New repositories created through `gh_repo_create` receive this setup automatically.

`gh_main_protection_configure` opts an existing GitHub repository into the
managed `main` ruleset. It defaults to `false` and is not saved in the answers
file. Newly created GitHub repositories are protected automatically after the
initial push; reusing an existing remote requires this opt-in.
See [Maintain the Template](maintain_template.md) for setup commands.

## Main protection

The `python-package-template-main` branch ruleset requires pull requests into
`main`, including for administrators, blocks force pushes and deletion, and
requires review conversations to be resolved. No approving review is required,
so solo-maintained projects can merge their own PRs, including release PRs.
No status-check names are required by this baseline: CI jobs are conditional,
and existing required checks and stricter rules remain effective.

The setup creates this named ruleset once and updates it on subsequent runs.
It manages only this ruleset; other rulesets and classic branch protection are
left untouched and apply alongside it. Manual changes to the managed ruleset
are reset to the template baseline when setup is explicitly rerun.
It does not restrict tags or `release/*` branches or grant release bypasses.

## Dependabot

Both this repository and generated projects include `.github/dependabot.yml`.
Version checks run every Monday for `uv` and GitHub Actions. No fixed `time` is
configured, so GitHub assigns a random time instead of scheduling every generated
repository at the same hour.
The `uv` entry covers `pyproject.toml` and `uv.lock`, including runtime dependencies,
the build backend, and all declared dependency groups (`dev`, `docs`, `lint`, and
`qa`). The Actions entry covers references in `.github/workflows/`.

Minor and patch updates are grouped per ecosystem; major updates get individual
PRs. Security updates have separate groups and run when vulnerabilities are
identified, independently of the weekly version-update schedule. No target branch
is pinned: Dependabot uses each repository's default branch.
See the [GitHub Dependabot reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference).

## Locked dependencies

CI checks `uv.lock` with `uv lock --check` before dependency-backed jobs.
Project commands run with `uv run --locked`, so stale or missing lockfiles fail
instead of being silently refreshed on a runner. The isolated wheel smoke test
uses `--no-project` and intentionally does not use the project's lockfile.

After changing dependency declarations, run `uv lock` (or `uv sync`) locally and
commit the updated `uv.lock` alongside `pyproject.toml`. The generated template
update workflow regenerates the lockfile after Copier updates and includes it
in the update PR. Fresh generated smoke projects initialize their dependencies
once before running locked checks.
