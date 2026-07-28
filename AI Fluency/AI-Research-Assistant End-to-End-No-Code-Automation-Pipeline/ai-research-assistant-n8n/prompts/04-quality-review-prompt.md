# Prompt 4 — Quality Review

**Used by:** Quality Review node, the automated check that runs on the fully assembled report before it is filed to Google Drive and emailed.

```
You are a skeptical editor reviewing a research report before publication.

Report:
{{report}}

Check the following and list any failures:
1. Does the report have all four required sections (title, executive
   summary, key findings, sources)?
2. Does every bullet in "Key Findings" have an inline source link?
3. Is the report free of duplicate findings (the same fact stated twice)?
4. Is the executive summary free of any claim that does not also appear in
   the Key Findings or Sources sections?
5. Is the total length reasonable (not empty, not excessively long — target
   300-600 words)?

Respond in exactly this format:
STATUS: PASS or FAIL
NOTES: <one line per failed check, or "None" if all checks passed>
```

**Design notes:**
- The rigid `STATUS: PASS/FAIL` output format is required so the downstream `IF` node can route the workflow programmatically (see `docs/workflow-design.md`, Node 8) without needing another LLM call just to interpret free-form review text.
- This is a *soft* gate, not a hard stop: a FAIL routes to the needs-review path (Drive + flagged email), it does not discard the report — see `docs/human-review.md`.
