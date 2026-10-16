---
description: Goal → spec, phased plan and tracker issues (one pass; confirms before writing).
argument-hint: <goal description, plus any attachment paths or links> [--deep]
---

Goal: $ARGUMENTS

Do all of it **in this session, inline**. Tracker writes use the installed issue-tracker skill's operations (`create-issue`, `create-board`, `add-to-board`, `set-board-field`, `query-board`). No subagents unless `--deep`.

1. **Explore before asking** — `CLAUDE.md`, `docs/architecture/`, existing specs, the related code, open issues/projects; grep `docs/agent-lessons/` for the topic rather than reading it. Don't ask what the repo already answers.
2. **Ask once** — one batch of at most five questions, each unlocking a decision. Skip if there are none.
3. **Draft the spec** at `docs/specs/<slug>.md`: Goal · users and stories · flow and states (happy, loading, empty, error, restricted) · testable acceptance criteria · technical approach · data/API contracts · edge cases · risks.
4. **Lens pass (inline)** — apply the `lenses` skill: architecture/scale, security (quick), testing, plus product/UX if it is user-facing. Fold the fixes into the spec and list real findings under "Risks & decisions". If a finding changes product scope, stop and ask me.
5. **Plan, then confirm** — propose phases and issues as a table: phase · issue · size S/M/L · depends on · one-line acceptance criteria. One phase = one implementation PR; one issue = one commit; order contracts → schema → logic + tests → wiring → UI/e2e. **Wait for my OK before touching the tracker.**
6. **Create** (after OK) — a board with fields `Phase` (`P0: name`, `P1: …`), `Priority` (P0–P3) and `Owner`; issues from `tmp/issue-body-<slug>.md` files (no heredocs), each with acceptance criteria, dependencies, size, and labels (type + area). Then `query-board` and verify **no item has an empty Phase** — [/implement-project](implement-project.md) can't run without it. On GitHub, boards need `gh project` / `gh api graphql` (the GitHub MCP can't do ProjectV2); the tracker skill carries the details.
7. **Report** — spec path, board URL, issues by phase, decisions/risks that need me. Stop. Implementation starts only when I run `/implement-project`.

`--deep` adds two subagent passes on top: **nyx** over the spec's security surface, and one fresh general-purpose reviewer who reads only the spec and issues (no session context) for gaps and contradictions. Reserve it for auth, payments, or multi-tenant work.
