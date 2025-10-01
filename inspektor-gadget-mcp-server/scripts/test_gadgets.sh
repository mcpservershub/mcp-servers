#!/bin/bash

# Test script for ig v0.43.0 gadgets
# Run with: sudo ./test_gadgets.sh

set -e

echo "Testing Inspektor Gadget v0.43.0 Commands"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (sudo)"
    exit 1
fi

echo "1. Testing top_process gadget..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 5 --max-entries 10"
ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 5 --max-entries 10
echo ""

echo "2. Testing trace_exec gadget..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5"
ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5
echo ""

echo "3. Testing snapshot_process gadget..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0 -t 2"
ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0 -t 2
echo ""

echo "4. Testing list-containers (direct command)..."
echo "Command: ig list-containers --runtimes docker"
ig list-containers --runtimes docker
echo ""

echo "5. Testing trace_tcp gadget..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 5 --connect-only"
ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 5 --connect-only
echo ""

echo "All tests completed!"
echo ""
echo "To test with a specific container, add: --containername CONTAINER_NAME"
echo "Example: ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5 --containername my-container"