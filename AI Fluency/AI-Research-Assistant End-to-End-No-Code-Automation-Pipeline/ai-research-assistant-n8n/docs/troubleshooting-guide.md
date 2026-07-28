# Troubleshooting Guide

| Symptom | Likely Cause | Fix |
|---|---|---|
| Workflow stops immediately at Set Topic → HTTP Request | `topic` field is empty | Enter a non-empty topic before executing; see `docs/error-handling.md`, "Invalid topic" |
| HTTP Request (Search API) node shows a red error, 401/403 | Search API credential is missing, expired, or misnamed | Re-check the `Tavily API` (or SerpAPI) credential in **Settings → Credentials**; regenerate the key if needed (`docs/api-setup-guide.md`) |
| HTTP Request (Search API) node shows a 429 error | Rate limit hit on the Search API plan | Wait and retry; consider lowering `MAX_SEARCH_RESULTS` or upgrading the API plan; see `docs/error-handling.md`, "Rate limits" |
| Split Out produces 0 items downstream | Search API returned zero results for an overly narrow or misspelled topic | Rephrase the topic to be broader or check spelling; this is expected behavior per FR-2/"No search results" handling, not a bug |
| LLM Summarizer node times out repeatedly | LLM provider is experiencing latency, or `LLM_MODEL` is set to an invalid/retired model string | Check the provider's status page; verify `LLM_MODEL` against the provider's current model list (`docs/api-setup-guide.md`) |
| Final report is very short or says "No findings could be summarized" | Most/all LLM Summarizer calls failed or returned `INSUFFICIENT_CONTENT` | Check LLM credential and model string first; if those are fine, the search results themselves may have been too thin — try a more specific topic (see `docs/testing.md`, Run 5 lesson learned) |
| Google Drive Upload fails with a permissions error | The connected Google account doesn't have write access to `DRIVE_FOLDER_ID`, or the folder ID is wrong | Re-copy the folder ID from the Drive URL; confirm the authorized account owns or has edit access to that folder |
| Report content missing from Drive after an upload failure | Should not happen — the fallback path attaches report text directly to the alert email | If this occurs, check that the fallback branch (`docs/error-handling.md`, "Google Drive upload failure") is still wired correctly after any manual edits to the workflow |
| Gmail Notification fails | Gmail credential expired, or `NOTIFY_EMAIL` is malformed | Re-authenticate the Gmail OAuth2 credential; verify `NOTIFY_EMAIL` is a valid address or comma-separated list |
| Workflow JSON won't import | File was edited outside n8n and has invalid JSON syntax, or was exported from a much older/newer n8n version with incompatible node `typeVersion`s | Validate the JSON with any JSON linter; check `workflows/ai-research-assistant.json`'s node `typeVersion` fields against your n8n version's supported ranges |
| Credential values appear to be visible in an exported workflow file | This should never happen with n8n's standard export — credentials export as a reference (name + type) only | Do not commit the export if you see raw key values; check whether a node parameter was edited to hard-code a key directly instead of using the credential dropdown (a security anti-pattern — see `docs/security.md`) |

## General Debugging Steps
1. Open the failed execution in n8n's **Executions** tab and click the red node to see the exact error payload.
2. Check `docs/n8n-configuration.md` to confirm the node's parameters match the documented configuration exactly.
3. Re-run `docs/installation-guide.md`, Section 5 (Test Run) with a known-good topic (e.g., one of the five from `docs/testing.md`) to isolate whether the issue is topic-specific or systemic.
