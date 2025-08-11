#!/bin/bash
# Setup script for Hurl MCP Server

set -e

echo "Setting up Hurl MCP Server..."

# Create virtual environment
echo "Creating Python virtual environment..."
python3.12 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package in development mode
echo "Installing hurl-mcp-server..."
pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev]"

echo "Setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run the MCP server:"
echo "  python -m hurl_mcp.server"
echo ""
echo "To run tests:"
echo "  pytest"