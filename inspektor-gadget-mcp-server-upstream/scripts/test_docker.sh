#!/bin/bash
# Test the Docker container

set -e

echo "Testing Inspektor-Gadget MCP Server Docker Container"
echo "===================================================="

# Test 1: Check ig binary
echo -n "1. Testing ig binary installation... "
if docker run --rm --entrypoint ig inspektor-gadget-mcp:latest version > /dev/null 2>&1; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    exit 1
fi

# Test 2: Test MCP server can be imported
echo -n "2. Testing MCP server import... "
if docker run --rm --entrypoint python inspektor-gadget-mcp:latest -c "from inspektor_mcp.server import mcp; print('OK')" 2>/dev/null | grep -q "OK"; then
    echo "✅ PASSED"
else
    echo "❌ FAILED"
    exit 1
fi

# Test 3: Test privileged container command
echo "3. Testing privileged container command (will fail without privileges):"
echo "   docker run --rm --privileged inspektor-gadget-mcp:latest"
echo "   Note: This requires --privileged flag for eBPF operations"

echo ""
echo "===================================================="
echo "Basic tests completed successfully!"
echo ""
echo "To run the MCP server with full capabilities, use:"
echo ""
echo "docker run --rm -i \\"
echo "  --privileged \\"
echo "  --pid=host \\"
echo "  --network=host \\"
echo "  -v /sys/kernel/debug:/sys/kernel/debug:ro \\"
echo "  -v /sys/fs/bpf:/sys/fs/bpf:rw \\"
echo "  -v /sys/fs/cgroup:/sys/fs/cgroup:ro \\"
echo "  -v /proc:/host/proc:ro \\"
echo "  -v /var/run/docker.sock:/var/run/docker.sock:ro \\"
echo "  inspektor-gadget-mcp:latest"