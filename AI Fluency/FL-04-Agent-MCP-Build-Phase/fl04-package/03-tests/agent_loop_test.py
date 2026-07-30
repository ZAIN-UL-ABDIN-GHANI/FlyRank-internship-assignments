"""
Part 6 loop-mechanics test.

This does NOT call a real LLM (no Anthropic API key is available in this
sandbox -- confirmed via `env | grep -i anthropic` returning nothing).
What it DOES genuinely test, against the real filesystem MCP server from
Parts 2-3, in a single long-lived session (mirroring how one n8n Agent
node execution would hold one session open across multiple tool calls):

  1. An initial flawed draft is staged on disk (real write_file).
  2. A SCRIPTED decision policy (clearly marked) stands in for the LLM,
     choosing which tool to call based on the previous tool's real result.
  3. edit_file is called to fix the flaw -> verified independently on disk.
  4. get_file_info confirms the change -> real metadata.
  5. Loop terminates with APPROVE, within the Max Iterations=3 bound.
  6. A second run proves the stop condition: a policy that never resolves
     is capped at 3 iterations and forced to ESCALATE, not left to loop
     forever.
"""

import asyncio
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402
import pathlib  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("fl04.agent_loop_test")

STAGING = "/home/claude/fl04-mcp-integration/staging"
ENTRYPOINT = (
    pathlib.Path("/home/claude/fl04-mcp-integration")
    / "node_modules" / "@modelcontextprotocol" / "server-filesystem" / "dist" / "index.js"
)
DRAFT_PATH = f"{STAGING}/Fintech_2026-07-29.md"

FLAWED_DRAFT = (
    "# Fintech Weekly Brief - Week of July 20, 2026\n\n"
    "Stripe and Advent International are acquiring PayPal for $53B.\n"
)
FIXED_LINE = (
    "Stripe and Advent International reportedly made an unconfirmed "
    "~$53B joint bid for PayPal, per Reuters sourcing.\n"
)


async def scripted_agent_loop(max_iterations: int, always_stuck: bool = False):
    server_params = StdioServerParameters(
        command="node", args=[str(ENTRYPOINT), STAGING], env=None
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            log.info("Session initialized (one session held open for the whole loop).")

            iteration = 0
            verdict = None
            while iteration < max_iterations:
                iteration += 1
                log.info("--- Iteration %d ---", iteration)

                if always_stuck:
                    # SCRIPTED: policy that deliberately never resolves,
                    # to prove the stop condition works.
                    log.info("[SCRIPTED DECISION] re-reading file, never satisfied")
                    result = await session.call_tool(
                        "read_text_file", {"path": DRAFT_PATH}
                    )
                    _ = result.content[0].text
                    continue

                if iteration == 1:
                    log.info(
                        "[SCRIPTED DECISION] overconfident claim detected -> "
                        "call edit_file"
                    )
                    result = await session.call_tool(
                        "edit_file",
                        {
                            "path": DRAFT_PATH,
                            "edits": [
                                {
                                    "oldText": "Stripe and Advent International are acquiring PayPal for $53B.\n",
                                    "newText": FIXED_LINE,
                                }
                            ],
                        },
                    )
                    log.info("Real tool result (diff): %s", result.content[0].text[:200])

                elif iteration == 2:
                    log.info(
                        "[SCRIPTED DECISION] verify the edit landed -> call get_file_info"
                    )
                    result = await session.call_tool(
                        "get_file_info", {"path": DRAFT_PATH}
                    )
                    log.info("Real tool result: %s", result.content[0].text.replace("\n", " | "))

                elif iteration == 3:
                    log.info(
                        "[SCRIPTED DECISION] re-read to confirm fix is present -> "
                        "call read_text_file, then emit verdict"
                    )
                    result = await session.call_tool(
                        "read_text_file", {"path": DRAFT_PATH}
                    )
                    current_text = result.content[0].text
                    if "reportedly" in current_text and "unconfirmed" in current_text:
                        verdict = "APPROVE"
                    break

            if verdict is None:
                verdict = "ESCALATE"

            log.info("LOOP TERMINATED after %d iteration(s). Verdict: %s", iteration, verdict)
            return iteration, verdict


async def main():
    os.makedirs(STAGING, exist_ok=True)
    with open(DRAFT_PATH, "w") as f:
        f.write(FLAWED_DRAFT)
    print("=== RUN 1: normal resolution path (max_iterations=3) ===")
    iters, verdict = await scripted_agent_loop(max_iterations=3, always_stuck=False)
    print(f"RESULT: {iters} iteration(s), verdict={verdict}")

    with open(DRAFT_PATH) as f:
        on_disk = f.read()
    print("--- Independent check: real file content on disk after the loop ---")
    print(on_disk)
    assert "reportedly" in on_disk and "unconfirmed" in on_disk, "Edit did not actually land on disk"
    print("CONFIRMED: edit_file's change is really on disk, not just claimed.")

    print()
    print("=== RUN 2: stop-condition test (policy that never resolves) ===")
    with open(DRAFT_PATH, "w") as f:
        f.write(FLAWED_DRAFT)
    iters, verdict = await scripted_agent_loop(max_iterations=3, always_stuck=True)
    print(f"RESULT: {iters} iteration(s), verdict={verdict}")
    assert iters == 3 and verdict == "ESCALATE", "Stop condition failed"
    print("CONFIRMED: loop was capped at Max Iterations=3 and forced to ESCALATE.")


if __name__ == "__main__":
    asyncio.run(main())
