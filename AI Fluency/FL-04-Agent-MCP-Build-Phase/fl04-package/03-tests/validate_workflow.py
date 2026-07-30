import json
import sys

path = sys.argv[1] if len(sys.argv) > 1 else "ai-research-assistant.v2-mcp.json"

with open(path) as f:
    wf = json.load(f)

errors = []

node_names = [n["name"] for n in wf["nodes"]]
node_ids = [n["id"] for n in wf["nodes"]]

if len(node_names) != len(set(node_names)):
    errors.append("Duplicate node names found")
if len(node_ids) != len(set(node_ids)):
    errors.append("Duplicate node ids found")

name_set = set(node_names)

# Every connection source must be a real node
for source in wf["connections"]:
    if source not in name_set:
        errors.append(f"Connection source '{source}' is not a defined node")

# Every connection target must be a real node (across ALL connection
# types: main, ai_languageModel, ai_tool, etc. -- not just "main")
for source, outputs in wf["connections"].items():
    for conn_type, output_lists in outputs.items():
        for output_list in output_lists:
            for edge in output_list:
                target = edge.get("node")
                if target not in name_set:
                    errors.append(
                        f"Connection target '{target}' (from '{source}', "
                        f"type '{conn_type}') is not a defined node"
                    )

# Every node referenced by name in an expression like $('Node Name') should exist
# (spot check only for the new node's expression)
for n in wf["nodes"]:
    if n["name"] == "MCP: Stage Report to Disk":
        expr = n["parameters"]["toolParameters"]
        if "$('Set Topic')" in expr and "Set Topic" not in name_set:
            errors.append("New node references missing node 'Set Topic'")

# Confirm required new node fields are present and match the verified package API
new_nodes = [n for n in wf["nodes"] if n["name"] == "MCP: Stage Report to Disk"]
if len(new_nodes) != 1:
    errors.append("Expected exactly 1 new MCP node")
else:
    nn = new_nodes[0]
    if nn["type"] != "n8n-nodes-mcp.mcpClient":
        errors.append("New node type does not match verified n8n-nodes-mcp package")
    if nn["parameters"].get("connectionType") != "cmd":
        errors.append("New node not configured for STDIO transport")
    if "mcpClientApi" not in nn.get("credentials", {}):
        errors.append("New node missing mcpClientApi credential reference")

print(f"Total nodes: {len(wf['nodes'])}")
print(f"Total connection sources: {len(wf['connections'])}")

# --- Part 6 specific checks ---
removed = {"Quality Review (LLM)", "Review Passed?"}
for source, outputs in wf["connections"].items():
    for conn_type, output_lists in outputs.items():
        for output_list in output_lists:
            for edge in output_list:
                if edge.get("node") in removed:
                    errors.append(f"Dangling reference to removed node '{edge['node']}'")
if any(n["name"] in removed for n in wf["nodes"]):
    errors.append("A removed node still exists in the nodes list")

agent_nodes = [n for n in wf["nodes"] if n["type"].endswith("langchain.agent")]
if agent_nodes:
    agent_name = agent_nodes[0]["name"]
    has_lm = any(
        conn_type == "ai_languageModel"
        and any(edge["node"] == agent_name for lst in outs for edge in lst)
        for src, o in wf["connections"].items()
        for conn_type, outs in o.items()
    )
    has_tool = any(
        conn_type == "ai_tool"
        and any(edge["node"] == agent_name for lst in outs for edge in lst)
        for src, o in wf["connections"].items()
        for conn_type, outs in o.items()
    )
    if not has_lm:
        errors.append("AI Agent node has no ai_languageModel input wired")
    if not has_tool:
        errors.append("AI Agent node has no ai_tool input wired (n8n requires >=1)")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)
else:
    print("VALIDATION PASSED: workflow graph is structurally sound.")
