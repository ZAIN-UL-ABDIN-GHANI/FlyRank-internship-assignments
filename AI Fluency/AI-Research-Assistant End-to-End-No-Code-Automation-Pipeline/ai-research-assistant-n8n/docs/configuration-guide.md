# Configuration Guide

This guide covers **tuning** the workflow after installation (see `docs/installation-guide.md` for first-time setup). All settings below map directly to the environment variables and node parameters documented in `docs/n8n-configuration.md`.

## Adjusting Search Breadth
- `MAX_SEARCH_RESULTS` (default `8`) controls how many sources are gathered per run. Lower it (e.g., `5`) to reduce LLM Summarizer cost and runtime; raise it (e.g., `12`) for broader coverage on high-volume topics (see Run 2, Cybersecurity, in `docs/testing.md`, where a higher result count helped surface more distinct stories before triage).

## Switching Search Providers
- Set `SEARCH_API_PROVIDER` to `tavily` or `serpapi`. If switching to SerpAPI:
  1. Create a `SerpAPI` credential (Generic Header Auth or Query Auth, per SerpAPI's documented auth method).
  2. Update the Search API HTTP Request node's URL to SerpAPI's endpoint and adjust the request body/query parameters to SerpAPI's schema (different field names than Tavily — see `docs/api-setup-guide.md`).
  3. No other node needs to change; downstream nodes only depend on the normalized `{title, url, snippet}` shape, which a small Code node ("Normalize Results") maps both providers into.

## Switching LLM Providers
- Set `LLM_MODEL` to your provider's current model identifier (see `docs/api-setup-guide.md` for how to find the current one — do not hard-code a specific model string long-term, since providers update these).
- If switching from Anthropic to OpenAI (or vice versa), update the HTTP Request URL (`api.anthropic.com/v1/messages` vs. `api.openai.com/v1/chat/completions`) and the request body shape in the LLM Summarizer and Quality Review nodes; the response-parsing expression also needs updating since the two providers return content in different JSON shapes.

## Adjusting the Report Template
- The Markdown template lives entirely in the Markdown Generator Code node (see `docs/n8n-configuration.md`). Edit the JavaScript template string directly to change section headers, add a new section (e.g., "Open Questions"), or change formatting — no other node needs to change, since this node is the only place structure is defined.

## Adjusting Notification Behavior
- `NOTIFY_EMAIL` can be a single address or a comma-separated list, per Gmail node conventions.
- To route failed-review reports to a different recipient than successful ones, add a second environment variable (e.g., `NOTIFY_EMAIL_REVIEW`) and reference it conditionally in the Gmail node's "To" expression.

## Adjusting Retry/Timeout Behavior
- All retry counts and timeouts are set per-node (see `docs/error-handling.md` for the full table); adjust them directly in each node's **Settings → Retry On Fail** panel rather than via environment variables, since n8n does not expose these as workflow-level globals.
