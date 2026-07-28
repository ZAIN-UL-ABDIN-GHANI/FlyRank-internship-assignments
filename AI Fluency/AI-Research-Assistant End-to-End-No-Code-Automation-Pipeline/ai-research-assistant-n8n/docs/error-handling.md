# Error Handling

Governing principle: **fail loud and specific, never fail silent.** Every external-API node has an explicit failure path; nothing is allowed to quietly produce a degraded result that looks normal.

## Failure Modes and Handling

| Failure Mode | Detection | Retry Strategy | Fallback Strategy |
|---|---|---|---|
| **Search API failure** (Tavily/SerpAPI unreachable, 5xx) | HTTP Request node's error output fires | 3 retries, exponential backoff (2s, 4s, 8s) | If all retries fail: workflow branches to an operator-alert email ("Search failed for topic X") and the run ends; no report is generated from stale/no data |
| **Rate limits** (HTTP 429) | Status code check on error output | Same retry policy, but backoff starts higher (5s) and respects a `Retry-After` header if present | If still rate-limited after retries: run is queued for manual re-trigger (documented in `docs/troubleshooting-guide.md`), not silently dropped |
| **LLM timeout** (Summarizer or Quality Review call exceeds 30s) | Node-level timeout setting | 2 retries | Per-item: that single source is marked `failed: true` and excluded from the report rather than blocking the whole run (see `docs/workflow-design.md`, Node 5). If **every** item times out, branch to operator alert (see "No search results" handling below, same pattern) |
| **No search results** (Search API returns an empty array) | Split Out produces 0 items; an `IF` node checks item count immediately after Split Out | N/A — not a transient condition | Branch directly to an operator/requester email: "No current sources found for topic X — try rephrasing." No empty report is ever generated |
| **Google Drive upload failure** | Node error output | 3 retries | Report content is attached as plain text directly in the fallback notification email, so the content is never lost even if filing fails; operator is alerted to manually save it |
| **Gmail failure** | Node error output | 2 retries | Run is still marked a partial success (report exists in Drive); failure is logged to n8n's execution log for the operator to notice and manually notify the requester |
| **Invalid topic** (empty string, or non-text input) | `IF` node immediately after Set Topic checks `topic.trim().length > 0` | N/A | Workflow stops immediately with a clear "Topic cannot be empty" error, before any API calls are made — protects API quota from wasted calls |

## Retry Strategy (General Policy)
- All external-API nodes use n8n's built-in `Retry On Fail` with capped attempts (2–3, tuned per node above) and exponential backoff, never immediate infinite retry.
- Retries are bounded so a single bad run cannot silently consume the whole API quota for the day.

## Fallback Strategy (General Policy)
- No failure mode is allowed to produce a *false-looking-successful* report. If the pipeline cannot produce a genuinely sourced report, it fails toward an explicit alert, not toward a thin or fabricated one.
- The Drive upload is treated as the canonical artifact; the fallback path for a Drive failure (attaching the report to the alert email) exists specifically so a Gmail-only failure never means the actual research work is lost.

## Error Workflow (n8n Error Trigger)
A secondary, minimal n8n workflow using the `Error Trigger` node is configured at the instance level to catch any unhandled exception in the main workflow (one not already covered by a per-node error branch above) and post a Slack/email alert to the operator with the failed execution's ID, so nothing fails completely invisibly even outside the cases explicitly enumerated above.
