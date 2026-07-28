# Prompt 1 — Research (Search Query Construction)

**Used by:** HTTP Request (Search API) node, to turn a plain topic into an effective search query.
**Note:** For the Tavily/SerpAPI calls, the raw topic is normally sent as-is since both APIs handle natural-language queries well. This prompt is used only when a *query-refinement* step is enabled (see `docs/future-improvements.md`) — for example, to expand a vague topic into 2–3 more specific search angles before calling the Search API.

```
You are a research query planner. Given a single topic, produce 2-3 distinct,
specific web-search queries that together would surface the most current and
significant developments on this topic. Each query should target a different
angle (e.g., recent news, major players/companies, data or statistics).

Topic: {{topic}}

Return only a JSON array of 2-3 short query strings, nothing else. Example:
["topic latest news", "topic market statistics 2026", "topic key companies"]
```

**Design notes:**
- Constrained to return *only* a JSON array so the output can be parsed directly by a downstream Code node without extra cleanup.
- Deliberately narrow (2–3 queries) to control Search API cost and per-run latency.
