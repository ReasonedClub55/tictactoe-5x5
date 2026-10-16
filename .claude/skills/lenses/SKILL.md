---
name: lenses
description: Focused review lenses (architecture/scale, testing, product/UX spec, design critique, quick security, LLM cost) applied inline to a spec, diff or design. Use instead of spawning specialist agents — name the lens, e.g. "apply the testing lens to this spec".
---

# Review lenses

Apply the lens **in this session, to what is already in context** — no subagent, no parallel fan-out. Pick the one to three that fit; skip the rest. Output findings only, each as `[severity] what · why it bites · fix direction`; drop anything you can't tie to a concrete failure. For a deep security pass on a large change, use the `nyx` agent instead of the quick lens below.

## architecture / scale
- **Ask first**: traffic shape (steady/bursty) · where state lives and the read/write ratio · latency targets (p95/p99, cold starts) · blast radius of a failure or primary failover · cost cliffs (egress, compute-seconds, DB IOPS) · coordination points (locks, ordering, idempotency) · hard limits/quotas · observability (metrics, traces, alerts on the right things).
- **Prefer** statelessness, partitioning, isolation; graceful degradation; bounded, idempotent retries. State the trade-off explicitly (latency↔consistency, cost↔complexity).
- **Reject** premature optimization and "rewrite everything" without cause. Close with: do now · defer · never.

## testing
- **Testable?** Acceptance criteria specific and measurable, edge and error cases named. If vague, send it back.
- **Mix**: static analysis as the base · integration tests of real flows carry most of the value · unit tests for pure logic · e2e only for critical journeys.
- **Scenarios**: happy path · sad path (network/API errors, timeouts, 4xx/5xx, rate limits) · boundaries (0, 1, max, max+1, empty, dates/timezones) · every input field (null/missing, empty/whitespace, wrong type, length limits, special chars/unicode, injection payloads, duplicate submit/races) · security boundaries (tenant A↛B, admin-only actions, no PII/tokens in logs and errors) · accessibility for UI (keyboard, screen reader, contrast).
- **Done** = static clean · success and error paths tested · critical journey covered · input validation covered · no flakes (3 green runs). Effort guide: low-risk UI 20–30% of dev time · CRUD/API 30–50% · auth/payments/multi-service 50–80% · security/isolation/migrations 80%+.

## product / UX spec
- **Why first**: is this the right problem, for whom, and what does success look like per persona?
- **Spec** (`docs/specs/<slug>.md`): Goal · user stories · placement/IA · flow from entry to success · states (happy, loading, empty, error, restricted) · acceptance criteria ("user sees X", not "X works") · technical notes · edge cases.
- **Standards**: progressive disclosure · empty states are onboarding · sensible defaults and filtering · fewest steps to value · untrusted content gets an explicit trust boundary · native idiom per platform (web conventions, iOS HIG, Android Material) with capability parity.

## design critique
- **Intent**: what is this for, who uses it, what should they be able to do? If nobody can say, that is the first finding (S0).
- **Cold open**: first ten seconds, no instructions — what does it signify, what would a stranger try first?
- **Walk the primary task**: will they try the right action, notice it, connect it to their goal, see progress? Any "no" is a defect at that step.
- **Sweep** Nielsen's ten heuristics across every state (happy, empty, loading, error, restricted); for data displays, is the message and the comparison clear; accessibility: perceivable, operable, understandable, robust.
- **Report** each as `[S0–S3] principle → the moment it bites → confirmed | guess`. S0 fundamental (rework before building) · S1 significant · S2 minor · S3 nitpick; when torn between S1 and S2, pick S1. Name the problem, not the implementation. No findings on taste alone. End with the top three to fix first.

## security (quick)
- Assets and trust boundaries · authn/authz (can tenant/user A reach B? admin-only actions gated?) · injection and SSRF on every untrusted input · secrets and PII in code, config, logs · over-broad roles or public resources · third-party/dependency exposure.
- Output the 3 most plausible attack paths as short stories with `file:line` or spec section, each with a fix. Anything beyond that → `nyx`.

## LLM cost
- Where do the tokens go? Per call: static prefix vs dynamic tail · output cap · smallest model that passes the eval · prompt caching (stable prefix first) · batch/async for non-interactive work · structured output instead of prose + re-parse · bounded, jittered retries · tool-schema bloat · chatty agent loops (merge steps, early exit, step caps) · rate-limit handling and backpressure.
- Measure before and after; report tokens/latency/cost deltas, not impressions.
