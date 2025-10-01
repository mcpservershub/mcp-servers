#!/bin/bash

# Test script for ig v0.43.0 host monitoring
# Run with: sudo ./test_host_monitoring.sh

set -e

echo "Testing Inspektor Gadget v0.43.0 Host Monitoring"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Error: This script must be run as root (sudo)"
    exit 1
fi

echo "Testing gadgets with --host flag for monitoring the Linux host"
echo ""

echo "1. Testing top_process on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 5 --host --max-entries 10"
ig run ghcr.io/inspektor-gadget/gadget/top_process:v0.43.0 -t 5 --host --max-entries 10
echo ""

echo "2. Testing trace_exec on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5 --host"
ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5 --host
echo ""

echo "3. Testing snapshot_process on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0 -t 2 --host"
ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:v0.43.0 -t 2 --host
echo ""

echo "4. Testing trace_tcp on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 5 --host --connect-only"
ig run ghcr.io/inspektor-gadget/gadget/trace_tcp:v0.43.0 -t 5 --host --connect-only
echo ""

echo "5. Testing top_file on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0 -t 5 --host"
ig run ghcr.io/inspektor-gadget/gadget/top_file:v0.43.0 -t 5 --host
echo ""

echo "6. Testing profile_cpu on HOST..."
echo "Command: ig run ghcr.io/inspektor-gadget/gadget/profile_cpu:v0.43.0 -t 10 --host"
ig run ghcr.io/inspektor-gadget/gadget/profile_cpu:v0.43.0 -t 10 --host
echo ""

echo "All host monitoring tests completed!"
echo ""
echo "To monitor a specific container instead, use: --containername CONTAINER_NAME"
echo "Example: ig run ghcr.io/inspektor-gadget/gadget/trace_exec:v0.43.0 -t 5 --containername my-container"