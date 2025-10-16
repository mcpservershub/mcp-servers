"""
Main entry point for running the MultilsPy MCP Server.

This module allows the package to be run directly:
    python -m multilspy_mcp
"""

import sys
from .server import main

if __name__ == "__main__":
    sys.exit(main())