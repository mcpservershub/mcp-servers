"""
OneFileLLM MCP Server Entry Point

This module allows the package to be run as:
    python -m onefilellm_mcp
"""

import sys
import logging
from .server import run_server

# Setup root logger for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr
)


def main():
    """Main entry point for the MCP server"""
    try:
        run_server()
    except KeyboardInterrupt:
        logging.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()