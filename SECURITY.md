# Security policy

## Scope

tictactoe-5x5 is a standard-library-only Python terminal game. It makes no
network connections, writes no files while running, and reads only keyboard
input. The realistic attack surface is small: input handling in
`tictactoe5/rules.py` and `tictactoe5/cli.py`, and the development tooling in
this repo (`.githooks/`, `.github/workflows/`, `.claude/`).

## Supported versions

Only the latest commit on `main` is supported.

## Reporting a vulnerability

Please report privately through GitHub: **Security → Report a vulnerability**
on this repository. Don't open a public issue for a security problem.

Include what you found, how to reproduce it, and the impact you expect. This is
a hobby project, so responses are best-effort, but reports are welcome and
will be acknowledged.

## Opening this repo in Claude Code

`.claude/settings.json` ships a permission allowlist and a `PostToolUse` hook
(`.claude/hooks/post-edit-reminders.sh`) from the engsys installer. Review
both before you trust the project in Claude Code, as you would for any repo
you clone.
