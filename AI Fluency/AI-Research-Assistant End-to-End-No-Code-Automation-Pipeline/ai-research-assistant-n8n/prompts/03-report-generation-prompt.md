# Prompt 3 — Report Generation (Executive Summary Only)

**Used by:** An optional sub-step inside the Markdown Generator stage. The report's structural Markdown (headings, bullets, sources list) is generated deterministically by the Code node in `docs/n8n-configuration.md`, **not** by this prompt — this prompt's only job is to produce the one-paragraph executive summary that sits at the top of the report, since that paragraph benefits from LLM synthesis across all sources in a way pure templating cannot provide.

```
You are writing the executive summary paragraph for a research report on:
{{topic}}

Below are {{summaryCount}} individually-summarized sources:
{{summariesJoined}}

Write a single paragraph (3-4 sentences) that identifies the dominant theme
or through-line across these sources. Do not list every source individually
in this paragraph — that happens elsewhere in the report. Do not introduce
any fact that is not present in the summaries above.

Return only the paragraph text.
```

**Design notes:**
- "Do not introduce any fact not present in the summaries above" is the primary hallucination guard for this stage — the executive summary is the part of the report most likely to read as more authoritative than the underlying sources support if left unconstrained.
- Kept separate from Prompt 2 (Summarization) because it operates over the *aggregate* result set, not a single source, and therefore must run after the Merge Results stage, not before it.
