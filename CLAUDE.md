# tictactoe-5x5 — Claude Code working notes

5x5 four-in-a-row tic-tac-toe for the terminal in pure Python, with easy/medium/hard/expert difficulty levels.

Loaded into every session in this repo: keep it tight, link out to `docs/` for depth.

## Usage discipline (lite profile)

This repo is set up for a limited Claude plan. Take the cheapest path that is still correct:

- **Work inline.** Spawn a subagent only for isolated, high-volume work (implementing an issue, a diff-wide security pass). Never run subagents in parallel unless asked. Specialist review = the `lenses` skill, not an agent.
- **Search before reading.** grep/glob first, read only the lines you need. No whole-directory or generated-file reads; don't re-read what is already in context; don't re-run a passing check.
- **Stop on repeat failure.** Same error twice → stop and report what you tried. No retry loops.
- **One review pass**, not a loop. Fix Critical; note the rest.
- **Short outputs.** Don't recap what the diff already shows.
- Suggest `/clear` between unrelated tasks and `/compact` when context gets long.
- Sonnet is the default (`.claude/settings.json`). Use Opus only when I explicitly ask.

## Communication

- Factual tone: "changes applied" / "ready for testing", not "fixed!". Ship ≠ verified until I confirm end-to-end.
- Push back on weak assumptions rather than agreeing politely.
- No PII in logs; never log tokens, cookies, emails, IPs, or auth headers.

## Issue tracking

- **Active tracker: GitHub Issues + Projects.** Agents use the `issue-tracker-github`
  skill for all issue and board operations (create/list/get/update/comment/close issue;
  create/add-to/query board; set board field; link PR).
- PRs and CI stay on GitHub via `gh`. A merged PR closes its work item through the
  `Closes #<n>` convention (one keyword per line).

<!-- naturalize: confirm the repo (<owner>/<repo>) and the GitHub Project number + owner
(user/org) that hold the board, plus the Phase/Priority/Owner field option values. -->

## Git / PR conventions

- **Never** push to `main`; work goes through PRs, opened as **draft** (`gh pr create --draft`). Branches: `agent/<n>-<slug>` (issue) or `agent/project-<n>-phase-<p>-<slug>` (phase).
- Commits: `type(scope): subject (#issue)` — `feat|fix|chore|docs|test|refactor|style|perf|build|ci|revert`. One commit per issue.
- PR closes: **one `Closes #N` per line** (a comma list only closes the first).
- Stacked branches: rebase on `origin/main`, then `git push --force-with-lease`; never `--force`.
- Commit/PR/issue bodies go in files under `tmp/` (Write tool) → `--body-file`/`-F`. **No heredocs.**
- Commit and push only when asked (the `/implement-*` commands count as asking). End commits with the `Co-Authored-By: Claude` trailer.

## Review and issues

- Review locally **before push** with the built-in `/code-review` (see `.claude/skills/code-review/SKILL.md`); `/security-review` for a deeper security pass.
- File issues after investigating root cause: body in `tmp/issue-body-<slug>.md`, create via the issue-tracker skill (`/file-issue`). Typos and one-liners: just fix.
- Tool order: `gh` CLI → `github` MCP (if `gh` fails) → manual. ProjectV2 boards need `gh project` / `gh api graphql`.

## MCP servers

_No MCP servers required by the selected stack._

Project-scoped config lives in [`.mcp.json`](.mcp.json). Approve each server on first startup.

## Slash commands

- `/design-critique` — One-pass design critique of a proposal, mockup or live screen.
- `/file-issue` — Investigate to root cause and file a tracker issue.
- `/generate-project` — Goal → spec, phased plan and tracker issues (one pass; confirms before writing).
- `/implement-issue` — Implement one issue in a worktree → draft PR. Stops before merge.
- `/implement-project` — Do the next phase of a tracker project → one draft PR, then stop.
- `/naturalize` — Fill this project's CLAUDE.md PROJECT-FACTS and replace naturalize placeholders — project facts only, never folder/plumbing setup.
- `/pre-push` — Run the project's full local pre-push gate (build/lint/format/test plus any path-gated checks for migrations, IaC, and containers)
- `/project-closeout` — Verify merges, clean up, close the board, record a few lessons.

A `PostToolUse` hook (`.claude/hooks/post-edit-reminders.sh`, wired in `.claude/settings.json`) nudges after edits to sensitive files.

## Lessons

Project-specific lessons accrue in `docs/agent-lessons/`.

<!--
  ENGSYS:PROJECT-FACTS region.
  The installer (and/or the model during init) fills the block below with project-specific
  facts: stack details, service names, conventions, key paths, north star, etc.
  `engsys update` regenerates everything OUTSIDE this region but NEVER overwrites what's
  between the START and END markers. Hand-edit freely inside it.
-->
<!-- ENGSYS:PROJECT-FACTS:START -->
## Project facts

- **What:** terminal game — 5x5 board, four in a row (horizontal, vertical, diagonal) wins. Human vs. computer with difficulty levels (easy / medium / hard / expert).
- **Runtime:** Python 3.12+, **standard library only** — no third-party runtime deps, no network, no files written at runtime.
- **Run:** `python -m tictactoe5`
- **Test:** `python -m unittest discover -s tests -v` (stdlib `unittest`; tests must also run under pytest if present).
- **Key paths:** `tictactoe5/` (package), `tests/`, `docs/specs/` (spec + plan).
- **Invariants:**
  - Game rules live in one module and are the only source of truth for win/draw detection.
  - AI never returns an illegal move; at every level it takes an immediate win if available, and from medium up it always blocks an immediate loss.
  - The expert move must come back within ~2 s on a typical laptop (iterative deepening with a time budget).
  - Don't claim the expert is "unbeatable": it is a strong search, not a proven solve.
- **Origin:** idea discussed in a Dream Team session (Eon, Joss): a draw against a strong level should feel earned (announce blocked threats/near-wins), and weaker levels should feel like a mind, not a random mover.
<!-- ENGSYS:PROJECT-FACTS:END -->
