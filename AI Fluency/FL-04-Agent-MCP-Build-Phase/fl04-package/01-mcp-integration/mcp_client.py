"""
FL-04 MCP Client — Filesystem MCP Server Integration
-----------------------------------------------------
Connects to the official @modelcontextprotocol/server-filesystem MCP server
over stdio, discovers its tools, and demonstrates real tool calls against
the FL-04 project directory.

This is the MCP CLIENT half of the integration. The MCP SERVER
(@modelcontextprotocol/server-filesystem) is a separate process, started
automatically by this script via stdio transport (the standard way MCP
clients launch local MCP servers).

Usage:
    python mcp_client.py <command> [args...]

Commands:
    list-tools                  Discover available tools on the server
    list-dir <path>              Call the list_directory tool
    read-file <path>             Call the read_text_file tool
    file-info <path>             Call the get_file_info tool
    write-file <path> <content>  Call the write_file tool (used to verify the
                                  same operation the n8n "MCP: Stage Report"
                                  node performs in Part 3)

Configuration (env vars, see .env.example):
    MCP_FS_ROOT   - Root directory the filesystem MCP server is allowed
                    to access (least-privilege boundary). Defaults to
                    the FL-04 project directory.
"""

import asyncio
import logging
import os
import pathlib
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("fl04.mcp_client")

# Least-privilege boundary: the server can ONLY see this directory tree.
MCP_FS_ROOT = os.environ.get("MCP_FS_ROOT", "/mnt/project")

# Direct path to the locally installed server entrypoint. We invoke this
# with `node` directly (instead of `npx ... `) because `npx`/`npm exec`
# spawns an extra wrapper process that can be left orphaned if the parent
# is ever killed on a timeout, leaving stray processes holding the stdio
# pipes open.
_SERVER_ENTRYPOINT = (
    pathlib.Path(__file__).parent
    / "node_modules"
    / "@modelcontextprotocol"
    / "server-filesystem"
    / "dist"
    / "index.js"
)


def _server_params() -> StdioServerParameters:
    """Build the stdio launch parameters for the filesystem MCP server."""
    return StdioServerParameters(
        command="node",
        args=[str(_SERVER_ENTRYPOINT), MCP_FS_ROOT],
        env=None,
    )


async def _run(command: str, arg: str | None) -> None:
    log.info("Launching filesystem MCP server scoped to: %s", MCP_FS_ROOT)

    try:
        async with stdio_client(_server_params()) as (read, write):
            async with ClientSession(read, write) as session:
                log.info("Initializing MCP session...")
                await session.initialize()
                log.info("MCP session initialized successfully.")

                if command == "list-tools":
                    tools = await session.list_tools()
                    log.info("Discovered %d tool(s):", len(tools.tools))
                    for t in tools.tools:
                        print(f"  - {t.name}: {t.description}")
                    return

                if command == "list-dir":
                    target = arg or MCP_FS_ROOT
                    log.info("Calling tool 'list_directory' on: %s", target)
                    result = await session.call_tool(
                        "list_directory", {"path": target}
                    )
                    for block in result.content:
                        print(getattr(block, "text", block))
                    return

                if command == "read-file":
                    if not arg:
                        raise ValueError("read-file requires a file path argument")
                    log.info("Calling tool 'read_text_file' on: %s", arg)
                    result = await session.call_tool(
                        "read_text_file", {"path": arg}
                    )
                    for block in result.content:
                        print(getattr(block, "text", block))
                    return

                if command == "file-info":
                    if not arg:
                        raise ValueError("file-info requires a file path argument")
                    log.info("Calling tool 'get_file_info' on: %s", arg)
                    result = await session.call_tool(
                        "get_file_info", {"path": arg}
                    )
                    for block in result.content:
                        print(getattr(block, "text", block))
                    return

                if command == "write-file":
                    if not arg:
                        raise ValueError("write-file requires a file path argument")
                    content = sys.argv[3] if len(sys.argv) > 3 else ""
                    log.info("Calling tool 'write_file' on: %s", arg)
                    result = await session.call_tool(
                        "write_file", {"path": arg, "content": content}
                    )
                    for block in result.content:
                        print(getattr(block, "text", block))
                    return

                raise ValueError(f"Unknown command: {command}")

    except Exception:
        log.exception("MCP client operation failed")
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else None
    asyncio.run(_run(command, arg))


if __name__ == "__main__":
    main()
