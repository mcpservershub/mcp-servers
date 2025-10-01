#!/bin/bash

# Script to install and start MCP Inspector for testing

echo "🔍 MCP Inspector Setup and Launch"
echo "=================================="

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    echo "Please install Node.js 18+ first:"
    echo "  Ubuntu/Debian: sudo apt install nodejs npm"
    echo "  Or visit: https://nodejs.org/"
    exit 1
fi

# Check Node version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${YELLOW}Warning: Node.js version is less than 18${NC}"
    echo "Current version: $(node -v)"
    echo "Recommended: v18 or higher"
fi

# Check if MCP Inspector is installed
if ! command -v mcp-inspector &> /dev/null; then
    echo -e "${YELLOW}MCP Inspector not found. Installing...${NC}"
    npm install -g @modelcontextprotocol/inspector
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install MCP Inspector${NC}"
        echo "Try with sudo: sudo npm install -g @modelcontextprotocol/inspector"
        exit 1
    fi
fi

# Check if virtual environment exists and is activated
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3.12 -m venv .venv
fi

if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source .venv/bin/activate
fi

# Install Python dependencies if needed
if ! python -c "import mcp" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q -e .
fi

# Display available configurations
echo -e "\n${GREEN}Available configurations:${NC}"
echo "1. test_config.json         - Local Python application"
echo "2. docker_test_config.json  - Docker container"
echo "3. mcp_config.json          - Default configuration"

# Ask user which config to use
echo -e "\n${GREEN}Which configuration would you like to use?${NC}"
echo -n "Enter choice (1-3) or config filename [default: 1]: "
read choice

case $choice in
    2)
        CONFIG_FILE="docker_test_config.json"
        echo -e "\n${YELLOW}Note: Make sure Docker is running and the image is built${NC}"
        echo "Build with: docker build -t multilspy-mcp-server:latest ."
        ;;
    3)
        CONFIG_FILE="mcp_config.json"
        ;;
    "")
        CONFIG_FILE="test_config.json"
        ;;
    *)
        if [ -f "$choice" ]; then
            CONFIG_FILE="$choice"
        else
            CONFIG_FILE="test_config.json"
        fi
        ;;
esac

echo -e "\n${GREEN}Starting MCP Inspector with: $CONFIG_FILE${NC}"
echo "=================================="
echo "The inspector will open in your browser at http://localhost:5173"
echo "Press Ctrl+C to stop"
echo ""

# Set environment variables
export WORKSPACE_ROOT="$(pwd)/workspace"
export MCP_LSP_CACHE_DIR="/tmp/mcp-lsp-cache"
export LOG_LEVEL="DEBUG"

# Create workspace directory if it doesn't exist
mkdir -p "$WORKSPACE_ROOT/examples"

# Start MCP Inspector
mcp-inspector "$CONFIG_FILE"