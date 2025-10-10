#!/bin/bash

# Complete Workflow Test Script for Qdrant MCP Server
# This script runs through the entire workflow automatically

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_step() {
    echo -e "\n${BLUE}═══ $1 ═══${NC}"
}

# Header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║   Qdrant MCP Server Complete Workflow Test  ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Check Prerequisites
print_step "Step 1: Checking Prerequisites"

# Check Docker
if command -v docker &> /dev/null; then
    print_status "Docker is installed"
else
    print_error "Docker is not installed"
    exit 1
fi

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_status "Python $PYTHON_VERSION is installed"
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Step 2: Start Qdrant
print_step "Step 2: Starting Qdrant Vector Database"

# Check if Qdrant is already running
if docker ps | grep -q qdrant-local; then
    print_info "Qdrant is already running"
else
    print_info "Starting Qdrant container..."
    docker-compose up -d
    
    # Wait for Qdrant to be ready
    print_info "Waiting for Qdrant to be ready..."
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:6333/health > /dev/null 2>&1; then
            print_status "Qdrant is ready!"
            break
        fi
        sleep 1
        attempt=$((attempt + 1))
        echo -n "."
    done
    echo ""
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Qdrant failed to start"
        exit 1
    fi
fi

# Display Qdrant info
QDRANT_VERSION=$(curl -s http://localhost:6333 | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))" 2>/dev/null || echo "unknown")
print_info "Qdrant Dashboard: http://localhost:6333/dashboard"
print_info "Qdrant Version: $QDRANT_VERSION"

# Step 3: Install Dependencies
print_step "Step 3: Installing Python Dependencies"

print_info "Installing required packages..."
pip install -q qdrant-client sentence-transformers mcp requests 2>/dev/null || {
    print_error "Failed to install dependencies"
    print_info "Try: pip install qdrant-client sentence-transformers mcp requests"
    exit 1
}
print_status "Dependencies installed"

# Step 4: Load Mock Data
print_step "Step 4: Loading Mock Data into Qdrant"

if [ -f "load_mock_data_client.py" ]; then
    print_info "Running mock data loader..."
    python3 load_mock_data_client.py --skip-search 2>/dev/null || {
        print_error "Failed to load mock data"
        exit 1
    }
    print_status "Mock data loaded successfully"
else
    print_error "Mock data loader script not found"
    exit 1
fi

# Step 5: Test MCP Server Connection
print_step "Step 5: Testing MCP Server"

# First, check if MCP server can be started
print_info "Checking MCP server availability..."
if command -v uvx &> /dev/null; then
    print_status "uvx is available"
else
    print_info "Installing uvx..."
    pip install -q uv uvx
fi

# Test MCP tools availability
print_info "Testing MCP server tools..."
TOOLS_TEST=$(echo '{"jsonrpc": "2.0", "method": "tools/list", "id": 1}' | \
    QDRANT_URL="http://localhost:6333" COLLECTION_NAME="test-collection" \
    timeout 5 uvx mcp-server-qdrant 2>/dev/null | grep -c "qdrant" || echo "0")

if [ "$TOOLS_TEST" -gt "0" ]; then
    print_status "MCP Server tools are available"
else
    print_error "MCP Server tools not responding properly"
    print_info "You may need to install: pip install mcp-server-qdrant"
fi

# Step 6: Run Python MCP Client Tests (if available)
print_step "Step 6: Testing MCP Client Interaction"

if [ -f "mcp_client_test.py" ]; then
    print_info "Running MCP client tests..."
    print_info "This will:"
    print_info "  1. Search existing mock data"
    print_info "  2. Store new information"
    print_info "  3. Verify stored data"
    echo ""
    
    # Run the test with timeout
    timeout 30 python3 mcp_client_test.py 2>/dev/null || {
        print_error "MCP client tests failed or timed out"
        print_info "You can run manually: python3 mcp_client_test.py"
    }
else
    print_info "MCP client test script not found"
    print_info "Skipping client tests"
fi

# Step 7: Verify Data in Qdrant
print_step "Step 7: Verifying Data in Qdrant"

# Get collection info
COLLECTION_INFO=$(curl -s http://localhost:6333/collections/test-collection 2>/dev/null)
if [ $? -eq 0 ]; then
    POINT_COUNT=$(echo "$COLLECTION_INFO" | python3 -c "import sys, json; print(json.load(sys.stdin)['result']['points_count'])" 2>/dev/null || echo "0")
    print_status "Collection 'test-collection' has $POINT_COUNT points"
else
    print_error "Could not fetch collection information"
fi

# Final Summary
print_step "Summary"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║         ✅ Workflow Test Complete!          ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
print_info "🚀 Quick Start Commands:"
echo ""
echo "1. Start MCP Server (stdio mode):"
echo "   ${BLUE}QDRANT_URL=\"http://localhost:6333\" COLLECTION_NAME=\"test-collection\" uvx mcp-server-qdrant${NC}"
echo ""
echo "2. Use MCP Inspector:"
echo "   ${BLUE}npx @modelcontextprotocol/inspector uvx mcp-server-qdrant${NC}"
echo ""
echo "3. Run Python client tests:"
echo "   ${BLUE}python3 mcp_client_test.py${NC}"
echo ""
echo "4. View Qdrant Dashboard:"
echo "   ${BLUE}http://localhost:6333/dashboard${NC}"
echo ""
echo "5. Stop Qdrant when done:"
echo "   ${BLUE}docker-compose down${NC}"
echo ""

print_info "📚 For detailed instructions, see COMPLETE_WORKFLOW.md"