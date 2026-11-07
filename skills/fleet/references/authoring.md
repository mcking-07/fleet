# Writing Skills and Commands

## Descriptions

- Format: `<What> - <detail>. Use when <triggers>. Avoid for <non-triggers>.`
- Name the triggers a user would say: product names, URLs, verbs.
- Name the nearest neighbouring skill under "Avoid for", so the agent picks the right one.

## Body

- Open with one line: `You are a **<role>** for <scope>.` It is the only bold text in the file.
- Keep `SKILL.md` short. Move long procedures, tables, and templates into `references/`, and link each one with when to read it.
- Headings use title case, including words after a hyphen, a colon, or in parentheses: `Pre-Flight Checks`.
- Use bullets by default. Use numbers only for steps that change external state, or that are referenced by number.
- One idea per sentence. Condition before the instruction: "When X, do Y."
- No em dashes in prose. No capitals for emphasis.
- Do not name a specific person, or write "his" or "your". "The user" is fine.
- Do not list tool flags or versions the agent already knows.
- When agents need different runtime text, keep each agent's text unchanged inside a block. Share only text that is the same for every agent.
- Check wording with the `unslop` pattern catalog, and structure with the `authoring` discipline.

## Commands

- Use `$ARGUMENTS`. Do not use `$1`, `$2`, or `${@:N}`. Claude reads `$1` as the second argument, and OpenCode does not expand `${@:N}`.
- Describe the arguments by what they look like, not by position. When a skill defines argument rules, point to them.
- Keep a command thin: name the skill to load and the workflow to run.
