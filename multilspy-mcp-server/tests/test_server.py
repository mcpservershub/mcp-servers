#!/usr/bin/env python
"""
Simple test script to verify the MCP server implementation.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from multilspy_mcp.models import (
    NavigationRequest, CompletionRequest, 
    DocumentSymbolRequest, HoverRequest,
    WorkspaceSymbolRequest
)
from multilspy_mcp.lsp_manager import LSPManager


def test_models():
    """Test Pydantic models."""
    print("Testing Pydantic models...")
    
    # Test NavigationRequest
    nav_req = NavigationRequest(
        file_path="test.py",
        line=10,
        column=5,
        language="python"
    )
    assert nav_req.file_path == "test.py"
    assert nav_req.line == 10
    print("✓ NavigationRequest model works")
    
    # Test CompletionRequest
    comp_req = CompletionRequest(
        file_path="test.py",
        line=20,
        column=10,
        allow_incomplete=True
    )
    assert comp_req.allow_incomplete == True
    print("✓ CompletionRequest model works")
    
    print("All model tests passed!\n")


def test_lsp_manager():
    """Test LSP Manager basic functionality."""
    print("Testing LSP Manager...")
    
    # Create test workspace
    workspace = Path.cwd()
    manager = LSPManager(str(workspace))
    
    # Test language detection
    lang = manager.detect_language("test.py")
    assert lang is not None
    print(f"✓ Language detection works: test.py -> {lang}")
    
    # Test session management
    manager.save_session()
    print(f"✓ Session saved to: {manager.session_file}")
    
    # Test cleanup
    manager.cleanup()
    print("✓ Cleanup successful")
    
    print("LSP Manager tests passed!\n")


async def test_mcp_tools():
    """Test MCP tools (requires server to be running)."""
    print("Testing MCP tools...")
    print("Note: This requires the MCP server to be running")
    
    try:
        from multilspy_mcp import server
        
        # Initialize workspace
        result = server.initialize_workspace(
            workspace_root=str(Path.cwd()),
            cache_dir=None
        )
        assert result["success"]
        print("✓ Workspace initialization works")
        
        # Test language detection
        result = server.detect_file_language(
            file_path="test.py"
        )
        print(f"✓ Language detection: {result}")
        
        print("MCP tools tests passed!\n")
        
    except Exception as e:
        print(f"⚠ MCP tools test failed: {e}")
        print("Make sure the server dependencies are installed\n")


def main():
    """Run all tests."""
    print("=" * 50)
    print("MultilsPy MCP Server Test Suite")
    print("=" * 50 + "\n")
    
    # Test models
    test_models()
    
    # Test LSP Manager
    try:
        test_lsp_manager()
    except Exception as e:
        print(f"⚠ LSP Manager test failed: {e}\n")
    
    # Test MCP tools
    asyncio.run(test_mcp_tools())
    
    print("=" * 50)
    print("Test suite completed!")
    print("=" * 50)


if __name__ == "__main__":
    main()