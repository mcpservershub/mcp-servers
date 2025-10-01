#!/usr/bin/env python
"""
Manual test script for testing MCP server functions directly.
This can be run without MCP Inspector to verify functionality.
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set environment variables
os.environ["WORKSPACE_ROOT"] = str(Path(__file__).parent.parent / "workspace")
os.environ["MCP_LSP_CACHE_DIR"] = "/tmp/mcp-lsp-cache"

# Import server functions
from multilspy_mcp import server

def test_tools():
    """Test MCP tools directly."""
    print("🧪 Manual MCP Server Test")
    print("=" * 50)
    
    # Test 1: Initialize workspace
    print("\n1. Testing workspace initialization...")
    result = server.initialize_workspace(
        workspace_root=os.environ["WORKSPACE_ROOT"]
    )
    print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success']:
        print(f"   Session ID: {result['session_id']}")
    
    # Test 2: Detect language
    print("\n2. Testing language detection...")
    result = server.detect_file_language(
        file_path="examples/example.py"
    )
    print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success']:
        print(f"   Language: {result['language']}")
    
    # Test 3: Get document symbols
    print("\n3. Testing document symbols...")
    try:
        result = server.get_document_symbols(
            file_path="examples/example.py",
            language="python"
        )
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed'}")
        if result.success:
            print(f"   Found {len(result.symbols)} symbols")
            for symbol in result.symbols[:3]:  # Show first 3
                print(f"   - {symbol.name} ({symbol.kind})")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Get hover information
    print("\n4. Testing hover information...")
    try:
        result = server.get_hover_info(
            file_path="examples/example.py",
            line=10,  # Calculator.__init__ method
            column=15,
            language="python"
        )
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed'}")
        if result.success and result.hover:
            content = str(result.hover.contents)[:100]  # First 100 chars
            print(f"   Hover content: {content}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Search workspace
    print("\n5. Testing workspace symbol search...")
    try:
        result = server.search_workspace_symbols(
            query="Calculator",
            language="python",
            limit=5
        )
        print(f"   Result: {'✅ Success' if result.success else '❌ Failed'}")
        if result.success:
            print(f"   Found {len(result.symbols)} matching symbols")
            for symbol in result.symbols:
                print(f"   - {symbol.name}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 6: Save session
    print("\n6. Testing session save...")
    result = server.save_session()
    print(f"   Result: {'✅ Success' if result['success'] else '❌ Failed'}")
    if result['success']:
        print(f"   Session file: {result['session_file']}")
    
    print("\n" + "=" * 50)
    print("✅ Manual test complete!")
    print("\nNext steps:")
    print("1. Run with MCP Inspector: ./start_inspector.sh")
    print("2. Or test in Docker: docker-compose up")


if __name__ == "__main__":
    test_tools()