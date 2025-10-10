"""Entry point for spec-kit MCP server."""

import sys
import logging
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent))

from spec_kit_mcp.server import mcp


def main():
    """Main entry point."""
    try:
        # FastMCP handles its own async loop
        mcp.run()
    except KeyboardInterrupt:
        print("\nServer shutdown requested")
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()