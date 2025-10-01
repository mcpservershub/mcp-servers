#!/bin/bash

# Dependency Check MCP Server Runner for MCP Inspector
# This script runs the container with proper user permissions

echo "Starting Dependency Check MCP Server..."

# Create output directory if it doesn't exist
mkdir -p output

# Run with current user permissions to avoid root-owned files
docker run -it --rm \
  --user $(id -u):$(id -g) \
  -v dependency-check_dependency-check-data:/data/dependency-check \
  -v $(pwd):/workspace:ro \
  -v $(pwd)/output:/output \
  -e DEPENDENCY_CHECK_DATA=/data/dependency-check \
  -e DISABLE_AUTO_UPDATE=false \
  -e JAVA_OPTS="-Xmx4G" \
  -e HOME=/tmp \
  dependency-check-mcp:fixed3