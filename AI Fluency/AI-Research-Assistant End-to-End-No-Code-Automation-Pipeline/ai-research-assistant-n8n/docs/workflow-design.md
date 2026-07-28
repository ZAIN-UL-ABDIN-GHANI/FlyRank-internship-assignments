# Workflow Design

## Node Sequence

```
Manual Trigger
      |
      v
  Set Topic
      |
      v
HTTP Request (Search API)
      |
      v
  Split Out
      |
      v
LLM Summarizer  (runs once per item)
      |
      v
Merge Results (Aggregate)
      |
      v
Markdown Generator (Code)
      |
      v
Quality Review (LLM, single call)
      |
      v
Google Drive Upload
      |
      v
Gmail Notification
```

Two nodes beyond the minimum list in the brief were added deliberately — **Quality Review** (between Markdown Generator and Google Drive Upload) and implicit **error-handling branches** on every external-API node — and are called out explicitly below, since every added node must be justified per the engineering rules of this project.

---

## Node-by-Node Specification

### 1. Manual Trigger
| Field | Detail |
|---|---|
| Purpose | Entry point for the workflow; starts a run when the user clicks Execute. |
| Inputs | None. |
| Outputs | An empty item, used only to start the chain. |
| Configuration | No parameters. (n8n node type: `n8n-nodes-base.manualTrigger`.) |
| Failure handling | N/A — cannot fail; it only fires on explicit user action. |

### 2. Set Topic
| Field | Detail |
|---|---|
| Purpose | Defines the single run-time input: the research topic. |
| Inputs | Empty item from Manual Trigger. |
| Outputs | `{ topic: "<string>" }` |
| Configuration | `Set`/"Edit Fields" node with one string field, `topic`, defaulted to an example value (e.g. `"Artificial Intelligence"`) that the user overwrites before each run. |
| Failure handling | Validated downstream by the HTTP Request node's expression; if `topic` is empty, the workflow is configured to stop with a clear error rather than call the Search API with a blank query (see `docs/error-handling.md`, "Invalid topic"). |

