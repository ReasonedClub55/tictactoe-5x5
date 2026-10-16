---
description: One-pass design critique of a proposal, mockup or live screen.
argument-hint: <proposal name, route, file path, screenshot path, URL, or description>
---

Target: $ARGUMENTS

Critique the **design itself** (is the idea sound, does it belong to this product's system and voice) before anyone implements it. Do it inline with the `design critique` lens of the `lenses` skill — no subagent. If the target is a live page, separate "the design is bad" from "the implementation drifted from the design system".

The project's design reference (tokens, component library, brand/voice brief, personas and flows) is wherever `CLAUDE.md` or the project's design docs say; read only what the target needs.

Work through all ten questions: (1) does it serve the actor's job-to-be-done · (2) is the IA/mental model right · (3) is the most important thing the most prominent · (4) clicks/decisions/words to value · (5) every realistic state — empty, partial, loading, error, dense · (6) does it feel like *this product* or generic SaaS chrome · (7) are we showing or asking for data we shouldn't (cross-tenant/PII) · (8) where does this actor get stuck on this kind of screen · (9) better, worse or same vs the closest competitor · (10) does a cold user get the value in under 30 seconds.

Each finding:

```markdown
### <one-line summary>
- **Severity**: S0 fundamental | S1 significant | S2 minor | S3 nitpick
- **Question**: which of the ten
- **Observed** → **Concern** → **Evidence** (persona, rule, heuristic, competitor) → **Recommended change** (specific) → **Redesign effort** S|M|L
```

Be specific ("three equal-weight CTAs — the user can't tell which to click first", not "confusing"); cite evidence, not taste; label speculation about user reaction as a guess; when torn between S1 and S2 pick S1.

Output: a quick inline findings table plus verdict for small scope; for a full surface or if asked, write `docs/critiques/<target-slug>-<YYYY-MM-DD>.md`. Verdict: ✅ sound — proceed · ⚠️ rework on N items (list the S0/S1s) · 🛑 fundamentally broken — redesign first.
