#!/bin/bash
# Script to run the strace MCP server

echo "Starting strace MCP Server..."
echo "================================"
echo ""
echo "To test with MCP Inspector, run in another terminal:"
echo "  npx @modelcontextprotocol/inspector uv run python -m strace_mcp.server"
echo ""
echo "Or add to your MCP client config:"
echo '  {
    "mcpServers": {
      "strace": {
        "command": "uv",
        "args": ["run", "python", "-m", "strace_mcp.server"],
        "cwd": "'$(pwd)'"
      }
    }
  }'
echo ""
echo "Starting server..."
echo "================================"

uv run python -m strace_mcp.server