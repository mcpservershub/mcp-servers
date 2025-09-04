"""Main entry point for running the MCP server"""

import asyncio
from .server import mcp

def main():
    """Run the MCP server via stdio"""
    # FastMCP has a run() method for stdio mode
    mcp.run()

if __name__ == "__main__":
    main()