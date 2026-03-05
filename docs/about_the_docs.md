# About These Docs

The README is the short, practical entrypoint.
This documentation exists to expand that content for people who want to start and maintain projects with this template.

We use [Diataxis](https://diataxis.fr/) to keep intent clear:

- tutorial for first steps,
- how-to guides for repeatable tasks,
- reference for factual lookup,
- explanation for rationale.

That separation matters here because two audiences coexist:

1. users consuming the template (`uvx git+...`, project lifecycle, update flow),
2. contributors evolving this repository itself.

In earlier versions of these docs, that boundary was blurry.
The current structure keeps \"how to use the template\" front and center, and moves local-template development details to dedicated sections.

Environment variables should be defined once in [Configuration](configuration.md) and referenced as glossary terms (for example {term}`GH_TOKEN` and {term}`GITHUB_TOKEN`) in other chapters.
