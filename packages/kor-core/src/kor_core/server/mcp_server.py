"""
KOR MCP Server

Exposes KOR capabilities as an MCP server, allowing external agents to use KOR tools.
"""

import asyncio
import json
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent
from ..tools import TerminalTool, BrowserTool, ReadFileTool, WriteFileTool, ListDirTool

# Create the MCP server
app = Server("kor-server")

# Define available tools
TOOLS = {
    "terminal": TerminalTool(),
    "browser": BrowserTool(),
    "read_file": ReadFileTool(),
    "write_file": WriteFileTool(),
    "list_dir": ListDirTool(),
}

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Returns the list of available KOR tools."""
    return [
        Tool(
            name="terminal",
            description="Execute a shell command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The command to execute"}
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="browser",
            description="Search the web",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="read_file",
            description="Read a file's contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_dir",
            description="List directory contents",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to directory", "default": "."}
                }
            }
        ),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Executes the requested tool with given arguments."""
    tool = TOOLS.get(name)
    if not tool:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    try:
        result = tool._run(**arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    """Runs the MCP server via stdio."""
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

def run_server():
    """Entry point for running the server."""
    asyncio.run(main())

if __name__ == "__main__":
    run_server()
