# Software Requirements Specification (SRS)
## AI Research Assistant (n8n No-Code Workflow)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the requirements for an AI-powered research automation workflow built on n8n. The system accepts a topic from a user, searches the web for current information, summarizes findings with a large language model (LLM), compiles a Markdown report, stores the report in Google Drive, and emails a notification with a link to the report.

### 1.2 Scope
The system automates a single, well-defined research task end to end: **topic in → sourced Markdown report out, filed and delivered**. It is designed to be triggered manually per topic (with scheduled/batch execution documented as a future improvement in `docs/future-improvements.md`), and to be operable by a non-technical user after a one-time setup performed by a technical operator.

### 1.3 Definitions
| Term | Meaning |
|---|---|
| Node | A single processing unit in an n8n workflow (e.g., HTTP Request, Code, Google Drive) |
| Run | One execution of the workflow for one topic |
| Item | A unit of data (JSON object) flowing between n8n nodes |
| LLM | Large Language Model (Claude or OpenAI, called via HTTP Request) |
| Search API | A third-party API returning web search results (Tavily or SerpAPI) |

---

## 2. Overall Description

### 2.1 Product Perspective
A standalone n8n workflow that composes existing services (a search API, an LLM API, Google Drive, Gmail) rather than a custom-coded application. It is intentionally "no-code": all logic lives in n8n node configuration and a small amount of JavaScript inside Code nodes, not in an externally hosted backend.

### 2.2 Product Functions
- Accept a research topic as input.
- Query a search API for current, relevant sources.
- Summarize each source (or the aggregate result set) using an LLM.
- Assemble a structured Markdown report with a title, executive summary, key findings, and a sources section.
- Run a quality-review pass on the report before it is filed.
- Upload the final report to a designated Google Drive folder.
- Send an email notification containing the report title, summary, and Drive link.

### 2.3 User Characteristics
- **Operator**: sets up credentials and the workflow once; may or may not run it day to day.
- **Requester**: types a topic and clicks "Execute Workflow"; needs no n8n or API knowledge.
- **Report recipient**: reads the emailed notification and opens the linked Drive report; needs no technical knowledge at all.

### 2.4 Constraints
- Must be built entirely in n8n using core, documented nodes — no invented or unsupported node types.
- Must not hard-code API keys inside node parameters; all credentials must use n8n's credential store or environment variables.
- Must produce a single, portable Markdown file per run (no proprietary document format).
- Must be reproducible by another engineer from this documentation and the exported workflow JSON alone.

### 2.5 Assumptions
- The operator has (or can create) accounts with a search API provider (Tavily or SerpAPI) and an LLM provider (Anthropic or OpenAI).
- The operator has a Google Workspace or personal Google account that can authorize n8n's Google Drive and Gmail OAuth scopes.
- n8n is available either as n8n Cloud or a self-hosted instance (Docker) reachable by the operator.
- Research topics are general-interest or business topics, not requiring access to paywalled or classified sources.

### 2.6 Success Criteria
| # | Criterion | Target |
|---|---|---|
| 1 | End-to-end run completes without manual intervention on a well-formed topic | ≥ 90% of test runs |
| 2 | Report contains a working Google Drive link and correct topic title | 100% of successful runs |
| 3 | Every claim in the report traces to at least one search result | 100% of successful runs |
| 4 | Total automated runtime per topic | Under 3 minutes |
| 5 | Email notification delivered within 30 seconds of report upload | ≥ 95% of successful runs |
| 6 | Workflow degrades gracefully (documented fallback, no silent data loss) on each failure mode in `docs/troubleshooting-guide.md` | 100% of failure modes tested |

---

## 3. Specific Requirements

### 3.1 Functional Requirements
| ID | Requirement |
|---|---|
| FR-1 | The system shall accept a topic string as its only required run-time input. |
| FR-2 | The system shall query a search API and retrieve at least 5 candidate results per topic. |
| FR-3 | The system shall split the result set into individual items for per-source processing. |
| FR-4 | The system shall summarize each source using an LLM prompt that preserves attribution (source title/URL). |
| FR-5 | The system shall merge per-source summaries into a single aggregated result set. |
| FR-6 | The system shall generate a Markdown report with a fixed structure: title, executive summary, key findings (bulleted, sourced), and a sources list. |
| FR-7 | The system shall run an LLM-based quality-review pass on the assembled report before filing it. |
| FR-8 | The system shall upload the final Markdown report to a designated Google Drive folder with a deterministic filename (`Topic_YYYY-MM-DD.md`). |
| FR-9 | The system shall send an email via Gmail containing the report title, a short summary, and the Google Drive link. |
| FR-10 | The system shall handle and log failures at every external-API node without silently dropping the run. |

### 3.2 Non-Functional Requirements
| ID | Requirement |
|---|---|
| NFR-1 (Performance) | A single run shall complete in under 3 minutes under normal API latency. |
| NFR-2 (Reliability) | The workflow shall retry transient API failures (HTTP 429/5xx) at least twice before falling back. |
| NFR-3 (Security) | All credentials shall be stored in n8n's encrypted credential store; no API key shall appear in plain text in node parameters, workflow JSON, or logs. |
| NFR-4 (Maintainability) | Every node shall have a descriptive name and every LLM prompt shall be stored in a single, version-controlled prompt library (`/prompts`). |
| NFR-5 (Portability) | The workflow shall be exportable/importable as a single JSON file with no environment-specific hard-coded values (only credential references and environment variables). |
| NFR-6 (Usability) | A non-technical user shall be able to trigger a run by editing one field ("topic") and clicking Execute. |

---

## 4. Traceability
Every FR/NFR above is re-checked against the finished deliverable in `docs/testing.md` (Section "Validation Summary") and is not considered complete until that checklist passes.