### 3. HTTP Request (Search API)
| Field | Detail |
|---|---|
| Purpose | Retrieve current web search results for the topic. |
| Inputs | `{ topic }` |
| Outputs | `{ topic, results: [ { title, url, snippet }, ... ] }` |
| Configuration | `POST` to `https://api.tavily.com/search` (or SerpAPI's equivalent GET endpoint), `Authorization` header from the **Tavily API** credential, JSON body `{ "query": "={{$json.topic}}", "max_results": 8 }`. |
| Failure handling | `retryOnFail: true`, `maxTries: 3`, exponential backoff; `onError: continueErrorOutput` routing to a dedicated error branch (see `docs/error-handling.md`, "Search API failure" and "Rate limits"). |

### 4. Split Out
| Field | Detail |
|---|---|
| Purpose | Convert the single `results` array into one n8n item per search result, so each can be summarized independently. |
| Inputs | `{ topic, results: [...] }` |
| Outputs | N items, each `{ topic, title, url, snippet }` |
| Configuration | Field to split out: `results`. (n8n node type: `n8n-nodes-base.splitOut`.) |
| Failure handling | If `results` is empty (zero search hits), Split Out produces zero items and the branch downstream is empty; this is explicitly detected and handled — see `docs/error-handling.md`, "No search results". |

### 5. LLM Summarizer
| Field | Detail |
|---|---|
| Purpose | Produce a short, attributed summary of one search result. |
| Inputs | One item: `{ topic, title, url, snippet }` |
| Outputs | Same item plus `{ summary: "<2-3 sentence text>" }` |
| Configuration | HTTP Request to the LLM provider's chat/messages endpoint, using **Prompt 2 (Summarization)** from `/prompts/02-summarization-prompt.md`, with `title`, `url`, and `snippet` interpolated into the prompt. Runs once per item (n8n executes downstream nodes once per incoming item by default). |
| Failure handling | `retryOnFail: true`, `maxTries: 2`; per-item timeout of 30s; on repeated failure for a single item, that item is marked `summary: null, failed: true` and passed through rather than aborting the whole run — see `docs/error-handling.md`, "LLM timeout". |

### 6. Merge Results (Aggregate)
| Field | Detail |
|---|---|
| Purpose | Recombine the N per-item summaries back into a single item so the report can be assembled as one document. |
| Inputs | N items: `{ topic, title, url, snippet, summary, failed? }` |
| Outputs | One item: `{ topic, summaries: [ {title, url, summary}, ... ], failedCount }` |
| Configuration | `Aggregate` node, "Aggregate All Item Data", output field name `summaries`. Items where `failed: true` are filtered out immediately before aggregation with a small `Filter` node so they don't pollute the report. |
| Failure handling | If `failedCount` equals the total item count (every summarization failed), the workflow branches to a fallback path that emails an operator alert instead of a report — see `docs/error-handling.md`. |

### 7. Markdown Generator (Code)
| Field | Detail |
|---|---|
| Purpose | Deterministically assemble the final Markdown report from structured data. |
| Inputs | `{ topic, summaries[] }` |
| Outputs | `{ topic, report: "<markdown string>" }` |
| Configuration | `Code` node (JavaScript), building a template: `# {topic} — Research Report`, a one-paragraph executive summary line, a `## Key Findings` bulleted list (one bullet per summary with an inline `[source](url)` link), and a `## Sources` list. See exact template in `docs/n8n-configuration.md`. |
| Failure handling | Pure function, no external calls — cannot fail except on malformed input, which is guarded with a null-check that produces a minimal "insufficient data" report rather than throwing. |

### 8. Quality Review (LLM, single call) — *added node, justified*
| Field | Detail |
|---|---|
| Purpose | A final automated check that the report is well-formed and every claim is traceable, before it is filed and emailed. |
| Inputs | `{ topic, report }` |
| Outputs | `{ topic, report, reviewPassed: boolean, reviewNotes: string }` |
| Configuration | HTTP Request to the LLM using **Prompt 4 (Quality Review)** from `/prompts/04-quality-review-prompt.md`. |
| Failure handling | If `reviewPassed` is false, the run branches to a "needs human review" path — the report is still uploaded to Drive (in a `Needs-Review/` subfolder) but the Gmail step's subject line is prefixed `[NEEDS REVIEW]` rather than sent as a normal notification. This is deliberately a soft-fail, not a hard stop — see `docs/human-review.md`. |

### 9. Google Drive Upload
| Field | Detail |
|---|---|
| Purpose | File the final report as the system of record. |
| Inputs | `{ topic, report }` |
| Outputs | `{ topic, report, driveFileId, driveLink }` |
| Configuration | `Google Drive` node, operation **Upload**, target folder ID from an environment variable (`DRIVE_FOLDER_ID`), filename `={{$json.topic.replace(/\s+/g,"_")}}_{{$now.format('yyyy-MM-dd')}}.md`. |
| Failure handling | `retryOnFail: true`, `maxTries: 3`; on final failure, the report content is not lost — it is attached directly to the fallback notification email instead (see `docs/error-handling.md`, "Google Drive upload failure"). |

### 10. Gmail Notification
| Field | Detail |
|---|---|
| Purpose | Notify the requester that the report is ready. |
| Inputs | `{ topic, report, driveLink }` |
| Outputs | Send confirmation (no further nodes). |
| Configuration | `Gmail` node, operation **Send**, subject `="Research Report: " + $json.topic`, body built from **Prompt 5 (Email Notification)** in `/prompts/05-email-notification-prompt.md`, including the Drive link. |
| Failure handling | `retryOnFail: true`, `maxTries: 2`; on final failure, the run is still considered a partial success (the report exists in Drive) and the failure is logged for the operator — see `docs/error-handling.md`, "Gmail failure". |

---

## Success Criteria per Stage
| Stage | Success criterion |
|---|---|
| Search API | ≥ 5 results returned |
| Split Out | ≥ 1 item produced |
| LLM Summarizer | ≥ 60% of items summarized successfully |
| Merge Results | `summaries` array non-empty |
| Markdown Generator | Output contains all four required sections (title, executive summary, key findings, sources) |
| Quality Review | `reviewPassed = true`, or explicitly routed to the needs-review path |
| Google Drive Upload | `driveFileId` present |
| Gmail Notification | Send API returns a message ID |
