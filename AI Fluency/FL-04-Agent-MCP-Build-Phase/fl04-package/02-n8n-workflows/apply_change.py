"""
Applies the Part 3 minimal change to the FL-04 n8n workflow:
inserts one new "MCP: Stage Report to Disk" node between
"Markdown Generator" and "Quality Review (LLM)".

Node type/credential/property names below are taken directly from the
installed n8n-nodes-mcp@0.1.37 package source (dist/nodes/McpClient/McpClient.node.js
and dist/credentials/McpClientApi.credentials.js) - not guessed.
"""

import json

SRC = "/home/claude/fl04-n8n-workflow/ai-research-assistant.v2-mcp.json"

with open(SRC) as f:
    wf = json.load(f)

new_node = {
    "id": "17",
    "name": "MCP: Stage Report to Disk",
    "type": "n8n-nodes-mcp.mcpClient",
    "typeVersion": 1,
    "position": [560, 600],
    "notes": (
        "Part 3 addition. Calls the filesystem MCP server (built in Part 2) "
        "to write a durable, disk-backed copy of the generated report before "
        "the LLM quality gate and Drive upload. This is an independent, "
        "protocol-standardized audit checkpoint that n8n's native nodes did "
        "not previously provide for this in-memory report string."
    ),
    "parameters": {
        "connectionType": "cmd",
        "operation": "executeTool",
        "toolName": "write_file",
        "toolParameters": (
            "={{ { \"path\": $env.MCP_STAGING_ROOT + \"/\" + "
            "$('Set Topic').item.json.topic.replace(/\\s+/g,'_') + \"_\" + "
            "$now.format('yyyy-MM-dd') + \".md\", \"content\": $json.report } }}"
        ),
    },
    "credentials": {
        "mcpClientApi": {"name": "MCP Filesystem Server (STDIO)"}
    },
}

wf["nodes"].append(new_node)

# Rewire: Markdown Generator -> MCP: Stage Report to Disk -> Quality Review (LLM)
old_target = wf["connections"]["Markdown Generator"]["main"][0]
assert old_target[0]["node"] == "Quality Review (LLM)"

wf["connections"]["Markdown Generator"]["main"] = [
    [{"node": "MCP: Stage Report to Disk", "type": "main", "index": 0}]
]
wf["connections"]["MCP: Stage Report to Disk"] = {
    "main": [[{"node": "Quality Review (LLM)", "type": "main", "index": 0}]]
}

with open(SRC, "w") as f:
    json.dump(wf, f, indent=2)

print("Node inserted. Total nodes now:", len(wf["nodes"]))
print("Markdown Generator ->", wf["connections"]["Markdown Generator"])
print("MCP: Stage Report to Disk ->", wf["connections"]["MCP: Stage Report to Disk"])
