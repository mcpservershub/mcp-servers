#!/bin/bash
# Test script for Skim MCP Server tools

echo "=========================================="
echo "Testing Skim MCP Server"
echo "=========================================="
echo ""

# Create test workspace
TEST_DIR=$(mktemp -d)
echo "Created test directory: $TEST_DIR"

# Create test files
mkdir -p "$TEST_DIR/src"
echo "def main():" > "$TEST_DIR/src/main.py"
echo "    print('Hello')" >> "$TEST_DIR/src/main.py"
echo "def helper():" > "$TEST_DIR/src/utils.py"
echo "    pass" >> "$TEST_DIR/src/utils.py"
echo "# README" > "$TEST_DIR/README.md"
echo "function test() {}" > "$TEST_DIR/test.js"

echo "Created test files in $TEST_DIR"
echo ""

# Test 1: fuzzy_filter_lines
echo "=========================================="
echo "Test 1: fuzzy_filter_lines"
echo "=========================================="
cat <<'EOF' | docker run -i --rm skim-mcp-server python -c "
import sys
import json
sys.path.insert(0, '/app/src')
from skim_mcp_server.server import fuzzy_filter_lines

result = fuzzy_filter_lines(
    input_text='apple\nbanana\ncherry\napricot\navocado',
    query='',
    multi=False
)
print(json.dumps(result, indent=2))
"
EOF
echo ""

# Test 2: Check sk command works in container
echo "=========================================="
echo "Test 2: Verify sk command"
echo "=========================================="
docker run --rm --entrypoint sk skim-mcp-server --version
docker run --rm --entrypoint which skim-mcp-server sk
echo ""

# Test 3: Check Python imports
echo "=========================================="
echo "Test 3: Check Python module imports"
echo "=========================================="
docker run --rm skim-mcp-server python -c "
import sys
sys.path.insert(0, '/app/src')
from skim_mcp_server.server import app, check_sk_installed
print('✓ Imports successful')
print(f'✓ sk installed: {check_sk_installed()}')
print(f'✓ MCP app name: {app.name}')
"
echo ""

# Test 4: Test fuzzy_find_files with mounted directory
echo "=========================================="
echo "Test 4: fuzzy_find_files (with test directory)"
echo "=========================================="
docker run -i --rm -v "$TEST_DIR:/workspace" skim-mcp-server python -c "
import sys
import json
sys.path.insert(0, '/app/src')
from skim_mcp_server.server import fuzzy_find_files

result = fuzzy_find_files(
    directory='/workspace',
    query='',
    preview=False,
    multi=False
)
print('Result keys:', list(result.keys()))
print('Success:', result.get('success'))
print('Exit code:', result.get('exit_code'))
if result.get('error'):
    print('Error:', result.get('error'))
"
echo ""

# Test 5: Test fuzzy_search_content
echo "=========================================="
echo "Test 5: fuzzy_search_content"
echo "=========================================="
docker run -i --rm -v "$TEST_DIR:/workspace" skim-mcp-server python -c "
import sys
import json
sys.path.insert(0, '/app/src')
from skim_mcp_server.server import fuzzy_search_content

result = fuzzy_search_content(
    directory='/workspace',
    query='',
    preview=False,
    multi=False
)
print('Result keys:', list(result.keys()))
print('Success:', result.get('success'))
print('Exit code:', result.get('exit_code'))
if result.get('error'):
    print('Error:', result.get('error'))
"
echo ""

# Test 6: List all available tools
echo "=========================================="
echo "Test 6: List MCP Tools"
echo "=========================================="
docker run --rm skim-mcp-server python -c "
import sys
sys.path.insert(0, '/app/src')
from skim_mcp_server.server import app

print('Available MCP Tools:')
for tool in app._tool_manager.list_tools():
    print(f'  - {tool.name}')
    if tool.description:
        desc = tool.description.split('\n')[0][:60]
        print(f'    {desc}...')
"
echo ""

# Test 7: Test with ripgrep availability
echo "=========================================="
echo "Test 7: Check tool dependencies"
echo "=========================================="
docker run --rm skim-mcp-server sh -c "
echo 'Checking installed tools:'
echo -n '  sk: ' && which sk && sk --version
echo -n '  fd: ' && which fd && fd --version | head -1
echo -n '  rg: ' && which rg && rg --version | head -1
echo -n '  bat: ' && which bat && bat --version
echo -n '  git: ' && which git && git --version
"
echo ""

# Cleanup
echo "=========================================="
echo "Cleaning up test directory: $TEST_DIR"
rm -rf "$TEST_DIR"
echo "=========================================="
echo "All tests completed!"
echo "=========================================="