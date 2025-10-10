#!/bin/bash
# Comprehensive LocAgent MCP Server Runner

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}LocAgent MCP Server Setup${NC}"

# Function to print status
print_status() {
    echo -e "${YELLOW}==> $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Set up LocAgent required environment variables
print_status "Setting up LocAgent environment variables"
export GRAPH_INDEX_DIR="$PROJECT_ROOT/graph_index"
export BM25_INDEX_DIR="$PROJECT_ROOT/bm25_index"

# Create index directories if they don't exist
mkdir -p "$GRAPH_INDEX_DIR"
mkdir -p "$BM25_INDEX_DIR"

echo "GRAPH_INDEX_DIR: $GRAPH_INDEX_DIR"
echo "BM25_INDEX_DIR: $BM25_INDEX_DIR"

# Check Python version
print_status "Checking Python version"
if ! python3.12 --version &> /dev/null; then
    print_error "python3.12 is not available. Please install Python 3.12"
    exit 1
fi
print_success "Python 3.12 found"

# Set up virtual environment
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    print_status "Creating virtual environment with python3.12"
    python3.12 -m venv "$VENV_DIR"
fi

# Activate virtual environment
print_status "Activating virtual environment"
source "$VENV_DIR/bin/activate"

# Upgrade pip
print_status "Upgrading pip"
python -m pip install --upgrade pip

# Install dependencies
print_status "Installing dependencies from main requirements.txt"
if [ -f "$PROJECT_ROOT/requirements.txt" ]; then
    pip install -r "$PROJECT_ROOT/requirements.txt"
else
    print_error "requirements.txt not found in $PROJECT_ROOT"
    exit 1
fi

# Install MCP Server in development mode
print_status "Installing MCP Server in development mode"
cd "$SCRIPT_DIR"
pip install -e .

# Verify environment setup
print_status "Verifying LocAgent environment"
python3 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_ROOT')

# Check environment variables
assert os.environ.get('GRAPH_INDEX_DIR'), 'GRAPH_INDEX_DIR not set'
assert os.environ.get('BM25_INDEX_DIR'), 'BM25_INDEX_DIR not set'

# Test LocAgent imports
try:
    from plugins.location_tools.utils.util import GRAPH_INDEX_DIR, BM25_INDEX_DIR
    print('✓ LocAgent modules import successfully')
    print(f'  GRAPH_INDEX_DIR: {GRAPH_INDEX_DIR}')
    print(f'  BM25_INDEX_DIR: {BM25_INDEX_DIR}')
except Exception as e:
    print(f'✗ LocAgent import failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    print_success "Environment verification successful"
else
    print_error "Environment verification failed"
    exit 1
fi

# Run the server
print_status "Starting LocAgent MCP Server"
echo -e "${GREEN}Server is running. Press Ctrl+C to stop.${NC}"
echo -e "${YELLOW}Environment:${NC}"
# echo -e "  GRAPH_INDEX_DIR: $GRAPH_INDEX_DIR"
# echo -e "  BM25_INDEX_DIR: $BM25_INDEX_DIR"
# echo ""

# Pass any command line arguments to the server
locagent-mcp-server "$@"
