#!/bin/bash
# Script to test the MCP server with MCP Inspector

set -e

echo "Testing Universal CTags MCP Server with MCP Inspector..."

# Check if MCP Inspector is installed
if ! command -v mcp-inspector &> /dev/null; then
    echo "MCP Inspector not found. Installing..."
    npm install -g @modelcontextprotocol/inspector
fi

# Check if ctags is installed
if ! command -v ctags &> /dev/null; then
    echo "Universal CTags not found. Please run: ./scripts/install_ctags.sh"
    exit 1
fi

# Install Python dependencies if needed
if ! python -c "import ctags_mcp" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -e .
fi

# Generate sample tags file for testing
echo "Generating sample tags file..."
ctags -R -f tests/fixtures/sample_code/tags tests/fixtures/sample_code/

# Start the MCP server in background
echo "Starting MCP server..."
python -m ctags_mcp.server &
SERVER_PID=$!

# Wait for server to start
sleep 3

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    kill $SERVER_PID 2>/dev/null || true
}
trap cleanup EXIT

echo "MCP Server started with PID: $SERVER_PID"
echo "Opening MCP Inspector..."
echo ""
echo "You can test the following tools in the Inspector:"
echo "  - generate_tags: Generate tags for a directory"
echo "  - find_symbol: Search for symbols"
echo "  - go_to_definition: Navigate to symbol definitions"
echo "  - list_symbols_in_file: List symbols in a file"
echo "  - get_file_outline: Get file structure"
echo ""
echo "Example test commands:"
echo '  generate_tags(path="tests/fixtures/sample_code", output_file="test.tags")'
echo '  find_symbol(symbol_name="DatabaseConnection", tags_file="test.tags")'
echo '  go_to_definition(symbol_name="main", tags_file="test.tags")'
echo ""

# Open MCP Inspector
mcp-inspector --url http://localhost:3000

# Keep server running until user exits
echo "Press Ctrl+C to stop the server..."
wait $SERVER_PID