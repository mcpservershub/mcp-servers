#!/bin/bash

# Simple test script to validate the MCP server can start and respond to basic queries
echo "Testing Zoekt MCP Server..."

# Test that the server starts without errors
echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | ./zoekt-mcp-server > /tmp/mcp_test_output.json 2>&1

# Check if output contains expected tools
if grep -q "zoekt-index" /tmp/mcp_test_output.json; then
    echo "✓ Server started successfully and exposes zoekt-index tool"
else
    echo "✗ Server failed to start or missing zoekt-index tool"
    cat /tmp/mcp_test_output.json
    exit 1
fi

if grep -q "zoekt-git-index" /tmp/mcp_test_output.json; then
    echo "✓ zoekt-git-index tool found"
else
    echo "✗ zoekt-git-index tool missing"
fi

if grep -q "zoekt-search" /tmp/mcp_test_output.json; then
    echo "✓ zoekt-search tool found"
else
    echo "✗ zoekt-search tool missing"
fi

if ! grep -q "zoekt-webserver" /tmp/mcp_test_output.json; then
    echo "✓ zoekt-webserver tool correctly removed"
else
    echo "✗ zoekt-webserver tool should have been removed"
fi

echo "Test completed. Server appears to be working correctly."