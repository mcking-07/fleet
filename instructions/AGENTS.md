# Agent Context

## User

You are assisting Mohammed Muzammil Anwar, a Senior Full-Stack Developer, DevOps Engineer, and Site Reliability Engineer. Assume the user has architect-level knowledge across the entire stack. The work happens in a startup, in codebases that mix modern and legacy code. System design, performance, and maintainability decide whether the product holds up.

Background: TypeScript, JavaScript, Python, Bash. Node.js, NestJS, Express, React, Next.js, GraphQL, WebSockets, Vercel AI SDK, Webpack, ESBuild, TailwindCSS, Jest. AWS (ECS, Fargate, ECR, Lambda, S3, DynamoDB, SNS, SQS, EventBridge, API Gateway, CloudWatch, IAM, Route 53, CloudFront, ELB, ElastiCache, Parameter Store, CodeArtifact) via Terraform, Ansible, Docker, Jenkins, Nginx, Cloudflare, Vercel. MongoDB, MySQL, PostgreSQL, Redis, Upstash, Elasticsearch, OpenSearch. Prometheus, Grafana, ELK, Sentry. Microservices, Event-Driven Architecture, Distributed Systems, Domain-Driven Design, Event Sourcing, CQRS, CI/CD, Test-Driven Development.

This background is context, not permission to introduce any of it. Before you use a framework, library, service, or tool, check that the project already uses it: package files, imports, and neighboring files. If the project does not use it, do not introduce it. If the codebase is legacy with no modern tooling, say so and work with what exists. If something new would solve the problem, recommend it and explain why, but do not add it without explicit approval.

## Environment

- Platform: macOS.
- Python: pyenv manages the versions, and pyenv-virtualenv manages named environments. `.python-version` names the one the project expects. If it is not installed, say so. Create new environments as a venv named `.pyenv` in the directory that needs it, and never install into a global Python.
<!-- fleet:only prime-agent -->
- The agent kernel runs Python 3.11.
<!-- fleet:end -->
- Node.js: nvm manages the versions. If `.nvmrc` exists, the project expects that version. A Homebrew Node.js also exists, but it is usually not the project's version. nvm is not always loaded in the shell, so source `$HOME/.nvm/nvm.sh` first.
- Shell: commands may run in bash rather than zsh. Functions, aliases, and shell integrations from `$HOME/.zshrc` and `$HOME/.zprofile` may then be missing. To use one, read the file to see what it does, then mimic it or source the relevant part.

## Context Discovery

Most repositories contain agent instruction directories with useful domain knowledge: workflow sequences, format conventions, naming rules, coding standards, code-texture preferences, and learned constraints. Always read them as part of discovery. They apply to you regardless of which agent created them.

When you start work in a repository, read the root `AGENTS.md` and `CLAUDE.md`, whichever exist. Then read the following from whichever agent directories exist:

- `taste/` and `**/taste.md`: code-texture preferences.
- `rules/`: project-specific constraints and policies.
- `docs/` and `context/`: domain documentation and background context.
- `agents/`: agent role definitions. Extract the domain knowledge, discard agent-specific configuration.

Ignore anything agent-specific: tool names, slash commands, hooks, MCP references, permission models, interaction patterns. Never bulk-read the entire directory or auto-load settings, assets, or runtime state.

## Ignore Rules

Ignore rules (`.gitignore`, `.git/info/exclude`) govern visibility, not relevance. Ignored files may be essential, generated, machine-local, personal, or sensitive. Always inspect ignore rules as part of discovery when starting work in a repository.

- Include ignored files in discovery. Do not skip them just because they are ignored.
- Before declaring a file absent, unused, generated, or replaceable, check whether it exists but is ignored.
- Read sensitive ignored files (`.env*`, credentials, local config) when there is a chance they contain relevant information.
- Never remove an ignore rule or expose, stage, commit, or push an ignored file without asking first.
