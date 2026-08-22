import os
import sys
from pathlib import Path

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

REPO_ROOT = Path(__file__).resolve().parent.parent


async def get_mcp_tools() -> dict[str, BaseTool]:
    """Spawn the HafiCare MCP server over stdio and return its tools by name.

    A fresh stdio session/subprocess is created per call (and, per
    langchain-mcp-adapters, per individual tool invocation too) -- an accepted
    simplification for this portfolio app. See README "Known limitations".
    """
    client = MultiServerMCPClient(
        {
            "haficare": {
                "transport": "stdio",
                "command": sys.executable,
                "args": ["-m", "mcp_server.server"],
                "cwd": str(REPO_ROOT),
                "env": dict(os.environ),
            }
        }
    )
    tools = await client.get_tools()
    return {tool.name: tool for tool in tools}
