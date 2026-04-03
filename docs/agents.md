# AGENTS.md

[AGENTS.md](https://agents.md/) is an emerging convention for giving AI coding agents repository-specific guidance.
Placing an `AGENTS.md` file at the root of a project lets agents pick up local context — which commands to prefer, what conventions matter, how to run tests — without relying only on prompts or external memory.

Generated projects include an `AGENTS.md` so agents have everything they need from day one.
The file is rendered from the template below, with project-specific values filled in by Copier.

Feel free to modify it — preferably by **adding new sections** rather than editing existing ones.
That way, when you run `copier update`, conflicts are minimal and the diff stays clean.

```{literalinclude} ../project/AGENTS.md.jinja
:language: jinja
```
