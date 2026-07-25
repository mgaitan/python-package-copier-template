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
