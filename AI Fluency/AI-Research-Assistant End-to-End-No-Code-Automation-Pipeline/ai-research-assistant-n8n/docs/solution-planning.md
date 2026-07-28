# Solution Planning: Platform Selection

Three no-code/low-code automation platforms were evaluated for this project: **n8n**, **Make.com**, and **Zapier**. All three can call HTTP APIs, branch logic, and connect to Google Drive/Gmail, so the comparison below focuses on the criteria that actually matter for *this* workflow: multi-step LLM orchestration, per-item looping over search results, cost at moderate volume, and self-hosting/portfolio value.

## Comparison Matrix

| Criterion (weight) | n8n | Make.com | Zapier |
|---|---|---|---|
| Native looping over a list of items (search results → per-item summarization) (×3) | 5 — first-class `Split Out`/`Loop Over Items` nodes, full control of batch size (15) | 4 — Iterator module supports this well (12) | 2 — looping requires Sub-Zaps or Paths workarounds, clunky for this pattern (6) |
| Custom code when a node doesn't fit (JS in Code node) (×2) | 5 — full Code node (JavaScript/Python) (10) | 3 — limited custom function support (6) | 2 — Code steps exist on higher tiers only (4) |
| Self-hosting option (cost control, portfolio/ops value) (×2) | 5 — official Docker image, run entirely on your own infra (10) | 1 — cloud-only (2) | 1 — cloud-only (2) |
| Pricing at moderate run volume (×2) | 5 — free self-hosted, or low-cost cloud tier (10) | 3 — operation-based pricing grows with volume (6) | 2 — task-based pricing is the most expensive at this workflow's node count (4) |
| Credential/security model (OAuth store, env vars) (×1) | 4 (4) | 4 (4) | 4 (4) |
| **Weighted total** | **59** | **34** | **20** |

## Decision

**n8n is selected.** The deciding factors are the native item-looping model (this workflow must run an LLM summarization call once per search result, then re-aggregate — exactly what n8n's `Split Out` → per-item processing → `Aggregate` pattern is built for) and the ability to self-host, which matters both for cost control at scale and for this being a portfolio-grade engineering artifact (an exportable, versionable, Docker-deployable workflow is a stronger deliverable than a platform-locked Zap or Scenario).

Make.com was the closest alternative and would be a reasonable second choice if the team already standardized on it; it was not selected primarily because of cloud-only pricing and weaker custom-code support for the Markdown-assembly step. Zapier was ruled out for this specific workflow shape — its per-item looping model (Sub-Zaps) adds orchestration complexity disproportionate to the task, and its task-based pricing is the least favorable of the three at this workflow's ~8-node, multi-item execution profile.

## Engineering Decision Log

| Decision | Rationale |
|---|---|
| Use n8n over Make.com/Zapier | Native looping, self-hosting, cost, custom code (see matrix above) |
| Use HTTP Request nodes for both the Search API and the LLM calls, rather than a dedicated community node | Keeps the workflow portable across n8n versions and avoids depending on node names/availability that vary by n8n release ("do not invent unsupported nodes") |
| Use `Aggregate` (labeled "Merge Results") rather than `Merge` after per-item summarization | `Merge` combines two *different* input branches; `Aggregate` combines *N items from one branch* back into a single item — the correct semantic for re-joining per-source summaries |
| Generate Markdown in a `Code` node rather than an LLM call | Deterministic formatting (headings, bullet structure) should not depend on an LLM's willingness to follow a template exactly; the LLM's job is content, the Code node's job is structure |
| Add a dedicated "Quality Review" LLM pass before filing | Cheap insurance against an obviously broken or hallucinated report reaching Drive/Gmail; documented fully in `docs/human-review.md` |
