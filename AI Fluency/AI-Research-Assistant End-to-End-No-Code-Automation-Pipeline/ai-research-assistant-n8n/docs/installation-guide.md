# Installation Guide

Assumes n8n is already running (see `docs/deployment-guide.md`).

## 1. Import the Workflow
1. In the n8n editor, click **Workflows → Import from File**.
2. Select `workflows/ai-research-assistant.json` from this repository.
3. The full node graph (Manual Trigger → ... → Gmail Notification) appears on the canvas.

## 2. Create Credentials
Follow `docs/api-setup-guide.md` to obtain each API key/OAuth client first, then in n8n:
1. **Settings → Credentials → Add Credential** for each of the four credential types listed in `docs/n8n-configuration.md`, Section 1: `Tavily API`, `Anthropic API` (or `OpenAI API`), `Google Drive OAuth2`, `Gmail OAuth2`.
2. Open each node in the imported workflow that requires a credential (HTTP Request nodes, Google Drive node, Gmail node) and select the matching credential from the dropdown.

## 3. Set Environment Variables
Add the variables listed in `docs/n8n-configuration.md`, Section 2 (`SEARCH_API_PROVIDER`, `DRIVE_FOLDER_ID`, `NOTIFY_EMAIL`, `MAX_SEARCH_RESULTS`, `LLM_MODEL`) to your n8n instance's environment (Docker `.env` file, or n8n Cloud's environment variable settings page).

## 4. Configure the Target Drive Folder
1. In Google Drive, create a folder (e.g., "Weekly Research Reports").
2. Open the folder and copy its ID from the URL (`https://drive.google.com/drive/folders/<THIS_PART_IS_THE_ID>`).
3. Set this as `DRIVE_FOLDER_ID`.

## 5. Test Run
1. Open the **Set Topic** node and enter a test topic, e.g., `"Artificial Intelligence"`.
2. Click **Execute Workflow**.
3. Watch each node execute in sequence; a green checkmark indicates success, red indicates failure (click the node to see the error detail).
4. Confirm: a Markdown file appears in the configured Drive folder, and a notification email arrives at `NOTIFY_EMAIL`.

## 6. Compare Against Expected Behavior
Compare your test run's output structure against the example runs in `docs/testing.md` — the report should have the same four sections (title, executive summary, key findings, sources) regardless of topic.

If anything fails, go to `docs/troubleshooting-guide.md` before changing any node configuration.
