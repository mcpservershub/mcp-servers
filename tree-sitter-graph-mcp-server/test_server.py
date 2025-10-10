#!/usr/bin/env python3
"""Test script for the tree-sitter-graph MCP server."""

import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tree_sitter_graph_mcp.server import tree_sitter_graph

async def test_tree_sitter_graph():
    """Test the tree_sitter_graph tool."""
    print("Testing tree-sitter-graph MCP server...")
    print("-" * 50)
    
    # Test 1: Using actual files
    print("\nTest 1: Using actual file paths")
    result = await tree_sitter_graph(
        tsg_file="examples/js_working.tsg",
        source_file="examples/example.js",
        output_file="test_output.json"
    )
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get("success"):
        print("✓ Test 1 passed: Successfully generated graph from files")
        # Check if output file exists
        if os.path.exists("test_output.json"):
            with open("test_output.json", "r") as f:
                graph_data = json.load(f)
                print(f"  Output file contains {len(graph_data)} graph elements")
    else:
        print(f"✗ Test 1 failed: {result.get('error')}")
    
    print("-" * 50)
    
    # Test 2: Using content strings
    print("\nTest 2: Using content strings with temporary files")
    
    simple_tsg = """
(function_declaration
  name: (identifier) @name) @func
{
  node @func
  attribute @func.label = @name
}
"""
    
    simple_js = """
function hello() {
    console.log("Hello, world!");
}

function goodbye() {
    console.log("Goodbye!");
}
"""
    
    result2 = await tree_sitter_graph(
        tsg_file=simple_tsg,
        source_file=simple_js,
        output_file="test_output2.json",
        create_temp_files=True
    )
    
    print(f"Result: {json.dumps(result2, indent=2)}")
    
    if result2.get("success"):
        print("✓ Test 2 passed: Successfully generated graph from content strings")
        if os.path.exists("test_output2.json"):
            with open("test_output2.json", "r") as f:
                graph_data = json.load(f)
                print(f"  Output file contains {len(graph_data)} graph elements")
    else:
        print(f"✗ Test 2 failed: {result2.get('error')}")
        if "tree-sitter-graph: command not found" in str(result2.get('error', '')):
            print("\n⚠️  tree-sitter-graph CLI is not installed!")
            print("   Install it with: npm install -g @tree-sitter/graph")
            print("   Or: cargo install tree-sitter-graph")
    
    print("-" * 50)
    
    # Clean up test files
    for file in ["test_output.json", "test_output2.json"]:
        if os.path.exists(file):
            os.remove(file)
            print(f"Cleaned up: {file}")

if __name__ == "__main__":
    asyncio.run(test_tree_sitter_graph())