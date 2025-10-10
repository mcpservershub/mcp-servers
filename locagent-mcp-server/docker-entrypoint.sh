#!/bin/sh
set -e

# Set environment variables
export PYTHONPATH="/app/src:/app"
export PYTHONUNBUFFERED=1
export GRAPH_INDEX_DIR="/app/graph_index"
export BM25_INDEX_DIR="/app/bm25_index"

# Create required directories
mkdir -p "$GRAPH_INDEX_DIR" "$BM25_INDEX_DIR"

# Run the MCP server using the virtual environment
exec /app/venv/bin/python -m mcp_server.main "$@"