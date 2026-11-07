---
name: fleet
description: Fleet repo operations - create, edit, adopt, and render the skills, commands, and global instructions shared by every coding agent. Use when creating or changing a skill, command, or global instruction, when a loaded skill resolves into a fleet repo, or when the user mentions fleet or bin/render. Avoid for project code, or for agent runtime config such as settings, sessions, and auth.
metadata:
  agents: ["claude", "codex", "opencode", "pi", "prime-agent"]
  verbatim: true
---

# Fleet

You are a **fleet maintainer** for the skills, commands, and global instructions shared by every coding agent.

fleet is one git repo, with an optional `private/` submodule for private skills and commands. `bin/render` renders each source file per agent, fills in secrets from `.env`, and links the result into each agent's config folder.

Read [references/syntax.md](references/syntax.md) before writing frontmatter, blocks, or placeholders. Read [references/authoring.md](references/authoring.md) before writing a skill or command.

## Finding the Repo

- The repo is usually at `~/.config/fleet`.
- To confirm, resolve the real path of this skill's `references/` folder. The real path is `<fleet>/skills/fleet/references`.
- The repo root is the folder that holds `bin/render`. Run every fleet command from there.

## Source and Output

- Sources: `skills/<name>/`, `commands/<name>.md`, and `instructions/`.
- Private sources: `private/skills/<name>/` and `private/commands/<name>.md`, in the `private/` submodule. A name must be unique across fleet and `private/`.
- Output: `rendered/`. It is generated, read-only, and overwritten on the next render.
- Edit through the repo path, never through an agent's config folder.
- Everything in `rendered/` is a read-only copy. An edit goes live only after `bin/render --apply`.
- Runtime folders (`.pyenv`, `node_modules`, `__pycache__`) link back to the source, so they survive a render.
- Global instructions come from `instructions/AGENTS.md` (context) and `instructions/APPEND_SYSTEM.md` (working rules). Pi and Prime Agent get two files. The other agents get one file with both joined.

## Workflow

1. Create or edit the source.
2. Run `bin/render` and read the dry run.
3. Run `bin/render --diff` when content changed.
4. Run `bin/render --apply` only after the output matches the intent.
5. Check that each target agent's link resolves to the expected file.

After changing `bin/render`, run `bin/test`. Every test must pass.

## Adopting an Existing Skill or Command

A real skill or command in an agent's config folder is not managed by fleet.

1. Ask before moving it.
2. Back it up outside the agent's config folder.
3. Move it into `skills/<name>/` or `commands/<name>.md`, under `private/` for a private one. Add `metadata.agents`.
4. Replace secrets, personal values, and machine paths with placeholders. Add each key to `.env`. Add it to `.env.example` too, or to `private/.env.example` for a private one.
5. When several agents hold a copy, merge them into one source. Keep text that differs per agent in blocks.
6. Run `bin/render`. When the old entry is a link that points outside fleet, apply with `--replace-links`. Otherwise use `--apply`.

## Rules

- Never write a secret into a source file. Use a placeholder, and put the value in `.env`.
- Never print `.env`, or a rendered file that holds secrets. Use `bin/render --diff`, which masks values.
- Never stage `.env`.
- Edits do not authorize commits. Commit only when asked.
- A rendered file edited by hand blocks `--apply`. Move the change into the source. Use `--force` only to discard the hand edit.
- Do not change agents' runtime files: settings, sessions, auth, history.
