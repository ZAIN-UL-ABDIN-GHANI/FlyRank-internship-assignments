# Performance Analysis

## Time and Cost Comparison

| Metric | Manual Process | This Workflow |
|---|---|---|
| Manual workflow time | 45–75 minutes: search manually, read multiple pages, take notes, write a summary document, save it, email it | N/A |
| Automated workflow time | N/A | 90–150 seconds of active runtime (see Section 10 test runs for measured values) |
| Setup cost (one-time) | N/A | 1–2 hours: create API accounts, configure credentials, import and test the workflow (see `docs/installation-guide.md`) |
| Runtime (average, across 5 test topics) | N/A | ~110 seconds |
| Time saved | — | ~95–97% reduction per report |
| Scalability | Linear with analyst headcount | Linear with API rate limits; a single n8n instance can run many topics in parallel or in sequence with no added setup cost per topic |

## Cost Estimate (Order of Magnitude)
| Item | Approx. cost per run | Notes |
|---|---|---|
| Search API (Tavily, 8 results) | ~$0.005–$0.01 | Varies by plan/tier |
| LLM calls (1 per source + 1 quality review, short prompts) | ~$0.01–$0.03 | Depends on model choice and result count |
| Google Drive / Gmail | $0 | Included in standard Google account quota |
| n8n | $0 if self-hosted; otherwise per n8n Cloud plan | See `docs/deployment-guide.md` |
| **Total per report** | **≈ $0.02–$0.05** | Orders of magnitude below the fully-loaded cost of 45–75 minutes of analyst time |

## Runtime Breakdown (Typical Run)
| Stage | Approx. time |
|---|---|
| Search API call | 2–5 seconds |
| Split Out | <1 second |
| LLM Summarizer (per item, 8 items, largely parallelizable but run sequentially by default in n8n) | 40–70 seconds total |
| Merge Results | <1 second |
| Markdown Generator | <1 second |
| Quality Review | 5–8 seconds |
| Google Drive Upload | 2–4 seconds |
| Gmail Notification | 1–2 seconds |
| **Total** | **~90–150 seconds** |

## Scalability Notes
- The dominant cost as topic volume grows is LLM Summarizer calls (one per search result per topic); this scales linearly and predictably, and can be reduced by lowering `MAX_SEARCH_RESULTS` if cost matters more than coverage.
- Running multiple topics is trivially parallel at the n8n level (separate executions), bounded only by the Search API and LLM provider's own rate limits — see `docs/error-handling.md`, "Rate limits."
- Because credentials and prompts are centralized (not duplicated per topic), adding a new recurring topic has zero marginal setup cost beyond typing the topic string.
