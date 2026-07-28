# Human Review

## What AI Cannot Verify
- Whether a reported deal, breach, or regulatory action is fully confirmed versus preliminary or disputed (several Run 2 and Run 3 items in `docs/testing.md` are still-developing stories).
- Long-term significance or materiality of any single finding — the AI can report that something happened, not whether it will matter in six months.
- Whether a statistic or figure is precisely accurate without checking a primary source (a regulator's own release, a company filing, or a named database).
- Whether two similarly named entities, products, or people have been conflated.

## What Humans Must Check
- That every bullet in the report has a matching, correctly linked entry in the Sources section.
- That the executive summary does not introduce any claim absent from the Key Findings (this is also checked automatically by the Quality Review stage, but a human check is the final backstop).
- Tone and appropriateness for the intended audience, especially for sensitive topics (health, security incidents, market-moving financial news).
- That no confidential or internal-only information was accidentally included if the topic touches on internal business matters.

## Hallucination Risks
- **Invented statistics or quotes** not present in any real search result.
- **Source misattribution** — a claim credited to the wrong publisher or date.
- **Stale content miscategorized as current** — observed directly in Run 1 and Run 4 of `docs/testing.md`, where a 2023 and a 2024 result surfaced despite topic and recency intent.
- **Over-broad synthesis** — the executive summary overstating a "through-line" across sources that don't actually agree with each other.

## Quality Checklist (used at the Quality Review stage and by a human reviewer)
- [ ] All four report sections present (title, executive summary, key findings, sources).
- [ ] Every finding has an inline source link.
- [ ] No duplicate findings.
- [ ] Executive summary claims are all traceable to the findings below it.
- [ ] Report length is within the 300–600 word target.
- [ ] No off-topic or stale (wrong-year) items made it into the final report.
- [ ] Filename and Drive folder match the naming convention in `docs/n8n-configuration.md`.
- [ ] Email notification correctly reflects PASS/FAIL review status.

## Escalation Path
If a report fails the Quality Review stage (`STATUS: FAIL`), it is still filed to Drive (in a `Needs-Review/` subfolder per `docs/workflow-design.md`) and the notification email is prefixed `[NEEDS REVIEW]` rather than being silently sent as if it passed — this ensures the requester is not misled about how much confidence to place in the report before a human has looked at it.
