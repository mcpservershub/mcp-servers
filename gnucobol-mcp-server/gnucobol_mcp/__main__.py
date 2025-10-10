"""
GnuCOBOL MCP Server - Main Entry Point

This module serves as the entry point for running the MCP server in STDIO mode.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from gnucobol_mcp.server import app


def main():
    """
    Main entry point for the GnuCOBOL MCP server.

    Runs the FastMCP server in STDIO mode for communication with MCP clients.
    """
    try:
        # Run the FastMCP app in STDIO mode
        # This allows the server to communicate via stdin/stdout with MCP clients
        app.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
