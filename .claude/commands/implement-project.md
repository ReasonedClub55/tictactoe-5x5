---
description: Do the next phase of a tracker project → one draft PR, then stop.
argument-hint: <project-number> [--review]
---

Use the **isabelle** subagent (Sonnet), following [/implement-issue](implement-issue.md) for each issue. Board reads/writes (`query-board`, `set-board-field`) go through the installed **issue-tracker skill**; PRs and CI stay on `gh`.

Project: $ARGUMENTS   (`--review` = also run the independent review below)

**One phase per run.** Cheap, predictable, and you merge between phases.

1. **Read the board** (`query-board`). It needs a `Phase` field with `P<n>: <name>` options — if missing, stop and tell me to run [/generate-project](generate-project.md). Never invent phases or work an item with an empty Phase.
2. **Pick the next phase** — lowest-numbered with open issues. Print the phase name and its issues. No approval needed; running this command is the authorization.
3. **Do the phase** — one phase = one branch `agent/project-<N>-phase-<n>-<slug>` = one worktree = one draft PR. Set Status=In Progress (`set-board-field`). Per issue: implement-issue steps 1–4, one commit each citing `(#num)`. After the last commit: **one** `/code-review` pass over the phase diff (lowest effort level if it takes one), push once, open the draft PR with one `Closes #num` per line, post the findings comment (`<!-- local-review-findings -->`).
4. **Independent review — opt-in.** Only when `--review` is passed or the phase is `risk: high`:
   - **Worker layer installed** (`.claude/scripts/providers.json`)? Send the review to a non-Anthropic worker — it runs on that provider's quota, not yours; follow `.claude/workflows/worker-dispatch.md` § objective review.
   - **Otherwise** one fresh **Sonnet** reviewer subagent with none of the implementation context: re-run the gate from scratch, check each issue's acceptance criteria against the diff, hunt regressions, dead or duplicate code, dropped work. It ends with `VERDICT: CLEAN` or `VERDICT: FINDINGS` (severity-tagged, `file:line`).
   - FINDINGS → back to Isabelle once; still failing → stop and report.
5. **Stop and report** — PR link, findings, review verdict (if run), and the command to continue: `/implement-project $ARGUMENTS` after I merge.

Hard rules:

- Never merge, never mark ready, never push to `main` — the human does.
- Status=Done **only after the phase PR has merged**: the board's built-in "Auto-close issue" workflow closes the linked issue the moment Status=Done, even for an unmerged draft.
- Stop and ask on: a review that errored, the same failure twice, or anything that needs a product or architecture decision.
- Commit/PR bodies via `tmp/` files, never heredocs.

When the last phase's PR has merged, suggest [/project-closeout $ARGUMENTS](project-closeout.md) — don't run it unprompted.
