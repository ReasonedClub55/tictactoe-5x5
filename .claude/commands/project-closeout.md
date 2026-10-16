---
description: Verify merges, clean up, close the board, record a few lessons.
argument-hint: <project-number>
---

Close out project #$ARGUMENTS. Tracker reads go through the installed issue-tracker skill (`list-issues`, `get-issue`, `query-board`, `close-board`); PR state via `gh`.

1. **Verify merged** — `gh pr view <n> --json state` for every PR in the project; all must be `MERGED` (squash merges make `git branch --merged` lie). Anything still open → stop and report.
2. **Clean up** — only this project's worktrees (`git worktree remove --force`, then `git worktree prune`), merged local branches, and dangling remote branches (`git push origin --delete`). Leave unrelated worktrees. Return the main checkout to `main`.
3. **Close the board** — only if every issue on it is closed (skill `close-board`); otherwise report what blocks it.
4. **Lessons, bounded** — read the `<!-- local-review-findings -->` comments from this project's PRs. Write a lesson in `docs/agent-lessons/` only for a mistake family that recurred in ≥2 PRs and isn't already recorded (strengthen an existing lesson rather than duplicating it). At most three; none is a fine outcome. A lesson that generalizes beyond this project can optionally be PR'd back to the engsys `lessons-library/`.
5. **Report** — PRs merged, cleanup done, board closed or the issues blocking it, lessons added.

Commit lessons on `agent/project-$ARGUMENTS-lessons` as one docs PR. Bodies and messages via `tmp/` files, never heredocs.
