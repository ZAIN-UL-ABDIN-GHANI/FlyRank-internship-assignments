# FL-04 — Agent & MCP Build Phase — Complete Package

This package contains the original FL-04 project as received, plus everything
built across Parts 1–6: a real MCP integration, an n8n workflow update, and
an agentic upgrade — each inspected, implemented minimally, and tested before
moving on. Nothing here was fabricated: every result in the submission
document was produced by actually running the commands in Appendix A.

## Read First

**`FL-04_Agent_MCP_Build_Phase.docx`** — the final submission document
(problem, goal, architecture, implementation, testing/MCP evidence, agentic
upgrade, limitations). Start here.

## Folder Guide

| Folder | Part(s) | Contents |
|---|---|---|
| `00-original-project/` | Part 1 | The FL-04 project exactly as received, untouched. Includes a second, unrelated deliverable (`Weekly_Industry_Brief_Engineering_Deliverable_v2.docx`) that was identified but not used in this build — kept here for reference/transparency, not because it's part of the MCP/agent work. |
| `01-mcp-integration/` | Part 2 | The MCP client (`mcp_client.py`) and its config. Connects to the official `@modelcontextprotocol/server-filesystem` reference server (installed via `npm install`, not vendored in this zip). |
| `02-n8n-workflows/` | Parts 3, 5, 6 | Two versioned copies of the n8n workflow — `v2-mcp` (adds MCP staging) and `v3-agent` (adds the Editor Agent) — plus the Python scripts used to generate each from the last, and the agent's system prompt. |
| `03-tests/` | Parts 3, 4, 6 | `validate_workflow.py` (structural graph validation) and `agent_loop_test.py` (real tool-call loop test against the live MCP server). |

## What's Deliberately Not Included

- `node_modules/`, `.venv/` — regenerable via the commands below, not source
- Real API keys/credentials — never committed; see `.env.example`

## Setup & Verification (Appendix A of the submission doc, repeated here)

```bash
cd 01-mcp-integration
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
npm install
cp .env.example .env   # set MCP_FS_ROOT to your project path

# Verify the MCP connection
.venv/bin/python mcp_client.py list-tools
.venv/bin/python mcp_client.py list-dir <your-project-dir>

# Validate the n8n workflow structure
cd ../02-n8n-workflows
python3 ../03-tests/validate_workflow.py ai-research-assistant.v3-agent.json

# Run the agent tool-loop mechanics test (uses the same MCP server)
cd ../03-tests
python3 agent_loop_test.py
```

## Honest Gaps (also in the submission doc, Section 9.5)

- No live n8n instance was available in the build sandbox (`npm install n8n`
  timed out — its dependency tree is large). Import `v3-agent.json` into your
  own n8n instance to verify live execution.
- No Anthropic API key was available in the build sandbox, so the Editor
  Agent's tool-*selection* was tested with a scripted stand-in, not a live
  model call. The tool-*execution* side (against the real MCP server) was
  genuinely verified.
- `lmChatAnthropic` as a node type is inferred by naming pattern from a
  confirmed `lmChatOpenAi` example, not directly observed — a one-time check
  on import into your n8n version.
