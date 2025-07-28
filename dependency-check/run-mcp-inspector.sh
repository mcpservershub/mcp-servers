#!/bin/bash

echo "=== Dependency Check MCP Server for MCP Inspector ==="
echo
echo "This script shows how to run the MCP server with MCP Inspector"
echo

# Create necessary directories
mkdir -p output workspace

echo "1. First, ensure you have MCP Inspector installed:"
echo "   npm install -g @modelcontextprotocol/inspector"
echo

echo "2. Run the MCP server container with this command:"
echo
echo "docker run -it --rm \\"
echo "  -v dependency-check_dependency-check-data:/data/dependency-check \\"
echo "  -v \$(pwd):/workspace:ro \\"
echo "  -v \$(pwd)/output:/output \\"
echo "  -e DEPENDENCY_CHECK_DATA=/data/dependency-check \\"
echo "  -e DISABLE_AUTO_UPDATE=false \\"
echo "  -e JAVA_OPTS=\"-Xmx4G\" \\"
echo "  dependency-check-mcp:fixed2"
echo

echo "3. In another terminal, run MCP Inspector:"
echo "   mcp-inspector"
echo

echo "4. In MCP Inspector:"
echo "   - Select 'Add Server'"
echo "   - Transport: stdio"
echo "   - Command: Copy the docker run command above"
echo

echo "5. Available tools and example parameters:"
echo
echo "scan_project:"
echo "{"
echo '  "path": "/workspace",  // The mounted project directory'
echo '  "output_file": "/output/dependency-check-report.json",'
echo '  "output_format": "JSON",'
echo '  "exclude_patterns": ["**/node_modules/**", "**/test/**"],'
echo '  "enable_experimental": false'
echo "}"
echo
echo "update_database:"
echo "{"
echo '  "data_directory": "/data/dependency-check"'
echo "}"
echo
echo "get_scan_summary:"
echo "{"
echo '  "report_path": "/output/dependency-check-report.json"'
echo "}"
echo

echo "IMPORTANT NOTES:"
echo "- First scan may take 5-10 minutes if database needs updating"
echo "- Increase timeout in MCP Inspector settings (10-15 minutes recommended)"
echo "- The /workspace path maps to your current directory"
echo "- Scan results will be saved to ./output/"
echo

echo "To test if the container works, run this test command:"
echo "docker run --rm -v \$(pwd):/workspace:ro dependency-check-mcp:fixed2 ls -la /workspace"