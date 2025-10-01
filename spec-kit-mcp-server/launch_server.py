#!/usr/bin/env python3
"""Launcher script for spec-kit MCP server that can be run from any directory."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
server_dir = Path(__file__).parent.absolute()
src_dir = server_dir / "src"
sys.path.insert(0, str(src_dir))

# Set up environment variables
os.environ.setdefault("SPEC_KIT_REPO_PATH", str(server_dir.parent / "spec-kit"))
os.environ.setdefault("SPEC_KIT_TEMPLATES_PATH", str(server_dir.parent / "spec-kit" / "templates"))
os.environ.setdefault("SPEC_KIT_SCRIPTS_PATH", str(server_dir.parent / "spec-kit" / ".specify" / "scripts"))

# Import and run the server
from spec_kit_mcp.server import mcp

if __name__ == "__main__":
    mcp.run()