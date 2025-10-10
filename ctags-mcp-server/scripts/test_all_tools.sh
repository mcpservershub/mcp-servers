#!/bin/bash
# test_all_tools.sh - Test all MCP tools in container

set -e

echo "==================================="
echo "Universal CTags MCP Server Test Suite"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -f Dockerfile.simple -t ctags-mcp-server . > /dev/null 2>&1
print_status $? "Docker image built"

# Stop any existing container with the same name
docker stop ctags-mcp-test 2>/dev/null || true
docker rm ctags-mcp-test 2>/dev/null || true

# Start container in background
echo -e "${YELLOW}Starting MCP server container...${NC}"
docker run -d --rm \
  -p 3000:3000 \
  -v $(pwd):/workspace \
  --name ctags-mcp-test \
  ctags-mcp-server > /dev/null 2>&1
print_status $? "Container started"

# Wait for server to start
echo "Waiting for server to initialize..."
sleep 5

# Function to test a tool
test_tool() {
    local tool_name=$1
    local json_data=$2
    
    echo -e "\n${YELLOW}Testing: ${tool_name}${NC}"
    
    response=$(curl -s -X POST http://localhost:3000/tool \
        -H "Content-Type: application/json" \
        -d "$json_data" 2>/dev/null || echo '{"error": "Connection failed"}')
    
    if echo "$response" | grep -q "error"; then
        echo -e "${RED}Failed:${NC} $response"
        return 1
    else
        echo -e "${GREEN}Success${NC}"
        echo "Response preview: $(echo "$response" | head -c 200)..."
        return 0
    fi
}

# Test 1: Generate tags
test_tool "generate_tags" '{
    "tool": "generate_tags",
    "arguments": {
        "path": "/workspace/tests/fixtures/sample_code",
        "recursive": true,
        "output_file": "/workspace/test.tags"
    }
}'

# Test 2: Get tags info
test_tool "get_tags_info" '{
    "tool": "get_tags_info",
    "arguments": {
        "tags_file": "/workspace/test.tags"
    }
}'

# Test 3: Find symbol (exact match)
test_tool "find_symbol (exact)" '{
    "tool": "find_symbol",
    "arguments": {
        "symbol_name": "DatabaseConnection",
        "tags_file": "/workspace/test.tags",
        "match_type": "exact"
    }
}'

# Test 4: Find symbol (partial match)
test_tool "find_symbol (partial)" '{
    "tool": "find_symbol",
    "arguments": {
        "symbol_name": "get",
        "tags_file": "/workspace/test.tags",
        "match_type": "partial",
        "limit": 5
    }
}'

# Test 5: Go to definition
test_tool "go_to_definition" '{
    "tool": "go_to_definition",
    "arguments": {
        "symbol_name": "main",
        "tags_file": "/workspace/test.tags"
    }
}'

# Test 6: List symbols in file
test_tool "list_symbols_in_file" '{
    "tool": "list_symbols_in_file",
    "arguments": {
        "file_path": "/workspace/tests/fixtures/sample_code/example.py",
        "tags_file": "/workspace/test.tags",
        "group_by_kind": true
    }
}'

# Test 7: Get file outline
test_tool "get_file_outline" '{
    "tool": "get_file_outline",
    "arguments": {
        "file_path": "/workspace/tests/fixtures/sample_code/example.py",
        "tags_file": "/workspace/test.tags",
        "include_private": false
    }
}'

# Test 8: List tags files
test_tool "list_tags_files" '{
    "tool": "list_tags_files",
    "arguments": {
        "search_path": "/workspace",
        "include_stats": true
    }
}'

# Test 9: Validate tags file
test_tool "validate_tags_file" '{
    "tool": "validate_tags_file",
    "arguments": {
        "tags_file": "/workspace/test.tags",
        "check_files_exist": true
    }
}'

# Test 10: Update tags (incremental)
test_tool "update_tags" '{
    "tool": "update_tags",
    "arguments": {
        "tags_file": "/workspace/test.tags",
        "modified_files": ["/workspace/tests/fixtures/sample_code/example.js"]
    }
}'

# Test 11: Find references
test_tool "find_references" '{
    "tool": "find_references",
    "arguments": {
        "symbol_name": "UserModel",
        "tags_file": "/workspace/test.tags"
    }
}'

# Clean up
echo -e "\n${YELLOW}Cleaning up...${NC}"
docker stop ctags-mcp-test > /dev/null 2>&1
print_status $? "Container stopped"

echo -e "\n${GREEN}Testing complete!${NC}"
echo "To run interactive tests with MCP Inspector:"
echo "  1. Start container: docker run -it --rm -p 3000:3000 -v \$(pwd):/workspace ctags-mcp-server"
echo "  2. Run inspector: npx @modelcontextprotocol/inspector test --url http://localhost:3000"