# Dogfood

Systematic exploratory testing with repro-first evidence. At session start, read the issue taxonomy that ships with the binary to calibrate severity and coverage: `$(agent-browser skills path dogfood)/references/issue-taxonomy.md`.

## Setup

Launch clean, so no saved login leaks into the test. Use a temporary profile as the operational rules describe.

Only the target URL is required. Session named after the slugified domain, output under `./dogfood-output/`, full-app scope, no auth. Start immediately on a bare URL. Ask only when auth is mentioned but credentials are missing. Never drive through `npx`.

## Workflow

- Setup. Create output dirs, copy `$(agent-browser skills path dogfood)/templates/dogfood-report-template.md` as the report, open a named session, wait for network idle. Log in when needed, then save state.
- Survey. Annotated screenshot plus snapshot. Map the sections to visit.
- Sweep. Work top navigation first, then features, then edge cases: empty states, errors, boundaries, end-to-end create-edit-delete, console on every page. Stop and write each issue the moment it reproduces. Never batch for later.
- Report. Fix severity counts, close the session, report totals plus the worst items.

## Evidence Rules

Interactive issues need video plus step-by-step screenshots: record before reproducing, pace at human speed, screenshot each step, end on an annotated result. Static issues visible on load need one annotated screenshot, no video. Retry once before collecting anything. Five issues with proof beat twenty vague ones. Never delete output mid-session. Never read the app's source. Type with `type` on camera, `fill` off camera.
