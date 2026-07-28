# System Architecture

## 1. High-Level Component Diagram

```
                 +-------------------+
                 |       User        |
                 |  (types a topic)  |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        n8n        |
                 |  (orchestrator)   |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |     Search API     |
                 |  (Tavily / SerpAPI)|
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        LLM         |
                 |  (Claude / OpenAI) |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |  Markdown Generator |
                 |     (Code node)     |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |    Google Drive    |
                 |   (report storage) |
                 +---------+---------+
                           |
                           v
                 +-------------------+
                 |        Gmail        |
                 |   (notification)     |
                 +-------------------+
```

## 2. Component Explanations

### 2.1 User
The human requester. Their only interaction with the system is editing a single "topic" field and clicking **Execute Workflow** in the n8n editor (or, once the Future Improvements in `docs/future-improvements.md` are adopted, submitting the topic via a form or scheduled list). No n8n, API, or prompt knowledge is required.

### 2.2 n8n (Orchestrator)
The central engine. n8n owns the control flow: it decides the order operations happen in, passes data between nodes as JSON items, applies retry/error-handling policy per node, and is the single place all credentials are referenced from (never duplicated across nodes). n8n does not itself have "intelligence" — it is glue, not a model.

### 2.3 Search API (Tavily or SerpAPI)
An external HTTP API that returns current web search results for the topic: titles, URLs, and short snippets. This is the system's only source of *current* information; the LLM's own training knowledge is deliberately not used as the primary source, because training data goes stale and is not attributable to a checkable source. Tavily is used as the primary choice (it is purpose-built for LLM-pipeline search and returns clean, pre-summarized snippets); SerpAPI is documented as a drop-in alternative in `docs/api-setup-guide.md`.

### 2.4 LLM (Claude or OpenAI)
Called twice in this pipeline, each time for a narrow, well-defined job:
1. **Summarization** — one call per search result, condensing it into 2–3 sentences with the source preserved (Prompt 2 in `/prompts`).
2. **Quality Review** — one call over the assembled draft report, checking structure and traceability before filing (Prompt 4 in `/prompts`).

The LLM is called via a generic **HTTP Request** node against the provider's standard chat/messages endpoint, rather than a dedicated node, so the workflow is portable regardless of which LLM-specific nodes a given n8n version ships with.

### 2.5 Markdown Generator (Code node)
A `Code` node that assembles the final report from structured data (topic, executive summary, per-source summaries, sources list) into a fixed Markdown template. Formatting is done in code, not by asking the LLM to "please format this as Markdown," because deterministic string templating cannot fail to produce valid headings/structure the way an LLM occasionally can.

### 2.6 Google Drive
Stores the final `.md` report in a designated folder, using the Google Drive node's **upload** operation. This is the system of record for every report the workflow has ever produced.

### 2.7 Gmail
Sends a short notification email (subject, one-paragraph summary, Drive link) using the Gmail node's **send** operation. Gmail is used only for notification, never as storage — the Drive file is always the canonical artifact.

## 3. Data Flow Summary
A single JSON payload grows as it moves left to right through the pipeline: `{ topic }` → `{ topic, searchResults[] }` → `{ topic, searchResults[], summaries[] }` → `{ topic, report(markdown) }` → `{ topic, report, driveFileId, driveLink }` → email sent. Every stage adds to this object; nothing earlier in the object is discarded, which is what allows the Quality Review step (2.4, second call) to check the final report against the original search results if needed.

## 4. Deployment Topology
```
+-------------------------------------------------------------+
|                      n8n instance                            |
|   (n8n Cloud, or self-hosted via Docker — see                |
|    docs/deployment-guide.md)                                 |
|                                                                |
|   Credentials store (encrypted):                              |
|     - Tavily/SerpAPI key                                       |
|     - Anthropic/OpenAI key                                     |
|     - Google OAuth2 (Drive + Gmail scopes)                      |
+-------------------------------------------------------------+
        |                  |                    |
        v                  v                    v
  Search API           LLM API              Google APIs
  (external)          (external)           (Drive, Gmail)
```
