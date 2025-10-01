#!/bin/bash

# Setup script for Inspektor Gadget MCP Server
# This script helps configure the environment for running ig commands

set -e

echo "Inspektor Gadget MCP Server Setup"
echo "=================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Warning: Not running as root. Some operations may require sudo privileges."
    echo "For full functionality, consider running this script with sudo."
    echo ""
fi

# Check if ig is installed
if ! command -v ig &> /dev/null; then
    echo "Error: ig command not found. Please install Inspektor Gadget first."
    echo "Visit: https://www.inspektor-gadget.io/docs/latest/getting-started/install/"
    exit 1
fi

echo "Found ig version: $(ig version)"
echo ""

# Check container runtime
echo "Checking container runtime..."
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
    if docker info &> /dev/null; then
        echo "  Docker daemon is running"
    else
        echo "  Warning: Docker daemon is not accessible. You may need sudo privileges."
    fi
fi

if command -v containerd &> /dev/null; then
    echo "✓ Containerd found"
fi

if command -v crictl &> /dev/null; then
    echo "✓ CRI-CTL found"
fi

echo ""

# Test ig functionality
echo "Testing ig run command..."
echo "Running: ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:latest -t 1"
echo ""

if [ "$EUID" -eq 0 ]; then
    # Running as root, execute directly
    ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:latest -t 1 2>&1 | head -20
else
    # Not root, try with sudo
    echo "Attempting with sudo (you may be prompted for password)..."
    sudo ig run ghcr.io/inspektor-gadget/gadget/snapshot_process:latest -t 1 2>&1 | head -20
fi

echo ""
echo "Setup check complete!"
echo ""
echo "To run the MCP server with proper permissions:"
echo "  sudo python -m inspektor_mcp"
echo ""
echo "Or run in Docker container (recommended):"
echo "  docker build -t inspektor-mcp ."
echo "  docker run --privileged -it inspektor-mcp"
echo ""