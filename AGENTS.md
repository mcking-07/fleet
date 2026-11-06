# AGENTS.md

This repo is the source of truth for the skills, commands, and global instructions used by the coding agents listed in `README.md`.

## Edit the Source, Never the Output

- Edit files in `skills/`, `commands/`, and `instructions/`, or in `private/skills/` and `private/commands/`.
- `private/` is a submodule. Commit a change there first, then commit the new `private` pointer in fleet. `git push` in fleet pushes both.
- Never edit `rendered/`. It is generated, read-only, and overwritten on the next render.
- Edit through the repo path, never through an agent's config folder.
- Everything in `rendered/` is a read-only copy. An edit goes live only after `bin/render --apply`.
- If an agent's config folder holds a real skill or command that is not in this repo, report it. Do not move it without asking.

## Writing Skills and Commands

Use the fleet skill. It covers frontmatter, blocks, placeholders, rendering, and the writing conventions.

After changing `bin/render`, run `bin/test`. Every test must pass.

## Checks

- Before committing, run `npx markdownlint-cli '**/*.md' --ignore rendered`, `ruff check .`, and `ruff format --check .`.
- The repo's `.markdownlint.json` and `ruff.toml` hold the settings.

## Git

- Write commit messages as one line, lowercase, imperative, with a trailing period. No conventional-commit prefixes, no scopes, no bodies.

## Scope

- Touch only the skills, commands, or instructions the task names.
- Do not change agents' runtime files (`settings.json`, sessions, auth, history).

## Adding an Agent

Update `bin/render`, the README overview, `.env.example`, and the agent IDs in `skills/fleet/references/syntax.md`.
