# About the Documentation

This repository documents both the template itself and the documentation scaffold generated for new projects.
The goal of this page is to explain that baseline so it stays coherent as the template evolves.

## Structure

Generated projects ship documentation as a first-class artifact and follow [Diataxis](https://diataxis.fr/):

| Chapter | Type | Purpose |
|---|---|---|
| `getting_started.md` | Tutorial | Onboarding, first steps |
| `development_workflow.md` | How-to | Common operational tasks |
| `configuration.md` | Reference | Factual lookup, env vars glossary |
| `about_the_docs.md` | Explanation | Rationale and doc conventions |

This template repository adds extra pages around that core set, such as template maintenance, CLI behavior, and adoption notes.
Those pages document the template itself rather than the generated project skeleton.

## Tooling

- **[Sphinx](https://www.sphinx-doc.org/) + [MyST](https://myst-parser.readthedocs.io/)** — docs written in Markdown, built with Sphinx.
- **[sphinx-book-theme](https://sphinx-book-theme.readthedocs.io/)** — the visual theme used by the generated documentation.
- **[richterm](https://github.com/mgaitan/richterm)** — CLI captures generated at build time, not copied by hand.
- **[sphinxcontrib-mermaid](https://github.com/mgaitan/sphinxcontrib-mermaid)** — diagrams defined as code.

Build locally with:

```bash
make docs
make docs-open
```

The build runs in warning-as-error mode, so broken links or directives are caught early.

## Conventions

- **Environment variables** should be defined once in `configuration.md` using the Sphinx `glossary` directive and referenced everywhere else with `` {term}`VAR_NAME` ``.
- **Any behavior or feature change** should update the relevant doc page in the same PR.
- **Generated projects should prefer adding new sections** over rewriting seeded ones, to keep `copier update` diffs clean.

## Publishing

GitHub Actions (defined in `.github/workflows/cd.yml`) deploys docs to GitHub Pages automatically:

- Release or manual dispatch publishes the canonical site.
- PRs that touch `docs/` get a preview deployment under `/_preview/pr-<N>/`.
