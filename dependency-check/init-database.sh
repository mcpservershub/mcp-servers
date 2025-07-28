#!/bin/bash

echo "=== Dependency Check Database Initialization ==="
echo
echo "This script pre-downloads the vulnerability database to prevent timeouts."
echo "This only needs to be run once."
echo

echo "Downloading vulnerability database (this may take 5-30 minutes)..."

docker run --rm \
  -v dependency-check_dependency-check-data:/data/dependency-check \
  -e DEPENDENCY_CHECK_DATA=/data/dependency-check \
  santoshkal/dependency-check-mcp:cgr \
  /opt/dependency-check/bin/dependency-check.sh \
    --updateonly \
    --data /data/dependency-check

if [ $? -eq 0 ]; then
    echo
    echo "Database initialization complete!"
    echo "You can now use the MCP server without timeout issues."
else
    echo
    echo "Database initialization failed. Please check the error messages above."
fi