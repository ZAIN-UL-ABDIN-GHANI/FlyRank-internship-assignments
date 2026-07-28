# Prompt 2 — Summarization

**Used by:** LLM Summarizer node (runs once per search result item).

```
You are summarizing one web search result for a research report on: {{topic}}

Source title: {{title}}
Source URL: {{url}}
Source snippet: {{snippet}}

Write a 2-3 sentence summary in your own original words (never copy phrasing
from the snippet). Focus on: what happened or was found, and why it is
relevant to {{topic}}. If the snippet does not contain enough information to
summarize meaningfully, respond with exactly: INSUFFICIENT_CONTENT

Return only the summary text (or INSUFFICIENT_CONTENT), with no preamble.
```

**Design notes:**
- The explicit `INSUFFICIENT_CONTENT` sentinel lets the Merge Results node filter out low-value items programmatically instead of the LLM inventing padding to reach a sentence count.
- "Never copy phrasing" is a copyright and quality control: it forces genuine synthesis rather than a reworded snippet.
- No formatting instructions here — formatting is handled entirely by the Markdown Generator Code node, keeping this prompt's only job "produce good content."
