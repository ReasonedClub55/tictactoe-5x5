---
description: Implement one issue in a worktree → draft PR. Stops before merge.
argument-hint: <issue-number>
---

Use the **isabelle** subagent (Sonnet — don't escalate the model unless I ask). Issue reads/writes go through the installed **issue-tracker skill** (`.claude/skills/issue-tracker-*/`); PRs and CI stay on `gh`.

Issue: #$ARGUMENTS

1. **Read + claim** — skill `get-issue`, then `update-issue` (assign to self). Acceptance criteria missing or vague, or the issue is clearly bigger than it claims → stop and ask; don't guess.
2. **Worktree** — branch and worktree in one command, from a fresh `origin/main`:

   ```bash
   git fetch origin
   git worktree add ../worktrees/issue-$ARGUMENTS-<slug> -b agent/$ARGUMENTS-<slug> origin/main
   cd ../worktrees/issue-$ARGUMENTS-<slug>
   cp ../../.env .env 2>/dev/null || cp .env.example .env 2>/dev/null || true
   ```

   Install deps and run codegen per `CLAUDE.md`. Run every command from inside the worktree.
3. **Implement** — grep before reading; match existing patterns; one commit `type(scope): subject (#$ARGUMENTS)` (message from a `tmp/` file, no heredocs).
4. **Gate** — the project's pre-push checks ([/pre-push](pre-push.md)), cheapest first. The same check failing twice → stop and report; don't loop.
5. **Review once** — run the built-in `/code-review` against `origin/main` (lowest effort level if it takes one), a single pass. Fix Critical findings and one-line Warnings; list the rest in the PR comment. Re-run only if you fixed a Critical.
6. **Push + draft PR** — `git push -u origin agent/$ARGUMENTS-<slug>`, then `gh pr create --draft --base main --body-file tmp/pr-body-$ARGUMENTS.md` with `Closes #$ARGUMENTS` (see `link-pr` in the tracker skill). Post the review findings (or "0 findings") as one comment starting `<!-- local-review-findings -->`.
7. **Stop.** Report: PR URL, three-line summary, checks run, open findings. Don't mark ready and don't merge — I do. After it merges: `git worktree remove ../worktrees/issue-$ARGUMENTS-<slug> --force && git branch -D agent/$ARGUMENTS-<slug> && git worktree prune`.

Conventions: `CLAUDE.md`. Only if the work exposed a reusable gotcha, add one bullet to `docs/agent-lessons/`.
