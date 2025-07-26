#!/bin/bash

# Test script for Docker image
set -e

IMAGE_NAME="zoekt-mcp-server:latest"

echo "Testing Zoekt MCP Server Docker image..."

# Check if image exists
if ! docker images | grep -q "zoekt-mcp-server"; then
    echo "❌ Docker image not found. Run ./build-docker.sh first."
    exit 1
fi

echo "✅ Docker image found: $IMAGE_NAME"

# Test 1: Check if MCP server can list tools
echo "🔍 Testing MCP server tool listing..."
TOOLS_OUTPUT=$(echo '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | \
    docker run -i --rm $IMAGE_NAME 2>/dev/null)

if echo "$TOOLS_OUTPUT" | grep -q "zoekt-search"; then
    echo "✅ MCP server responds correctly to tools/list"
else
    echo "❌ MCP server failed to list tools"
    echo "Output: $TOOLS_OUTPUT"
    exit 1
fi

# Test 2: Check if Zoekt CLI tools are available
echo "🔍 Testing Zoekt CLI tools availability..."
CLI_TOOLS=("zoekt" "zoekt-index" "zoekt-git-index" "zoekt-git-clone" "zoekt-mirror-github")

for tool in "${CLI_TOOLS[@]}"; do
    if docker run --rm $IMAGE_NAME /usr/local/bin/$tool --help > /dev/null 2>&1; then
        echo "✅ $tool is available and working"
    else
        echo "❌ $tool is not working properly"
        exit 1
    fi
done

echo ""
echo "🎉 All tests passed! Docker image is ready to use."
echo ""
echo "To run the container:"
echo "docker run -it --rm -v \$(pwd)/data:/app/.zoekt $IMAGE_NAME"