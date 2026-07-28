# API Setup Guide

Step-by-step instructions for obtaining every credential referenced in `docs/n8n-configuration.md`.

## 1. Search API — Tavily (primary choice)
1. Create an account at Tavily's developer site.
2. Generate an API key from the dashboard.
3. In n8n, create a **Generic Header Auth** credential named `Tavily API` with header name `Authorization` and value `Bearer <your key>`.

### Alternative: SerpAPI
1. Create an account at SerpAPI's site and generate a key.
2. In n8n, create a credential per SerpAPI's documented auth method (typically an API key passed as a query parameter, configured via n8n's Query Auth credential type).
3. Follow `docs/configuration-guide.md`, "Switching Search Providers," to update the HTTP Request node accordingly.

## 2. LLM API — Anthropic (primary choice) or OpenAI
### Anthropic
1. Create an account at Anthropic's console and generate an API key.
2. In n8n, create a **Generic Header Auth** credential named `Anthropic API` with header name `x-api-key` and value `<your key>`. Also add the required `anthropic-version` header directly in the HTTP Request node (not the credential), as documented in `docs/n8n-configuration.md`.
3. Set `LLM_MODEL` to your account's current available model string — check Anthropic's documentation for the current model list, since this changes over time.

### OpenAI (alternative)
1. Create an account at OpenAI's platform and generate an API key.
2. In n8n, create a **Generic Header Auth** credential named `OpenAI API` with header name `Authorization` and value `Bearer <your key>`.
3. Follow `docs/configuration-guide.md`, "Switching LLM Providers."

## 3. Google Drive
1. In n8n, go to **Settings → Credentials → Add Credential → Google Drive OAuth2 API**.
2. n8n displays an OAuth redirect URL — if self-hosting, ensure this URL is reachable (see `docs/deployment-guide.md`, Production Notes).
3. Follow n8n's in-app instructions to create a Google Cloud project, enable the Google Drive API, create an OAuth 2.0 Client ID (type: Web application), and add n8n's redirect URL to the client's authorized redirect URIs.
4. Complete the OAuth consent flow from within n8n; request only the `drive.file` scope (least privilege — see `docs/security.md`).

## 4. Gmail
1. In n8n, go to **Settings → Credentials → Add Credential → Gmail OAuth2**.
2. In the same Google Cloud project used for Drive, enable the Gmail API and add the `gmail.send` scope only.
3. Complete the OAuth consent flow from within n8n.

## 5. Verifying All Credentials
Run through `docs/installation-guide.md`, Section 5 (Test Run) once all four credentials are created and attached to their respective nodes. A successful test run is the definitive check that every credential is configured correctly.
