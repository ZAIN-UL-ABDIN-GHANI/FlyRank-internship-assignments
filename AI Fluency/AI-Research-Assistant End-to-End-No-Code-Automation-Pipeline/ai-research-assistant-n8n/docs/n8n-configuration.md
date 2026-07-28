# n8n Configuration Reference

This document is the single source of truth for every credential, parameter, expression, and environment variable used in `workflows/ai-research-assistant.json`. Configure these before importing the workflow — see `docs/installation-guide.md` for the step-by-step setup.

## 1. Credentials (n8n Credential Store)

| Credential Name | Type | Used By | Notes |
|---|---|---|---|
| `Tavily API` | Generic Header Auth (`Authorization: Bearer <key>`) | HTTP Request (Search API) | Least privilege: search-only API key, no account-management scope |
| `Anthropic API` (or `OpenAI API`) | Generic Header Auth (`x-api-key` for Anthropic / `Authorization: Bearer` for OpenAI) | LLM Summarizer, Quality Review | Same credential reused by both LLM call nodes |
| `Google Drive OAuth2` | n8n built-in Google OAuth2 | Google Drive Upload | Scope restricted to `drive.file` (access only to files the app creates), not full Drive access |
| `Gmail OAuth2` | n8n built-in Google OAuth2 | Gmail Notification | Scope restricted to `gmail.send` only — never `gmail.readonly` or `gmail.modify` |

**Never** paste any of the above keys directly into a node's parameters. All four are referenced only by credential name inside the node, and the credential itself is stored encrypted by n8n.

## 2. Environment Variables

Set these on the n8n instance (Docker `.env` file or n8n Cloud's environment variable settings — see `docs/deployment-guide.md`):

| Variable | Purpose | Example |
|---|---|---|
| `SEARCH_API_PROVIDER` | Switches the HTTP Request URL/body between Tavily and SerpAPI | `tavily` |
| `DRIVE_FOLDER_ID` | Target Google Drive folder for report uploads | `1AbCDefGhIJKlmNoPQRstuVWxyZ` |
| `NOTIFY_EMAIL` | Default recipient for the Gmail notification | `research-team@example.com` |
| `MAX_SEARCH_RESULTS` | Number of results requested per run | `8` |
| `LLM_MODEL` | Model identifier passed to the LLM HTTP Request body | `claude-sonnet-4-6` (or your provider's current model string — see `docs/api-setup-guide.md`) |

A ready-to-copy template is provided at the repository root as `.env.example`.

## 3. Node Parameters and Expressions

### Set Topic
```
Field: topic (String)
Value: Artificial Intelligence      // placeholder — user overwrites before each run
```

### HTTP Request — Search API (Tavily)
```
Method: POST
URL: https://api.tavily.com/search
Authentication: Predefined Credential Type → Tavily API
Send Body: JSON
Body:
{
  "query": "={{ $json.topic }}",
  "max_results": {{ $env.MAX_SEARCH_RESULTS }},
  "search_depth": "advanced"
}
Options → Retry On Fail: true, Max Tries: 3, Wait Between Tries: 2000ms
Options → On Error: Continue (using error output)
```

### Split Out
```
Field To Split Out: results
```

### LLM Summarizer (HTTP Request to Anthropic Messages API)
```
Method: POST
URL: https://api.anthropic.com/v1/messages
Authentication: Predefined Credential Type → Anthropic API
Headers: anthropic-version: 2023-06-01
Send Body: JSON
Body:
{
  "model": "={{ $env.LLM_MODEL }}",
  "max_tokens": 300,
  "messages": [
    { "role": "user", "content": "={{ $('Prompt Library').item.json.summarizationPrompt
        .replace('{{title}}', $json.title)
        .replace('{{url}}', $json.url)
        .replace('{{snippet}}', $json.snippet) }}" }
  ]
}
Options → Retry On Fail: true, Max Tries: 2, Timeout: 30000ms
Options → On Error: Continue (using error output)
```
*(The literal prompt text lives in `/prompts/02-summarization-prompt.md`; in the exported workflow JSON it is inlined directly into the expression for portability — see `workflows/ai-research-assistant.json`.)*

### Merge Results (Aggregate)
```
Aggregate: All Item Data Into a Single List
Output Field Name: summaries
Include: All Fields Except → failed
```

### Markdown Generator (Code)
```javascript
const topic = $input.first().json.topic;
const summaries = $input.first().json.summaries || [];

const findings = summaries.map(s =>
  `- **${s.title}**: ${s.summary} ([source](${s.url}))`
).join('\n');

const sources = summaries.map(s => `- [${s.title}](${s.url})`).join('\n');

const report = `# ${topic} — Research Report

## Executive Summary
This report summarizes ${summaries.length} current sources on "${topic}",
gathered and synthesized automatically on ${new Date().toISOString().slice(0,10)}.

## Key Findings
${findings || '_No findings could be summarized for this run._'}

## Sources
${sources || '_No sources available._'}
`;

return [{ json: { topic, report } }];
```

### Quality Review (HTTP Request to LLM)
```
Method: POST
URL: https://api.anthropic.com/v1/messages
Authentication: Predefined Credential Type → Anthropic API
Body:
{
  "model": "={{ $env.LLM_MODEL }}",
  "max_tokens": 200,
  "messages": [
    { "role": "user", "content": "={{ $('Prompt Library').item.json.qualityReviewPrompt
        .replace('{{report}}', $json.report) }}" }
  ]
}
```
Downstream `IF` node parses the review response for a `PASS`/`FAIL` token and routes accordingly (see `docs/workflow-design.md`, Node 8).

### Google Drive Upload
```
Resource: File
Operation: Upload
File Name: ={{ $json.topic.replace(/\s+/g, '_') }}_{{ $now.format('yyyy-MM-dd') }}.md
Parent Folder: ={{ $env.DRIVE_FOLDER_ID }}
Binary Data: false → Text content from $json.report converted to binary in a preceding "Convert to File" node
```

### Gmail Notification
```
Resource: Message
Operation: Send
To: ={{ $env.NOTIFY_EMAIL }}
Subject: ="Research Report: " + $json.topic
Message: ={{ $json.reviewPassed
    ? "Your report on " + $json.topic + " is ready: " + $json.driveLink
    : "[NEEDS REVIEW] Report on " + $json.topic + " needs a human check before sharing: " + $json.driveLink }}
```

## 4. Connections Map
See `workflows/ai-research-assistant.json` → `connections` object for the exact node-to-node wiring; it matches the sequence documented in `docs/workflow-design.md` exactly, including the error-output branches described in `docs/error-handling.md`.
