#!/bin/bash

# Quick Start Script for Qdrant MCP Server
# This script automates the setup and testing process

set -e

echo "🚀 Qdrant MCP Server - Quick Start Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check prerequisites
echo ""
echo "Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_status "All prerequisites are installed"

# Navigate to project directory
cd "$(dirname "$0")"
PROJECT_DIR=$(pwd)
echo ""
print_info "Working directory: $PROJECT_DIR"

# Step 1: Start Qdrant
echo ""
echo "Step 1: Starting Qdrant Vector Database..."
echo "----------------------------------------"

if [ "$(docker ps -q -f name=qdrant-local)" ]; then
    print_info "Qdrant is already running"
else
    docker-compose up -d
    print_status "Qdrant started successfully"
    
    # Wait for Qdrant to be ready
    echo "Waiting for Qdrant to be ready..."
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
    
    if [ $attempt -eq $max_attempts ]; then
        print_error "Qdrant failed to start. Check docker logs."
        exit 1
    fi
fi

# Step 2: Install Python dependencies
echo ""
echo "Step 2: Installing Python dependencies..."
echo "----------------------------------------"

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    print_info "Installing uv package manager..."
    pip install uv
fi

# Install dependencies from requirements.txt
print_info "Installing Python dependencies..."
pip install -q qdrant-client sentence-transformers requests

print_status "Dependencies installed"

# Step 3: Run tests
echo ""
echo "Step 3: Running Qdrant tests..."
echo "----------------------------------------"

python3 test_qdrant_mcp.py

# Step 3.5: Ask about loading mock data
echo ""
echo "Step 3.5: Mock Data Loading"
echo "----------------------------------------"
read -p "Would you like to load mock data for testing? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Loading mock data into Qdrant..."
    python3 load_mock_data_client.py
else
    print_info "Skipping mock data loading"
fi

# Step 4: Display connection info
echo ""
echo "Step 4: Connection Information"
echo "----------------------------------------"
print_info "Qdrant Dashboard: http://localhost:6333/dashboard"
print_info "Qdrant API: http://localhost:6333"
print_info "Collection Name: test-collection"

# Step 5: Show how to start MCP server
echo ""
echo "Step 5: Starting MCP Server"
echo "----------------------------------------"
echo "To start the MCP server, run one of these commands:"
echo ""
echo "Option 1: Using environment variables from .env file:"
echo "  source .env && uvx mcp-server-qdrant"
echo ""
echo "Option 2: Direct command:"
echo "  QDRANT_URL=\"http://localhost:6333\" COLLECTION_NAME=\"test-collection\" uvx mcp-server-qdrant"
echo ""
echo "Option 3: HTTP server mode:"
echo "  QDRANT_URL=\"http://localhost:6333\" COLLECTION_NAME=\"test-collection\" FASTMCP_PORT=8000 uvx mcp-server-qdrant"

# Step 6: Cleanup instructions
echo ""
echo "Cleanup Instructions"
echo "----------------------------------------"
echo "To stop Qdrant:"
echo "  docker-compose down"
echo ""
echo "To remove all data:"
echo "  docker-compose down -v"
echo "  rm -rf qdrant_storage qdrant_snapshots"

echo ""
print_status "Setup complete! Qdrant MCP Server is ready for testing."
echo ""
echo "📚 For detailed instructions, see TESTING_INSTRUCTIONS.md"