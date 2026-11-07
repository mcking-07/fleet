# Fleet Syntax

## Agent IDs

`claude`, `codex`, `opencode`, `pi`, `prime-agent`.

## Frontmatter

Skills:

```yaml
---
name: example-skill
description: <What> - <detail>. Use when <triggers>. Avoid for <non-triggers>.
metadata:
  agents: ["claude", "codex", "opencode", "pi", "prime-agent"]
---
```

Commands have no `name`, and may add `argument-hint`:

```yaml
---
description: <What> - <detail>. Use when <triggers>. Avoid for <non-triggers>.
argument-hint: "<pr-url> [notes]"
metadata:
  agents: ["claude", "opencode", "pi", "prime-agent"]
---
```

- Skills: `name`, `description`, `metadata`. Commands: `description`, `argument-hint`, `metadata`. Ask before adding any other key.
- A skill's `name` matches its folder name: lowercase, with hyphens.
- `metadata.agents` lists the agents that get the file, as a flow array. Only fleet reads it; `bin/render` strips it from the output.
- An unknown ID fails the render. An empty list renders the file for no agent.
- An agent without a `FLEET_<AGENT>_DIR` line in `.env` is skipped.
- Codex has no commands. Listing `codex` on a command fails the render.

## Blocks

Wrap text that differs per agent in a block.

| Marker                        | Keeps the text for                          |
| ----------------------------- | ------------------------------------------- |
| `<!-- fleet:only <ids> -->`   | the listed agents                           |
| `<!-- fleet:except <ids> -->` | every agent except the listed ones          |
| `<!-- fleet:else -->`         | the other agents, inside `only` or `except` |
| `<!-- fleet:end -->`          | closes the block                            |

Every agent drops notes:

- `<!-- fleet:note <text> -->` on one line.
- `<!-- fleet:note -->` ... `<!-- fleet:end -->` for several lines.

```md
<!-- fleet:only prime-agent -->
Run it with the host's existing `python3` through `bash()`.
<!-- fleet:else -->
Run it with the host's existing `python3` from the shell.
<!-- fleet:end -->

<!-- fleet:except codex opencode -->
Use this agent's web search tool.
<!-- fleet:end -->
```

- Separate IDs with spaces.
- One block at a time. No nesting.
- At most one `else` per block. No `else` in a note.
- No blocks inside frontmatter.
- Each marker sits alone on its line. A marker inside other text, or any other `<!-- fleet:` line, fails the render.
- Blocks work in markdown files only.
- Markers inside code fences still apply.
- Prefer `except` over listing every other agent, and `else` over a second block with the opposite list.
- Prefer one file with blocks over two copies of a file.

## Placeholders

`bin/render` replaces `{{fleet:env:NAME}}` with the value of `NAME` from `.env`:

```md
| `API_TOKEN` | `{{fleet:env:API_TOKEN}}` |
```

- Works in any text file: markdown, shell, Python. Executable files stay executable.
- `bin/render` rejects binary files in skills.
- A missing key, a malformed placeholder, or a placeholder in frontmatter fails the render.
- `.env` is plain `KEY=value`. Quotes are stripped, and `export` is allowed.
- An empty value renders as empty, without an error.
- `bin/render` does not expand values. `$HOME` stays as written, and the shell expands it when the agent runs the command.
- Add every new key to `.env.example`, with a comment naming the skill and a made-up value. For a private skill or command, use `private/.env.example`.
- Keep non-secret constants shared by everyone, such as board IDs and channel names, in the source.

## Verbatim Skills

`metadata.verbatim: true` turns off blocks and placeholders for a whole skill or command. fleet still strips its `metadata` keys. Every file is copied unchanged. Use it only for a file that documents fleet syntax, like this skill. A placeholder in a verbatim file reaches the agent as literal text.
