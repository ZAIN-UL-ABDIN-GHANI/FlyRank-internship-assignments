# 🔎 AI Research Assistant (n8n No-Code Workflow)

![n8n](https://img.shields.io/badge/n8n-workflow-EA4B71?logo=n8n&logoColor=white)
![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Status](https://img.shields.io/badge/status-active-brightgreen)
![No Code](https://img.shields.io/badge/no--code-AI%20automation-purple)

An end-to-end, no-code AI automation pipeline: give it a topic, and it researches the web, summarizes findings with an LLM, generates a sourced Markdown report, files it in Google Drive, and emails you when it's ready — in under 2 minutes, with production-grade error handling and security built in.

> ![Full workflow canvas](assets/screenshots/01-full-workflow-canvas.png)
> *(Screenshot placeholder — see `docs/screenshots.md` for what to capture here.)*

---

## ✨ Features

- **Fully automated research pipeline** — topic in, sourced report out, no manual searching or writing.
- **Multi-source synthesis** — searches multiple current sources per topic and summarizes each individually before merging.
- **Automated quality review** — an LLM self-check gates every report before it's filed or sent, flagging anything questionable for human review instead of silently shipping it.
- **Production-grade error handling** — retries, timeouts, and documented fallbacks for every external API call (search, LLM, Drive, Gmail).
- **Security-first credential design** — least-privilege OAuth scopes, no hard-coded keys, documented prompt-injection mitigations.
- **Fully documented** — every node, prompt, credential, and failure mode is written down; see `docs/`.
- **Validated on 5 real topics** — Artificial Intelligence, Cybersecurity, Healthcare, Climate Change, and Finance — with genuine test data, not fabricated examples. See `docs/testing.md`.

## 🏗️ Architecture

```
User → n8n → Search API (Tavily/SerpAPI) → LLM (Claude/OpenAI) →
Markdown Generator → Google Drive → Gmail
```

Full component breakdown: [`docs/architecture.md`](docs/architecture.md) · Diagram: [`diagrams/architecture-diagram.md`](diagrams/architecture-diagram.md)

## 🔀 Workflow

```
Manual Trigger → Set Topic → HTTP Request (Search API) → Split Out →
LLM Summarizer → Merge Results (Aggregate) → Markdown Generator →
Quality Review (LLM) → [IF Passed] → Google Drive Upload → Gmail Notification
```

Full node-by-node design: [`docs/workflow-design.md`](docs/workflow-design.md) · Diagram with error branches: [`diagrams/workflow-diagram.md`](diagrams/workflow-diagram.md)

## 🛠️ Technologies Used

| Layer | Technology |
|---|---|
| Orchestration | [n8n](https://n8n.io) (self-hosted or Cloud) |
| Web Search | Tavily API (or SerpAPI) |
| LLM | Anthropic Claude (or OpenAI), called via HTTP Request |
| Storage | Google Drive API |
| Notification | Gmail API |

**Why n8n over Make.com/Zapier?** See the full weighted comparison in [`docs/solution-planning.md`](docs/solution-planning.md) — in short: native per-item looping, self-hosting for cost control, and full custom-code support.

## 🚀 Quick Start

1. **Deploy n8n** — [`docs/deployment-guide.md`](docs/deployment-guide.md) (Docker or n8n Cloud)
2. **Get your API keys** — [`docs/api-setup-guide.md`](docs/api-setup-guide.md) (Tavily/SerpAPI, Anthropic/OpenAI, Google OAuth)
3. **Import & configure** — [`docs/installation-guide.md`](docs/installation-guide.md) (import `workflows/ai-research-assistant.json`, attach credentials, set environment variables)
4. **Run it** — open the **Set Topic** node, type a topic, click **Execute Workflow**.

Need to tune search breadth, swap providers, or edit the report template? See [`docs/configuration-guide.md`](docs/configuration-guide.md).

## 📸 Example Output

> ![Generated Markdown report](assets/screenshots/07-generated-markdown-report.png)
> *(Screenshot placeholder — see `docs/screenshots.md`.)*

Five full example runs (Artificial Intelligence, Cybersecurity, Healthcare, Climate Change, Finance), each with real inputs, real outputs, timing, problems found, and lessons learned: [`docs/testing.md`](docs/testing.md)

## 📊 Performance

| Metric | Manual | Automated |
|---|---|---|
| Time per report | 45–75 min | ~90–150 sec |
| Time saved | — | ~95–97% |
| Cost per report | Analyst time | ≈ $0.02–$0.05 in API costs |

Full breakdown: [`docs/performance.md`](docs/performance.md)

## 🔒 Security

- No API keys or secrets committed to this repository — see `.env.example` for the variable names only.
- Least-privilege OAuth scopes (`drive.file`, `gmail.send`) — full policy in [`docs/security.md`](docs/security.md).
- Documented prompt-injection mitigations for untrusted web content.

## 🧠 Prompt Library

Five versioned, reusable prompts drive every LLM call in this workflow — see [`prompts/`](prompts/):
1. [Research (query planning)](prompts/01-research-prompt.md)
2. [Summarization](prompts/02-summarization-prompt.md)
3. [Report Generation](prompts/03-report-generation-prompt.md)
4. [Quality Review](prompts/04-quality-review-prompt.md)
5. [Email Notification](prompts/05-email-notification-prompt.md)

## 🧩 Full Documentation Index

| Doc | Purpose |
|---|---|
| [`docs/srs.md`](docs/srs.md) | Requirement Analysis (Software Requirements Specification) |
| [`docs/solution-planning.md`](docs/solution-planning.md) | Platform comparison (n8n vs. Make.com vs. Zapier) |
| [`docs/architecture.md`](docs/architecture.md) | System architecture and component detail |
| [`docs/workflow-design.md`](docs/workflow-design.md) | Node-by-node workflow design |
| [`docs/n8n-configuration.md`](docs/n8n-configuration.md) | Credentials, parameters, expressions, env vars |
| [`docs/error-handling.md`](docs/error-handling.md) | Failure modes, retry, and fallback strategy |
| [`docs/security.md`](docs/security.md) | API key/OAuth protection, least privilege, prompt injection |
| [`docs/performance.md`](docs/performance.md) | Time, cost, and scalability analysis |
| [`docs/testing.md`](docs/testing.md) | Five real end-to-end test runs |
| [`docs/human-review.md`](docs/human-review.md) | What AI can't verify, QA checklist |
| [`docs/future-improvements.md`](docs/future-improvements.md) | Slack/Notion integration, RAG, multi-agent, and more |
| [`docs/deployment-guide.md`](docs/deployment-guide.md) | Deploying n8n itself (Docker/Cloud) |
| [`docs/installation-guide.md`](docs/installation-guide.md) | Importing and first-run setup |
| [`docs/configuration-guide.md`](docs/configuration-guide.md) | Tuning the workflow post-install |
| [`docs/api-setup-guide.md`](docs/api-setup-guide.md) | Obtaining every API key/OAuth credential |
| [`docs/troubleshooting-guide.md`](docs/troubleshooting-guide.md) | Symptom → cause → fix reference table |
| [`docs/repository-structure.md`](docs/repository-structure.md) | Full repo layout and rationale |
| [`docs/screenshots.md`](docs/screenshots.md) | Screenshot capture checklist |
| [`docs/demo-video-script.md`](docs/demo-video-script.md) | 2–3 minute demo script |
| [`docs/resume-bullets.md`](docs/resume-bullets.md) | ATS-friendly resume bullets for this project |

## 🔮 Future Improvements

Slack integration · Notion integration · scheduled execution · vector database + RAG · multi-agent workflow. Full detail with rationale: [`docs/future-improvements.md`](docs/future-improvements.md)

## 📄 License

MIT — see [`LICENSE`](LICENSE).
