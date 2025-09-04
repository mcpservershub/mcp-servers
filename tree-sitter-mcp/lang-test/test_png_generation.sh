#!/bin/sh
# Test PNG generation in container

echo "Testing PNG generation with updated code..."

# Simple test using the MCP tool
cat << 'EOF' > /tmp/test_request.json
{
  "tool": "generate_graph",
  "arguments": {
    "source_code": "function test() { return 42; }",
    "language": "javascript",
    "format": "png",
    "output_file": "/test/output/test_graph.png"
  }
}
EOF

echo "Request:"
cat /tmp/test_request.json

echo -e "\nTesting with docker run..."
docker run -i -v $(pwd):/test tree-sitter-mcp python3.12 -c "
import sys
sys.path.insert(0, '/app/src')
from tree_sitter_mcp.server import generate_graph
import asyncio

async def test():
    result = await generate_graph(
        source_code='function test() { return 42; }',
        language='javascript',
        format='png',
        output_file='/test/output/test_direct.png'
    )
    print('Result:', result)
    return result

result = asyncio.run(test())
print('Success!' if result.get('success') else 'Failed')
"