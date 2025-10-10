"""Main entry point for the ripgrep MCP server.

This module allows the package to be run as a module:
    python -m ripgrep_mcp
"""

from .server import main

if __name__ == "__main__":
    main()