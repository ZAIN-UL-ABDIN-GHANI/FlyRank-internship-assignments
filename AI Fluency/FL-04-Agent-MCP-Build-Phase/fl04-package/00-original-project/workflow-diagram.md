# Workflow Diagram (n8n Node Graph)

```
Manual Trigger
      |
      v
  Set Topic  ----------------------+
      |                            |  topic is empty
      v                            v
HTTP Request (Search API)    STOP: "Topic cannot be empty"
      |         \
      |          \ error (429/5xx after retries)
      |           v
      |     Operator Alert Email
      v
  Split Out  --------------------+
      |                          |  0 items (no results)
      v                          v
LLM Summarizer (per item)   Requester Email: "No sources found"
      |         \
      |          \ per-item timeout/failure (after retries)
      |           v
      |     item marked failed, excluded
      v
Merge Results (Aggregate)  ------+
      |                          |  all items failed
      v                          v
Markdown Generator (Code)   Operator Alert Email
      |
      v
Quality Review (LLM)
      |         \
      |          \ STATUS: FAIL
      |           v
      |     File to Drive "Needs-Review/" + flagged email
      v  STATUS: PASS
Google Drive Upload  -------------+
      |                           |  upload error (after retries)
      |                           v
      |                     Attach report to fallback email
      v
Gmail Notification  --------------+
      |                           |  send error (after retries)
      v                           v
   Done                    Log failure; report still safe in Drive
```

See `docs/workflow-design.md` for full per-node purpose/input/output/configuration/failure-handling detail, and `docs/error-handling.md` for the retry/fallback policy behind each error branch shown above.
