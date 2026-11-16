# fleet

One source for the skills, commands, and global instructions of every coding agent you use.

## Overview

Every coding agent keeps its own skills, commands, and instruction files. Kept by hand, the copies drift: a fix lands in one agent and not the others, and secrets end up pasted into each one.

fleet keeps one source for all of them. `bin/render` renders each file per agent, fills in secrets from a local `.env`, and links the result into each agent's config folder. Edit once, render, and every agent picks up the change.

It supports Claude Code (`claude`), Codex (`codex`), OpenCode (`opencode`), Pi (`pi`), and Prime Agent (`prime-agent`).

> [!NOTE]
> Text that differs per agent sits between fleet markers, which are HTML comments. GitHub's Preview hides the markers. To see which text goes to which agent, switch the file to Code view.

## Setup

1. Clone this repo to `~/.config/fleet`.
2. Copy `.env.example` to `.env` and run `chmod 600 .env`.
3. In `.env`, keep a `FLEET_<AGENT>_DIR` line for each agent you use, pointing at its config folder. `$HOME` works here. Remove the lines for agents you do not use.
4. With access to the private skills, set up `private/`. Then add the keys from `private/.env.example` to `.env`. Without access, skip this step.

   ```sh
   git submodule update --init
   git config --local submodule.recurse true
   ```

5. Fill in the values for the skills you use. `.env` holds secrets and machine paths, and the sources hold placeholders, so `.env` never goes in git.
6. Run `bin/render` to see what will change, then `bin/render --apply --replace-links`.

`bin/render` needs only `python3`.

## Usage

```sh
bin/render           # dry run: show what would change
bin/render --diff    # show content changes, with secrets masked
bin/render --apply   # write rendered files and links
```

To write or change a skill, command, or instruction, use the fleet skill in [`skills/fleet/`](./skills/fleet/SKILL.md). Every agent fleet manages loads it.

Good to know:

- Rendered files are read-only. A rendered file edited by hand blocks `--apply`. Move the change into the source, or overwrite it with `--force`.
- `bin/render` only manages links that point into fleet. A real file, or a link that points elsewhere, is reported as a conflict. `--replace-links` takes over such links.
- Removing a skill, disabling an agent, or moving an agent's folder removes the old links on the next `--apply`.
- `private/` holds the maintainer's private skills and commands, as a submodule with the same `skills/` and `commands/` layout as fleet. Without access, it stays empty, and fleet works without it.
- To change a private skill or command, commit in `private/`, then commit the new `private` pointer in fleet. `git push` in fleet pushes both.
- Before your first private change, run `git -C private switch main` and `git config --local push.recurseSubmodules on-demand` once.
- Codex has no commands. Invoke the skill instead, for example `$example-skill`.

## For Agents

Read [`AGENTS.md`](./AGENTS.md) before editing this repo, and use the fleet skill to write skills, commands, and instructions.

## Contributing

Before opening a pull request, run `bin/test`, `npx markdownlint-cli '**/*.md' --ignore rendered`, `ruff check .`, and `ruff format --check .`.

## License

[MIT](./LICENSE)
