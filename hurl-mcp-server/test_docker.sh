#!/bin/bash
# Test script for Docker container

echo "Testing Hurl MCP Server Docker container..."

# Test 1: Check if container can start and list tools
echo -e "\n1. Testing MCP server tool listing..."
echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | \
docker run -i --rm hurl-mcp-server 2>/dev/null | \
jq -r '.result.tools[] | .name' | head -5

# Test 2: Test if hurl is available in container
echo -e "\n2. Testing Hurl availability in container..."
docker run --rm hurl-mcp-server hurl --version

echo -e "\nDocker tests completed!"