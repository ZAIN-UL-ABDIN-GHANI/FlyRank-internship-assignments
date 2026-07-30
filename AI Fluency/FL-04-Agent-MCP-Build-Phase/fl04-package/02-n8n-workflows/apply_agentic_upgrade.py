"""
Applies the Part 6 agentic upgrade to a copy of the Part 3 (v2) workflow.

Removes: "Quality Review (LLM)", "Review Passed?" (the deterministic,
single-shot gate).

Adds:
  - "Anthropic Chat Model"   (@n8n/n8n-nodes-langchain.lmChatAnthropic)
  - "MCP Tool: Filesystem"   (n8n-nodes-mcp.mcpClient, same node type/server
                              as Part 3, reused via its usableAsTool=true
                              flag instead of a "main" connection)
  - "AI Agent: Editor"       (@n8n/n8n-nodes-langchain.agent)
  - "Route by Verdict"       (n8n-nodes-base.if — deterministic routing on
                              the agent's structured final output)

Node type strings for the LangChain nodes were confirmed from real,
user-exported n8n workflow JSON (n8n GitHub issues #15883, #12961), NOT
guessed. "lmChatAnthropic" is inferred by the same naming pattern used for
lmChatOpenAi in those examples (Anthropic-specific example was not directly
observed) -- flagged in the Part 6 write-up as needing a one-time check
against the target n8n version.
"""

import json

SRC = "/home/claude/fl04-n8n-workflow/ai-research-assistant.v3-agent.json"

with open(SRC) as f:
    wf = json.load(f)

REMOVE = {"Quality Review (LLM)", "Review Passed?"}
wf["nodes"] = [n for n in wf["nodes"] if n["name"] not in REMOVE]
for name in REMOVE:
    wf["connections"].pop(name, None)

new_nodes = [
    {
        "id": "18",
        "name": "Anthropic Chat Model",
        "type": "@n8n/n8n-nodes-langchain.lmChatAnthropic",
        "typeVersion": 1.3,
        "position": [1000, 560],
        "notes": "Part 6. Reuses the same Anthropic account already used by "
                 "the LLM Summarizer/old Quality Review nodes, but as a "
                 "native n8n credential (required by this node type) "
                 "rather than the generic HTTP Header Auth used by the "
                 "existing httpRequest-based Anthropic calls.",
        "parameters": {"model": "claude-sonnet-4-6", "options": {}},
        "credentials": {"anthropicApi": {"name": "Anthropic API (native)"}},
    },
    {
        "id": "19",
        "name": "MCP Tool: Filesystem",
        "type": "n8n-nodes-mcp.mcpClient",
        "typeVersion": 1,
        "position": [1000, 700],
        "notes": "Part 6. Same server/process as Part 2-3's "
                 "'MCP: Stage Report to Disk' node -- exposed to the Agent "
                 "as a tool instead of a fixed workflow step. Recommend "
                 "restricting Allowed Tools in this node's config to "
                 "read_text_file, get_file_info, edit_file only (agent "
                 "never needs write_file/move_file/create_directory).",
        "parameters": {
            "connectionType": "cmd",
            "operation": "executeTool",
        },
        "credentials": {"mcpClientApi": {"name": "MCP Filesystem Server (STDIO)"}},
    },
    {
        "id": "20",
        "name": "AI Agent: Editor",
        "type": "@n8n/n8n-nodes-langchain.agent",
        "typeVersion": 2,
        "position": [780, 420],
        "notes": "Part 6. Replaces the deterministic 'Quality Review (LLM)' "
                 "+ 'Review Passed?' pair. Max Iterations=3. Emits a "
                 "structured final verdict (APPROVE or ESCALATE) after an "
                 "internal reason -> tool call -> observe loop using the "
                 "MCP Tool: Filesystem node.",
        "parameters": {
            "promptType": "define",
            "text": "={{ $json.report }}",
            "hasOutputParser": True,
            "options": {"maxIterations": 3, "systemMessage": "={{ $('Load System Prompt').item.json.systemPrompt }}"},
        },
        "credentials": {},
    },
    {
        "id": "21",
        "name": "Route by Verdict",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [1220, 420],
        "notes": "Part 6. Deterministic routing on the agent's structured "
                 "output field 'verdict'. REVISE is handled INSIDE the "
                 "agent's own tool-loop via edit_file, not as a workflow "
                 "cycle back to Markdown Generator -- see Part 6 write-up "
                 "for why that Part 5 diagram detail was simplified.",
        "parameters": {
            "conditions": {
                "options": {"caseSensitive": True, "typeValidation": "strict"},
                "conditions": [
                    {
                        "id": "cond-approve",
                        "leftValue": "={{ $json.output.verdict }}",
                        "rightValue": "APPROVE",
                        "operator": {"type": "string", "operation": "equals"},
                    }
                ],
                "combinator": "and",
            }
        },
    },
]

wf["nodes"].extend(new_nodes)

# --- Rewire ---
# MCP: Stage Report to Disk -> AI Agent: Editor (was -> Quality Review (LLM))
wf["connections"]["MCP: Stage Report to Disk"] = {
    "main": [[{"node": "AI Agent: Editor", "type": "main", "index": 0}]]
}

# Anthropic Chat Model -> AI Agent: Editor (ai_languageModel link)
wf["connections"]["Anthropic Chat Model"] = {
    "ai_languageModel": [
        [{"node": "AI Agent: Editor", "type": "ai_languageModel", "index": 0}]
    ]
}

# MCP Tool: Filesystem -> AI Agent: Editor (ai_tool link)
wf["connections"]["MCP Tool: Filesystem"] = {
    "ai_tool": [[{"node": "AI Agent: Editor", "type": "ai_tool", "index": 0}]]
}

# AI Agent: Editor -> Route by Verdict (main)
wf["connections"]["AI Agent: Editor"] = {
    "main": [[{"node": "Route by Verdict", "type": "main", "index": 0}]]
}

# Route by Verdict -> existing Drive Upload branches
wf["connections"]["Route by Verdict"] = {
    "main": [
        [{"node": "Google Drive Upload (Approved)", "type": "main", "index": 0}],
        [{"node": "Google Drive Upload (Needs Review)", "type": "main", "index": 0}],
    ]
}

with open(SRC, "w") as f:
    json.dump(wf, f, indent=2)

print("Total nodes now:", len(wf["nodes"]))
print("Removed:", REMOVE)
print("Added:", [n["name"] for n in new_nodes])
