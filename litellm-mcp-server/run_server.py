#!/usr/bin/env python3
"""Run the LiteLLM MCP Server."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from litellm_mcp.server import create_server

if __name__ == "__main__":
    server = create_server()
    server.run(transport="stdio")