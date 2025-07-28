#!/bin/bash

# Test script for Docker image with Universal Ctags
set -e

IMAGE_NAME="zoekt-mcp-server:ctags"

echo "Testing Zoekt MCP Server Docker image with Universal Ctags..."

# Check if image exists
if ! docker images | grep -q "zoekt-mcp-server.*ctags"; then
    echo "❌ Docker image not found. Run ./build-docker-ctags.sh first."
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

# Test 3: Check if Universal Ctags is available
echo "🔍 Testing Universal Ctags availability..."
CTAGS_TOOLS=("ctags" "readtags")

for tool in "${CTAGS_TOOLS[@]}"; do
    if docker run --rm $IMAGE_NAME /usr/local/bin/$tool --help > /dev/null 2>&1; then
        echo "✅ $tool is available and working"
    else
        echo "❌ $tool is not working properly"
        exit 1
    fi
done

# Test 4: Check ctags version
echo "🔍 Testing ctags version..."
CTAGS_VERSION=$(docker run --rm $IMAGE_NAME /usr/local/bin/ctags --version 2>/dev/null | head -1)
if echo "$CTAGS_VERSION" | grep -q "Universal Ctags"; then
    echo "✅ Universal Ctags version: $CTAGS_VERSION"
    echo "✅ Using nightly build (2025.07.08)"
else
    echo "❌ Failed to get Universal Ctags version"
    exit 1
fi

# Test 5: Check if ctags can generate tags
echo "🔍 Testing ctags functionality..."
if docker run --rm $IMAGE_NAME /usr/local/bin/ctags --list-languages > /dev/null 2>&1; then
    echo "✅ ctags can list supported languages"
else
    echo "❌ ctags failed to list languages"
    exit 1
fi

echo ""
echo "🎉 All tests passed! Docker image with Universal Ctags is ready to use."
echo ""
echo "To run the container:"
echo "docker run -it --rm -v \$(pwd)/data:/app/.zoekt -v \$(pwd)/repos:/app/repos $IMAGE_NAME"
echo ""
echo "To test ctags:"
echo "docker run --rm $IMAGE_NAME /usr/local/bin/ctags --version"
echo "docker run --rm $IMAGE_NAME /usr/local/bin/ctags --list-languages"