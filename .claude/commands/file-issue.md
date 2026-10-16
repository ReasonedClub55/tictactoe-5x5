---
description: Investigate to root cause and file a tracker issue.
argument-hint: <brief description of the issue>
---

Issue context: $ARGUMENTS

Investigate inline; hand off to the **bert** subagent only if the trace spans many files. Issue writes go through the installed issue-tracker skill's `create-issue`.

1. **Find the real root cause** — search, read the actual code, cite `file:line`. No band-aids. A typo or one-liner: just fix it, don't file.
2. **Write the body** to `tmp/issue-body-<slug>.md` with the Write tool (no heredocs): Summary · Root cause (or motivation) · Affected files · Recommended fix (the correct one) · Acceptance criteria · Dependencies · Effort S/M/L.
3. **Title** with the type emoji: 🐛 Bug · ✨ Feature · 💄 Enhancement · 📄 Content · 🏗️ Infra. **Labels**: one type plus one area.
4. **Create** via `create-issue` (GitHub: `gh issue create --body-file …`). Report number, URL, a two-line RCA, and labels.

Unsure whether to file or fix? Ask.
