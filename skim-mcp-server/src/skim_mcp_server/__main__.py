"""
Entry point for running the skim MCP server as a module.

Usage:
    python -m skim_mcp_server.server
"""

from .server import main

if __name__ == "__main__":
    main()