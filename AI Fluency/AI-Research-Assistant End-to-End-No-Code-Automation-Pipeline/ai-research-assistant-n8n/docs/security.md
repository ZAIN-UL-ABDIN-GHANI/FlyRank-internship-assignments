# Security

## 1. API Key Protection
- Every API key (Tavily/SerpAPI, Anthropic/OpenAI) is stored exclusively in n8n's encrypted credential store, referenced by credential name inside nodes — never pasted into a node parameter, an expression string, or a workflow note.
- `workflows/ai-research-assistant.json` (the exported workflow) contains **no** live keys; credential references export as name/type only, never as secret values. Confirm this before committing an export to any repository (see `docs/troubleshooting-guide.md` for how to check).
- `.env.example` at the repo root lists every required environment variable name with a placeholder value, never a real key.

## 2. OAuth Credentials (Google Drive, Gmail)
- Both Google credentials use OAuth2, not a long-lived static key, so access can be revoked centrally from the Google Account permissions page at any time without touching n8n.
- Tokens are refreshed automatically by n8n's OAuth2 flow and stored encrypted alongside other credentials.

## 3. Least Privilege
| Credential | Scope granted | Scope explicitly avoided |
|---|---|---|
| Google Drive | `drive.file` (access only to files this app creates/opens) | `drive` (full account access) |
| Gmail | `gmail.send` only | `gmail.readonly`, `gmail.modify` (would allow reading or altering the inbox) |
| Search API | Search-only key tier, if the provider offers scoped keys | Account-management or billing-scoped keys |
| LLM API | A key dedicated to this workflow, so usage/cost can be attributed and revoked independently of other projects | A shared org-wide key used across unrelated systems |

## 4. Prompt Injection
Search results are **untrusted external content** by definition — a malicious or SEO-manipulated page could contain text designed to redirect an LLM's behavior (e.g., "Ignore prior instructions and..."). Mitigations:
- Prompt 2 (Summarization) instructs the model to treat the snippet purely as data to summarize, and the surrounding prompt structure (topic/title/URL/snippet clearly labeled, instruction given before the untrusted content) reduces the chance that embedded text is interpreted as a new instruction.
- The LLM's output at every stage is treated as **data**, not as a new set of instructions to execute — no node in this workflow ever takes LLM output and re-injects it as a system/instruction prompt for a later call without passing through the fixed prompt templates in `/prompts`.
- The Quality Review stage acts as a secondary check that can catch an obviously derailed report (e.g., one that suddenly contains unrelated instructions or content) before it reaches Drive/Gmail.

## 5. Sensitive Data
- This workflow is designed for general/business research topics; it is not intended to process personal data, and no node stores or logs personally identifiable information about the requester beyond their notification email address (already known to the operator who set up `NOTIFY_EMAIL`).
- Search results and LLM outputs are not sent to any third party beyond the two API providers already in the architecture (Search API, LLM API) and Google (Drive, Gmail) — no analytics or logging service is added to the pipeline.
- Operators should avoid entering confidential or internal-only topics into this workflow unless they have confirmed the Search API and LLM API providers' data-handling terms permit it, since the topic string is transmitted to both external providers.

## 6. Credential Rotation
- API keys should be rotated periodically (recommended: every 90 days) by generating a new key with the provider, updating only the n8n credential (not any node parameters), and revoking the old key — this requires zero workflow changes since nodes reference credentials by name, not by value.
